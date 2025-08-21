"""
Financial penalties configuration for DRC Mining Code violations
Updated per CAMI Decision No. 003/2024
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class PenaltyInfo:
    """Information about a specific penalty"""
    article: str
    violation_description: str
    min_fine_usd: float
    max_fine_usd: float  # We focus on max as per client request
    applies_to: str  # Entity, Individual, or Entity or Individual
    legal_reference: str
    adjustment_factors: Optional[str] = None
    keywords: List[str] = None  # Keywords to match in compliance findings
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


# DRC Mining Code Penalties per Articles 299-311 with CAMI 003/2024 adjustments
# NOTE: Certain penalties excluded from compliance calculations as they fall outside typical audit scope
DRC_MINING_PENALTIES: Dict[str, PenaltyInfo] = {
    # Article 299 - Excluded from calculations (fraud assessment requires forensic/criminal investigation)
    # Note: While penalties up to $2.1M exist for fraud/pillage, these are not assessed in compliance audits
    "299_excluded": PenaltyInfo(
        article="299",
        violation_description="Illicit exploitation (excluding fraud/pillage aspects)",
        min_fine_usd=0,  # Excluded from calculations
        max_fine_usd=0,  # Excluded from calculations
        applies_to="Entity or Individual",
        legal_reference="Mining Code + CAMI 003/2024 (Note: Fraud penalties excluded from audit scope)",
        adjustment_factors="Not calculated - requires criminal investigation",
        keywords=["illegal exploitation", "unauthorized mining", "unlicensed extraction"]
    ),
    
    "299bis": PenaltyInfo(
        article="299 bis",
        violation_description="Human rights violations in mining",
        min_fine_usd=10000,  # per day
        max_fine_usd=42912.25,  # each violation
        applies_to="Entity",
        legal_reference="Mining Code + CAMI 003/2024",
        adjustment_factors="Indexing clause for daily accrual",
        keywords=["human rights", "forced labor", "child labor", "worker abuse", 
                  "community displacement", "violence"]
    ),
    
    "300": PenaltyInfo(
        article="300",
        violation_description="Theft, concealment of minerals (& embezzlement, illicit possession and illegal transport per CAMI)",
        min_fine_usd=10000,
        max_fine_usd=85824.43,
        applies_to="Individual",
        legal_reference="Mining Code + CAMI 003/2024",
        adjustment_factors="Severity-weighted, inflation-indexed",
        keywords=["theft", "concealment", "embezzlement", "illicit possession", 
                  "illegal transport", "stolen minerals", "hidden minerals"]
    ),
    
    "301": PenaltyInfo(
        article="301",
        violation_description="Administrative/procedural noncompliance (including CAMI category of facilitation of diversion)",
        min_fine_usd=500,
        max_fine_usd=42912.25,
        applies_to="Entity",
        legal_reference="Mining Code + CAMI 003/2024",
        adjustment_factors="Base fine scaled annually",
        keywords=["administrative", "procedural", "noncompliance", "missing permits", 
                  "expired licenses", "documentation", "facilitation of diversion"]
    ),
    
    "302": PenaltyInfo(
        article="302",
        violation_description="Unauthorized purchase/sale of minerals",
        min_fine_usd=10000,
        max_fine_usd=128736.67,
        applies_to="Entity or Individual",
        legal_reference="Mining Code + CAMI 003/2024",
        adjustment_factors="Value-based, adjusted to market value",
        keywords=["unauthorized purchase", "unauthorized sale", "illegal trading", 
                  "unlicensed buyer", "black market", "informal trading"]
    ),
    
    "303": PenaltyInfo(
        article="303",
        violation_description="Unauthorized detention of minerals",
        min_fine_usd=5000,
        max_fine_usd=25000,
        applies_to="Individual",
        legal_reference="Mining Code",
        adjustment_factors="Standard administrative fines",
        keywords=["unauthorized detention", "illegal storage", "minerals detention", 
                  "stockpiling without permit"]
    ),
    
    "304": PenaltyInfo(
        article="304 (&299)",
        violation_description="Unauthorized processing/transformation (Illicit activities)",
        min_fine_usd=10000,
        max_fine_usd=1072805.65,
        applies_to="Entity",
        legal_reference="Mining Code + CAMI 003/2024",
        adjustment_factors="Administrative adjustment",
        keywords=["unauthorized processing", "illegal transformation", "unlicensed refining", 
                  "illegal smelting", "processing without permit"]
    ),
    
    "305": PenaltyInfo(
        article="305",
        violation_description="Illegal mineral transport or storage (illicit possession/transport)",
        min_fine_usd=10000,
        max_fine_usd=85824.43,
        applies_to="Entity",
        legal_reference="Mining Code + CAMI 003/2024",
        adjustment_factors="Variable, sector indexed",
        keywords=["illegal transport", "illegal storage", "transport without permit", 
                  "unauthorized movement", "smuggling", "illicit possession"]
    ),
    
    # Article 306 - Modified (obstruction penalties excluded, transparency/traceability included)
    "306": PenaltyInfo(
        article="306",
        violation_description="Transparency & traceability non-compliance",
        min_fine_usd=8000,
        max_fine_usd=42912.25,  # Using standard administrative penalty (obstruction excluded)
        applies_to="Entity or Individual",
        legal_reference="Mining Code + CAMI 003/2024 (Note: Obstruction penalties up to $4.2M excluded)",
        adjustment_factors="Administrative penalties only - obstruction requires separate assessment",
        keywords=["transparency", "traceability", "reporting", "documentation gaps", 
                  "incomplete records", "missing data"]
    ),
    
    "307": PenaltyInfo(
        article="307",
        violation_description="Health, safety, environmental violations",
        min_fine_usd=20000,
        max_fine_usd=42912.25,
        applies_to="Entity",
        legal_reference="Mining Code + CAMI 003/2024",
        adjustment_factors="Administrative decree driven",
        keywords=["health", "safety", "environmental", "pollution", "contamination", 
                  "safety equipment", "protective gear", "environmental damage", "waste"]
    ),
    
    "308": PenaltyInfo(
        article="308",
        violation_description="Damage to mining infrastructure",
        min_fine_usd=20000,
        max_fine_usd=50000,
        applies_to="Entity or Individual",
        legal_reference="Mining Code",
        adjustment_factors="Criminal code also applies",
        keywords=["infrastructure damage", "equipment damage", "vandalism", 
                  "destruction of property", "sabotage"]
    ),
    
    "309": PenaltyInfo(
        article="309",
        violation_description="Breach of ministerial/provincial decrees",
        min_fine_usd=4000,
        max_fine_usd=42912.25,
        applies_to="Entity",
        legal_reference="Mining Code+ CAMI 003/2024",
        adjustment_factors="Administrative adjustment",
        keywords=["ministerial decree", "provincial decree", "decree violation", 
                  "regulatory breach", "government order"]
    ),
    
    "310": PenaltyInfo(
        article="310",
        violation_description="Insult or assault of officials",
        min_fine_usd=1000,
        max_fine_usd=21456.11,
        applies_to="Individual",
        legal_reference="Mining Code + CAMI 003/2024",
        adjustment_factors="Judicial penalties, no adjustment",
        keywords=["insult", "assault", "official", "violence against inspector", 
                  "threatening behavior", "verbal abuse"]
    ),
    
    "311": PenaltyInfo(
        article="311",
        violation_description="Corruption of public officials",
        min_fine_usd=4291.24,
        max_fine_usd=4291.24,  # Fixed amount
        applies_to="Individual",
        legal_reference="Mining Code + CAMI 003/2024",
        adjustment_factors="Criminal sanctions. Anti-corruption law also applies",
        keywords=["corruption", "bribery", "kickback", "illicit payment", 
                  "influence peddling", "graft"]
    )
}

# Penalties excluded from audit calculations but referenced for context
EXCLUDED_PENALTIES = {
    "299_fraud": {
        "article": "299",
        "description": "Fraud and pillage",
        "max_fine_usd": 2145611.26,
        "reason_excluded": "Requires forensic/criminal investigation beyond compliance audit scope",
        "note": "While fraud carries significant penalties, assessment requires specialized investigation"
    },
    "306_obstruction": {
        "article": "306", 
        "description": "Obstruction of mining authorities",
        "max_fine_usd": 4291222.57,
        "reason_excluded": "Operational/criminal matter, not a compliance gap assessment",
        "note": "Obstruction penalties apply to active interference with inspections"
    }
}


def identify_potential_violations(gap_description: str, recommendation: str) -> List[str]:
    """
    Identify potential DRC Mining Code violations based on gap description and recommendations
    
    Args:
        gap_description: The identified compliance gap
        recommendation: The recommendation to address the gap
        
    Returns:
        List of article numbers that may apply
    """
    potential_articles = []
    combined_text = f"{gap_description} {recommendation}".lower()
    
    for article, penalty in DRC_MINING_PENALTIES.items():
        # Check if any keywords match
        for keyword in penalty.keywords:
            if keyword.lower() in combined_text:
                potential_articles.append(article)
                break
    
    return potential_articles


def calculate_max_penalty(articles: List[str]) -> float:
    """
    Calculate maximum potential penalty for a list of violations
    
    Args:
        articles: List of article numbers
        
    Returns:
        Maximum total penalty in USD
    """
    total_penalty = 0.0
    
    for article in articles:
        if article in DRC_MINING_PENALTIES:
            total_penalty += DRC_MINING_PENALTIES[article].max_fine_usd
    
    return total_penalty


def get_penalty_details(article: str) -> Optional[PenaltyInfo]:
    """
    Get detailed penalty information for a specific article
    
    Args:
        article: Article number (e.g., "299", "306")
        
    Returns:
        PenaltyInfo object or None if article not found
    """
    return DRC_MINING_PENALTIES.get(article)


def format_penalty_amount(amount: float) -> str:
    """
    Format penalty amount with proper currency formatting
    
    Args:
        amount: Penalty amount in USD
        
    Returns:
        Formatted string like "$1,234,567.89"
    """
    return f"${amount:,.2f}"


def get_excluded_penalties_context() -> str:
    """
    Get contextual information about penalties excluded from calculations
    
    Returns:
        String with information about excluded penalties for report notes
    """
    context = "Note: Certain DRC Mining Code penalties are excluded from financial exposure calculations:\n"
    
    for key, info in EXCLUDED_PENALTIES.items():
        context += f"- Article {info['article']} ({info['description']}): "
        context += f"Up to {format_penalty_amount(info['max_fine_usd'])} - "
        context += f"{info['reason_excluded']}\n"
    
    return context


def get_audit_scope_disclaimer() -> str:
    """
    Get disclaimer text for audit reports regarding penalty calculations
    
    Returns:
        Disclaimer text for inclusion in reports
    """
    return (
        "Financial exposure calculations are based on compliance gaps identified during "
        "the audit and include administrative and regulatory penalties only. "
        "Penalties related to criminal matters (fraud, obstruction) are noted for reference "
        "but excluded from calculations as they require specialized investigation beyond "
        "the scope of a compliance audit."
    )