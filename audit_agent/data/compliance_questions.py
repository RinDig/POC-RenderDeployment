"""
Compliance question banks for different regulatory frameworks
Comprehensive questions covering all aspects of compliance
"""

from typing import List, Dict, Any
from audit_agent.models.interview_models import QuestionType


def get_drc_mining_questions() -> List[Dict[str, Any]]:
    """
    DRC Mining Code compliance questions covering Articles 299-311
    Based on CAMI Decision No. 003/2024 requirements
    """
    return [
        # PERMITS & LICENSING (Art. 299, 301)
        {
            "id": "drc_001",
            "category": "Permits",
            "framework_ref": "DRC Art. 299",
            "question_text": "Does the mining operation have a valid exploitation permit?",
            "question_type": QuestionType.YES_NO,
            "weight": 3.0,
            "required": True,
            "follow_up_trigger": {"no": "drc_001a"},
            "evidence_required": True,
            "help_text": "A valid permit is required for all mining operations"
        },
        {
            "id": "drc_001a",
            "category": "Permits",
            "framework_ref": "DRC Art. 299",
            "question_text": "What is preventing permit acquisition?",
            "question_type": QuestionType.TEXT,
            "required": False,
            "weight": 2.0
        },
        {
            "id": "drc_002",
            "category": "Permits",
            "framework_ref": "DRC Art. 301",
            "question_text": "When was the exploitation permit last renewed?",
            "question_type": QuestionType.DATE,
            "required": True,
            "weight": 2.0,
            "help_text": "Provide the most recent renewal date"
        },
        {
            "id": "drc_003",
            "category": "Permits",
            "framework_ref": "DRC Art. 301",
            "question_text": "Are all required administrative documents maintained on-site?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 2.0,
            "evidence_required": True
        },
        {
            "id": "drc_004",
            "category": "Permits",
            "framework_ref": "DRC Art. 301",
            "question_text": "Which documents are currently missing or expired?",
            "question_type": QuestionType.MULTI_SELECT,
            "options": [
                "None - all documents current",
                "Exploitation permit",
                "Environmental permit",
                "Safety certificates",
                "Tax clearance",
                "Export authorization",
                "Other regulatory documents"
            ],
            "required": True,
            "weight": 2.5
        },
        
        # COMMUNITY ENGAGEMENT (Art. 299 bis)
        {
            "id": "drc_010",
            "category": "Community",
            "framework_ref": "DRC Art. 299 bis",
            "question_text": "Have community consultations been conducted in the last 6 months?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 2.5,
            "follow_up_trigger": {"yes": "drc_010a"},
            "evidence_required": True
        },
        {
            "id": "drc_010a",
            "category": "Community",
            "framework_ref": "DRC Art. 299 bis",
            "question_text": "How many community meetings were held?",
            "question_type": QuestionType.NUMBER,
            "validation_rules": {"min": 0, "max": 100},
            "required": False,
            "weight": 1.5
        },
        {
            "id": "drc_011",
            "category": "Community",
            "framework_ref": "DRC Art. 299 bis",
            "question_text": "How many community grievances were received this quarter?",
            "question_type": QuestionType.NUMBER,
            "validation_rules": {"min": 0},
            "required": True,
            "weight": 2.0
        },
        {
            "id": "drc_012",
            "category": "Community",
            "framework_ref": "DRC Art. 299 bis",
            "question_text": "What percentage of grievances have been resolved?",
            "question_type": QuestionType.NUMBER,
            "validation_rules": {"min": 0, "max": 100},
            "required": True,
            "weight": 2.0,
            "help_text": "Enter a percentage between 0 and 100"
        },
        {
            "id": "drc_013",
            "category": "Community",
            "framework_ref": "DRC Art. 299 bis",
            "question_text": "Is there evidence of forced labor or child labor at the site?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 5.0,
            "follow_up_trigger": {"yes": "drc_013a"}
        },
        {
            "id": "drc_013a",
            "category": "Community",
            "framework_ref": "DRC Art. 299 bis",
            "question_text": "Describe the human rights violations observed:",
            "question_type": QuestionType.TEXT,
            "required": False,
            "weight": 5.0
        },
        
        # ENVIRONMENTAL COMPLIANCE (Art. 307)
        {
            "id": "drc_020",
            "category": "Environmental",
            "framework_ref": "DRC Art. 307",
            "question_text": "Is there a current Environmental Impact Assessment (EIA)?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 3.0,
            "evidence_required": True,
            "follow_up_trigger": {"no": "drc_020a"}
        },
        {
            "id": "drc_020a",
            "category": "Environmental",
            "framework_ref": "DRC Art. 307",
            "question_text": "When was the last EIA conducted?",
            "question_type": QuestionType.DATE,
            "required": False,
            "weight": 2.0
        },
        {
            "id": "drc_021",
            "category": "Environmental",
            "framework_ref": "DRC Art. 307",
            "question_text": "Rate the waste management system implementation:",
            "question_type": QuestionType.SCALE,
            "required": True,
            "weight": 2.5,
            "help_text": "1=Non-existent, 2=Poor, 3=Basic, 4=Good, 5=Excellent"
        },
        {
            "id": "drc_022",
            "category": "Environmental",
            "framework_ref": "DRC Art. 307",
            "question_text": "How often is water quality testing performed?",
            "question_type": QuestionType.MULTIPLE_CHOICE,
            "options": ["Never", "Annually", "Quarterly", "Monthly", "Weekly", "Daily"],
            "required": True,
            "weight": 2.0
        },
        {
            "id": "drc_023",
            "category": "Environmental",
            "framework_ref": "DRC Art. 307",
            "question_text": "Have there been any environmental incidents in the past year?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 2.5,
            "follow_up_trigger": {"yes": "drc_023a"}
        },
        {
            "id": "drc_023a",
            "category": "Environmental",
            "framework_ref": "DRC Art. 307",
            "question_text": "Describe the environmental incidents and remediation actions:",
            "question_type": QuestionType.TEXT,
            "required": False,
            "weight": 2.0
        },
        
        # SAFETY & HEALTH (Art. 307)
        {
            "id": "drc_030",
            "category": "Safety",
            "framework_ref": "DRC Art. 307",
            "question_text": "Is personal protective equipment (PPE) provided to all workers?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 3.0
        },
        {
            "id": "drc_031",
            "category": "Safety",
            "framework_ref": "DRC Art. 307",
            "question_text": "How many safety incidents occurred in the last quarter?",
            "question_type": QuestionType.NUMBER,
            "validation_rules": {"min": 0},
            "required": True,
            "weight": 2.5
        },
        {
            "id": "drc_032",
            "category": "Safety",
            "framework_ref": "DRC Art. 307",
            "question_text": "Is there an emergency response plan in place?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 2.5,
            "evidence_required": True
        },
        {
            "id": "drc_033",
            "category": "Safety",
            "framework_ref": "DRC Art. 307",
            "question_text": "When was the last safety drill conducted?",
            "question_type": QuestionType.DATE,
            "required": True,
            "weight": 1.5
        },
        
        # MINERAL TRADING & TRANSPORT (Art. 302, 305)
        {
            "id": "drc_040",
            "category": "Trading",
            "framework_ref": "DRC Art. 302",
            "question_text": "Are all mineral sales conducted through authorized channels?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 3.0
        },
        {
            "id": "drc_041",
            "category": "Trading",
            "framework_ref": "DRC Art. 302",
            "question_text": "Is there evidence of unauthorized mineral trading?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 4.0,
            "follow_up_trigger": {"yes": "drc_041a"}
        },
        {
            "id": "drc_041a",
            "category": "Trading",
            "framework_ref": "DRC Art. 302",
            "question_text": "Describe the unauthorized trading activities:",
            "question_type": QuestionType.TEXT,
            "required": False,
            "weight": 3.0
        },
        {
            "id": "drc_042",
            "category": "Trading",
            "framework_ref": "DRC Art. 305",
            "question_text": "Do all mineral transports have proper documentation?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 2.5,
            "evidence_required": True
        },
        {
            "id": "drc_043",
            "category": "Trading",
            "framework_ref": "DRC Art. 305",
            "question_text": "How many transport permits were issued this month?",
            "question_type": QuestionType.NUMBER,
            "validation_rules": {"min": 0},
            "required": True,
            "weight": 1.5
        },
        
        # TRANSPARENCY & TRACEABILITY (Art. 306)
        {
            "id": "drc_050",
            "category": "Transparency",
            "framework_ref": "DRC Art. 306",
            "question_text": "Are production records maintained and accessible?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 2.5,
            "evidence_required": True
        },
        {
            "id": "drc_051",
            "category": "Transparency",
            "framework_ref": "DRC Art. 306",
            "question_text": "Has the site ever obstructed mining authority inspections?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 4.0,
            "follow_up_trigger": {"yes": "drc_051a"}
        },
        {
            "id": "drc_051a",
            "category": "Transparency",
            "framework_ref": "DRC Art. 306",
            "question_text": "Describe the obstruction incidents:",
            "question_type": QuestionType.TEXT,
            "required": False,
            "weight": 3.0
        },
        {
            "id": "drc_052",
            "category": "Transparency",
            "framework_ref": "DRC Art. 306",
            "question_text": "Is there a mineral traceability system in place?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 2.5
        },
        {
            "id": "drc_053",
            "category": "Transparency",
            "framework_ref": "DRC Art. 306",
            "question_text": "Rate the completeness of production reporting:",
            "question_type": QuestionType.SCALE,
            "required": True,
            "weight": 2.0,
            "help_text": "1=Very incomplete, 5=Fully complete and transparent"
        },
        
        # MINERAL SECURITY (Art. 300, 303)
        {
            "id": "drc_060",
            "category": "Security",
            "framework_ref": "DRC Art. 300",
            "question_text": "Have there been any incidents of mineral theft?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 3.0,
            "follow_up_trigger": {"yes": "drc_060a"}
        },
        {
            "id": "drc_060a",
            "category": "Security",
            "framework_ref": "DRC Art. 300",
            "question_text": "Estimated value of stolen minerals (USD):",
            "question_type": QuestionType.NUMBER,
            "validation_rules": {"min": 0},
            "required": False,
            "weight": 2.5
        },
        {
            "id": "drc_061",
            "category": "Security",
            "framework_ref": "DRC Art. 303",
            "question_text": "Are mineral storage areas properly secured?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 2.0
        },
        {
            "id": "drc_062",
            "category": "Security",
            "framework_ref": "DRC Art. 303",
            "question_text": "Is there 24/7 security monitoring of mineral stockpiles?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 2.0
        },
        
        # PROCESSING & TRANSFORMATION (Art. 304)
        {
            "id": "drc_070",
            "category": "Processing",
            "framework_ref": "DRC Art. 304",
            "question_text": "Does the site have authorization for mineral processing?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 3.0,
            "evidence_required": True
        },
        {
            "id": "drc_071",
            "category": "Processing",
            "framework_ref": "DRC Art. 304",
            "question_text": "Is any unauthorized processing or transformation occurring?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 4.0,
            "follow_up_trigger": {"yes": "drc_071a"}
        },
        {
            "id": "drc_071a",
            "category": "Processing",
            "framework_ref": "DRC Art. 304",
            "question_text": "Describe the unauthorized processing activities:",
            "question_type": QuestionType.TEXT,
            "required": False,
            "weight": 3.0
        }
    ]


