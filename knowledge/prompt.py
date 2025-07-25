from typing import Optional, List, Dict, Any
from core.models import VideoDescription, SubProcessDescription, ReviewFeedback


class DirectorPrompts:
    """Prompt templates for LLM-Director agent"""
    
    @staticmethod
    def get_decomposition_prompt(video_desc: VideoDescription, context: str = "") -> str:
        """Get prompt for decomposing video description"""
        
        prompt = f"""You are a film director agent. Decompose the following video description into 5 sub-processes based on mise-en-scène principles:
                1. Scene: Environmental 3D assets (location, scale, textures)
                2. Character: Main actors/characters (selection, position, scale)  
                3. Motion: Character movements and animations
                4. Lighting: Lighting conditions and mood
                5. Cinematography: Camera parameters and movements

                Video Description: {video_desc.text}
                Duration: {video_desc.duration} seconds
                FPS: {video_desc.fps}
                Resolution: {video_desc.resolution[0]}x{video_desc.resolution[1]}

                {f"Relevant Context from Knowledge Base:" if context else ""}
                {context}

                Please provide detailed descriptions for each sub-process in JSON format. Be specific about:
                - Exact positions and scales
                - Timing of actions
                - Visual style and mood
                - Technical parameters

                Output format:
                {{
                    "scene": {{
                        "description": "Detailed scene description",
                        "parameters": {{
                            "environment": "type of environment",
                            "assets": ["list", "of", "assets"],
                            "layout": "spatial arrangement"
                        }}
                    }},
                    "character": {{
                        "description": "Character details",
                        "parameters": {{
                            "character_type": "human/animal/creature",
                            "count": number,
                            "positions": [[x, y, z]],
                            "attributes": {{}}
                        }}
                    }},
                    "motion": {{
                        "description": "Motion and animation details",
                        "parameters": {{
                            "motion_type": "walk/run/custom",
                            "path": [[x1,y1,z1], [x2,y2,z2]],
                            "timing": {{"start": 0, "end": 5}}
                        }}
                    }},
                    "lighting": {{
                        "description": "Lighting setup",
                        "parameters": {{
                            "type": "sun/point/hdri",
                            "time_of_day": "morning/noon/evening/night",
                            "mood": "bright/moody/dramatic"
                        }}
                    }},
                    "cinematography": {{
                        "description": "Camera work",
                        "parameters": {{
                            "shot_type": "wide/medium/close-up",
                            "movement": "static/pan/dolly/orbit",
                            "focal_length": 50
                        }}
                    }}
                }}"""
        
        return prompt
    
    @staticmethod
    def get_enhancement_prompt(video_desc: VideoDescription) -> str:
        """Get prompt for enhancing video description"""
        
        return f"""As a creative film director, enhance this video description with cinematic details:
                Original: {video_desc.text}

                Add specific details about:
                - Visual atmosphere and mood
                - Character appearance and emotions
                - Environmental details
                - Dramatic elements
                - Pacing and rhythm

                Keep the core concept but make it more vivid and production-ready.
                Enhanced description:"""


