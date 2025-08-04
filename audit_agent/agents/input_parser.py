"""
Input Parser Agent - Parses raw input documents into structured data
"""

import os
import json
from typing import Optional
from pypdf import PdfReader
from pydantic import ValidationError

from ..core.base_agent import BaseAgent
from ..models.compliance_models import ParsedInput, ParsedStatement


class InputParserAgent(BaseAgent):
    """Parses raw input (PDF, JSON, text) into structured data"""
    
    def __init__(self, api_key: str = None):
        super().__init__("InputParser", api_key=api_key)
    
    def extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF with proper resource cleanup"""
        reader = None
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            raise ValueError(f"Error extracting PDF: {e}")
        finally:
            # Ensure PDF reader is properly closed
            if reader and hasattr(reader, 'stream'):
                reader.stream.close()
    
    async def process(self, input_path: str) -> ParsedInput:
        """Parse input file into structured format"""
        print(f"[{self.name}] Processing input: {input_path}")
        
        # Determine input type and extract content
        if input_path.endswith('.pdf'):
            content = self.extract_pdf_text(input_path)
            input_type = "PDF"
        elif input_path.endswith('.json'):
            with open(input_path, 'r', encoding='utf-8') as f:
                content = json.dumps(json.load(f))
            input_type = "JSON"
        else:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            input_type = "TEXT"
        # TODO: Add support for other input types like Excel, CSV, etc.
        
        # Create parsing prompt
        prompt = f"""
        Parse this {input_type} content into structured compliance statements.
        
        Group statements by relevant compliance categories such as (but not limited to):
        - Site Access and Security
        - Mining Operations
        - Environmental Compliance
        - Safety Procedures
        - Corporate Governance
        - Community Relations
        
        Extract all factual statements, observations, and findings.
        
        Output as JSON in this exact format:
        {{
            "source": "{os.path.basename(input_path)}",
            "parsed_data": [
                {{
                    "category": "Category Name",
                    "statements": ["statement 1", "statement 2", ...]
                }}
            ]
        }}
        
        Content to parse:
        {content[:50000]}  # Limit to prevent token overflow
        """
        
        system_prompt = ("You are an expert compliance auditor parsing field reports and questionnaires, "
                        "your goal is to parse for anything that would be relevant to a compliance audit.")
        
        response = self.call_llm(prompt, system_prompt)
        
        try:
            parsed_json = self.extract_json(response)
        except (ValueError, json.JSONDecodeError) as e:
            print(f"[{self.name}] JSON extraction error: {e}")
            print(f"[{self.name}] Retrying with simpler prompt...")
            
            # Retry with a simpler prompt
            simple_prompt = f"""
            Extract key statements from this {input_type} document.
            
            Return a simple JSON with this format:
            {{
                "source": "{os.path.basename(input_path)}",
                "parsed_data": [
                    {{
                        "category": "General",
                        "statements": ["statement 1", "statement 2"]
                    }}
                ]
            }}
            
            Content (first 10000 chars):
            {content[:10000]}
            """
            
            try:
                response = self.call_llm(simple_prompt, system_prompt)
                parsed_json = self.extract_json(response)
            except Exception as retry_e:
                print(f"[{self.name}] Retry failed: {retry_e}")
                # Return fallback structure
                return ParsedInput(
                    source=os.path.basename(input_path),
                    parsed_data=[ParsedStatement(
                        category="General",
                        statements=[f"Failed to parse {input_type} input. The document may be too complex or contain invalid formatting."]
                    )]
                )
        
        # Validate with Pydantic
        try:
            result = ParsedInput(**parsed_json)
            print(f"[{self.name}] Parsed {len(result.parsed_data)} categories")
            return result
        except ValidationError as e:
            print(f"[{self.name}] Validation error: {e}")
            # Return a basic structure if validation fails
            return ParsedInput(
                source=os.path.basename(input_path),
                parsed_data=[ParsedStatement(
                    category="General",
                    statements=["Failed to parse input properly. Manual review needed."]
                )]
            )