def get_iso_14001_questions() -> List[Dict[str, Any]]:
    """
    ISO 14001:2015 Environmental Management System questions
    """
    return [
        # CONTEXT OF THE ORGANIZATION (Clause 4)
        {
            "id": "iso14001_001",
            "category": "Environmental Management",
            "framework_ref": "ISO 14001:4.1",
            "question_text": "Has the organization determined external and internal issues relevant to its environmental management?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 2.0,
            "evidence_required": True
        },
        {
            "id": "iso14001_002",
            "category": "Environmental Management",
            "framework_ref": "ISO 14001:4.2",
            "question_text": "Are interested parties and their requirements identified?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 2.0
        },
        {
            "id": "iso14001_003",
            "category": "Environmental Management",
            "framework_ref": "ISO 14001:4.3",
            "question_text": "Is the scope of the Environmental Management System documented?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 2.5,
            "evidence_required": True
        },
        {
            "id": "iso14001_004",
            "category": "Environmental Management",
            "framework_ref": "ISO 14001:4.4",
            "question_text": "Rate the maturity of your Environmental Management System:",
            "question_type": QuestionType.SCALE,
            "required": True,
            "weight": 3.0,
            "help_text": "1=Non-existent, 2=Initial, 3=Developing, 4=Established, 5=Optimized"
        },
        
        # ENVIRONMENTAL ASPECTS (Clause 6.1.2)
        {
            "id": "iso14001_010",
            "category": "Environmental Aspects",
            "framework_ref": "ISO 14001:6.1.2",
            "question_text": "Have environmental aspects been identified and documented?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 3.0,
            "evidence_required": True
        },
        {
            "id": "iso14001_011",
            "category": "Environmental Aspects",
            "framework_ref": "ISO 14001:6.1.2",
            "question_text": "How often are environmental aspects reviewed?",
            "question_type": QuestionType.MULTIPLE_CHOICE,
            "options": ["Never", "Every 3 years", "Every 2 years", "Annually", "Semi-annually", "Quarterly"],
            "required": True,
            "weight": 2.0
        },
        {
            "id": "iso14001_012",
            "category": "Environmental Aspects",
            "framework_ref": "ISO 14001:6.1.2",
            "question_text": "Are significant environmental aspects determined using defined criteria?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 2.5
        },
        
        # OPERATIONAL CONTROL (Clause 8.1)
        {
            "id": "iso14001_020",
            "category": "Operational Control",
            "framework_ref": "ISO 14001:8.1",
            "question_text": "Are operational controls established for significant environmental aspects?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 3.0
        },
        {
            "id": "iso14001_021",
            "category": "Operational Control",
            "framework_ref": "ISO 14001:8.1",
            "question_text": "Which areas have operational controls in place?",
            "question_type": QuestionType.MULTI_SELECT,
            "options": [
                "Waste management",
                "Air emissions",
                "Water discharge",
                "Energy consumption",
                "Chemical handling",
                "Noise control",
                "Soil contamination prevention"
            ],
            "required": True,
            "weight": 2.5
        },
        {
            "id": "iso14001_022",
            "category": "Operational Control",
            "framework_ref": "ISO 14001:8.2",
            "question_text": "Is there an emergency preparedness and response procedure?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 3.0,
            "evidence_required": True
        },
        
        # PERFORMANCE EVALUATION (Clause 9)
        {
            "id": "iso14001_030",
            "category": "Performance Evaluation",
            "framework_ref": "ISO 14001:9.1",
            "question_text": "Are environmental performance indicators monitored and measured?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 2.5
        },
        {
            "id": "iso14001_031",
            "category": "Performance Evaluation",
            "framework_ref": "ISO 14001:9.1",
            "question_text": "How frequently are internal environmental audits conducted?",
            "question_type": QuestionType.MULTIPLE_CHOICE,
            "options": ["Never", "Every 3 years", "Every 2 years", "Annually", "Semi-annually"],
            "required": True,
            "weight": 2.0
        },
        {
            "id": "iso14001_032",
            "category": "Performance Evaluation",
            "framework_ref": "ISO 14001:9.3",
            "question_text": "When was the last management review conducted?",
            "question_type": QuestionType.DATE,
            "required": True,
            "weight": 2.0
        }
    ]


