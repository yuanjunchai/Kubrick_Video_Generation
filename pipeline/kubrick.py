import os
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path
import logging

from core.models import (
    VideoDescription, SubProcessDescription, ReviewFeedback,
    ScriptResult, RenderSettings
)
from core.enums import ReviewStatus
from agents.director import LLMDirector
from agents.programmer import LLMProgrammer
from agents.reviewer import VLMReviewer
from blender.executor import BlenderExecutor
from blender.library import BlenderFunctionLibrary
from knowledge.rag import RAGKnowledgeBase
from utils.logging import setup_logging


class KubrickPipeline:
    """Main pipeline orchestrating all agents for video generation"""
    
    def __init__(self, api_key: str, 
                 blender_path: str = "blender",
                 max_iterations: int = 15,
                 output_dir: str = "./output",
                 config: Optional[Dict[str, Any]] = None):
        
        # Setup logging
        self.logger = setup_logging()
        
        # Configuration
        self.api_key = api_key
        self.blender_path = blender_path
        self.max_iterations = max_iterations
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.config = config or {}
        
        # Initialize knowledge base
        self.logger.info("Initializing RAG knowledge base...")
        self.rag_kb = RAGKnowledgeBase(
            collection_name="kubrick_knowledge",
            persist_directory=str(self.output_dir / "chroma_db")
        )
        
        # Initialize components
        self.logger.info("Initializing pipeline components...")
        self.library = BlenderFunctionLibrary(
            custom_functions_path=str(self.output_dir / "custom_functions.json")
        )
        
        # Initialize agents
        self.director = LLMDirector(api_key, self.rag_kb, self.config.get('director', {}))
        self.programmer = LLMProgrammer(
            api_key, self.library, self.rag_kb, 
            self.config.get('programmer', {})
        )
        self.reviewer = VLMReviewer(api_key, self.rag_kb, self.config.get('reviewer', {}))
        
        # Initialize executor
        self.executor = BlenderExecutor(
            blender_path, 
            temp_dir=str(self.output_dir / "temp")
        )
        
        self.logger.info("Pipeline initialized successfully")
    
    def generate_video(self, description: str, 
                      output_filename: Optional[str] = None,
                      render_settings: Optional[RenderSettings] = None) -> Dict[str, Any]:
        """Generate video from text description
        
        Args:
            description: Text description of the video
            output_filename: Output filename (auto-generated if not provided)
            render_settings: Render settings (uses defaults if not provided)
        
        Returns:
            Dictionary with generation results and metadata
        """
        
        start_time = datetime.now()
        self.logger.info(f"Starting video generation: {description[:100]}...")
        
        # Create video description object
        video_desc = VideoDescription(
            text=description,
            duration=self.config.get('default_duration', 5.0),
            fps=self.config.get('default_fps', 24)
        )
        
        # Generate output filename if not provided
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"video_{timestamp}.mp4"
        
        output_path = str(self.output_dir / output_filename)
        
        # Initialize results tracking
        results = {
            "success": False,
            "output_path": output_path,
            "description": description,
            "sub_processes": [],
            "total_iterations": 0,
            "generation_time": 0,
            "errors": []
        }
        
        try:
            # Phase 1: Decompose into sub-processes
            self.logger.info("Phase 1: Decomposing video description...")
            sub_processes = self.director.decompose(video_desc)
            results["sub_processes"] = [sp.process_type.value for sp in sub_processes]
            
            # Save decomposition for reference
            self._save_decomposition(video_desc, sub_processes)
            
            # Accumulate scripts
            accumulated_script = self._get_base_script()
            
            # Phase 2: Generate and review scripts for each sub-process
            for idx, sub_process in enumerate(sub_processes):
                self.logger.info(
                    f"Phase 2.{idx+1}: Processing {sub_process.process_type.value}"
                )
                
                sub_result = self._process_subprocess(
                    sub_process, 
                    accumulated_script,
                    video_desc
                )
                
                if sub_result["success"]:
                    accumulated_script += "\n\n" + sub_result["script"]
                    results["total_iterations"] += sub_result["iterations"]
                else:
                    self.logger.warning(
                        f"Failed to process {sub_process.process_type.value}: "
                        f"{sub_result['error']}"
                    )
                    results["errors"].append({
                        "sub_process": sub_process.process_type.value,
                        "error": sub_result["error"]
                    })
            
            # Phase 3: Render final video
            self.logger.info("Phase 3: Rendering final video...")
            render_result = self._render_final_video(
                accumulated_script,
                output_path,
                video_desc,
                render_settings
            )
            
            if render_result.success:
                self.logger.info(f"Video successfully generated: {output_path}")
                results["success"] = True
                
                # Final review of complete video
                final_feedback = self.reviewer.review_final_video(
                    output_path,
                    description
                )
                results["final_score"] = final_feedback.score
                results["final_review"] = {
                    "status": final_feedback.status.value,
                    "score": final_feedback.score,
                    "issues": final_feedback.issues
                }
            else:
                results["errors"].append({
                    "phase": "rendering",
                    "error": render_result.error
                })
        
        except Exception as e:
            self.logger.error(f"Pipeline error: {str(e)}")
            results["errors"].append({
                "phase": "pipeline",
                "error": str(e)
            })
        
        # Calculate total time
        results["generation_time"] = (datetime.now() - start_time).total_seconds()
        
        # Save results
        self._save_results(results)
        
        return results
    
    def _process_subprocess(self, sub_process: SubProcessDescription,
                          accumulated_script: str,
                          video_desc: VideoDescription) -> Dict[str, Any]:
        """Process a single sub-process with iteration loop"""
        
        iteration = 0
        review_feedback = None
        success = False
        final_script = ""
        
        while iteration < self.max_iterations and not success:
            self.logger.info(
                f"  Iteration {iteration + 1}/{self.max_iterations} "
                f"for {sub_process.process_type.value}"
            )
            
            # Generate script
            script_result = self.programmer.process(sub_process, review_feedback)
            
            if not script_result.success:
                self.logger.error(f"  Script generation failed: {script_result.error}")
                return {
                    "success": False,
                    "error": script_result.error,
                    "iterations": iteration + 1
                }
            
            # Validate script syntax
            valid, error = self.executor.validate_script(
                accumulated_script + "\n" + script_result.script
            )
            
            if not valid:
                self.logger.error(f"  Script validation failed: {error}")
                review_feedback = ReviewFeedback(
                    status=ReviewStatus.FAILED,
                    score=0.0,
                    issues=[f"Script syntax error: {error}"],
                    suggestions=["Fix Python syntax errors", "Check Blender API usage"]
                )
            else:
                # Execute and capture screenshots for review
                self.logger.info("  Capturing screenshots for review...")
                
                # Determine key frames based on video duration
                fps = video_desc.fps
                duration = video_desc.duration
                total_frames = int(fps * duration)
                key_frames = self._calculate_key_frames(total_frames)
                
                screenshots = self.executor.capture_screenshots(
                    accumulated_script + "\n" + script_result.script,
                    key_frames,
                    RenderSettings()  # Use default for preview
                )
                
                if not screenshots:
                    self.logger.error("  Failed to capture screenshots")
                    review_feedback = ReviewFeedback(
                        status=ReviewStatus.FAILED,
                        score=0.0,
                        issues=["Failed to render preview"],
                        suggestions=["Check script execution", "Verify scene setup"]
                    )
                else:
                    # Review output
                    self.logger.info("  Reviewing visual output...")
                    review_feedback = self.reviewer.review_output(
                        sub_process, 
                        screenshots
                    )
                    
                    if review_feedback.passed:
                        self.logger.info(
                            f"  Review passed with score: {review_feedback.score}"
                        )
                        final_script = script_result.script
                        success = True
                    else:
                        self.logger.info(
                            f"  Review failed. Issues: {review_feedback.issues}"
                        )
                        
                        # Update library if needed (after a few attempts)
                        if iteration > self.config.get('library_update_threshold', 3):
                            self.logger.info("  Attempting to update function library...")
                            updated = self.programmer.update_library(review_feedback)
                            if updated:
                                self.logger.info("  Function library updated")
            
            iteration += 1
        
        if not success:
            self.logger.warning(
                f"  Max iterations reached for {sub_process.process_type.value}"
            )
        
        return {
            "success": success,
            "script": final_script,
            "iterations": iteration,
            "error": None if success else "Max iterations reached"
        }
    
    def _calculate_key_frames(self, total_frames: int, 
                            num_keys: int = 5) -> List[int]:
        """Calculate key frame indices for review"""
        
        if total_frames <= num_keys:
            return list(range(1, total_frames + 1))
        
        # Sample evenly across the video
        step = total_frames / (num_keys - 1)
        frames = [int(i * step) + 1 for i in range(num_keys - 1)]
        frames.append(total_frames)
        
        return frames
    
    def _get_base_script(self) -> str:
        """Get base Blender setup script"""
        
        return '''
                import bpy
                import math
                from mathutils import Vector, Matrix, Euler

                # Clear existing mesh objects (keep cameras and lights initially)
                for obj in bpy.data.objects:
                    if obj.type == 'MESH':
                        bpy.data.objects.remove(obj, do_unlink=True)

                # Reset to default scene settings
                scene = bpy.context.scene
                scene.frame_set(1)

                # Ensure we have a camera
                if "Camera" not in bpy.data.objects:
                    cam_data = bpy.data.cameras.new(name="Camera")
                    cam = bpy.data.objects.new("Camera", cam_data)
                    scene.collection.objects.link(cam)
                    scene.camera = cam
                    cam.location = (7, -7, 5)
                    cam.rotation_euler = (1.1, 0, 0.785)

                # Basic world lighting
                world = bpy.data.worlds.new(name="World")
                scene.world = world
                world.use_nodes = True
                bg = world.node_tree.nodes["Background"]
                bg.inputs[0].default_value[:3] = (0.05, 0.05, 0.05)  # Dark background
                '''
    
    def _render_final_video(self, script: str, output_path: str,
                          video_desc: VideoDescription,
                          render_settings: Optional[RenderSettings]) -> ScriptResult:
        """Render the final video"""
        
        # Add final render call to script
        final_script = script + '''
                                # Final render
                                render_output()
                                '''
        
        # Use provided settings or defaults
        if not render_settings:
            render_settings = RenderSettings(
                resolution_x=video_desc.resolution[0],
                resolution_y=video_desc.resolution[1],
                fps=video_desc.fps
            )
        
        # Calculate frame range
        total_frames = int(video_desc.fps * video_desc.duration)
        
        return self.executor.execute_script(
            final_script,
            output_path,
            render_settings,
            start_frame=1,
            end_frame=total_frames
        )
    
    def _save_decomposition(self, video_desc: VideoDescription,
                          sub_processes: List[SubProcessDescription]):
        """Save decomposition results for reference"""
        
        decomp_data = {
            "video_description": {
                "text": video_desc.text,
                "duration": video_desc.duration,
                "fps": video_desc.fps,
                "resolution": video_desc.resolution
            },
            "sub_processes": [
                {
                    "type": sp.process_type.value,
                    "description": sp.description,
                    "parameters": sp.parameters
                }
                for sp in sub_processes
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        decomp_path = self.output_dir / "decompositions" / f"decomp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        decomp_path.parent.mkdir(exist_ok=True)
        
        with open(decomp_path, 'w') as f:
            json.dump(decomp_data, f, indent=2)
    
    def _save_results(self, results: Dict[str, Any]):
        """Save generation results"""
        
        results_path = self.output_dir / "results" / f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        results_path.parent.mkdir(exist_ok=True)
        
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
    
    def load_knowledge(self, documents: List[str], 
                      metadata: Optional[List[Dict]] = None,
                      source_type: str = "general") -> int:
        """Load knowledge into RAG system
        
        Args:
            documents: List of document strings
            metadata: Optional metadata for each document
            source_type: Type of knowledge (general, tutorial, api_docs)
        
        Returns:
            Number of documents loaded
        """
        
        self.logger.info(f"Loading {len(documents)} documents into knowledge base...")
        return self.rag_kb.add_knowledge(documents, metadata, source_type=source_type)
    
    def load_tutorials_from_file(self, filepath: str) -> int:
        """Load video tutorials from a JSON file
        
        Expected format:
        [
            {
                "title": "Tutorial Title",
                "transcript": "Tutorial transcript...",
                "url": "optional URL"
            },
            ...
        ]
        """
        
        with open(filepath, 'r') as f:
            tutorials = json.load(f)
        
        return self.rag_kb.load_video_tutorials(tutorials)
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get statistics about the pipeline"""
        
        return {
            "knowledge_base": self.rag_kb.get_stats(),
            "function_library": {
                "total_functions": len(self.library.list_functions()),
                "functions": self.library.list_functions()
            },
            "configuration": {
                "max_iterations": self.max_iterations,
                "output_directory": str(self.output_dir),
                "blender_path": self.blender_path
            }
        }