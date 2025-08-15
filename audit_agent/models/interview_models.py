"""
Pydantic models for the compliance interview system
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
from datetime import datetime


class QuestionType(str, Enum):
    """Types of questions supported in interviews"""
    YES_NO = "yes_no"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    SCALE = "scale"  # 1-5 rating
    MULTI_SELECT = "multi_select"  # Multiple selections allowed


class ComplianceQuestion(BaseModel):
    """Individual compliance question with metadata"""
    id: str
    category: str = Field(description="Category this question belongs to (e.g., Permits, Environmental)")
    framework_ref: str = Field(description="Framework reference (e.g., 'DRC Art. 299', 'ISO 14001:4.4')")
    question_text: str = Field(description="The question to ask")
    question_type: QuestionType
    options: Optional[List[str]] = Field(None, description="Options for multiple choice questions")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Validation constraints")
    follow_up_trigger: Optional[Dict[str, str]] = Field(None, description="Conditional follow-up questions")
    weight: float = Field(1.0, ge=0.0, le=5.0, description="Importance weight for scoring")
    required: bool = Field(True, description="Whether this question must be answered")
    help_text: Optional[str] = Field(None, description="Additional guidance for the user")
    evidence_required: bool = Field(False, description="Whether supporting documentation is needed")
    
    @field_validator('options')
    @classmethod
    def validate_options(cls, v, info):
        """Ensure options are provided for multiple choice questions"""
        if info.data.get('question_type') in [QuestionType.MULTIPLE_CHOICE, QuestionType.MULTI_SELECT]:
            if not v or len(v) < 2:
                raise ValueError("Multiple choice questions must have at least 2 options")
        return v


class InterviewAnswer(BaseModel):
    """Answer to a compliance question"""
    question_id: str
    answer: Any = Field(description="The answer value (type depends on question type)")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="User's confidence in answer (0-1)")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes or context")
    evidence_files: Optional[List[str]] = Field(default_factory=list, description="Paths to uploaded evidence")
    ai_clarifications: Optional[List[Dict[str, str]]] = Field(None, description="AI-generated follow-up Q&As")
    needs_ai_followup: Optional[bool] = Field(False, description="Whether AI clarification is needed")
    
    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        """Ensure confidence is within valid range"""
        if v is not None and not 0 <= v <= 1:
            raise ValueError('Confidence must be between 0 and 1')
        return v


class InterviewStatus(str, Enum):
    """Status of an interview session"""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"
    ABANDONED = "abandoned"


class InterviewSession(BaseModel):
    """Complete interview session state"""
    session_id: str
    framework: str = Field(description="Framework being assessed (e.g., 'DRC_Mining_Code')")
    site_name: str
    site_code: Optional[str] = None
    operator: Optional[str] = None
    auditor_name: str
    auditor_email: Optional[str] = None
    language: str = Field("en", description="Language code for the interview")
    started_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    last_activity_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    current_question_index: int = Field(0, ge=0)
    total_questions: int = Field(ge=0)
    answers: List[InterviewAnswer] = Field(default_factory=list)
    status: InterviewStatus = Field(InterviewStatus.IN_PROGRESS)
    progress_percentage: float = Field(0.0, ge=0.0, le=100.0)
    categories_completed: List[str] = Field(default_factory=list)
    estimated_time_remaining_minutes: Optional[int] = None
    
    @model_validator(mode='after')
    def update_progress(self) -> 'InterviewSession':
        """Update progress percentage based on answers"""
        if self.total_questions > 0:
            # Ensure progress doesn't exceed 100%
            self.progress_percentage = min(100.0, round((len(self.answers) / self.total_questions) * 100, 1))
        
        # Update last activity
        self.last_activity_at = datetime.now().isoformat()
        
        # Estimate remaining time (30 seconds per question average)
        remaining_questions = self.total_questions - len(self.answers)
        self.estimated_time_remaining_minutes = max(0, (remaining_questions * 30) // 60)
        
        return self


class CategoryProgress(BaseModel):
    """Progress tracking for a specific category"""
    category: str
    total_questions: int = Field(ge=0)
    answered_questions: int = Field(ge=0)
    required_questions: int = Field(ge=0)
    required_answered: int = Field(ge=0)
    completion_percentage: float = Field(0.0, ge=0.0, le=100.0)
    
    @model_validator(mode='after')
    def calculate_completion(self) -> 'CategoryProgress':
        """Calculate completion percentage"""
        if self.total_questions > 0:
            self.completion_percentage = round((self.answered_questions / self.total_questions) * 100, 1)
        return self


class InterviewProgressResponse(BaseModel):
    """Response for progress check endpoint"""
    session_id: str
    overall_progress: float = Field(ge=0.0, le=100.0)
    questions_answered: int = Field(ge=0)
    total_questions: int = Field(ge=0)
    required_remaining: int = Field(ge=0)
    category_progress: List[CategoryProgress]
    estimated_time_remaining_minutes: int = Field(ge=0)
    current_category: Optional[str] = None
    status: InterviewStatus


class InterviewExport(BaseModel):
    """Export format compatible with existing pipeline"""
    session_metadata: InterviewSession
    structured_responses: Dict[str, List[str]] = Field(
        description="Category -> List of compliance statements"
    )
    compliance_summary: str = Field(
        description="AI-generated summary of compliance status"
    )
    compliance_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Category -> Score (0.0-1.0)"
    )
    identified_gaps: List[str] = Field(
        default_factory=list,
        description="List of identified compliance gaps"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="List of recommendations"
    )
    raw_qa_pairs: List[Dict[str, Any]] = Field(
        description="Complete Q&A data for reference"
    )
    export_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    format_version: str = Field("1.0", description="Export format version")


class QuestionValidationError(BaseModel):
    """Error details for answer validation"""
    question_id: str
    error_type: str
    message: str
    expected_format: Optional[str] = None


class AnswerSubmissionResponse(BaseModel):
    """Response after submitting an answer"""
    status: Literal["accepted", "validation_error", "session_complete"]
    progress: float = Field(ge=0.0, le=100.0)
    next_question: Optional[ComplianceQuestion] = None
    validation_error: Optional[QuestionValidationError] = None
    session_complete: bool = Field(False)
    categories_remaining: Optional[List[str]] = None


class InterviewStartRequest(BaseModel):
    """Request to start a new interview session"""
    framework: str = Field(description="Framework to assess against")
    site_name: str
    site_code: Optional[str] = None
    operator: Optional[str] = None
    auditor_name: str
    auditor_email: Optional[str] = None
    language: str = Field("en")
    categories: Optional[List[str]] = Field(None, description="Specific categories to assess")


class InterviewResumeResponse(BaseModel):
    """Response when resuming an interview"""
    session: InterviewSession
    current_question: Optional[ComplianceQuestion] = None
    categories_available: List[str]
    message: str = Field("Interview session resumed successfully")