class ProgrammerPrompts:
    """Prompt templates for LLM-Programmer agent"""
    @staticmethod
    def get_script_generation_prompt(sub_process: SubProcessDescription,
                                   functions: str,
                                   context: str = "",
                                   feedback: Optional[ReviewFeedback] = None) -> str:
        """Get prompt for generating Blender script"""
        
        feedback_section = ""
        if feedback and not feedback.passed:
            feedback_section = f"""
                                IMPORTANT - Previous attempt failed:
                                Issues: {', '.join(feedback.issues)}
                                Suggestions: {', '.join(feedback.suggestions)}

                                Please address these issues in your script.
                                """
        
        prompt = f"""You are a Blender Python scripting expert. Generate a Python script for the following sub-process:
                Sub-process Type: {sub_process.process_type.value}
                Description: {sub_process.description}
                Parameters: {sub_process.parameters}

                Available Functions:
                {functions}

                {f"Relevant Blender Knowledge:" if context else ""}
                {context}

                {feedback_section}

                Requirements:
                1. Use the provided functions when possible
                2. Include proper error handling
                3. Add comments explaining each step
                4. Ensure compatibility with Blender 3.x Python API
                5. Set up the scene properly (clear existing objects if needed)
                6. Return references to created objects

                Generate a complete, executable Blender Python script:"""
        
        return prompt
    
    @staticmethod
    def get_library_update_prompt(feedback: ReviewFeedback) -> str:
        """Get prompt for updating function library"""
        
        return f"""Based on the review feedback, create or update Blender Python functions:
            Issues encountered: {feedback.issues}
            Suggestions: {feedback.suggestions}

            Create new functions or improve existing ones to address these issues. 
            Each function should:
            1. Have clear documentation
            2. Include error handling
            3. Be reusable and parameterized
            4. Follow Blender Python best practices

            Return functions in JSON format:
            {{
                "function_name": "def function_name(params):\\n    # function code",
                "another_function": "def another_function(params):\\n    # function code"
            }}"""
    
    @staticmethod
    def get_function_generation_prompt(function_name: str, 
                                     description: str,
                                     examples: Optional[List[str]] = None) -> str:
        """Get prompt for generating a specific function"""
        
        examples_section = ""
        if examples:
            examples_section = f"""
                                Example usage:
                                {chr(10).join(examples)}
                                """
        
        return f"""Create a Blender Python function with the following specification:
                Function Name: {function_name}
                Description: {description}
                {examples_section}

                Requirements:
                1. Compatible with Blender 3.x API
                2. Include docstring with parameters and return value
                3. Add error handling for common issues
                4. Make it flexible and reusable

                Generate the complete function:"""


class ReviewerPrompts:
    """Prompt templates for VLM-Reviewer agent"""
    @staticmethod
    def get_review_prompt(sub_process: SubProcessDescription,
                         metrics: Dict[str, List[str]]) -> str:
        """Get prompt for reviewing visual output"""
        
        return f"""You are a visual quality reviewer for 3D rendered videos. Review the provided frames:
                Sub-process Type: {sub_process.process_type.value}
                Expected Output: {sub_process.description}
                Parameters: {sub_process.parameters}

                Evaluation Metrics:
                Primary: {', '.join(metrics.get('primary', []))}
                Secondary: {', '.join(metrics.get('secondary', []))}
                General: {', '.join(metrics.get('general', []))}

                Analyze each frame and evaluate:
                1. Does the visual output match the description?
                2. Are all specified parameters correctly implemented?
                3. Technical quality (rendering, artifacts, consistency)
                4. Artistic quality (composition, aesthetics)

                For any issues found, provide specific, actionable suggestions.

                Output your review in JSON format:
                {{
                    "passed": true/false,
                    "score": 0.0-1.0,
                    "issues": [
                        "Specific issue 1",
                        "Specific issue 2"
                    ],
                    "suggestions": [
                        "Actionable suggestion 1",
                        "Actionable suggestion 2"
                    ],
                    "metrics": {{
                        "metric_name": score
                    }}
                }}"""
    
    @staticmethod
    def get_motion_review_prompt(motion_data: Dict[str, Any]) -> str:
        """Get prompt for reviewing character motion"""
        
        return f"""Review the character motion in the provided frames:
                Motion Type: {motion_data.get('type', 'unknown')}
                Start Position: {motion_data.get('start_pos', 'unknown')}
                End Position: {motion_data.get('end_pos', 'unknown')}
                Duration: {motion_data.get('duration', 'unknown')} seconds

                Evaluate:
                1. Motion smoothness and naturalness
                2. Trajectory accuracy
                3. Speed consistency
                4. Physics realism
                5. Start/end position accuracy

                Provide specific feedback on any issues."""
    
    @staticmethod
    def get_camera_review_prompt(camera_data: Dict[str, Any]) -> str:
        """Get prompt for reviewing camera work"""
        
        return f"""Review the camera work in the provided frames:
                Camera Movement: {camera_data.get('movement', 'unknown')}
                Shot Type: {camera_data.get('shot_type', 'unknown')}
                Focal Length: {camera_data.get('focal_length', 'unknown')}mm

                Evaluate:
                1. Framing and composition
                2. Movement smoothness
                3. Focus and depth of field
                4. Adherence to cinematography principles
                5. Overall visual impact

                Provide feedback on camera work quality."""