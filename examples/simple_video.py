import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.kubrick import KubrickPipeline
from core.models import RenderSettings


def generate_simple_animation():
    """Generate a simple animation example"""
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Please set OPENAI_API_KEY environment variable")
        return
    
    # Initialize pipeline
    print("Initializing Kubrick pipeline...")
    pipeline = KubrickPipeline(
        api_key=api_key,
        max_iterations=10,  # Fewer iterations for simple example
        output_dir="./output/examples"
    )
    
    # Example 1: Bouncing Ball
    print("\n" + "="*50)
    print("Example 1: Bouncing Ball")
    print("="*50)
    
    results = pipeline.generate_video(
        description="A red bouncing ball on a white floor with soft shadows",
        output_filename="bouncing_ball.mp4",
        render_settings=RenderSettings(
            resolution_x=1280,
            resolution_y=720,
            fps=24,
            quality="MEDIUM"
        )
    )
    
    print(f"Success: {results['success']}")
    print(f"Output: {results['output_path']}")
    
    # Example 2: Rotating Cube
    print("\n" + "="*50)
    print("Example 2: Rotating Cube")
    print("="*50)
    
    results = pipeline.generate_video(
        description="A blue metallic cube rotating slowly with studio lighting",
        output_filename="rotating_cube.mp4"
    )
    
    print(f"Success: {results['success']}")
    print(f"Output: {results['output_path']}")
    
    # Example 3: Simple Character Walk
    print("\n" + "="*50)
    print("Example 3: Character Walk")
    print("="*50)
    
    results = pipeline.generate_video(
        description="A simple character walking from left to right on grass",
        output_filename="character_walk.mp4"
    )
    
    print(f"Success: {results['success']}")
    print(f"Output: {results['output_path']}")


def generate_with_custom_knowledge():
    """Example with custom knowledge loading"""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Please set OPENAI_API_KEY environment variable")
        return
    
    # Initialize pipeline
    pipeline = KubrickPipeline(api_key=api_key)
    
    # Load custom knowledge
    custom_knowledge = [
        """
        To create a glowing effect in Blender:
        1. Add an Emission shader to the material
        2. Set the Emission strength to 5.0 or higher
        3. Enable Bloom in the compositor for glow effect
        """,
        """
        For realistic water:
        1. Use a Glass BSDF mixed with a Transparent BSDF
        2. Set IOR to 1.33 for water
        3. Add a Wave texture for surface displacement
        """
    ]
    
    pipeline.load_knowledge(custom_knowledge, source_type="custom_tips")
    
    # Generate video with specialized knowledge
    results = pipeline.generate_video(
        description="A glowing orb floating above a pool of water at night",
        output_filename="glowing_orb_water.mp4"
    )
    
    print(f"Success: {results['success']}")
    print(f"Output: {results['output_path']}")


if __name__ == "__main__":
    # Run simple examples
    generate_simple_animation()
    
    # Uncomment to run knowledge-enhanced example
    # generate_with_custom_knowledge()