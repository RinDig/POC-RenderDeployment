"""
Compliance Orchestrator - Coordinates all agents for compliance analysis
"""

import os
from typing import List, Optional, Dict

from ..agents.input_parser import InputParserAgent
from ..agents.framework_loader import FrameworkLoaderAgent
from ..agents.comparator import ComparatorAgent
from ..agents.aggregator import AggregatorAgent
from ..models.compliance_models import FinalReport


class ComplianceOrchestrator:
    """Orchestrates the multi-agent compliance analysis"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        # Share framework cache across all instances
        self.framework_cache: Dict[str, str] = {}
        self.input_parser = InputParserAgent(api_key=api_key)
        self.framework_loader = FrameworkLoaderAgent(api_key=api_key, framework_cache=self.framework_cache)
        self.aggregator = AggregatorAgent(api_key=api_key)
        self.comparators: Dict[str, ComparatorAgent] = {}
    
    def get_or_create_comparator(self, framework_name: str) -> ComparatorAgent:
        """Get or create a comparator agent for a framework"""
        if framework_name not in self.comparators:
            self.comparators[framework_name] = ComparatorAgent(framework_name, api_key=self.api_key)
        return self.comparators[framework_name]
    
    async def analyze(self, input_path: str, framework_paths: List[str], 
                    categories: Optional[List[str]] = None) -> FinalReport:
        """Run the complete compliance analysis"""
        print("\n=== Starting Multi-Agent Compliance Analysis ===\n")
        
        # Step 1: Parse input
        parsed_input = await self.input_parser.process(input_path)
        
        # Determine categories to analyze
        if not categories:
            categories = [stmt.category for stmt in parsed_input.parsed_data]
        
        # Step 2 & 3: Load frameworks and compare
        all_results = []
        
        for framework_path in framework_paths:
            framework_name = os.path.basename(framework_path).replace('.pdf', '')
            comparator = self.get_or_create_comparator(framework_name)
            
            for category in categories:
                # Find matching parsed statements
                matching_statements = next(
                    (stmt for stmt in parsed_input.parsed_data if stmt.category == category),
                    None
                )
                
                if not matching_statements:
                    continue
                
                # Load framework requirements
                framework_extract = await self.framework_loader.process(framework_path, category)
                
                # Compare
                comparison_result = await comparator.process(matching_statements, framework_extract)
                all_results.append(comparison_result)
        
        # Step 4: Aggregate results
        final_report = await self.aggregator.process(all_results)
        
        return final_report
    
    async def cleanup(self) -> None:
        """Cleanup all agent resources"""
        try:
            # Cleanup all agents
            await self.input_parser.cleanup()
            await self.framework_loader.cleanup()
            await self.aggregator.cleanup()
            
            # Cleanup all comparators
            for comparator in self.comparators.values():
                await comparator.cleanup()
            
            # Clear comparators dict
            self.comparators.clear()
            
            # Clear framework cache
            self.framework_cache.clear()
        except Exception as e:
            print(f"Error during orchestrator cleanup: {e}")