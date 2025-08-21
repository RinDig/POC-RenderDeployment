"""
Automated Interview Test - Simulates a mine site compliance interview
Answers questions as a typical DRC mining operation would
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

from audit_agent.agents.interview_agent import InterviewAgent
from audit_agent.models.interview_models import QuestionType

# Load environment variables
load_dotenv()

class AutomatedMineInterview:
    """Simulates a mine site answering compliance questions"""
    
    def __init__(self):
        self.site_name = "Kolwezi Copper Mine"
        self.site_code = "KCM-2024"
        self.operator = "Congo Mining Operations Ltd"
        self.auditor_name = "Automated Test System"
        self.auditor_email = "test@vigilore.com"
        
        # Realistic mine site answers (mix of compliant and non-compliant)
        self.answer_map = {
            # Permits - Some issues
            "drc_001": False,  # No valid exploitation permit - will trigger AI
            "drc_001a": "Permit expired 2 months ago, renewal application submitted",
            "drc_002": True,   # Has environmental permit
            "drc_003": True,   # Feasibility study conducted
            "drc_004": "2023-08-15",  # Last inspection date
            "drc_005": False,  # No artisanal mining agreement - will trigger AI
            
            # Environmental - Mostly compliant
            "drc_006": True,   # EIA conducted
            "drc_007": 4,      # Water management score
            "drc_008": True,   # Waste management plan
            "drc_009": ["Chemical treatment", "Settling ponds"],
            "drc_010": True,   # Rehabilitation fund established
            "drc_011": 85,     # 85% of fund secured
            "drc_012": False,  # No biodiversity offset - will trigger AI
            
            # Safety - Good compliance
            "drc_013": True,   # Safety management system
            "drc_014": "2024-01-10",  # Last safety training
            "drc_015": True,   # PPE provided
            "drc_016": 3,      # Emergency preparedness score
            "drc_017": 12,     # Incidents in last year
            "drc_018": True,   # Incident investigation process
            
            # Community - Mixed
            "drc_019": True,   # Community consultation conducted
            "drc_020": 3,      # Community relations score
            "drc_021": True,   # Grievance mechanism exists
            "drc_022": 45,     # Grievances received
            "drc_023": 38,     # Grievances resolved
            "drc_024": False,  # No local employment quota met - will trigger AI
            "drc_025": 35,     # Percentage of local employees
            
            # Financial - Compliant
            "drc_026": True,   # Royalties paid
            "drc_027": "2024-10-31",  # Last royalty payment
            "drc_028": True,   # Surface rights compensation paid
            "drc_029": 0,      # No outstanding penalties
            "drc_030": True,   # Financial guarantees in place
            
            # Reporting - Mostly compliant
            "drc_031": True,   # Regular reports submitted
            "drc_032": "Quarterly",  # Reporting frequency
            "drc_033": True,   # Production data accurate
            "drc_034": 2,      # Data accuracy score (needs improvement)
            "drc_035": True,   # Export declarations filed
            
            # Governance
            "drc_036": True,   # Anti-corruption policy
            "drc_037": 4,      # Governance score
            "drc_038": True,   # Board oversight exists
        }
        
        # Notes for critical questions
        self.notes_map = {
            "drc_001": "Working with CAMI on expedited renewal. Operating under provisional extension.",
            "drc_005": "Negotiations ongoing with local cooperatives. Draft agreement under review.",
            "drc_012": "Biodiversity study completed, offset program design in progress.",
            "drc_024": "Recruitment drive launched last month to increase local hiring to 60%.",
        }
        
        # AI clarification responses
        self.ai_responses = {
            "permit_timeline": "Application submitted Oct 1, 2024. CAMI indicated 4-6 week processing time.",
            "interim_measures": "Operating under ministerial letter dated Sept 15, 2024 allowing continued operations.",
            "artisanal_plans": "MOU signing scheduled for December 2024 with 3 local cooperatives.",
            "biodiversity_timeline": "Offset program implementation planned Q1 2025, budget approved.",
            "local_hiring_barriers": "Skills gap in technical roles. Training program launched with local technical school.",
        }
    
    def get_answer_for_question(self, question):
        """Generate appropriate answer based on question type and ID"""
        
        # Check if we have a predefined answer
        if question.id in self.answer_map:
            return self.answer_map[question.id]
        
        # Generate default answers by type
        if question.question_type == QuestionType.YES_NO:
            # Default to mostly compliant (70% yes)
            import random
            return random.random() > 0.3
        
        elif question.question_type == QuestionType.SCALE:
            # Default to moderate scores (3-4)
            import random
            return random.randint(3, 4)
        
        elif question.question_type == QuestionType.NUMBER:
            # Return reasonable defaults
            if "percentage" in question.question_text.lower():
                return 75
            elif "days" in question.question_text.lower():
                return 30
            else:
                return 10
        
        elif question.question_type == QuestionType.DATE:
            # Return dates within last 6 months
            days_ago = 60
            date = datetime.now() - timedelta(days=days_ago)
            return date.strftime("%Y-%m-%d")
        
        elif question.question_type == QuestionType.MULTIPLE_CHOICE:
            # Pick first option as default
            if question.options:
                return question.options[0]
            return "Standard procedure"
        
        elif question.question_type == QuestionType.MULTI_SELECT:
            # Select first two options
            if question.options and len(question.options) >= 2:
                return question.options[:2]
            return ["Option 1", "Option 2"]
        
        else:  # TEXT
            return "Standard compliance measures are in place as per regulations."
    
    def get_confidence(self, question, answer):
        """Determine confidence level based on answer"""
        if question.id in ["drc_001", "drc_005", "drc_012", "drc_024"]:
            return 0.6  # Lower confidence for problem areas
        
        if question.weight >= 3.0:
            return 0.85  # High confidence for critical areas we're sure about
        
        return 0.95  # Very confident in most answers
    
    def get_notes(self, question):
        """Get additional notes for specific questions"""
        return self.notes_map.get(question.id, None)
    
    def get_ai_clarification_response(self, ai_question):
        """Provide response to AI clarification questions"""
        q_lower = ai_question.lower()
        
        if "timeline" in q_lower or "when" in q_lower:
            return self.ai_responses.get("permit_timeline", "Timeline under development with authorities.")
        elif "interim" in q_lower or "temporary" in q_lower:
            return self.ai_responses.get("interim_measures", "Operating under existing protocols.")
        elif "artisanal" in q_lower or "local mining" in q_lower:
            return self.ai_responses.get("artisanal_plans", "Engagement process ongoing.")
        elif "biodiversity" in q_lower or "offset" in q_lower:
            return self.ai_responses.get("biodiversity_timeline", "Environmental programs being developed.")
        elif "local" in q_lower or "employment" in q_lower:
            return self.ai_responses.get("local_hiring_barriers", "Workforce development initiatives underway.")
        else:
            return "We are actively working with stakeholders to address this compliance gap."
    
    async def run_interview(self):
        """Run the automated interview"""
        print("\n" + "="*70)
        print("   AUTOMATED MINE SITE COMPLIANCE INTERVIEW")
        print("="*70)
        print(f"\nSite: {self.site_name}")
        print(f"Operator: {self.operator}")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("-"*70)
        
        # Initialize agent
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("[WARNING] No OpenAI API key found - AI clarifications will be skipped")
        
        agent = InterviewAgent(framework="DRC_Mining_Code", api_key=api_key)
        
        # Start session
        session = agent.start_session(
            site_name=self.site_name,
            site_code=self.site_code,
            operator=self.operator,
            auditor_name=self.auditor_name,
            auditor_email=self.auditor_email,
            categories=None  # All categories
        )
        
        session_id = session.session_id
        print(f"\n[SESSION STARTED]")
        print(f"Session ID: {session_id[:8]}...")
        print(f"Total questions: {session.total_questions}")
        print("\n" + "-"*70)
        
        # Answer all questions
        question_num = 0
        ai_clarification_count = 0
        
        while True:
            # Get next question
            question = agent.get_next_question(session_id)
            if not question:
                break
            
            question_num += 1
            
            # Get answer
            answer = self.get_answer_for_question(question)
            confidence = self.get_confidence(question, answer)
            notes = self.get_notes(question)
            
            # Display Q&A
            print(f"\n[Q{question_num}] {question.question_text}")
            print(f"Category: {question.category} | Weight: {question.weight}")
            print(f"Answer: {answer}")
            if notes:
                print(f"Notes: {notes}")
            
            # Submit answer
            result = agent.submit_answer(
                session_id=session_id,
                question_id=question.id,
                answer_value=answer,
                confidence=confidence,
                notes=notes
            )
            
            # Handle AI clarification if needed
            if (question.weight >= 2.5 and 
                answer in [False, "no", "No", 0] and
                question.category in ["Permits", "Environmental", "Safety", "Community"]):
                
                print("\n  [AI CLARIFICATION TRIGGERED]")
                
                # Get AI questions
                ai_questions = await agent.get_ai_clarification(question, answer, notes)
                
                if ai_questions:
                    ai_clarification_count += 1
                    ai_responses = []
                    
                    for ai_q in ai_questions[:3]:
                        ai_question_text = ai_q.get('question', '')
                        if ai_question_text:
                            ai_answer = self.get_ai_clarification_response(ai_question_text)
                            print(f"  AI: {ai_question_text}")
                            print(f"  Response: {ai_answer}")
                            ai_responses.append({
                                "question": ai_question_text,
                                "answer": ai_answer
                            })
                    
                    # Add to session answers
                    for ans in session.answers:
                        if ans.question_id == question.id:
                            ans.ai_clarifications = ai_responses
                            break
            
            # Update session
            session = agent.get_session(session_id)
            
            # Show progress every 10 questions
            if question_num % 10 == 0:
                print(f"\n[PROGRESS] {session.progress_percentage:.1f}% complete")
        
        # Interview complete
        print("\n" + "="*70)
        print("   INTERVIEW COMPLETE")
        print("="*70)
        print(f"Questions answered: {len(session.answers)}")
        print(f"AI clarifications triggered: {ai_clarification_count}")
        
        # Mark session as complete
        from audit_agent.models.interview_models import InterviewStatus
        session.status = InterviewStatus.COMPLETED
        session.completed_at = datetime.now().isoformat()
        
        # Export results
        print("\n[EXPORTING RESULTS]")
        export = await agent.export_session(session_id)
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"interview_export_{self.site_name.replace(' ', '_')}_{timestamp}.json"
        
        # Create exports directory
        export_dir = Path("interview_exports")
        export_dir.mkdir(exist_ok=True)
        
        export_path = export_dir / filename
        
        with open(export_path, 'w') as f:
            json.dump(export.model_dump(), f, indent=2, default=str)
        
        print(f"Export saved to: {export_path}")
        
        # Show summary
        print("\n[COMPLIANCE SUMMARY]")
        print("-"*70)
        
        for category, score in export.compliance_scores.items():
            score_pct = score * 100
            status = "[PASS]" if score >= 0.8 else "[REVIEW]" if score >= 0.6 else "[FAIL]"
            bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
            print(f"{category:20} [{bar}] {score_pct:5.1f}% {status}")
        
        # Show top gaps
        if export.identified_gaps:
            print(f"\n[TOP COMPLIANCE GAPS]")
            for i, gap in enumerate(export.identified_gaps[:5], 1):
                print(f"{i}. {gap}")
        
        # Show AI insights count
        statements_with_ai = sum(
            1 for statements in export.structured_responses.values()
            for s in statements if "[AI Deep-Dive:" in s
        )
        print(f"\n[AI ENHANCEMENTS]")
        print(f"Statements enriched with AI insights: {statements_with_ai}")
        
        print("\n" + "="*70)
        print("This export file can now be uploaded to /audits endpoint for full pipeline analysis")
        print("="*70)
        
        return export_path


async def main():
    """Run the automated interview"""
    interview = AutomatedMineInterview()
    export_path = await interview.run_interview()
    print(f"\n✓ Interview complete. Export file: {export_path}")


if __name__ == "__main__":
    asyncio.run(main())