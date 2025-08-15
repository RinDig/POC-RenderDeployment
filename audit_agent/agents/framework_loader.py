"""
Framework Loader Agent - Loads and extracts relevant sections from framework documents
"""

import os
from typing import Dict
from pypdf import PdfReader
from pydantic import ValidationError

from ..core.base_agent import BaseAgent
from ..models.compliance_models import FrameworkExtract, FrameworkClause


class FrameworkLoaderAgent(BaseAgent):
    """Loads and extracts relevant sections from framework documents"""
    
    def __init__(self, api_key: str = None, framework_cache: Dict[str, str] = None):
        super().__init__("FrameworkLoader", api_key=api_key)
        # Allow sharing framework cache across instances
        # also add a cache for the framework text 
        self.framework_cache = framework_cache if framework_cache is not None else {}
    
    def load_framework_text(self, framework_path: str) -> str:
        """Load framework document text with proper resource cleanup"""
        if framework_path in self.framework_cache:
            return self.framework_cache[framework_path]
        
        reader = None
        try:
            if framework_path.endswith('.pdf'):
                reader = PdfReader(framework_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            else:
                with open(framework_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            
            self.framework_cache[framework_path] = text
            return text
        finally:
            # Ensure PDF reader is properly closed
            if reader and hasattr(reader, 'stream'):
                reader.stream.close()
    
    async def process(self, framework_path: str, category: str) -> FrameworkExtract:
        """Extract relevant framework requirements for a category"""
        print(f"[{self.name}] Loading {framework_path} for category: {category}")
        
        framework_text = self.load_framework_text(framework_path)
        framework_name = os.path.basename(framework_path).replace('.pdf', '')
        
        # Customize prompt based on framework type
        framework_prompts = {
            "GSMS": "Focus on physical/procedural controls, signage requirements, access controls",
            "DRC": "Extract mining rights, exploitation permits, community consultation requirements",
            "ISO27001": "Extract information security controls from Annex A",
            "VPSHR": "Focus on human rights, use of force, grievance mechanisms"
        }
        
        focus_area = ""
        for key, prompt in framework_prompts.items():
            if key.lower() in framework_name.lower():
                focus_area = prompt
                break
        
        prompt = f"""
        Extract all requirements from this framework document related to '{category}'.
        {focus_area}
        
        Look for:
        - Specific requirements, standards, or procedures
        - Compliance obligations
        - Mandatory controls or measures
        - Legal or regulatory requirements
        
        Output as JSON list:
        [
            {{
                "ref": "Section/Para number",
                "requirement": "Specific requirement text"
            }}
        ]
        
        Framework text:
        {framework_text[:20000]}
        """
        
        system_prompt = f"You are a {framework_name} compliance expert extracting specific requirements."
        
        response = self.call_llm(prompt, system_prompt)
        clauses_json = self.extract_json(response)
        
        # Validate clauses
        clauses = []
        for clause in clauses_json:
            try:
                clauses.append(FrameworkClause(**clause))
            except ValidationError:
                continue
        
        return FrameworkExtract(
            category=category,
            framework_name=framework_name,
            clauses=clauses
        )