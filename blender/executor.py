import os
import subprocess
import tempfile
import json
from typing import Tuple, List, Optional, Dict, Any
from pathlib import Path
import logging
import time

import cv2
import numpy as np

from core.models import RenderSettings, ScriptResult


class BlenderExecutor:
    """Executes Blender scripts and captures output"""
    
    def __init__(self, blender_path: str = "blender", 
                 temp_dir: Optional[str] = None):
        self.blender_path = blender_path
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Verify Blender installation
        self._verify_blender()
    
    def _verify_blender(self):
        """Verify Blender is installed and accessible"""
        try:
            result = subprocess.run(
                [self.blender_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # Extract version info
                version_line = result.stdout.split('\n')[0]
                self.logger.info(f"Found {version_line}")
            else:
                raise RuntimeError("Blender not found or not accessible")
        except Exception as e:
            self.logger.error(f"Failed to verify Blender: {str(e)}")
            raise
    
    def execute_script(self, script: str, output_path: str,
                      render_settings: Optional[RenderSettings] = None,
                      start_frame: int = 1, end_frame: int = 120,
                      scene_file: Optional[str] = None) -> ScriptResult:
        """Execute Blender script and render output"""
        
        start_time = time.time()
        
        # Use default render settings if not provided
        if not render_settings:
            render_settings = RenderSettings()
        
        # Create render setup script
        render_setup = self._create_render_setup(
            output_path, render_settings, start_frame, end_frame
        )
        
        # Combine setup and user script
        full_script = f"{render_setup}\n\n# User Script\n{script}"
        
        # Write script to temporary file
        script_file = os.path.join(self.temp_dir, f"blender_script_{int(time.time())}.py")
        try:
            with open(script_file, 'w') as f:
                f.write(full_script)
            
            # Build Blender command
            cmd = [self.blender_path, "--background"]
            
            # Add scene file if provided
            if scene_file:
                cmd.extend([scene_file])
            
            # Add Python script
            cmd.extend(["--python", script_file])
            
            # Execute Blender
            self.logger.info(f"Executing Blender script: {script_file}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            execution_time = time.time() - start_time
            
            # Clean up temporary file
            os.unlink(script_file)
            
            # Check result
            if result.returncode == 0:
                self.logger.info(f"Script executed successfully in {execution_time:.2f}s")
                
                # Check if output file was created
                artifacts = []
                if os.path.exists(output_path):
                    artifacts.append(output_path)
                
                return ScriptResult(
                    success=True,
                    script=full_script,
                    output=result.stdout,
                    execution_time=execution_time,
                    artifacts=artifacts
                )
            else:
                self.logger.error(f"Script execution failed: {result.stderr}")
                return ScriptResult(
                    success=False,
                    script=full_script,
                    output=result.stdout,
                    error=result.stderr,
                    execution_time=execution_time
                )
                
        except subprocess.TimeoutExpired:
            self.logger.error("Script execution timed out")
            if os.path.exists(script_file):
                os.unlink(script_file)
            return ScriptResult(
                success=False,
                script=full_script,
                output="",
                error="Script execution timed out after 5 minutes",
                execution_time=300.0
            )
        except Exception as e:
            self.logger.error(f"Script execution failed: {str(e)}")
            if os.path.exists(script_file):
                os.unlink(script_file)
            return ScriptResult(
                success=False,
                script=full_script,
                output="",
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _create_render_setup(self, output_path: str, 
                           render_settings: RenderSettings,
                           start_frame: int, end_frame: int) -> str:
        """Create render setup script"""
        
        return f'''
import bpy

# Clear default scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Set render settings
scene = bpy.context.scene
scene.render.engine = 'CYCLES'  # or 'BLENDER_EEVEE'
scene.render.image_settings.file_format = '{render_settings.file_format}'

if '{render_settings.file_format}' == 'FFMPEG':
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = '{render_settings.codec}'
    scene.render.ffmpeg.constant_rate_factor = 'HIGH' if '{render_settings.quality}' == 'HIGH' else 'MEDIUM'

scene.render.resolution_x = {render_settings.resolution_x}
scene.render.resolution_y = {render_settings.resolution_y}
scene.render.resolution_percentage = {render_settings.resolution_percentage}
scene.render.fps = {render_settings.fps}

# Set frame range
scene.frame_start = {start_frame}
scene.frame_end = {end_frame}

# Set samples for quality
scene.cycles.samples = {render_settings.samples}

# Set output path
scene.render.filepath = "{output_path}"

# Function to render at the end
def render_output():
    bpy.ops.render.render(animation=True)
'''
    
    def capture_screenshots(self, script: str, frames: List[int],
                          render_settings: Optional[RenderSettings] = None) -> List[np.ndarray]:
        """Capture screenshots at specific frames"""
        
        screenshots = []
        
        for frame in frames:
            # Create output path for frame
            frame_path = os.path.join(
                self.temp_dir, 
                f"frame_{int(time.time())}_{frame}.png"
            )
            
            # Modified script to render single frame
            frame_script = f'''
{script}

# Set to specific frame and render
import bpy
bpy.context.scene.frame_set({frame})
bpy.context.scene.render.filepath = "{frame_path}"
bpy.ops.render.render(write_still=True)
'''
            
            # Execute script
            result = self.execute_script(
                frame_script, 
                frame_path,
                render_settings,
                frame, 
                frame
            )
            
            # Load screenshot if successful
            if result.success and os.path.exists(frame_path):
                img = cv2.imread(frame_path)
                if img is not None:
                    screenshots.append(img)
                os.unlink(frame_path)  # Clean up
            else:
                self.logger.warning(f"Failed to capture frame {frame}")
        
        return screenshots
    
    def render_viewport_preview(self, script: str, frame: int = 1,
                              resolution: Tuple[int, int] = (640, 480)) -> Optional[np.ndarray]:
        """Render a quick viewport preview"""
        
        preview_path = os.path.join(
            self.temp_dir,
            f"preview_{int(time.time())}.png"
        )
        
        preview_script = f'''
{script}

# Quick viewport render
import bpy
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'  # Fast renderer
scene.render.resolution_x = {resolution[0]}
scene.render.resolution_y = {resolution[1]}
scene.render.resolution_percentage = 100
scene.frame_set({frame})
scene.render.filepath = "{preview_path}"
bpy.ops.render.render(write_still=True)
'''
        
        result = self.execute_script(
            preview_script,
            preview_path,
            start_frame=frame,
            end_frame=frame
        )
        
        if result.success and os.path.exists(preview_path):
            img = cv2.imread(preview_path)
            os.unlink(preview_path)
            return img
        
        return None
    
    def extract_scene_info(self, script: str) -> Dict[str, Any]:
        """Extract information about the scene after script execution"""
        
        info_path = os.path.join(
            self.temp_dir,
            f"scene_info_{int(time.time())}.json"
        )
        
        info_script = f'''
{script}

# Extract scene information
import bpy
import json

scene_info = {{
    "objects": [],
    "materials": [],
    "animations": [],
    "cameras": [],
    "lights": []
}}

# Get all objects
for obj in bpy.data.objects:
    obj_info = {{
        "name": obj.name,
        "type": obj.type,
        "location": list(obj.location),
        "rotation": list(obj.rotation_euler),
        "scale": list(obj.scale),
        "visible": obj.visible_get()
    }}
    
    if obj.type == 'CAMERA':
        scene_info["cameras"].append(obj_info)
    elif obj.type == 'LIGHT':
        scene_info["lights"].append(obj_info)
    else:
        scene_info["objects"].append(obj_info)

# Get materials
for mat in bpy.data.materials:
    scene_info["materials"].append(mat.name)

# Get animations
for action in bpy.data.actions:
    scene_info["animations"].append(action.name)

# Save to file
with open("{info_path}", 'w') as f:
    json.dump(scene_info, f, indent=2)
'''
        
        result = self.execute_script(info_script, info_path)
        
        if result.success and os.path.exists(info_path):
            with open(info_path, 'r') as f:
                info = json.load(f)
            os.unlink(info_path)
            return info
        
        return {}
    
    def validate_script(self, script: str) -> Tuple[bool, Optional[str]]:
        """Validate script syntax without executing rendering"""
        
        validation_script = f'''
{script}

# If we got here, script is valid
print("SCRIPT_VALID")
'''
        
        result = self.execute_script(
            validation_script,
            "/tmp/dummy",  # No actual rendering
            start_frame=1,
            end_frame=1
        )
        
        if result.success and "SCRIPT_VALID" in result.output:
            return True, None
        else:
            return False, result.error or "Script validation failed"