def get_iso_45001_questions() -> List[Dict[str, Any]]:
    """
    ISO 45001:2018 Occupational Health and Safety questions
    """
    return [
        # HAZARD IDENTIFICATION (Clause 6.1)
        {
            "id": "iso45001_001",
            "category": "Hazard Management",
            "framework_ref": "ISO 45001:6.1",
            "question_text": "Has a hazard identification and risk assessment been conducted?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 3.0,
            "evidence_required": True
        },
        {
            "id": "iso45001_002",
            "category": "Hazard Management",
            "framework_ref": "ISO 45001:6.1",
            "question_text": "How many high-risk activities have been identified?",
            "question_type": QuestionType.NUMBER,
            "validation_rules": {"min": 0},
            "required": True,
            "weight": 2.5
        },
        {
            "id": "iso45001_003",
            "category": "Hazard Management",
            "framework_ref": "ISO 45001:6.1",
            "question_text": "Are control measures implemented for all identified hazards?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 3.0
        },
        
        # WORKER PARTICIPATION (Clause 5.4)
        {
            "id": "iso45001_010",
            "category": "Worker Participation",
            "framework_ref": "ISO 45001:5.4",
            "question_text": "Is there a formal mechanism for worker consultation on safety matters?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 2.5
        },
        {
            "id": "iso45001_011",
            "category": "Worker Participation",
            "framework_ref": "ISO 45001:5.4",
            "question_text": "How often are safety committee meetings held?",
            "question_type": QuestionType.MULTIPLE_CHOICE,
            "options": ["Never", "Annually", "Quarterly", "Monthly", "Weekly"],
            "required": True,
            "weight": 2.0
        },
        
        # INCIDENT INVESTIGATION (Clause 10.2)
        {
            "id": "iso45001_020",
            "category": "Incident Management",
            "framework_ref": "ISO 45001:10.2",
            "question_text": "Is there a formal incident investigation procedure?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 3.0,
            "evidence_required": True
        },
        {
            "id": "iso45001_021",
            "category": "Incident Management",
            "framework_ref": "ISO 45001:10.2",
            "question_text": "What percentage of incidents result in corrective actions?",
            "question_type": QuestionType.NUMBER,
            "validation_rules": {"min": 0, "max": 100},
            "required": True,
            "weight": 2.0
        }
    ]


