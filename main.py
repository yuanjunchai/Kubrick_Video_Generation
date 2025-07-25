import os
import sys
import argparse
import json
from pathlib import Path

from pipeline.kubrick import KubrickPipeline
from core.models import RenderSettings
from utils.logging import setup_logging


def main():
    """Main entry point"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Kubrick: Multimodal Agent Collaborations for Synthetic Video Generation"
    )
    
    # Required arguments
    parser.add_argument(
        "description",
        type=str,
        help="Text description of the video to generate"
    )
    
    # Optional arguments
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output filename (auto-generated if not specified)"
    )
    
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="OpenAI API key (uses OPENAI_API_KEY env var if not specified)"
    )
    
    parser.add_argument(
        "--blender-path",
        type=str,
        default="blender",
        help="Path to Blender executable"
    )
    
    parser.add_argument(
        "--duration",
        type=float,
        default=5.0,
        help="Video duration in seconds (default: 5.0)"
    )
    
    parser.add_argument(
        "--fps",
        type=int,
        default=24,
        help="Frames per second (default: 24)"
    )
    
    parser.add_argument(
        "--resolution",
        type=str,
        default="1920x1080",
        help="Video resolution (default: 1920x1080)"
    )
    
    parser.add_argument(
        "--quality",
        type=str,
        choices=["LOW", "MEDIUM", "HIGH"],
        default="HIGH",
        help="Render quality (default: HIGH)"
    )
    
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=15,
        help="Maximum review iterations per sub-process (default: 15)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./output",
        help="Output directory (default: ./output)"
    )
    
    parser.add_argument(
        "--load-knowledge",
        type=str,
        nargs="+",
        help="Load knowledge files (tutorials, docs) into RAG system"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (JSON)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(verbose=args.verbose)
    
    # Get API key
    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key not provided. Use --api-key or set OPENAI_API_KEY")
        sys.exit(1)
    
    # Parse resolution
    try:
        width, height = map(int, args.resolution.split('x'))
    except ValueError:
        logger.error(f"Invalid resolution format: {args.resolution}. Use WIDTHxHEIGHT")
        sys.exit(1)
    
    # Load configuration if provided
    config = {}
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {args.config}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}")
            sys.exit(1)
    
    # Update config with command line arguments
    config.update({
        "default_duration": args.duration,
        "default_fps": args.fps,
        "max_iterations": args.max_iterations
    })
    
    try:
        # Initialize pipeline
        logger.info("Initializing Kubrick pipeline...")
        pipeline = KubrickPipeline(
            api_key=api_key,
            blender_path=args.blender_path,
            max_iterations=args.max_iterations,
            output_dir=args.output_dir,
            config=config
        )
        
        # Load knowledge if provided
        if args.load_knowledge:
            for knowledge_file in args.load_knowledge:
                if knowledge_file.endswith('.json'):
                    # Assume it's a tutorials file
                    logger.info(f"Loading tutorials from {knowledge_file}")
                    count = pipeline.load_tutorials_from_file(knowledge_file)
                    logger.info(f"Loaded {count} tutorial documents")
                else:
                    # Load as text file
                    logger.info(f"Loading knowledge from {knowledge_file}")
                    with open(knowledge_file, 'r') as f:
                        content = f.read()
                    count = pipeline.load_knowledge([content])
                    logger.info(f"Loaded {count} documents")
        
        # Create render settings
        render_settings = RenderSettings(
            resolution_x=width,
            resolution_y=height,
            fps=args.fps,
            quality=args.quality
        )
        
        # Generate video
        logger.info(f"Generating video: {args.description}")
        results = pipeline.generate_video(
            description=args.description,
            output_filename=args.output,
            render_settings=render_settings
        )
        
        # Report results
        if results["success"]:
            logger.info(f"Video generated successfully!")
            logger.info(f"Output: {results['output_path']}")
            logger.info(f"Generation time: {results['generation_time']:.2f} seconds")
            logger.info(f"Total iterations: {results['total_iterations']}")
            
            if "final_review" in results:
                logger.info(f"Final score: {results['final_review']['score']:.2f}")
        else:
            logger.error("Video generation failed!")
            logger.error(f"Errors: {json.dumps(results['errors'], indent=2)}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Generation interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()