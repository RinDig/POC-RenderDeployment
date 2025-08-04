"""
Pydantic models for the compliance analyzer system
"""

from typing import List, Dict
from pydantic import BaseModel, Field


class ParsedStatement(BaseModel):
    """Individual parsed statement from input"""
    category: str = Field(description="Category this statement belongs to")
    statements: List[str] = Field(description="List of compliance-related statements")


class ParsedInput(BaseModel):
    """Structured representation of parsed input"""
    source: str = Field(description="Source document name")
    parsed_data: List[ParsedStatement]


class FrameworkClause(BaseModel):
    """Individual framework requirement"""
    ref: str = Field(description="Reference number/paragraph")
    requirement: str = Field(description="Specific requirement text")


class FrameworkExtract(BaseModel):
    """Extracted framework requirements for a category"""
    category: str
    framework_name: str
    clauses: List[FrameworkClause]


class ComplianceItem(BaseModel):
    """Individual compliance assessment item"""
    question: str = Field(description="What the framework requires")
    input_statement: str = Field(description="What was observed/stated")
    framework_ref: str = Field(description="Framework reference")
    match_score: float = Field(description="Compliance score 0.0-1.0", ge=0.0, le=1.0)
    gap: str = Field(description="Identified gap if any")
    recommendation: str = Field(description="Recommended action")
    # Financial penalty fields (for frameworks with penalties like DRC Mining Code)
    potential_violations: List[str] = Field(default_factory=list, description="Potential article violations")
    max_penalty_usd: float = Field(default=0.0, description="Maximum potential penalty in USD")


class ComparisonResult(BaseModel):
    """Results from comparing input to framework"""
    category: str
    framework: str
    overall_score: float
    items: List[ComplianceItem]
    total_max_penalty_usd: float = Field(default=0.0, description="Total maximum penalty for this category")


class FinalReport(BaseModel):
    """Complete compliance report"""
    timestamp: str
    frameworks: List[str]
    overall_compliance_score: float
    results: List[ComparisonResult]
    executive_summary: str
    critical_recommendations: List[str]
    # Financial exposure summary
    total_max_penalty_usd: float = Field(default=0.0, description="Total maximum financial exposure")
    penalty_summary: Dict[str, float] = Field(default_factory=dict, description="Penalties by framework")