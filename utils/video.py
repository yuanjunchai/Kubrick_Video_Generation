import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import cv2
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Handles video processing operations"""
    
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path
        self._verify_ffmpeg()
    
    def _verify_ffmpeg(self):
        """Verify FFmpeg installation"""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise RuntimeError("FFmpeg not found or not working")
            logger.info("FFmpeg verified successfully")
        except Exception as e:
            logger.error(f"FFmpeg verification failed: {e}")
            raise

    def extract_frames(self, video_path: str, output_dir: str, 
                      frame_rate: Optional[float] = None) -> List[str]:
        """Extract frames from video file
        
        Args:
            video_path: Path to input video
            output_dir: Directory to save frames
            frame_rate: Optional frame rate for extraction
            
        Returns:
            List of extracted frame file paths
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Build FFmpeg command
        cmd = [
            self.ffmpeg_path,
            "-i", video_path,
            "-y"  # Overwrite output files
        ]
        
        if frame_rate:
            cmd.extend(["-vf", f"fps={frame_rate}"])
        
        output_pattern = os.path.join(output_dir, "frame_%04d.png")
        cmd.append(output_pattern)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                raise RuntimeError(f"Frame extraction failed: {result.stderr}")
            
            # Get list of extracted frames
            frame_files = sorted([
                os.path.join(output_dir, f) 
                for f in os.listdir(output_dir) 
                if f.startswith("frame_") and f.endswith(".png")
            ])
            
            logger.info(f"Extracted {len(frame_files)} frames from {video_path}")
            return frame_files
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Frame extraction timed out")
        except Exception as e:
            raise RuntimeError(f"Frame extraction error: {e}")

    def create_video_from_frames(self, frame_dir: str, output_path: str,
                                fps: int = 24, codec: str = "libx264",
                                quality: str = "high") -> str:
        """Create video from frame sequence
        
        Args:
            frame_dir: Directory containing frame images
            output_path: Output video file path
            fps: Frames per second
            codec: Video codec
            quality: Video quality (low, medium, high, lossless)
            
        Returns:
            Path to created video file
        """
        # Quality settings
        quality_settings = {
            "low": ["-crf", "28"],
            "medium": ["-crf", "23"],
            "high": ["-crf", "18"],
            "lossless": ["-crf", "0"]
        }
        
        quality_args = quality_settings.get(quality, quality_settings["high"])
        
        # Find frame pattern
        frame_pattern = os.path.join(frame_dir, "frame_%04d.png")
        if not any(f.startswith("frame_") for f in os.listdir(frame_dir)):
            # Try other common patterns
            patterns = ["frame%04d.png", "%04d.png", "img_%04d.png"]
            for pattern in patterns:
                test_path = os.path.join(frame_dir, pattern.replace("%04d", "0001"))
                if os.path.exists(test_path):
                    frame_pattern = os.path.join(frame_dir, pattern)
                    break
            else:
                raise ValueError(f"No frame sequence found in {frame_dir}")
        
        # Build FFmpeg command
        cmd = [
            self.ffmpeg_path,
            "-y",  # Overwrite output
            "-r", str(fps),  # Input frame rate
            "-i", frame_pattern,
            "-c:v", codec,
            "-r", str(fps),  # Output frame rate
            "-pix_fmt", "yuv420p"  # Compatibility
        ]
        
        cmd.extend(quality_args)
        cmd.append(output_path)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                raise RuntimeError(f"Video creation failed: {result.stderr}")
            
            logger.info(f"Created video: {output_path}")
            return output_path
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Video creation timed out")
        except Exception as e:
            raise RuntimeError(f"Video creation error: {e}")

    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get video file information
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video information
        """
        cmd = [
            self.ffmpeg_path,
            "-i", video_path,
            "-f", "null", "-"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            stderr = result.stderr
            
            info = {}
            
            # Parse duration
            if "Duration:" in stderr:
                duration_line = [line for line in stderr.split('\n') if "Duration:" in line][0]
                duration_str = duration_line.split("Duration: ")[1].split(",")[0]
                info['duration'] = duration_str
            
            # Parse resolution and fps
            if "Video:" in stderr:
                video_line = [line for line in stderr.split('\n') if " Video:" in line][0]
                if "x" in video_line:
                    # Extract resolution
                    parts = video_line.split()
                    for part in parts:
                        if "x" in part and part.replace("x", "").replace(",", "").isdigit():
                            width, height = part.rstrip(",").split("x")
                            info['width'] = int(width)
                            info['height'] = int(height)
                            break
                
                # Extract fps
                if " fps" in video_line:
                    fps_part = video_line.split(" fps")[0].split()[-1]
                    try:
                        info['fps'] = float(fps_part)
                    except ValueError:
                        pass
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            return {}

    def resize_video(self, input_path: str, output_path: str, 
                    width: int, height: int) -> str:
        """Resize video to specified dimensions
        
        Args:
            input_path: Input video path
            output_path: Output video path
            width: Target width
            height: Target height
            
        Returns:
            Path to resized video
        """
        cmd = [
            self.ffmpeg_path,
            "-i", input_path,
            "-vf", f"scale={width}:{height}",
            "-c:a", "copy",  # Copy audio without re-encoding
            "-y",
            output_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                raise RuntimeError(f"Video resize failed: {result.stderr}")
            
            logger.info(f"Resized video: {output_path}")
            return output_path
            
        except Exception as e:
            raise RuntimeError(f"Video resize error: {e}")

    def add_audio_to_video(self, video_path: str, audio_path: str, 
                          output_path: str, audio_volume: float = 1.0) -> str:
        """Add audio track to video
        
        Args:
            video_path: Input video path
            audio_path: Audio file path
            output_path: Output video path
            audio_volume: Audio volume multiplier
            
        Returns:
            Path to video with audio
        """
        cmd = [
            self.ffmpeg_path,
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",  # Copy video without re-encoding
            "-c:a", "aac",   # Encode audio as AAC
            "-filter:a", f"volume={audio_volume}",
            "-shortest",     # Stop when shortest input ends
            "-y",
            output_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                raise RuntimeError(f"Audio addition failed: {result.stderr}")
            
            logger.info(f"Added audio to video: {output_path}")
            return output_path
            
        except Exception as e:
            raise RuntimeError(f"Audio addition error: {e}")

    def concatenate_videos(self, video_paths: List[str], output_path: str) -> str:
        """Concatenate multiple videos
        
        Args:
            video_paths: List of input video paths
            output_path: Output video path
            
        Returns:
            Path to concatenated video
        """
        if len(video_paths) < 2:
            raise ValueError("Need at least 2 videos to concatenate")
        
        # Create temporary file list
        temp_list = os.path.join(os.path.dirname(output_path), "temp_concat_list.txt")
        
        try:
            with open(temp_list, 'w') as f:
                for video_path in video_paths:
                    f.write(f"file '{os.path.abspath(video_path)}'\n")
            
            cmd = [
                self.ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", temp_list,
                "-c", "copy",
                "-y",
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                raise RuntimeError(f"Video concatenation failed: {result.stderr}")
            
            logger.info(f"Concatenated {len(video_paths)} videos: {output_path}")
            return output_path
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_list):
                os.remove(temp_list)


def create_thumbnail(video_path: str, output_path: str, 
                    timestamp: str = "00:00:01") -> str:
    """Create thumbnail from video
    
    Args:
        video_path: Input video path
        output_path: Output thumbnail path
        timestamp: Time position for thumbnail (HH:MM:SS format)
        
    Returns:
        Path to created thumbnail
    """
    processor = VideoProcessor()
    
    cmd = [
        processor.ffmpeg_path,
        "-i", video_path,
        "-ss", timestamp,
        "-vframes", "1",
        "-y",
        output_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            raise RuntimeError(f"Thumbnail creation failed: {result.stderr}")
        
        logger.info(f"Created thumbnail: {output_path}")
        return output_path
        
    except Exception as e:
        raise RuntimeError(f"Thumbnail creation error: {e}")


def validate_video_file(video_path: str) -> bool:
    """Validate that a file is a valid video
    
    Args:
        video_path: Path to video file
        
    Returns:
        True if valid video file
    """
    if not os.path.exists(video_path):
        return False
    
    try:
        processor = VideoProcessor()
        info = processor.get_video_info(video_path)
        return 'width' in info and 'height' in info
    except Exception:
        return False


def get_video_duration(video_path: str) -> Optional[float]:
    """Get video duration in seconds
    
    Args:
        video_path: Path to video file
        
    Returns:
        Duration in seconds or None if failed
    """
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        cap.release()
        
        if fps > 0:
            return frame_count / fps
        return None
        
    except Exception as e:
        logger.error(f"Failed to get video duration: {e}")
        return None


def optimize_video_for_web(input_path: str, output_path: str) -> str:
    """Optimize video for web delivery
    
    Args:
        input_path: Input video path
        output_path: Output video path
        
    Returns:
        Path to optimized video
    """
    processor = VideoProcessor()
    
    cmd = [
        processor.ffmpeg_path,
        "-i", input_path,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",  # Enable fast start for web
        "-y",
        output_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            raise RuntimeError(f"Video optimization failed: {result.stderr}")
        
        logger.info(f"Optimized video for web: {output_path}")
        return output_path
        
    except Exception as e:
        raise RuntimeError(f"Video optimization error: {e}") 