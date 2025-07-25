import json
import base64
from typing import List, Dict, Any, Optional
import numpy as np
import cv2
import openai

from agents.base import BaseAgent
from core.models import SubProcessDescription, ReviewFeedback
from core.enums import SubProcess, ReviewStatus
from knowledge.prompts import ReviewerPrompts


class VLMReviewer(BaseAgent):
    """Reviews visual outputs and provides feedback"""
    
    def _initialize(self):
        """Initialize OpenAI client"""
        self.client = openai.OpenAI(api_key=self.api_key)
        self.prompts = ReviewerPrompts()
        self.model = self.config.get('model', 'gpt-4-vision-preview')
        
        # Review configuration
        self.key_frame_count = self.config.get('key_frame_count', 5)
        self.max_image_size = self.config.get('max_image_size', (1024, 1024))
    
    def process(self, sub_process: SubProcessDescription,
                video_frames: List[np.ndarray]) -> ReviewFeedback:
        """Main processing: review visual output"""
        return self.review_output(sub_process, video_frames)
    
    def review_output(self, sub_process: SubProcessDescription,
                     video_frames: List[np.ndarray]) -> ReviewFeedback:
        """Review visual output for a sub-process"""
        
        self.log_info(f"Reviewing output for: {sub_process.process_type.value}")
        
        # Extract and prepare key frames
        key_frames = self._extract_key_frames(video_frames)
        encoded_frames = self._encode_frames(key_frames)
        
        # Get evaluation metrics
        metrics = self._get_evaluation_metrics(sub_process.process_type)
        
        # Build review prompt
        prompt = self.prompts.get_review_prompt(
            sub_process=sub_process,
            metrics=metrics
        )
        
        try:
            # Create message with images
            messages = self._build_review_message(prompt, encoded_frames)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                max_tokens=1000,
                temperature=0.5
            )
            
            review_data = json.loads(response.choices[0].message.content)
            
            # Parse review into feedback object
            feedback = self._parse_review(review_data)
            
            self.log_info(f"Review completed - Status: {feedback.status.value}, Score: {feedback.score}")
            return feedback
            
        except Exception as e:
            self.log_error(f"Failed to review output: {str(e)}")
            # Return failed review
            return ReviewFeedback(
                status=ReviewStatus.FAILED,
                score=0.0,
                issues=[f"Review failed: {str(e)}"],
                suggestions=["Check visual output generation"]
            )
    
    def _extract_key_frames(self, video_frames: List[np.ndarray]) -> List[np.ndarray]:
        """Extract key frames from video for review"""
        if len(video_frames) <= self.key_frame_count:
            return video_frames
        
        # Sample frames evenly throughout the video
        indices = np.linspace(0, len(video_frames) - 1, self.key_frame_count, dtype=int)
        key_frames = [video_frames[i] for i in indices]
        
        # Resize frames if needed
        resized_frames = []
        for frame in key_frames:
            if frame.shape[:2] > self.max_image_size:
                resized = self._resize_frame(frame)
                resized_frames.append(resized)
            else:
                resized_frames.append(frame)
        
        return resized_frames
    
    def _resize_frame(self, frame: np.ndarray) -> np.ndarray:
        """Resize frame while maintaining aspect ratio"""
        h, w = frame.shape[:2]
        max_h, max_w = self.max_image_size
        
        # Calculate scale factor
        scale = min(max_w / w, max_h / h)
        
        if scale < 1:
            new_w = int(w * scale)
            new_h = int(h * scale)
            return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        return frame
    
    def _encode_frames(self, frames: List[np.ndarray]) -> List[str]:
        """Encode frames as base64 for API"""
        encoded_frames = []
        
        for frame in frames:
            # Convert to JPEG
            success, buffer = cv2.imencode('.jpg', frame, 
                                         [cv2.IMWRITE_JPEG_QUALITY, 90])
            if success:
                # Encode to base64
                base64_image = base64.b64encode(buffer).decode('utf-8')
                encoded_frames.append(base64_image)
        
        return encoded_frames
    
    def _build_review_message(self, prompt: str, encoded_frames: List[str]) -> List[Dict]:
        """Build message with text and images for review"""
        content = [{"type": "text", "text": prompt}]
        
        # Add each frame as an image
        for i, frame_base64 in enumerate(encoded_frames):
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{frame_base64}",
                    "detail": "high"
                }
            })
        
        return [{"role": "user", "content": content}]
    
    def _get_evaluation_metrics(self, process_type: SubProcess) -> Dict[str, List[str]]:
        """Get evaluation metrics for each sub-process type"""
        metrics_map = {
            SubProcess.SCENE: {
                "primary": ["asset placement", "scale accuracy", "environment consistency"],
                "secondary": ["texture quality", "lighting integration"]
            },
            SubProcess.CHARACTER: {
                "primary": ["character visibility", "positioning", "scale", "orientation"],
                "secondary": ["rigging quality", "mesh integrity"]
            },
            SubProcess.MOTION: {
                "primary": ["motion smoothness", "trajectory accuracy", "speed consistency"],
                "secondary": ["physics realism", "keyframe timing"]
            },
            SubProcess.LIGHTING: {
                "primary": ["illumination quality", "shadow accuracy", "mood matching"],
                "secondary": ["color temperature", "exposure balance"]
            },
            SubProcess.CINEMATOGRAPHY: {
                "primary": ["framing", "camera movement", "focus", "composition"],
                "secondary": ["motion blur", "depth of field"]
            }
        }
        
        base_metrics = metrics_map.get(process_type, {"primary": [], "secondary": []})
        base_metrics["general"] = ["visual quality", "prompt adherence", "technical correctness"]
        
        return base_metrics
    
    def _parse_review(self, review_data: Dict[str, Any]) -> ReviewFeedback:
        """Parse review JSON into ReviewFeedback object"""
        
        # Determine status
        passed = review_data.get("passed", False)
        score = review_data.get("score", 0.0)
        
        if passed and score >= 0.8:
            status = ReviewStatus.PASSED
        elif score >= 0.5:
            status = ReviewStatus.NEEDS_REVISION
        else:
            status = ReviewStatus.FAILED
        
        return ReviewFeedback(
            status=status,
            score=score,
            issues=review_data.get("issues", []),
            suggestions=review_data.get("suggestions", []),
            metrics=review_data.get("metrics", {})
        )
    
    def review_final_video(self, video_path: str, 
                          video_description: str) -> ReviewFeedback:
        """Review the final generated video"""
        
        # Load video and extract frames
        cap = cv2.VideoCapture(video_path)
        frames = []
        
        while len(frames) < 30:  # Sample up to 30 frames
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        
        cap.release()
        
        if not frames:
            return ReviewFeedback(
                status=ReviewStatus.FAILED,
                score=0.0,
                issues=["Failed to load video"],
                suggestions=["Check video file path and format"]
            )
        
        # Create a synthetic sub-process for overall review
        overall_process = SubProcessDescription(
            process_type=SubProcess.CINEMATOGRAPHY,
            description=video_description,
            parameters={"review_type": "final"}
        )
        
        return self.review_output(overall_process, frames)