def get_vpshr_questions() -> List[Dict[str, Any]]:
    """
    Voluntary Principles on Security and Human Rights questions
    """
    return [
        # RISK ASSESSMENT
        {
            "id": "vpshr_001",
            "category": "Risk Assessment",
            "framework_ref": "VPSHR 1.A",
            "question_text": "Has a security and human rights risk assessment been conducted?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 3.0,
            "evidence_required": True
        },
        {
            "id": "vpshr_002",
            "category": "Risk Assessment",
            "framework_ref": "VPSHR 1.B",
            "question_text": "Does the risk assessment consider potential for violence?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 2.5
        },
        {
            "id": "vpshr_003",
            "category": "Risk Assessment",
            "framework_ref": "VPSHR 1.C",
            "question_text": "Are human rights records of security providers assessed?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 3.0
        },
        
        # SECURITY ARRANGEMENTS
        {
            "id": "vpshr_010",
            "category": "Security Arrangements",
            "framework_ref": "VPSHR 2.A",
            "question_text": "Are security personnel trained on human rights and use of force?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 3.5,
            "evidence_required": True
        },
        {
            "id": "vpshr_011",
            "category": "Security Arrangements",
            "framework_ref": "VPSHR 2.B",
            "question_text": "How many security personnel have received human rights training?",
            "question_type": QuestionType.NUMBER,
            "validation_rules": {"min": 0},
            "required": True,
            "weight": 2.0
        },
        {
            "id": "vpshr_012",
            "category": "Security Arrangements",
            "framework_ref": "VPSHR 2.C",
            "question_text": "Is there a policy on the use of force by security personnel?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 3.0,
            "evidence_required": True
        },
        
        # COMMUNITY ENGAGEMENT
        {
            "id": "vpshr_020",
            "category": "Community Engagement",
            "framework_ref": "VPSHR 3.A",
            "question_text": "Is there a grievance mechanism for security-related complaints?",
            "question_type": QuestionType.YES_NO,
            "required": True,
            "weight": 3.0
        },
        {
            "id": "vpshr_021",
            "category": "Community Engagement",
            "framework_ref": "VPSHR 3.B",
            "question_text": "How many security-related grievances were received last quarter?",
            "question_type": QuestionType.NUMBER,
            "validation_rules": {"min": 0},
            "required": True,
            "weight": 2.0
        },
        {
            "id": "vpshr_022",
            "category": "Community Engagement",
            "framework_ref": "VPSHR 3.C",
            "question_text": "Rate the effectiveness of community engagement on security issues:",
            "question_type": QuestionType.SCALE,
            "required": True,
            "weight": 2.5,
            "help_text": "1=Very poor, 5=Excellent"
        }
    ]


