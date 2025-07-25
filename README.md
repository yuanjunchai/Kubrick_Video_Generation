# Kubrick: Multimodal Agent Collaborations for Synthetic Video Generation

Implementation of the Kubrick framework for generating synthetic videos using collaborative LLM/VLM agents and Blender 3D.

Based on the paper: [Kubrick: Multimodal Agent Collaborations for Synthetic Video Generation](https://arxiv.org/pdf/2408.10453)

## Overview

Kubrick uses three collaborative agents to generate videos from text descriptions:

1. **LLM-Director**: Decomposes video descriptions into cinematic sub-processes
2. **LLM-Programmer**: Generates Blender Python scripts for each sub-process
3. **VLM-Reviewer**: Reviews visual outputs and provides feedback for iteration

The system leverages:
- Retrieval-Augmented Generation (RAG) for Blender knowledge
- Iterative refinement based on visual feedback
- Dynamic function library updates
- Professional 3D rendering via Blender

## Installation

### Prerequisites

1. **Python 3.8+**
2. **Blender 3.0+** (must be accessible from command line)
3. **OpenAI API Key** with GPT-4V access

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/kubrick.git
cd kubrick

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set OpenAI API key
export OPENAI_API_KEY="your-api-key-here"
```

### Verify Blender Installation

```bash
blender --version
```

If Blender is not in PATH, specify the full path when running Kubrick.

## Usage

### Basic Usage

```bash
python main.py "A red cube rotating on a wooden table with dramatic lighting"
```

### Advanced Options

```bash
python main.py "A character walking through a forest" \
    --output forest_walk.mp4 \
    --duration 10 \
    --fps 30 \
    --resolution 1920x1080 \
    --quality HIGH \
    --max-iterations 20
```

### Loading Knowledge Base

```bash
# Load Blender tutorials (JSON format)
python main.py "Complex animation" --load-knowledge tutorials.json

# Load API documentation
python main.py "Technical scene" --load-knowledge blender_api.txt
```

### Using Configuration Files

```bash
python main.py "Your video description" --config config.json
```

Example configuration file:
```json
{
    "generation": {
        "max_iterations": 20,
        "default_duration": 8.0
    },
    "rendering": {
        "engine": "CYCLES",
        "samples": 256,
        "quality": "HIGH"
    }
}
```

## Project Structure

```
kubrick/
├── core/               # Core data structures and enums
├── agents/             # LLM/VLM agent implementations
├── knowledge/          # RAG system and prompts
├── blender/            # Blender-specific code and functions
├── pipeline/           # Main orchestration pipeline
├── utils/              # Utilities and helpers
├── examples/           # Example scripts
└── tests/              # Unit tests
```

## Examples

### Simple Animation
```python
from pipeline.kubrick import KubrickPipeline

# Initialize pipeline
pipeline = KubrickPipeline(api_key="your-key")

# Generate video
results = pipeline.generate_video(
    "A bouncing ball on a reflective floor",
    output_filename="bouncing_ball.mp4"
)
```

### With Custom Knowledge
```python
# Load custom tutorials
pipeline.load_knowledge([
    "To create realistic water, use the Ocean modifier...",
    "For character rigging, start with the Armature object..."
])

# Generate with enhanced knowledge
results = pipeline.generate_video(
    "A character diving into water with splash effects"
)
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key
- `KUBRICK_OUTPUT_DIR`: Output directory (default: ./output)
- `KUBRICK_BLENDER_PATH`: Path to Blender executable
- `KUBRICK_MAX_ITERATIONS`: Maximum review iterations
- `KUBRICK_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Presets

Use built-in presets for common scenarios:

```python
from config import get_preset_config

# Fast preview mode
config = get_preset_config("fast")

# High quality final render
config = get_preset_config("high_quality")

# Optimized for character animation
config = get_preset_config("animation")
```

## Extending Kubrick

### Adding Custom Functions

Create custom Blender functions:

```python
from blender.library import BlenderFunctionLibrary

library = BlenderFunctionLibrary()
library.update_function("my_custom_function", '''
def my_custom_function(param1, param2):
    """Your custom Blender function"""
    import bpy
    # Implementation
''')
```

### Custom Agents

Extend the base agent class:

```python
from agents.base import BaseAgent

class CustomAgent(BaseAgent):
    def _initialize(self):
        # Your initialization
        pass
    
    def process(self, *args, **kwargs):
        # Your processing logic
        pass
```

## Troubleshooting

### Common Issues

1. **Blender not found**: Ensure Blender is in PATH or use `--blender-path`
2. **API rate limits**: Reduce `--max-iterations` or add delays
3. **Memory issues**: Reduce resolution or video length
4. **Script errors**: Check Blender console output in logs

### Debug Mode

Enable verbose logging:
```bash
python main.py "Your video" --verbose
```

Check logs in `./logs/` directory for detailed information.

## Performance Tips

1. **Use EEVEE renderer** for faster previews
2. **Reduce samples** for draft quality
3. **Lower resolution** during development
4. **Cache RAG results** for repeated queries
5. **Use presets** for optimized settings

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This implementation is for research purposes. Please cite the original paper:

```bibtex
@article{he2024kubrick,
  title={Kubrick: Multimodal Agent Collaborations for Synthetic Video Generation},
  author={He, Liu and Song, Yizhi and Huang, Hejun and others},
  journal={arXiv preprint arXiv:2408.10453},
  year={2024}
}
```

## Acknowledgments

- Original Kubrick paper authors
- OpenAI for GPT-4V API
- Blender Foundation for Blender 3D
- Open source community for supporting libraries

## Code Framework of the paper:

kubrick/
├── __init__.py
├── main.py                    # Main entry point
├── config.py                  # Configuration and settings
├── requirements.txt           # Dependencies
├── README.md                  # Project documentation
│
├── core/                      # Core data structures and enums
│   ├── __init__.py
│   ├── enums.py              # SubProcess enum and other enums
│   ├── data_models.py             # Data classes (VideoDescription, etc.)
│   └── exceptions.py         # Custom exceptions
│
├── agents/                    # Agent implementations
│   ├── __init__.py
│   ├── base.py              # Base agent class
│   ├── director.py          # LLM-Director implementation
│   ├── programmer.py        # LLM-Programmer implementation
│   └── reviewer.py          # VLM-Reviewer implementation
│
├── knowledge/                 # Knowledge and RAG system
│   ├── __init__.py
│   ├── rag.py               # RAG knowledge base
│   └── prompts.py           # Prompt templates for all agents
│
├── blender/                   # Blender-specific code
│   ├── __init__.py
│   ├── executor.py          # Blender script execution and rendering
│   ├── functions/           # Function library
│   │   ├── __init__.py
│   │   ├── base.py         # Base function utilities
│   │   ├── assets.py       # Asset import/manipulation functions for Blender
│   │   ├── motion.py       # Motion and animation functions
│   │   ├── lighting.py     # Lighting setup functions
│   │   └── camera.py       # Camera setup functions
│   └── library.py           # Blender function library manager
│
├── pipeline/                  # Pipeline orchestration
│   ├── __init__.py
│   └── kubrick.py           # Main Kubrick pipeline orchestrating all agents
│
├── utils/                     # Utility functions
│   ├── __init__.py
│   ├── video.py             # Video processing utilities
│   ├── logging.py           # Logging configuration
│   └── validation.py        # Input validation
│
├── examples/                  # Example scripts
│   ├── __init__.py
│   ├── simple_video.py      # Simple video generation example
│   └── load_knowledge.py    # Knowledge loading example
│
└── tests/                     # Unit tests
    ├── __init__.py
    ├── test_agents.py
    ├── test_blender.py
    └── test_pipeline.py