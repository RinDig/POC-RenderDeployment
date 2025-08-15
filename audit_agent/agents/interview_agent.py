"""
Interview Agent - Conducts structured compliance interviews
Uses async OpenAI for intelligent conversation and summary generation
"""

import json
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from audit_agent.models.interview_models import (
    ComplianceQuestion,
    InterviewAnswer,
    InterviewSession,
    InterviewStatus,
    InterviewExport,
    CategoryProgress,
    AnswerSubmissionResponse,
    QuestionValidationError,
    QuestionType
)
from audit_agent.data.compliance_questions import (
    get_questions_for_framework,
    get_categories_for_framework
)
from audit_agent.utils.client_pool import OpenAIClientPool

logger = logging.getLogger(__name__)


class InterviewAgent:
    """Conducts structured compliance interviews with intelligent processing"""
    
    def __init__(self, framework: str, api_key: str = None):
        """
        Initialize the interview agent for a specific framework
        
        Args:
            framework: The compliance framework to assess
            api_key: Optional OpenAI API key
        """
        self.framework = framework
        self.questions = self._load_and_prepare_questions()
        self.sessions: Dict[str, InterviewSession] = {}
        
        # Get OpenAI client from pool
        pool = OpenAIClientPool()
        import os
        self.client = pool.get_client(api_key or os.getenv("OPENAI_API_KEY", "dummy-key"))
        
        # Track follow-up questions
        self.follow_up_map: Dict[str, List[str]] = self._build_follow_up_map()
        
        logger.info(f"Initialized InterviewAgent for {framework} with {len(self.questions)} questions")
    
    def _load_and_prepare_questions(self) -> List[ComplianceQuestion]:
        """Load and convert questions to Pydantic models"""
        raw_questions = get_questions_for_framework(self.framework)
        questions = []
        
        for q_dict in raw_questions:
            try:
                question = ComplianceQuestion(**q_dict)
                questions.append(question)
            except Exception as e:
                logger.error(f"Failed to parse question {q_dict.get('id')}: {e}")
                continue
        
        return questions
    
    def _build_follow_up_map(self) -> Dict[str, List[str]]:
        """Build a map of question triggers to follow-up question IDs"""
        follow_up_map = {}
        
        for question in self.questions:
            if question.follow_up_trigger:
                for answer_value, follow_up_id in question.follow_up_trigger.items():
                    key = f"{question.id}:{answer_value}"
                    if key not in follow_up_map:
                        follow_up_map[key] = []
                    follow_up_map[key].append(follow_up_id)
        
        return follow_up_map
    
    async def get_ai_clarification(self, question: ComplianceQuestion, answer_value: Any, notes: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get AI-generated clarification for critical 'no' answers"""
        # Only trigger for critical questions with 'no' answers
        if not (question.weight >= 2.5 and answer_value in [False, "no", "No", 0]):
            return []
        
        # Skip if no valid API key
        if not self.client or "dummy" in str(self.client):
            return []
        
        try:
            prompt = f"""
Compliance gap detected. The auditor answered 'No' to:
Question: {question.question_text}
Reference: {question.framework_ref}
Category: {question.category}
{f'Notes: {notes}' if notes else ''}

Generate exactly 2-3 targeted follow-up questions to understand:
1. Root cause of non-compliance
2. Current mitigation measures or workarounds
3. Timeline and plan for remediation

Return as JSON with this structure:
{{"questions": [{{
  "question": "specific question text",
  "purpose": "what this reveals"
}}]}}

Keep questions short and specific.
"""
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a compliance expert. Generate precise follow-up questions for compliance gaps."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=400
            )
            
            content = response.choices[0].message.content
            # Parse JSON from response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("questions", [])[:3]
            
            return []
            
        except Exception as e:
            logger.warning(f"AI clarification failed: {e}")
            return []
    
    def start_session(
        self,
        site_name: str,
        auditor_name: str,
        site_code: Optional[str] = None,
        operator: Optional[str] = None,
        auditor_email: Optional[str] = None,
        language: str = "en",
        categories: Optional[List[str]] = None
    ) -> InterviewSession:
        """
        Start a new interview session
        
        Args:
            site_name: Name of the site being audited
            auditor_name: Name of the auditor
            site_code: Optional site code
            operator: Optional operator name
            auditor_email: Optional auditor email
            language: Language for the interview
            categories: Optional specific categories to assess
        
        Returns:
            New InterviewSession instance
        """
        # Filter questions by categories if specified
        session_questions = self.questions
        if categories:
            session_questions = [q for q in self.questions if q.category in categories]
        
        session = InterviewSession(
            session_id=str(uuid.uuid4()),
            framework=self.framework,
            site_name=site_name,
            site_code=site_code,
            operator=operator,
            auditor_name=auditor_name,
            auditor_email=auditor_email,
            language=language,
            total_questions=len(session_questions),
            status=InterviewStatus.IN_PROGRESS
        )
        
        self.sessions[session.session_id] = session
        logger.info(f"Started interview session {session.session_id} for {site_name}")
        
        return session
    
    def get_session(self, session_id: str) -> Optional[InterviewSession]:
        """Get a session by ID"""
        return self.sessions.get(session_id)
    
    def get_next_question(self, session_id: str) -> Optional[ComplianceQuestion]:
        """
        Get the next question for the session
        
        Args:
            session_id: The session ID
        
        Returns:
            Next ComplianceQuestion or None if complete
        """
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        # Check for triggered follow-ups first
        if session.answers:
            last_answer = session.answers[-1]
            follow_up = self._check_follow_up(last_answer)
            if follow_up:
                return follow_up
        
        # Get next regular question
        answered_ids = {a.question_id for a in session.answers}
        for question in self.questions:
            if question.id not in answered_ids:
                return question
        
        return None
    
    def _check_follow_up(self, answer: InterviewAnswer) -> Optional[ComplianceQuestion]:
        """Check if an answer triggers a follow-up question"""
        # Build trigger key based on answer value
        answer_str = str(answer.answer).lower()
        
        # For boolean answers
        if answer_str in ["true", "false"]:
            answer_str = "yes" if answer_str == "true" else "no"
        
        trigger_key = f"{answer.question_id}:{answer_str}"
        
        # Check if this triggers any follow-ups
        follow_up_ids = self.follow_up_map.get(trigger_key, [])
        
        # Return first follow-up that hasn't been answered
        session = next((s for s in self.sessions.values() if any(a.question_id == answer.question_id for a in s.answers)), None)
        if session:
            answered_ids = {a.question_id for a in session.answers}
            for follow_up_id in follow_up_ids:
                if follow_up_id not in answered_ids:
                    # Find and return the follow-up question
                    for question in self.questions:
                        if question.id == follow_up_id:
                            return question
        
        return None
    
    def validate_answer(self, question: ComplianceQuestion, answer_value: Any) -> Optional[QuestionValidationError]:
        """
        Validate an answer against question rules
        
        Args:
            question: The question being answered
            answer_value: The provided answer
        
        Returns:
            ValidationError if invalid, None if valid
        """
        # Type-specific validation
        if question.question_type == QuestionType.YES_NO:
            if not isinstance(answer_value, bool) and answer_value not in ["yes", "no", "true", "false", True, False]:
                return QuestionValidationError(
                    question_id=question.id,
                    error_type="type_error",
                    message="Answer must be yes/no or true/false",
                    expected_format="boolean"
                )
        
        elif question.question_type == QuestionType.NUMBER:
            try:
                num_value = float(answer_value)
                if question.validation_rules:
                    if "min" in question.validation_rules and num_value < question.validation_rules["min"]:
                        return QuestionValidationError(
                            question_id=question.id,
                            error_type="range_error",
                            message=f"Value must be at least {question.validation_rules['min']}",
                            expected_format="number"
                        )
                    if "max" in question.validation_rules and num_value > question.validation_rules["max"]:
                        return QuestionValidationError(
                            question_id=question.id,
                            error_type="range_error",
                            message=f"Value must be at most {question.validation_rules['max']}",
                            expected_format="number"
                        )
            except (ValueError, TypeError):
                return QuestionValidationError(
                    question_id=question.id,
                    error_type="type_error",
                    message="Answer must be a number",
                    expected_format="number"
                )
        
        elif question.question_type == QuestionType.SCALE:
            try:
                scale_value = int(answer_value)
                if scale_value < 1 or scale_value > 5:
                    return QuestionValidationError(
                        question_id=question.id,
                        error_type="range_error",
                        message="Scale value must be between 1 and 5",
                        expected_format="1-5"
                    )
            except (ValueError, TypeError):
                return QuestionValidationError(
                    question_id=question.id,
                    error_type="type_error",
                    message="Answer must be a number between 1 and 5",
                    expected_format="1-5"
                )
        
        elif question.question_type == QuestionType.MULTIPLE_CHOICE:
            if question.options and answer_value not in question.options:
                return QuestionValidationError(
                    question_id=question.id,
                    error_type="invalid_option",
                    message=f"Answer must be one of: {', '.join(question.options)}",
                    expected_format="select one option"
                )
        
        elif question.question_type == QuestionType.MULTI_SELECT:
            if not isinstance(answer_value, list):
                return QuestionValidationError(
                    question_id=question.id,
                    error_type="type_error",
                    message="Answer must be a list of selections",
                    expected_format="array"
                )
            if question.options:
                invalid_options = [v for v in answer_value if v not in question.options]
                if invalid_options:
                    return QuestionValidationError(
                        question_id=question.id,
                        error_type="invalid_option",
                        message=f"Invalid options: {', '.join(invalid_options)}",
                        expected_format="select from available options"
                    )
        
        elif question.question_type == QuestionType.DATE:
            try:
                # Try to parse as ISO date
                if isinstance(answer_value, str):
                    datetime.fromisoformat(answer_value.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return QuestionValidationError(
                    question_id=question.id,
                    error_type="format_error",
                    message="Date must be in ISO format (YYYY-MM-DD)",
                    expected_format="YYYY-MM-DD"
                )
        
        return None
    
    def submit_answer(
        self,
        session_id: str,
        question_id: str,
        answer_value: Any,
        confidence: Optional[float] = None,
        notes: Optional[str] = None,
        evidence_files: Optional[List[str]] = None
    ) -> AnswerSubmissionResponse:
        """
        Submit an answer to a question
        
        Args:
            session_id: The session ID
            question_id: The question ID
            answer_value: The answer value
            confidence: Optional confidence score (0-1)
            notes: Optional notes
            evidence_files: Optional list of evidence file paths
        
        Returns:
            AnswerSubmissionResponse with status and next question
        """
        session = self.sessions.get(session_id)
        if not session:
            return AnswerSubmissionResponse(
                status="validation_error",
                progress=0,
                validation_error=QuestionValidationError(
                    question_id=question_id,
                    error_type="session_error",
                    message="Session not found"
                )
            )
        
        # Find the question
        question = next((q for q in self.questions if q.id == question_id), None)
        if not question:
            return AnswerSubmissionResponse(
                status="validation_error",
                progress=session.progress_percentage,
                validation_error=QuestionValidationError(
                    question_id=question_id,
                    error_type="question_error",
                    message="Question not found"
                )
            )
        
        # Validate the answer
        validation_error = self.validate_answer(question, answer_value)
        if validation_error:
            return AnswerSubmissionResponse(
                status="validation_error",
                progress=session.progress_percentage,
                validation_error=validation_error
            )
        
        # Create and store the answer
        answer = InterviewAnswer(
            question_id=question_id,
            answer=answer_value,
            confidence=confidence,
            notes=notes,
            evidence_files=evidence_files or []
        )
        
        session.answers.append(answer)
        
        # Check if AI clarification needed (critical 'no' answers)
        needs_clarification = (
            question.weight >= 2.5 and 
            answer_value in [False, "no", "No", 0] and
            question.category in ["Permits", "Environmental", "Safety", "Community"]
        )
        
        if needs_clarification:
            # Mark that AI clarification is needed
            answer.needs_ai_followup = True
        
        # Update category tracking
        if question.category not in session.categories_completed:
            # Check if all questions in this category are answered
            category_questions = [q for q in self.questions if q.category == question.category]
            answered_in_category = [a for a in session.answers if any(q.id == a.question_id and q.category == question.category for q in self.questions)]
            
            if len(answered_in_category) >= len(category_questions):
                session.categories_completed.append(question.category)
        
        # Update progress (model validator will handle this)
        session = session.model_validate(session.model_dump())
        self.sessions[session_id] = session
        
        # Get next question
        next_question = self.get_next_question(session_id)
        
        # Check if complete
        if not next_question:
            session.status = InterviewStatus.COMPLETED
            session.completed_at = datetime.now().isoformat()
            
            return AnswerSubmissionResponse(
                status="session_complete",
                progress=100.0,
                session_complete=True,
                next_question=None
            )
        
        # Get remaining categories
        answered_categories = set()
        for answer in session.answers:
            for q in self.questions:
                if q.id == answer.question_id:
                    answered_categories.add(q.category)
        
        all_categories = set(q.category for q in self.questions)
        remaining_categories = list(all_categories - answered_categories)
        
        return AnswerSubmissionResponse(
            status="accepted",
            progress=session.progress_percentage,
            next_question=next_question,
            session_complete=False,
            categories_remaining=remaining_categories
        )
    
    def get_category_progress(self, session_id: str) -> List[CategoryProgress]:
        """
        Get progress by category for a session
        
        Args:
            session_id: The session ID
        
        Returns:
            List of CategoryProgress objects
        """
        session = self.sessions.get(session_id)
        if not session:
            return []
        
        # Build category stats
        category_stats = {}
        
        for question in self.questions:
            category = question.category
            if category not in category_stats:
                category_stats[category] = {
                    "total": 0,
                    "answered": 0,
                    "required": 0,
                    "required_answered": 0
                }
            
            category_stats[category]["total"] += 1
            if question.required:
                category_stats[category]["required"] += 1
            
            # Check if answered
            if any(a.question_id == question.id for a in session.answers):
                category_stats[category]["answered"] += 1
                if question.required:
                    category_stats[category]["required_answered"] += 1
        
        # Convert to CategoryProgress objects
        progress_list = []
        for category, stats in category_stats.items():
            progress = CategoryProgress(
                category=category,
                total_questions=stats["total"],
                answered_questions=stats["answered"],
                required_questions=stats["required"],
                required_answered=stats["required_answered"]
            )
            progress_list.append(progress)
        
        return progress_list
    
    def format_as_compliance_statement(self, question: ComplianceQuestion, answer: InterviewAnswer) -> str:
        """
        Convert Q&A pair to a compliance statement for the pipeline
        
        Args:
            question: The question
            answer: The answer
        
        Returns:
            Formatted compliance statement
        """
        q_text = question.question_text.lower()
        
        if question.question_type == QuestionType.YES_NO:
            answer_bool = answer.answer in [True, "yes", "true", "Yes", "True"]
            if answer_bool:
                # Positive compliance statement
                statement = f"The site confirms: {q_text.replace('?', '.')}"
            else:
                # Non-compliance statement
                if "have" in q_text or "has" in q_text:
                    statement = f"The site reports non-compliance: {q_text.replace('?', ' is not in place.')}"
                else:
                    statement = f"The site reports: {q_text.replace('?', ' - No.')}"
        
        elif question.question_type == QuestionType.SCALE:
            statement = f"Regarding {q_text.replace('?', '')}, the assessment score is {answer.answer}/5."
            if answer.answer <= 2:
                statement += " This indicates significant gaps requiring immediate attention."
            elif answer.answer == 3:
                statement += " This indicates partial compliance with room for improvement."
            else:
                statement += " This indicates good compliance with established procedures."
        
        elif question.question_type == QuestionType.NUMBER:
            statement = f"{question.question_text.replace('?', ':')} {answer.answer}"
            
            # Add context based on the question
            if "incidents" in q_text or "violations" in q_text or "grievances" in q_text:
                if answer.answer == 0:
                    statement += " (No issues reported)"
                elif answer.answer > 10:
                    statement += " (Significant number requiring attention)"
        
        elif question.question_type == QuestionType.DATE:
            statement = f"{question.question_text.replace('?', ':')} {answer.answer}"
            
            # Check recency for certain questions
            if "last" in q_text or "recent" in q_text:
                try:
                    date_val = datetime.fromisoformat(str(answer.answer).replace('Z', '+00:00'))
                    days_ago = (datetime.now() - date_val).days
                    if days_ago > 365:
                        statement += " (Over a year ago - review recommended)"
                    elif days_ago > 180:
                        statement += " (Over 6 months ago)"
                except:
                    pass
        
        elif question.question_type == QuestionType.MULTIPLE_CHOICE:
            statement = f"{question.question_text.replace('?', ':')} {answer.answer}"
        
        elif question.question_type == QuestionType.MULTI_SELECT:
            selections = ", ".join(answer.answer) if isinstance(answer.answer, list) else str(answer.answer)
            statement = f"{question.question_text.replace('?', ':')} {selections}"
        
        else:  # TEXT type
            statement = f"{question.question_text.replace('?', ':')} {answer.answer}"
        
        # Add notes if provided
        if answer.notes:
            statement += f" [Note: {answer.notes}]"
        
        # Add AI clarifications if present
        if hasattr(answer, 'ai_clarifications') and answer.ai_clarifications:
            statement += " [AI Deep-Dive: "
            for clarification in answer.ai_clarifications:
                q = clarification.get('question', '')
                a = clarification.get('answer', '')
                if q and a:
                    statement += f"{q} -> {a}; "
            statement = statement.rstrip("; ") + "]"
        
        # Add confidence indicator if low
        if answer.confidence and answer.confidence < 0.5:
            statement += " [Low confidence response]"
        
        return statement
    
    async def generate_compliance_summary(self, session: InterviewSession) -> str:
        """
        Generate an AI-powered compliance summary
        
        Args:
            session: The completed interview session
        
        Returns:
            Compliance summary text
        """
        # Prepare Q&A pairs for the prompt
        qa_pairs = []
        for answer in session.answers:
            question = next((q for q in self.questions if q.id == answer.question_id), None)
            if question:
                qa_pairs.append({
                    "category": question.category,
                    "question": question.question_text,
                    "answer": answer.answer,
                    "framework_ref": question.framework_ref,
                    "weight": question.weight
                })
        
        prompt = f"""
        Analyze this compliance interview for {session.site_name} against {self.framework}.
        
        Interview conducted by: {session.auditor_name}
        Date: {session.started_at}
        
        Questions and Answers:
        {json.dumps(qa_pairs, indent=2)}
        
        Generate a comprehensive compliance assessment summary that includes:
        1. Overall compliance status assessment
        2. Key strengths identified
        3. Critical gaps and non-compliance areas
        4. Risk level assessment
        5. Priority recommendations
        
        Format as a professional executive summary suitable for management review.
        Focus on actionable insights and specific compliance requirements.
        """
        
        try:
            # Use streaming for better performance
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a {self.framework} compliance expert generating an audit summary."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Failed to generate compliance summary: {e}")
            # Fallback to basic summary
            return self._generate_basic_summary(session)
    
    def _generate_basic_summary(self, session: InterviewSession) -> str:
        """Generate a basic summary without AI"""
        total_questions = len(session.answers)
        
        # Count compliance indicators
        compliant = 0
        non_compliant = 0
        review_needed = 0
        
        for answer in session.answers:
            question = next((q for q in self.questions if q.id == answer.question_id), None)
            if question and question.question_type == QuestionType.YES_NO:
                if answer.answer in [True, "yes", "Yes"]:
                    compliant += 1
                else:
                    non_compliant += 1
            elif question and question.question_type == QuestionType.SCALE:
                if answer.answer >= 4:
                    compliant += 1
                elif answer.answer == 3:
                    review_needed += 1
                else:
                    non_compliant += 1
        
        return f"""
        Compliance Assessment Summary for {session.site_name}
        
        Framework: {self.framework}
        Assessment Date: {session.started_at}
        Auditor: {session.auditor_name}
        
        Questions Assessed: {total_questions}
        - Compliant Items: {compliant}
        - Non-Compliant Items: {non_compliant}
        - Items Requiring Review: {review_needed}
        
        Overall Compliance Rate: {round((compliant / total_questions) * 100, 1)}%
        
        This assessment covers {len(session.categories_completed)} categories of compliance requirements.
        Detailed analysis and recommendations should be developed based on the specific findings.
        """
    
    async def export_session(self, session_id: str) -> InterviewExport:
        """
        Export session to pipeline-compatible format
        
        Args:
            session_id: The session ID
        
        Returns:
            InterviewExport object
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Group answers by category and convert to statements
        structured_responses = {}
        compliance_scores = {}
        identified_gaps = []
        recommendations = []
        
        for answer in session.answers:
            question = next((q for q in self.questions if q.id == answer.question_id), None)
            if not question:
                continue
            
            category = question.category
            
            # Convert to compliance statement
            statement = self.format_as_compliance_statement(question, answer)
            
            if category not in structured_responses:
                structured_responses[category] = []
                compliance_scores[category] = {"total_weight": 0, "achieved_weight": 0}
            
            structured_responses[category].append(statement)
            
            # Calculate scores
            compliance_scores[category]["total_weight"] += question.weight
            
            # Determine if answer indicates compliance
            is_compliant = False
            if question.question_type == QuestionType.YES_NO:
                is_compliant = answer.answer in [True, "yes", "Yes", "true", "True"]
            elif question.question_type == QuestionType.SCALE:
                is_compliant = answer.answer >= 3
            else:
                is_compliant = True  # Assume compliance for other types unless negative
            
            if is_compliant:
                if question.question_type == QuestionType.SCALE:
                    # Partial credit for scale questions
                    compliance_scores[category]["achieved_weight"] += question.weight * (answer.answer / 5)
                else:
                    compliance_scores[category]["achieved_weight"] += question.weight
            else:
                # Record gaps
                identified_gaps.append(f"{question.category}: {question.question_text}")
                
                # Generate recommendation
                if question.weight >= 3.0:  # High priority
                    recommendations.append(f"CRITICAL: Address {question.framework_ref} - {question.question_text}")
                elif question.weight >= 2.0:
                    recommendations.append(f"Important: Review {question.framework_ref} compliance")
        
        # Calculate final scores
        final_scores = {}
        for category, scores in compliance_scores.items():
            if scores["total_weight"] > 0:
                final_scores[category] = round(scores["achieved_weight"] / scores["total_weight"], 2)
            else:
                final_scores[category] = 0.0
        
        # Generate compliance summary
        compliance_summary = await self.generate_compliance_summary(session)
        
        # Prepare raw Q&A pairs
        raw_qa = []
        for answer in session.answers:
            question = next((q for q in self.questions if q.id == answer.question_id), None)
            if question:
                raw_qa.append({
                    "question": question.model_dump(),
                    "answer": answer.model_dump()
                })
        
        return InterviewExport(
            session_metadata=session,
            structured_responses=structured_responses,
            compliance_summary=compliance_summary,
            compliance_scores=final_scores,
            identified_gaps=identified_gaps[:20],  # Top 20 gaps
            recommendations=recommendations[:10],  # Top 10 recommendations
            raw_qa_pairs=raw_qa
        )