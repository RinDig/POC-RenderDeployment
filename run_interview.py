"""
Interactive Compliance Interview System
Run this script to conduct a compliance interview interactively
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from audit_agent.agents.interview_agent import InterviewAgent
from audit_agent.models.interview_models import QuestionType, InterviewStatus
from audit_agent.data.compliance_questions import (
    get_available_frameworks,
    get_categories_for_framework
)

# Load environment variables from .env file
load_dotenv()

class InteractiveInterview:
    """Interactive interview conductor"""
    
    def __init__(self):
        self.agent = None
        self.session = None
        self.session_id = None
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Print application header"""
        print("\n" + "="*70)
        print("     VIGILORE COMPLIANCE INTERVIEW SYSTEM     ")
        print("="*70)
    
    def print_separator(self):
        """Print section separator"""
        print("-" * 70)
    
    async def select_framework(self) -> str:
        """Let user select a framework"""
        print("\n[FRAMEWORKS] Available Compliance Frameworks:")
        print("-" * 50)
        
        frameworks = get_available_frameworks()
        unique_frameworks = {}
        
        # Group similar frameworks
        for fw in frameworks:
            base_name = fw.replace("_2018", "").replace("_2015", "").replace("_2020", "")
            if base_name not in unique_frameworks:
                unique_frameworks[base_name] = fw
        
        framework_list = list(unique_frameworks.values())
        
        for i, framework in enumerate(framework_list, 1):
            display_name = framework.replace("_", " ")
            print(f"  {i}. {display_name}")
        
        while True:
            try:
                choice = input(f"\nSelect framework (1-{len(framework_list)}): ").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(framework_list):
                    return framework_list[idx]
                print("[ERROR] Invalid choice. Please try again.")
            except (ValueError, IndexError):
                print("[ERROR] Please enter a valid number.")
    
    async def select_categories(self, framework: str) -> Optional[list]:
        """Let user select specific categories or all"""
        categories = get_categories_for_framework(framework)
        
        print(f"\n[CATEGORIES] Available categories for {framework.replace('_', ' ')}:")
        print("-" * 50)
        
        for i, category in enumerate(categories, 1):
            print(f"  {i}. {category}")
        
        print(f"\n  0. All categories (complete assessment)")
        
        while True:
            choice = input("\nSelect option (0 for all, or comma-separated numbers): ").strip()
            
            if choice == "0":
                return None  # None means all categories
            
            try:
                # Parse comma-separated choices
                choices = [int(c.strip()) - 1 for c in choice.split(",")]
                selected = []
                
                for idx in choices:
                    if 0 <= idx < len(categories):
                        selected.append(categories[idx])
                    else:
                        print(f"[WARNING] Invalid choice {idx + 1} ignored")
                
                if selected:
                    return selected
                    
                print("[ERROR] No valid categories selected.")
            except ValueError:
                print("[ERROR] Please enter valid numbers separated by commas.")
    
    def get_site_info(self) -> tuple:
        """Collect site and auditor information"""
        print("\n[SITE INFORMATION]")
        print("-" * 50)
        
        site_name = input("Site name: ").strip() or "Unknown Site"
        site_code = input("Site code (optional): ").strip() or None
        operator = input("Operator (optional): ").strip() or None
        
        print("\n[AUDITOR INFORMATION]")
        print("-" * 50)
        
        auditor_name = input("Your name: ").strip() or "Anonymous"
        auditor_email = input("Your email (optional): ").strip() or None
        
        return site_name, site_code, operator, auditor_name, auditor_email
    
    def format_question(self, question) -> str:
        """Format question for display"""
        lines = []
        lines.append(f"\n[QUESTION {self.current_question_num}/{self.total_questions}]")
        lines.append("=" * 70)
        lines.append(f"Category: {question.category}")
        lines.append(f"Reference: {question.framework_ref}")
        
        if question.weight > 2.5:
            lines.append("[CRITICAL] High-weight question")
        
        lines.append("")
        lines.append(question.question_text)
        
        if question.help_text:
            lines.append(f"\nHelp: {question.help_text}")
        
        return "\n".join(lines)
    
    def get_answer(self, question):
        """Get answer from user based on question type"""
        print(f"\nAnswer type: {question.question_type.value}")
        
        if question.question_type == QuestionType.YES_NO:
            while True:
                answer = input("\nAnswer (yes/no): ").strip().lower()
                if answer in ["yes", "y", "true", "1"]:
                    return True
                elif answer in ["no", "n", "false", "0"]:
                    return False
                print("[ERROR] Please answer yes or no")
        
        elif question.question_type == QuestionType.SCALE:
            while True:
                try:
                    answer = int(input("\nAnswer (1-5): ").strip())
                    if 1 <= answer <= 5:
                        return answer
                    print("[ERROR] Please enter a number between 1 and 5")
                except ValueError:
                    print("[ERROR] Please enter a valid number")
        
        elif question.question_type == QuestionType.NUMBER:
            validation = question.validation_rules or {}
            min_val = validation.get("min", 0)
            max_val = validation.get("max", float('inf'))
            
            while True:
                try:
                    answer = float(input(f"\nAnswer (number): ").strip())
                    if min_val <= answer <= max_val:
                        return int(answer) if answer.is_integer() else answer
                    print(f"[ERROR] Number must be between {min_val} and {max_val}")
                except ValueError:
                    print("[ERROR] Please enter a valid number")
        
        elif question.question_type == QuestionType.DATE:
            while True:
                answer = input("\nAnswer (YYYY-MM-DD): ").strip()
                try:
                    # Validate date format
                    datetime.fromisoformat(answer)
                    return answer
                except ValueError:
                    print("[ERROR] Please enter date in YYYY-MM-DD format")
        
        elif question.question_type == QuestionType.MULTIPLE_CHOICE:
            if question.options:
                print("\nOptions:")
                for i, option in enumerate(question.options, 1):
                    print(f"  {i}. {option}")
                
                while True:
                    try:
                        choice = int(input(f"\nSelect option (1-{len(question.options)}): ").strip())
                        if 1 <= choice <= len(question.options):
                            return question.options[choice - 1]
                        print("[ERROR] Invalid choice")
                    except ValueError:
                        print("[ERROR] Please enter a number")
            else:
                return input("\nAnswer: ").strip()
        
        elif question.question_type == QuestionType.MULTI_SELECT:
            if question.options:
                print("\nOptions (select multiple):")
                for i, option in enumerate(question.options, 1):
                    print(f"  {i}. {option}")
                
                print("\nEnter numbers separated by commas (e.g., 1,3,5)")
                
                while True:
                    try:
                        choices = input("Select options: ").strip()
                        if not choices:
                            return []
                        
                        indices = [int(c.strip()) - 1 for c in choices.split(",")]
                        selected = []
                        
                        for idx in indices:
                            if 0 <= idx < len(question.options):
                                selected.append(question.options[idx])
                        
                        if selected:
                            return selected
                        print("[ERROR] No valid options selected")
                    except (ValueError, IndexError):
                        print("[ERROR] Please enter valid numbers separated by commas")
            else:
                answers = input("\nAnswers (comma-separated): ").strip()
                return [a.strip() for a in answers.split(",") if a.strip()]
        
        else:  # TEXT
            return input("\nAnswer: ").strip() or "No answer provided"
    
    def get_confidence(self) -> float:
        """Get confidence level from user"""
        while True:
            conf = input("Confidence (0-100%, or press Enter for 100%): ").strip()
            if not conf:
                return 1.0
            
            try:
                value = float(conf.replace("%", ""))
                if 0 <= value <= 100:
                    return value / 100
                print("[ERROR] Confidence must be between 0 and 100")
            except ValueError:
                print("[ERROR] Please enter a valid number")
    
    def get_notes(self) -> Optional[str]:
        """Get optional notes from user"""
        notes = input("Additional notes (optional, press Enter to skip): ").strip()
        return notes if notes else None
    
    async def run_interview(self):
        """Run the complete interview flow"""
        try:
            self.clear_screen()
            self.print_header()
            
            # Check for API key - first from environment, then from .env
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("\n[WARNING] OPENAI_API_KEY not found in environment")
                print("AI-powered summaries will not be available.")
                print("To enable AI features:")
                print("  - Set OPENAI_API_KEY environment variable, or")
                print("  - Add to .env file: OPENAI_API_KEY=your-key-here")
                input("\nPress Enter to continue anyway...")
            else:
                print("\n[OK] OpenAI API key loaded successfully")
            
            # Select framework
            framework = await self.select_framework()
            print(f"\n[SELECTED] Framework: {framework.replace('_', ' ')}")
            
            # Select categories
            categories = await self.select_categories(framework)
            if categories:
                print(f"[SELECTED] Categories: {', '.join(categories)}")
            else:
                print("[SELECTED] All categories (complete assessment)")
            
            # Get site information
            site_name, site_code, operator, auditor_name, auditor_email = self.get_site_info()
            
            # Initialize agent
            print("\n[INITIALIZING] Setting up interview agent...")
            self.agent = InterviewAgent(framework=framework, api_key=api_key)
            
            # Start session
            self.session = self.agent.start_session(
                site_name=site_name,
                site_code=site_code,
                operator=operator,
                auditor_name=auditor_name,
                auditor_email=auditor_email,
                categories=categories
            )
            
            self.session_id = self.session.session_id
            self.total_questions = self.session.total_questions
            
            print(f"\n[SESSION STARTED]")
            print(f"Session ID: {self.session_id[:8]}...")
            print(f"Total questions: {self.total_questions}")
            print(f"Estimated time: {(self.total_questions * 30) // 60} minutes")
            
            input("\nPress Enter to begin the interview...")
            
            # Run interview loop
            self.current_question_num = 0
            
            while True:
                # Get next question
                question = self.agent.get_next_question(self.session_id)
                
                if not question:
                    break
                
                self.current_question_num += 1
                self.clear_screen()
                self.print_header()
                
                # Display progress
                progress = self.session.progress_percentage
                progress_bar = "█" * int(progress / 2) + "░" * (50 - int(progress / 2))
                print(f"\nProgress: [{progress_bar}] {progress:.1f}%")
                
                # Display question
                print(self.format_question(question))
                
                # Get answer
                answer = self.get_answer(question)
                
                # Get confidence if required question
                confidence = 1.0
                if question.required and question.weight >= 2.0:
                    print("\n[CONFIDENCE] How confident are you in this answer?")
                    confidence = self.get_confidence()
                
                # Get notes
                notes = None
                if question.evidence_required or question.weight >= 3.0:
                    print("\n[NOTES] This is a critical question. Please provide context:")
                    notes = self.get_notes()
                
                # Submit answer
                result = self.agent.submit_answer(
                    session_id=self.session_id,
                    question_id=question.id,
                    answer_value=answer,
                    confidence=confidence,
                    notes=notes
                )
                
                # Check if AI clarification is needed for critical 'no' answers
                if (
                    question.weight >= 2.5 and 
                    answer in [False, "no", "No", 0] and
                    question.category in ["Permits", "Environmental", "Safety", "Community"]
                ):
                    print("\n[AI ASSISTANT] This is a critical compliance gap. Let me ask a few clarifying questions...")
                    print("-" * 70)
                    
                    # Get AI clarification questions
                    ai_questions = await self.agent.get_ai_clarification(question, answer, notes)
                    
                    if ai_questions:
                        ai_responses = []
                        for i, ai_q in enumerate(ai_questions[:3], 1):
                            print(f"\n[AI Question {i}] {ai_q.get('question', 'Please provide more details')}")
                            ai_answer = input("Your answer: ").strip()
                            ai_responses.append({
                                "question": ai_q.get('question'),
                                "answer": ai_answer,
                                "purpose": ai_q.get('purpose', '')
                            })
                        
                        # Add AI clarifications to the answer
                        for ans in self.session.answers:
                            if ans.question_id == question.id:
                                ans.ai_clarifications = ai_responses
                                # Append clarifications to notes
                                clarification_text = "\n\nAI Clarifications:\n"
                                for resp in ai_responses:
                                    clarification_text += f"- Q: {resp['question']}\n  A: {resp['answer']}\n"
                                ans.notes = (ans.notes or "") + clarification_text
                                break
                        
                        print("\n[AI COMPLETE] Thank you for the additional information. Continuing with assessment...")
                        input("Press Enter to continue...")
                
                if result.validation_error:
                    print(f"\n[ERROR] {result.validation_error.message}")
                    input("Press Enter to try again...")
                    self.current_question_num -= 1
                    continue
                
                if result.next_question and result.next_question.id.endswith('a'):
                    print(f"\n[FOLLOW-UP] Your answer triggered a follow-up question")
                
                # Update session
                self.session = self.agent.get_session(self.session_id)
                
                if result.session_complete:
                    break
                
                # Option to pause
                if self.current_question_num % 10 == 0:
                    cont = input("\n\nContinue? (y/n, or 'p' to pause): ").strip().lower()
                    if cont == 'n':
                        print("\n[CANCELLED] Interview cancelled")
                        return
                    elif cont == 'p':
                        print("\n[PAUSED] Session saved. Resume later with session ID:")
                        print(self.session_id)
                        return
            
            # Interview complete
            self.clear_screen()
            self.print_header()
            print("\n[COMPLETE] Interview finished!")
            print(f"Questions answered: {len(self.session.answers)}")
            
            # Show category progress
            print("\n[RESULTS] Category Completion:")
            self.print_separator()
            
            category_progress = self.agent.get_category_progress(self.session_id)
            for cat_prog in category_progress:
                print(f"  {cat_prog.category}:")
                print(f"    Completion: {cat_prog.completion_percentage:.1f}%")
                print(f"    Questions: {cat_prog.answered_questions}/{cat_prog.total_questions}")
            
            # Export option
            export = input("\n\nExport interview results? (y/n): ").strip().lower()
            if export == 'y':
                await self.export_results()
            
        except KeyboardInterrupt:
            print("\n\n[INTERRUPTED] Interview interrupted by user")
            if self.session_id:
                print(f"Session ID for resume: {self.session_id}")
        except Exception as e:
            print(f"\n[ERROR] An error occurred: {e}")
            import traceback
            traceback.print_exc()
    
    async def export_results(self):
        """Export interview results"""
        print("\n[EXPORTING] Generating export file...")
        
        try:
            # Mark session as complete
            self.session.status = InterviewStatus.COMPLETED
            self.session.completed_at = datetime.now().isoformat()
            
            # Export session
            export = await self.agent.export_session(self.session_id)
            
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"interview_{self.session.site_name.replace(' ', '_')}_{timestamp}.json"
            
            # Create exports directory if it doesn't exist
            export_dir = Path("interview_exports")
            export_dir.mkdir(exist_ok=True)
            
            export_path = export_dir / filename
            
            with open(export_path, 'w') as f:
                json.dump(export.model_dump(), f, indent=2, default=str)
            
            print(f"\n[SAVED] Export saved to: {export_path}")
            
            # Show summary
            print("\n[SUMMARY] Compliance Assessment:")
            self.print_separator()
            
            # Count AI clarifications
            ai_clarification_count = sum(
                1 for ans in self.session.answers 
                if hasattr(ans, 'ai_clarifications') and ans.ai_clarifications
            )
            if ai_clarification_count > 0:
                print(f"\n[AI INSIGHTS] Added {ai_clarification_count} AI-generated clarifications for critical gaps")
            
            # Show scores
            print("\nCompliance Scores by Category:")
            for category, score in export.compliance_scores.items():
                score_pct = score * 100
                status = "[OK] Compliant" if score >= 0.8 else "[WARN] Review" if score >= 0.6 else "[CRITICAL] Non-compliant"
                print(f"  {category}: {score_pct:.1f}% - {status}")
            
            # Show top gaps
            if export.identified_gaps:
                print(f"\nTop Compliance Gaps ({len(export.identified_gaps)} total):")
                for gap in export.identified_gaps[:5]:
                    print(f"  • {gap}")
            
            # Show recommendations
            if export.recommendations:
                print(f"\nKey Recommendations ({len(export.recommendations)} total):")
                for rec in export.recommendations[:5]:
                    print(f"  • {rec}")
            
            print("\n[PIPELINE] This file can be uploaded to the compliance pipeline:")
            print("  1. Go to the /audits endpoint")
            print("  2. Upload this JSON as the input file")
            print("  3. Add the relevant framework PDFs")
            print("  4. Submit for full compliance analysis")
            
        except Exception as e:
            print(f"[ERROR] Export failed: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Main entry point"""
    interview = InteractiveInterview()
    await interview.run_interview()


if __name__ == "__main__":
    # Check for required package
    try:
        from dotenv import load_dotenv
    except ImportError:
        print("[ERROR] python-dotenv not installed")
        print("Install it with: pip install python-dotenv")
        exit(1)
    
    # Run the interview
    asyncio.run(main())