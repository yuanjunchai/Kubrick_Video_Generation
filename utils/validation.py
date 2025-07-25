import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import logging
from datetime import datetime

from core.enums import SubProcess, ReviewStatus, MotionType, CameraAnimation, LightingType

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def validate_video_description(description: str, min_length: int = 5, 
                             max_length: int = 2000) -> bool:
    """Validate video description text
    
    Args:
        description: Video description text
        min_length: Minimum description length
        max_length: Maximum description length
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(description, str):
        raise ValidationError("Description must be a string")
    
    description = description.strip()
    
    if len(description) < min_length:
        raise ValidationError(f"Description too short (minimum {min_length} characters)")
    
    if len(description) > max_length:
        raise ValidationError(f"Description too long (maximum {max_length} characters)")
    
    # Check for potentially problematic content
    if not description:
        raise ValidationError("Description cannot be empty")
    
    # Basic content validation
    prohibited_patterns = [
        r'\b(hack|exploit|virus|malware)\b',
        r'\b(illegal|criminal|violent)\b'
    ]
    
    for pattern in prohibited_patterns:
        if re.search(pattern, description.lower()):
            raise ValidationError("Description contains prohibited content")
    
    return True


def validate_duration(duration: float, min_duration: float = 0.1, 
                     max_duration: float = 300.0) -> bool:
    """Validate video duration
    
    Args:
        duration: Duration in seconds
        min_duration: Minimum allowed duration
        max_duration: Maximum allowed duration
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(duration, (int, float)):
        raise ValidationError("Duration must be a number")
    
    if duration < min_duration:
        raise ValidationError(f"Duration too short (minimum {min_duration}s)")
    
    if duration > max_duration:
        raise ValidationError(f"Duration too long (maximum {max_duration}s)")
    
    return True


def validate_resolution(resolution: Tuple[int, int]) -> bool:
    """Validate video resolution
    
    Args:
        resolution: (width, height) tuple
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(resolution, (list, tuple)) or len(resolution) != 2:
        raise ValidationError("Resolution must be a (width, height) tuple")
    
    width, height = resolution
    
    if not isinstance(width, int) or not isinstance(height, int):
        raise ValidationError("Resolution values must be integers")
    
    if width < 240 or height < 240:
        raise ValidationError("Resolution too small (minimum 240x240)")
    
    if width > 7680 or height > 4320:  # 8K limit
        raise ValidationError("Resolution too large (maximum 7680x4320)")
    
    # Check common aspect ratios
    common_ratios = [
        (16, 9), (4, 3), (21, 9), (1, 1), (9, 16)  # Including vertical video
    ]
    
    aspect_ratio = width / height
    tolerance = 0.05
    
    valid_ratio = False
    for ratio_w, ratio_h in common_ratios:
        expected_ratio = ratio_w / ratio_h
        if abs(aspect_ratio - expected_ratio) < tolerance:
            valid_ratio = True
            break
    
    if not valid_ratio:
        logger.warning(f"Unusual aspect ratio: {width}x{height} ({aspect_ratio:.2f})")
    
    return True


def validate_fps(fps: int, min_fps: int = 1, max_fps: int = 120) -> bool:
    """Validate frames per second
    
    Args:
        fps: Frames per second
        min_fps: Minimum allowed FPS
        max_fps: Maximum allowed FPS
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(fps, int):
        raise ValidationError("FPS must be an integer")
    
    if fps < min_fps:
        raise ValidationError(f"FPS too low (minimum {min_fps})")
    
    if fps > max_fps:
        raise ValidationError(f"FPS too high (maximum {max_fps})")
    
    # Check for common frame rates
    common_fps = [24, 25, 30, 48, 50, 60, 120]
    if fps not in common_fps:
        logger.warning(f"Unusual frame rate: {fps}fps")
    
    return True


def validate_file_path(file_path: str, must_exist: bool = False, 
                      allowed_extensions: Optional[List[str]] = None) -> bool:
    """Validate file path
    
    Args:
        file_path: Path to validate
        must_exist: Whether file must already exist
        allowed_extensions: List of allowed file extensions
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(file_path, str):
        raise ValidationError("File path must be a string")
    
    if not file_path.strip():
        raise ValidationError("File path cannot be empty")
    
    path = Path(file_path)
    
    if must_exist and not path.exists():
        raise ValidationError(f"File does not exist: {file_path}")
    
    if allowed_extensions:
        extension = path.suffix.lower()
        if extension not in [ext.lower() for ext in allowed_extensions]:
            raise ValidationError(f"Invalid file extension. Allowed: {allowed_extensions}")
    
    # Check for problematic characters
    problematic_chars = ['<', '>', ':', '"', '|', '?', '*']
    if any(char in file_path for char in problematic_chars):
        raise ValidationError("File path contains invalid characters")
    
    return True


def validate_blender_script(script: str, max_length: int = 100000) -> bool:
    """Validate Blender Python script
    
    Args:
        script: Python script code
        max_length: Maximum script length
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(script, str):
        raise ValidationError("Script must be a string")
    
    if len(script) > max_length:
        raise ValidationError(f"Script too long (maximum {max_length} characters)")
    
    # Check for dangerous operations
    dangerous_patterns = [
        r'\bos\.system\b',
        r'\bsubprocess\.',
        r'\bexec\(',
        r'\beval\(',
        r'\b__import__\b',
        r'\bopen\s*\(',  # File operations should be controlled
        r'\bfile\s*\(',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, script):
            logger.warning(f"Potentially dangerous operation detected: {pattern}")
    
    # Check for required Blender imports
    if 'import bpy' not in script and 'bpy.' in script:
        raise ValidationError("Script uses bpy but doesn't import it")
    
    return True


