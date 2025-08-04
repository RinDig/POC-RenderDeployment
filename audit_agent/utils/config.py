"""
Configuration settings and constants for the audit agent system
"""

# Model settings
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 2000

# Framework specific settings
FRAMEWORK_PROMPTS = {
    "GSMS": "Focus on physical/procedural controls, signage requirements, access controls",
    "DRC": "Extract mining rights, exploitation permits, community consultation requirements",
    "ISO27001": "Extract information security controls from Annex A",
    "VPSHR": "Focus on human rights, use of force, grievance mechanisms"
}

# Compliance categories
DEFAULT_CATEGORIES = [
    "Site Access and Security",
    "Mining Operations",
    "Environmental Compliance",
    "Safety Procedures",
    "Corporate Governance",
    "Community Relations"
]

# Scoring thresholds
CRITICAL_THRESHOLD = 0.5
WARNING_THRESHOLD = 0.8

# Excel formatting colors
EXCEL_COLORS = {
    "header": "1F4E78",
    "critical": "FF6B6B",
    "warning": "FFD93D",
    "good": "6BCF7F",
    "priority_critical": "D32F2F",
    "priority_medium": "F57C00",
    "priority_low": "388E3C"
}

# File size limits
MAX_PDF_PAGES = 500
MAX_TEXT_LENGTH = 50000  # Characters to send to LLM

# Supported file extensions
SUPPORTED_INPUT_FORMATS = [".pdf", ".json", ".txt", ".docx"]
SUPPORTED_FRAMEWORK_FORMATS = [".pdf", ".txt", ".docx"]