# Question bank registry
QUESTION_BANKS = {
    "DRC_Mining_Code": get_drc_mining_questions,
    "DRC_Mining_Code_2018": get_drc_mining_questions,
    "ISO_14001": get_iso_14001_questions,
    "ISO_14001_2015": get_iso_14001_questions,
    "ISO_45001": get_iso_45001_questions,
    "ISO_45001_2018": get_iso_45001_questions,
    "VPSHR": get_vpshr_questions,
    "VPSHR_2020": get_vpshr_questions
}


def get_questions_for_framework(framework: str, categories: List[str] = None) -> List[Dict[str, Any]]:
    """
    Get questions for a specific framework, optionally filtered by categories
    
    Args:
        framework: The framework identifier
        categories: Optional list of categories to filter by
    
    Returns:
        List of question dictionaries
    """
    # Get the question loader function
    loader = QUESTION_BANKS.get(framework)
    if not loader:
        # Try to find a partial match
        for key, func in QUESTION_BANKS.items():
            if framework.lower() in key.lower() or key.lower() in framework.lower():
                loader = func
                break
    
    if not loader:
        return []
    
    # Get all questions
    questions = loader()
    
    # Filter by categories if specified
    if categories:
        questions = [q for q in questions if q.get("category") in categories]
    
    return questions


def get_available_frameworks() -> List[str]:
    """Get list of available frameworks"""
    return list(QUESTION_BANKS.keys())


def get_categories_for_framework(framework: str) -> List[str]:
    """Get unique categories for a framework"""
    questions = get_questions_for_framework(framework)
    categories = list(set(q.get("category") for q in questions if q.get("category")))
    return sorted(categories)