"""
Custom exceptions for the audit agent system
"""


class AuditAgentError(Exception):
    """Base exception for all audit agent errors"""
    pass


class APIKeyError(AuditAgentError):
    """Raised when API key is missing or invalid"""
    pass


class DocumentParsingError(AuditAgentError):
    """Raised when document parsing fails"""
    def __init__(self, document_name: str, message: str):
        self.document_name = document_name
        super().__init__(f"Failed to parse {document_name}: {message}")


class FrameworkLoadError(AuditAgentError):
    """Raised when framework loading fails"""
    def __init__(self, framework_name: str, message: str):
        self.framework_name = framework_name
        super().__init__(f"Failed to load framework {framework_name}: {message}")


class ComplianceAnalysisError(AuditAgentError):
    """Raised when compliance analysis fails"""
    def __init__(self, category: str, framework: str, message: str):
        self.category = category
        self.framework = framework
        super().__init__(f"Analysis failed for {category} against {framework}: {message}")


class LLMError(AuditAgentError):
    """Raised when LLM operations fail"""
    def __init__(self, agent_name: str, message: str):
        self.agent_name = agent_name
        super().__init__(f"LLM error in {agent_name}: {message}")


class ValidationError(AuditAgentError):
    """Raised when data validation fails"""
    pass