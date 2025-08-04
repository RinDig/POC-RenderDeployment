"""
Comparator Agent - Compares input statements to framework requirements
"""

import json
from typing import Dict
from pydantic import ValidationError

from ..core.base_agent import BaseAgent
from ..models.compliance_models import (
    ParsedStatement, FrameworkExtract, ComparisonResult, ComplianceItem
)
from ..utils.penalties import (
    identify_potential_violations, 
    calculate_max_penalty,
    DRC_MINING_PENALTIES
)


class ComparatorAgent(BaseAgent):
    """Compares input statements to framework requirements"""
    
    def __init__(self, framework_name: str, api_key: str = None):
        super().__init__(f"Comparator_{framework_name}", api_key=api_key)
        self.framework_name = framework_name
    
    def get_framework_specific_prompt(self) -> str:
        """Get framework-specific comparison instructions"""
        prompts = {
            "GSMS": """
                Focus on physical and procedural controls:
                - Is signage compliant with statutory warnings?
                - Are access controls properly implemented?
                - Do procedures meet safety standards?
                Rate as Compliant/Partially Compliant/Non-Compliant.
            """,
            "DRC": """
                Check legal obligations per DRC Mining Code:
                - Valid exploitation permits? (Art. 299, 301)
                - Evidence of community consultations? (Art. 299 bis)
                - Environmental impact assessments? (Art. 307)
                - Proper documentation and procedures? (Art. 301)
                - Transparency and traceability compliance? (Art. 306)
                - Legal mineral trading and transport? (Art. 302, 305)
                Be specific about which articles may be violated.
            """,
            "ISO27001": """
                Map to security controls:
                - Access logging requirements met?
                - Risk treatment plans in place?
                - Information classification implemented?
                - Incident response procedures?
            """,
            "VPSHR": """
                Assess human rights aspects:
                - Training on use of force?
                - Grievance mechanisms for communities?
                - Risk assessments conducted?
                - Stakeholder engagement evidence?
            """
        }
        
        for key, prompt in prompts.items():
            if key.lower() in self.framework_name.lower():
                return prompt
        return "Compare input statements to framework requirements."
    
    async def process(self, parsed_input: ParsedStatement, 
                     framework_extract: FrameworkExtract) -> ComparisonResult:
        """Compare input statements to framework requirements"""
        print(f"[{self.name}] Comparing {framework_extract.category}")
        
        prompt = f"""
        Compare field observations to {self.framework_name} requirements.
        
        {self.get_framework_specific_prompt()}
        
        For each framework requirement:
        1. Find the most relevant input statement(s)
        2. Score compliance (0.0 = non-compliant, 0.5 = partially compliant, 1.0 = fully compliant)
        3. Identify specific gaps
        4. Provide actionable recommendations
        
        Framework requirements:
        {json.dumps([clause.model_dump() for clause in framework_extract.clauses], indent=2)}
        
        Field observations:
        {json.dumps(parsed_input.statements, indent=2)}
        
        Output as JSON list:
        [
            {{
                "question": "What the framework requires",
                "input_statement": "What was observed/reported",
                "framework_ref": "Specific reference",
                "match_score": 0.0 to 1.0,
                "gap": "Specific gap identified",
                "recommendation": "Specific action to close gap"
            }}
        ]
        """
        
        system_prompt = f"You are a {self.framework_name} compliance expert auditor."
        
        response = self.call_llm(prompt, system_prompt)
        items_json = self.extract_json(response)
        
        # Validate items and add penalty calculations for DRC Mining Code
        items = []
        total_penalty = 0.0
        
        for item in items_json:
            try:
                compliance_item = ComplianceItem(**item)
                
                # If this is DRC Mining Code and there's a gap (non-compliant)
                if "DRC" in self.framework_name.upper() and compliance_item.match_score < 1.0:
                    # Identify potential violations based on gap and recommendation
                    violations = identify_potential_violations(
                        compliance_item.gap, 
                        compliance_item.recommendation
                    )
                    
                    if violations:
                        compliance_item.potential_violations = violations
                        compliance_item.max_penalty_usd = calculate_max_penalty(violations)
                        total_penalty += compliance_item.max_penalty_usd
                
                items.append(compliance_item)
                
            except ValidationError as e:
                print(f"[{self.name}] Item validation error: {e}")
                continue
        
        # Calculate overall score
        overall_score = sum(item.match_score for item in items) / len(items) if items else 0.0
        
        return ComparisonResult(
            category=parsed_input.category,
            framework=self.framework_name,
            overall_score=overall_score,
            items=items,
            total_max_penalty_usd=total_penalty
        )