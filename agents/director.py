import json
from typing import List, Optional, Dict, Any
import openai

from agents.base import BaseAgent
from core.models import VideoDescription, SubProcessDescription
from core.enums import SubProcess
from knowledge.prompts import DirectorPrompts


class LLMDirector(BaseAgent):
    """Decomposes video descriptions into sub-processes"""
    
    def _initialize(self):
        """Initialize OpenAI client"""
        self.client = openai.OpenAI(api_key=self.api_key)
        self.prompts = DirectorPrompts()
        self.model = self.config.get('model', 'gpt-4-vision-preview')
    
    def process(self, video_desc: VideoDescription) -> List[SubProcessDescription]:
        """Main processing: decompose video description"""
        return self.decompose(video_desc)
    
    def decompose(self, video_desc: VideoDescription) -> List[SubProcessDescription]:
        """Decompose video description into sub-processes"""
        
        self.log_info(f"Decomposing video description: {video_desc.text[:50]}...")
        
        # Get relevant context from RAG
        context = self.get_rag_context(video_desc.text)
        
        # Build prompt
        prompt = self.prompts.get_decomposition_prompt(
            video_desc=video_desc,
            context=context
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            decomposition = json.loads(response.choices[0].message.content)
            
            # Convert to SubProcessDescription objects
            sub_processes = self._parse_decomposition(decomposition)
            
            self.log_info(f"Successfully decomposed into {len(sub_processes)} sub-processes")
            return sub_processes
            
        except Exception as e:
            self.log_error(f"Failed to decompose video description: {str(e)}")
            raise
    
    def _parse_decomposition(self, decomposition: Dict[str, Any]) -> List[SubProcessDescription]:
        """Parse decomposition JSON into SubProcessDescription objects"""
        sub_processes = []
        
        for idx, process_type in enumerate(SubProcess):
            if process_type.value in decomposition:
                sub_process_data = decomposition[process_type.value]
                sub_processes.append(SubProcessDescription(
                    process_type=process_type,
                    description=sub_process_data.get("description", ""),
                    parameters=sub_process_data.get("parameters", {}),
                    order=idx
                ))
        
        return sub_processes
    
    def enhance_description(self, video_desc: VideoDescription) -> VideoDescription:
        """Enhance video description with additional details"""
        
        prompt = self.prompts.get_enhancement_prompt(video_desc)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8
            )
            
            enhanced_text = response.choices[0].message.content
            video_desc.text = enhanced_text
            return video_desc
            
        except Exception as e:
            self.log_error(f"Failed to enhance description: {str(e)}")
            return video_desc