def validate_enum_value(value: Any, enum_class: type) -> bool:
    """Validate that value is valid enum member
    
    Args:
        value: Value to validate
        enum_class: Enum class to validate against
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If validation fails
    """
    if isinstance(value, enum_class):
        return True
    
    if isinstance(value, str):
        try:
            enum_class(value)
            return True
        except ValueError:
            valid_values = [e.value for e in enum_class]
            raise ValidationError(f"Invalid {enum_class.__name__}: {value}. Valid values: {valid_values}")
    
    raise ValidationError(f"Value must be {enum_class.__name__} or string")


def validate_3d_coordinates(coords: Union[Tuple, List], dimension: int = 3) -> bool:
    """Validate 3D coordinate tuple/list
    
    Args:
        coords: Coordinate tuple/list
        dimension: Expected dimension (2 or 3)
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(coords, (tuple, list)):
        raise ValidationError("Coordinates must be tuple or list")
    
    if len(coords) != dimension:
        raise ValidationError(f"Coordinates must have {dimension} values")
    
    for i, coord in enumerate(coords):
        if not isinstance(coord, (int, float)):
            raise ValidationError(f"Coordinate {i} must be a number")
        
        if abs(coord) > 10000:  # Reasonable scene bounds
            logger.warning(f"Large coordinate value: {coord}")
    
    return True


def validate_color(color: Union[Tuple, List], alpha: bool = False) -> bool:
    """Validate color tuple (RGB or RGBA)
    
    Args:
        color: Color tuple/list
        alpha: Whether alpha channel is expected
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If validation fails
    """
    expected_length = 4 if alpha else 3
    
    if not isinstance(color, (tuple, list)):
        raise ValidationError("Color must be tuple or list")
    
    if len(color) != expected_length:
        raise ValidationError(f"Color must have {expected_length} values")
    
    for i, value in enumerate(color):
        if not isinstance(value, (int, float)):
            raise ValidationError(f"Color value {i} must be a number")
        
        if not 0.0 <= value <= 1.0:
            raise ValidationError(f"Color value {i} must be between 0.0 and 1.0")
    
    return True


def validate_api_key(api_key: str) -> bool:
    """Validate API key format
    
    Args:
        api_key: API key string
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(api_key, str):
        raise ValidationError("API key must be a string")
    
    if not api_key.strip():
        raise ValidationError("API key cannot be empty")
    
    # Basic format check (adapt based on your API provider)
    if len(api_key) < 20:
        raise ValidationError("API key appears too short")
    
    # Check for suspicious patterns
    if api_key.lower() == "your-api-key-here" or "example" in api_key.lower():
        raise ValidationError("Please provide a real API key")
    
    return True


def validate_render_settings(settings: Dict[str, Any]) -> bool:
    """Validate render settings dictionary
    
    Args:
        settings: Render settings dictionary
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(settings, dict):
        raise ValidationError("Render settings must be a dictionary")
    
    # Required settings
    required_keys = ['resolution_x', 'resolution_y', 'fps']
    for key in required_keys:
        if key not in settings:
            raise ValidationError(f"Missing required render setting: {key}")
    
    # Validate individual settings
    if 'resolution_x' in settings and 'resolution_y' in settings:
        validate_resolution((settings['resolution_x'], settings['resolution_y']))
    
    if 'fps' in settings:
        validate_fps(settings['fps'])
    
    if 'samples' in settings:
        samples = settings['samples']
        if not isinstance(samples, int) or samples < 1 or samples > 10000:
            raise ValidationError("Samples must be integer between 1 and 10000")
    
    return True


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system usage
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove problematic characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Trim and ensure it's not empty
    sanitized = sanitized.strip('_. ')
    
    if not sanitized:
        sanitized = f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    return sanitized


def validate_configuration(config: Dict[str, Any]) -> bool:
    """Validate configuration dictionary
    
    Args:
        config: Configuration dictionary
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(config, dict):
        raise ValidationError("Configuration must be a dictionary")
    
    # Validate API configuration
    if 'api_key' in config:
        validate_api_key(config['api_key'])
    
    # Validate render settings
    if 'render_settings' in config:
        validate_render_settings(config['render_settings'])
    
    # Validate paths
    path_keys = ['output_dir', 'blender_path', 'asset_dir']
    for key in path_keys:
        if key in config and config[key]:
            validate_file_path(str(config[key]))
    
    # Validate numeric settings
    numeric_keys = {
        'max_iterations': (1, 100),
        'timeout': (10, 3600),
        'max_retries': (0, 10)
    }
    
    for key, (min_val, max_val) in numeric_keys.items():
        if key in config:
            value = config[key]
            if not isinstance(value, (int, float)) or not min_val <= value <= max_val:
                raise ValidationError(f"{key} must be between {min_val} and {max_val}")
    
    return True 