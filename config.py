import os
from typing import Dict, Any


# Default configuration
DEFAULT_CONFIG = {
    # Model settings
    "models": {
        "director": "gpt-4-vision-preview",
        "programmer": "gpt-4",
        "reviewer": "gpt-4-vision-preview"
    },
    
    # Generation settings
    "generation": {
        "default_duration": 5.0,  # seconds
        "default_fps": 24,
        "default_resolution": (1920, 1080),
        "max_iterations": 15,
        "library_update_threshold": 3  # iterations before trying library update
    },
    
    # Render settings
    "rendering": {
        "engine": "CYCLES",  # CYCLES or BLENDER_EEVEE
        "samples": 128,
        "quality": "HIGH",
        "file_format": "FFMPEG",
        "codec": "H264"
    },
    
    # Review settings
    "review": {
        "key_frame_count": 5,
        "max_image_size": (1024, 1024),
        "min_pass_score": 0.8
    },
    
    # RAG settings
    "rag": {
        "chunk_size": 1000,
        "chunk_overlap": 100,
        "n_results": 5,
        "embedding_model": "text-embedding-ada-002"
    },
    
    # Paths
    "paths": {
        "output_dir": "./output",
        "temp_dir": "./output/temp",
        "knowledge_dir": "./knowledge",
        "custom_functions": "./output/custom_functions.json"
    },
    
    # Logging
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": "kubrick.log"
    }
}


def load_config(config_path: str = None) -> Dict[str, Any]:
    """Load configuration from file or environment"""
    
    config = DEFAULT_CONFIG.copy()
    
    # Load from file if provided
    if config_path and os.path.exists(config_path):
        import json
        with open(config_path, 'r') as f:
            user_config = json.load(f)
        
        # Deep merge configurations
        config = deep_merge(config, user_config)
    
    # Override with environment variables
    env_overrides = {
        "KUBRICK_OUTPUT_DIR": ["paths", "output_dir"],
        "KUBRICK_BLENDER_PATH": ["blender_path"],
        "KUBRICK_MAX_ITERATIONS": ["generation", "max_iterations"],
        "KUBRICK_DEFAULT_DURATION": ["generation", "default_duration"],
        "KUBRICK_DEFAULT_FPS": ["generation", "default_fps"],
        "KUBRICK_RENDER_ENGINE": ["rendering", "engine"],
        "KUBRICK_LOG_LEVEL": ["logging", "level"]
    }
    
    for env_var, config_path in env_overrides.items():
        if env_var in os.environ:
            set_nested_value(config, config_path, os.environ[env_var])
    
    return config


def deep_merge(base: Dict, update: Dict) -> Dict:
    """Deep merge two dictionaries"""
    
    result = base.copy()
    
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def set_nested_value(d: Dict, path: list, value: Any):
    """Set value in nested dictionary using path"""
    
    for key in path[:-1]:
        d = d.setdefault(key, {})
    
    # Convert types for certain paths
    if path[-1] in ["max_iterations", "default_fps", "samples"]:
        value = int(value)
    elif path[-1] in ["default_duration"]:
        value = float(value)
    
    d[path[-1]] = value


# Preset configurations for different use cases
PRESETS = {
    "fast": {
        "generation": {
            "max_iterations": 5
        },
        "rendering": {
            "engine": "BLENDER_EEVEE",
            "samples": 32,
            "quality": "LOW"
        },
        "review": {
            "key_frame_count": 3
        }
    },
    
    "high_quality": {
        "generation": {
            "max_iterations": 20
        },
        "rendering": {
            "engine": "CYCLES",
            "samples": 256,
            "quality": "HIGH"
        },
        "review": {
            "key_frame_count": 8,
            "min_pass_score": 0.9
        }
    },
    
    "animation": {
        "generation": {
            "default_fps": 30,
            "default_duration": 10.0
        },
        "rendering": {
            "engine": "BLENDER_EEVEE",
            "samples": 64
        }
    }
}


def get_preset_config(preset_name: str) -> Dict[str, Any]:
    """Get configuration for a specific preset"""
    
    if preset_name not in PRESETS:
        raise ValueError(f"Unknown preset: {preset_name}. Available: {list(PRESETS.keys())}")
    
    return deep_merge(DEFAULT_CONFIG, PRESETS[preset_name])