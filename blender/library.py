import os
import json
from typing import Dict, List, Optional, Tuple
import logging

from core.enums import SubProcess
from blender.functions import (
    assets,
    motion,
    base,
    lighting,
    camera
)


class BlenderFunctionLibrary:
    """Manages the library of Blender Python functions"""
    
    def __init__(self, custom_functions_path: Optional[str] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.custom_functions_path = custom_functions_path
        
        # Initialize with built-in functions
        self.functions = self._load_builtin_functions()
        
        # Load custom functions if path provided
        if custom_functions_path:
            self._load_custom_functions()
    
    def _load_builtin_functions(self) -> Dict[str, str]:
        """Load built-in function definitions"""
        
        functions = {}
        
        # Asset functions
        functions.update({
            "import_asset": assets.IMPORT_ASSET_FUNCTION,
            "scale_asset": assets.SCALE_ASSET_FUNCTION,
            "rotate_asset": assets.ROTATE_ASSET_FUNCTION,
            "position_asset": assets.POSITION_ASSET_FUNCTION,
            "apply_material": assets.APPLY_MATERIAL_FUNCTION
        })
        
        # Motion functions
        functions.update({
            "set_motion": motion.SET_MOTION_FUNCTION,
            "create_walk_cycle": motion.WALK_CYCLE_FUNCTION,
            "create_jump_motion": motion.JUMP_MOTION_FUNCTION,
            "apply_armature_action": motion.ARMATURE_ACTION_FUNCTION
        })
        
        # Base utility functions
        functions.update(base.BASE_FUNCTIONS)
        
        # Lighting functions
        functions.update(lighting.LIGHTING_FUNCTIONS)
        
        # Camera functions
        functions.update(camera.CAMERA_FUNCTIONS)
        
        self.logger.info(f"Loaded {len(functions)} built-in functions")
        return functions
    
    def _load_custom_functions(self):
        """Load custom functions from file"""
        
        if not os.path.exists(self.custom_functions_path):
            self.logger.warning(f"Custom functions file not found: {self.custom_functions_path}")
            return
        
        try:
            with open(self.custom_functions_path, 'r') as f:
                custom_functions = json.load(f)
            
            self.functions.update(custom_functions)
            self.logger.info(f"Loaded {len(custom_functions)} custom functions")
            
        except Exception as e:
            self.logger.error(f"Failed to load custom functions: {str(e)}")
    
    def get_function(self, name: str) -> Optional[str]:
        """Get a function by name"""
        return self.functions.get(name)
    
    def get_relevant_functions(self, process_type: SubProcess) -> str:
        """Get functions relevant to a specific sub-process"""
        
        # Map sub-processes to relevant functions
        function_mapping = {
            SubProcess.SCENE: [
                "import_asset", 
                "scale_asset", 
                "position_asset",
                "apply_material"
            ],
            SubProcess.CHARACTER: [
                "import_asset", 
                "scale_asset", 
                "rotate_asset",
                "position_asset"
            ],
            SubProcess.MOTION: [
                "set_motion",
                "create_walk_cycle",
                "create_jump_motion",
                "apply_armature_action"
            ],
            SubProcess.LIGHTING: [
                "setup_lighting",
                "create_three_point_lighting",
                "setup_hdri_lighting"
            ],
            SubProcess.CINEMATOGRAPHY: [
                "setup_camera",
                "animate_camera_orbit",
                "animate_camera_dolly",
                "setup_camera_tracking"
            ]
        }
        
        relevant_names = function_mapping.get(process_type, [])
        
        # Collect function code
        functions_code = []
        for name in relevant_names:
            func_code = self.get_function(name)
            if func_code:
                functions_code.append(f"# Function: {name}\n{func_code}")
        
        return "\n\n".join(functions_code)
    
    def update_function(self, name: str, code: str, save: bool = True):
        """Update or add a function to the library"""
        
        self.functions[name] = code
        self.logger.info(f"Updated function: {name}")
        
        # Save to custom functions if configured
        if save and self.custom_functions_path:
            self._save_custom_functions()
    
    def _save_custom_functions(self):
        """Save custom functions to file"""
        
        # Filter out built-in functions
        builtin_names = set(self._load_builtin_functions().keys())
        custom_functions = {
            name: code for name, code in self.functions.items()
            if name not in builtin_names
        }
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.custom_functions_path), exist_ok=True)
            
            with open(self.custom_functions_path, 'w') as f:
                json.dump(custom_functions, f, indent=2)
            
            self.logger.info(f"Saved {len(custom_functions)} custom functions")
            
        except Exception as e:
            self.logger.error(f"Failed to save custom functions: {str(e)}")
    
    def list_functions(self) -> List[str]:
        """List all available function names"""
        return list(self.functions.keys())
    
    def get_function_signature(self, name: str) -> Optional[str]:
        """Extract function signature from code"""
        
        code = self.get_function(name)
        if not code:
            return None
        
        # Extract first line (def statement)
        lines = code.strip().split('\n')
        for line in lines:
            if line.strip().startswith('def '):
                return line.strip()
        
        return None
    
    def validate_function(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate function code syntax"""
        
        try:
            compile(code, '<string>', 'exec')
            return True, None
        except SyntaxError as e:
            return False, str(e)
    
    def export_library(self, output_path: str):
        """Export entire library to a Python module"""
        
        try:
            with open(output_path, 'w') as f:
                f.write('"""\nGenerated Blender Function Library\n"""\n\n')
                f.write('import bpy\nimport math\nimport numpy as np\n')
                f.write('from mathutils import Vector, Matrix, Euler\n\n')
                
                for name, code in self.functions.items():
                    f.write(f"# {name}\n{code}\n\n")
            
            self.logger.info(f"Exported library to: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export library: {str(e)}")