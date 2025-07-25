import json
from typing import Optional, Dict, Any, List
import openai

from agents.base import BaseAgent
from core.models import SubProcessDescription, ReviewFeedback, ScriptResult
from blender.library import BlenderFunctionLibrary
from knowledge.prompts import ProgrammerPrompts


class LLMProgrammer(BaseAgent):
    """Generates Blender Python scripts"""
    
    def __init__(self, api_key: str, function_library: BlenderFunctionLibrary,
                 rag_kb=None, config=None):
        self.library = function_library
        super().__init__(api_key, rag_kb, config)
    
    def _initialize(self):
        """Initialize OpenAI client"""
        self.client = openai.OpenAI(api_key=self.api_key)
        self.prompts = ProgrammerPrompts()
        self.model = self.config.get('model', 'gpt-4')
    
    def process(self, sub_process: SubProcessDescription, 
                review_feedback: Optional[ReviewFeedback] = None) -> ScriptResult:
        """Main processing: generate script for sub-process"""
        script = self.generate_script(sub_process, review_feedback)
        return ScriptResult(
            success=True,
            script=script,
            output="Script generated successfully"
        )
    
    def generate_script(self, sub_process: SubProcessDescription,
                       review_feedback: Optional[ReviewFeedback] = None) -> str:
        """Generate Blender Python script for sub-process"""
        
        self.log_info(f"Generating script for: {sub_process.process_type.value}")
        
        # Get relevant functions from library
        relevant_functions = self.library.get_relevant_functions(sub_process.process_type)
        
        # Get RAG context
        context = self.get_rag_context(sub_process.description)
        
        # Build prompt
        prompt = self.prompts.get_script_generation_prompt(
            sub_process=sub_process,
            functions=relevant_functions,
            context=context,
            feedback=review_feedback
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            
            script = response.choices[0].message.content
            
            # Extract code from markdown if present
            script = self._extract_code(script)
            
            self.log_info("Script generated successfully")
            return script
            
        except Exception as e:
            self.log_error(f"Failed to generate script: {str(e)}")
            raise
    
    def update_library(self, feedback: ReviewFeedback) -> bool:
        """Update function library based on feedback"""
        
        if not feedback.suggestions:
            return False
        
        self.log_info("Updating function library based on feedback")
        
        prompt = self.prompts.get_library_update_prompt(feedback)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            new_functions = json.loads(response.choices[0].message.content)
            
            # Update library
            updated_count = 0
            for name, code in new_functions.items():
                self.library.update_function(name, code)
                updated_count += 1
            
            self.log_info(f"Updated {updated_count} functions in library")
            return updated_count > 0
            
        except Exception as e:
            self.log_error(f"Failed to update library: {str(e)}")
            return False
    
    def _extract_code(self, text: str) -> str:
        """Extract Python code from markdown code blocks"""
        if "```python" in text:
            # Extract code between ```python and ```
            start = text.find("```python") + 9
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()
        elif "```" in text:
            # Extract code between ``` and ```
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()
        
        # Return as-is if no code blocks found
        return text.strip()
    
    def generate_function(self, function_name: str, description: str, 
                         examples: List[str] = None) -> str:
        """Generate a new function for the library"""
        
        prompt = self.prompts.get_function_generation_prompt(
            function_name=function_name,
            description=description,
            examples=examples
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            function_code = self._extract_code(response.choices[0].message.content)
            return function_code
            
        except Exception as e:
            self.log_error(f"Failed to generate function: {str(e)}")
            raise