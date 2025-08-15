# VigilOre Interview Chatbot - Frontend Integration Guide

## Overview
The VigilOre API provides a structured interview system that combines pre-defined compliance questions with AI-powered deep dives when critical gaps are detected. This creates comprehensive audit files for the main compliance pipeline.

## Key Concepts

### Hybrid Approach
1. **Structured Questions** - 70+ pre-loaded questions per framework (fast, consistent)
2. **AI Deep-Dive** - Triggered only for critical "no" answers (2-3 clarifying questions)
3. **Rich Export** - Creates comprehensive JSON for pipeline processing

### Interview Flow
```
User → Structured Questions → [Critical "No"?] → AI Clarification → Continue Questions → Export
```

## API Endpoints

### 1. Start Interview Session
```javascript
POST /interview/start
Content-Type: application/json

{
  "framework": "DRC_Mining_Code",  // or "ISO_14001", "ISO_45001", "VPSHR"
  "site_name": "Kolwezi Mine Site",
  "site_code": "KOL-001",          // optional
  "operator": "MiningCo",          // optional
  "auditor_name": "John Smith",
  "auditor_email": "john@example.com",  // optional
  "categories": ["Permits", "Environmental"]  // optional, null for all
}

Response:
{
  "session_id": "abc123...",
  "total_questions": 38,
  "estimated_time_minutes": 20,
  "first_question": {...}
}
```

### 2. Get Next Question
```javascript
GET /interview/{session_id}/question

Response:
{
  "question": {
    "id": "drc_001",
    "category": "Permits",
    "question_text": "Does the mining operation have a valid exploitation permit?",
    "question_type": "yes_no",
    "weight": 3.0,
    "framework_ref": "DRC Art. 299",
    "help_text": "This refers to the official permit issued by CAMI",
    "required": true
  },
  "progress": 15.5,
  "questions_remaining": 32
}
```

### 3. Submit Answer
```javascript
POST /interview/{session_id}/answer
Content-Type: application/json

{
  "question_id": "drc_001",
  "answer_value": false,  // for yes_no questions
  "confidence": 0.9,      // 0-1, optional
  "notes": "Permit expired last month, renewal in process"
}

Response:
{
  "status": "accepted",
  "progress": 18.5,
  "next_question": {...},
  "needs_ai_clarification": true  // Indicates AI will ask follow-ups
}
```

### 4. Handle AI Clarifications
When `needs_ai_clarification` is true, the frontend should prepare for AI follow-ups:

```javascript
GET /interview/{session_id}/ai-clarification

Response:
{
  "clarification_questions": [
    {
      "question": "When did the permit expire and what specific steps have been taken for renewal?",
      "type": "text"
    },
    {
      "question": "What interim measures are in place to maintain compliance during renewal?",
      "type": "text"
    }
  ]
}

// Submit clarification answers
POST /interview/{session_id}/ai-clarification
{
  "answers": [
    "Permit expired on Oct 15, 2024. Application submitted Oct 20.",
    "Operating under temporary extension letter from CAMI dated Oct 16."
  ]
}
```

### 5. Get Progress
```javascript
GET /interview/{session_id}/progress

Response:
{
  "overall_progress": 45.5,
  "questions_answered": 17,
  "total_questions": 38,
  "categories_completed": ["Permits"],
  "current_category": "Environmental",
  "estimated_time_remaining_minutes": 10,
  "ai_clarifications_count": 3
}
```

### 6. Export for Pipeline
```javascript
GET /interview/{session_id}/export

Response:
{
  "session_metadata": {...},
  "structured_responses": {
    "Permits": [
      "The site reports non-compliance: exploitation permit is not in place. [Note: Permit expired last month, renewal in process] [AI Deep-Dive: When did permit expire? -> Oct 15, 2024; What interim measures? -> Operating under temporary extension]",
      "The site confirms: environmental impact assessment was conducted.",
      ...
    ]
  },
  "compliance_summary": "AI-generated summary...",
  "compliance_scores": {
    "Permits": 0.65,
    "Environmental": 0.82
  },
  "identified_gaps": [...],
  "recommendations": [...],
  "export_timestamp": "2024-11-15T10:30:00Z"
}
```

## Frontend Implementation Guide

### 1. Chat Interface Structure
```jsx
// Suggested React component structure
<InterviewChat>
  <ProgressBar value={progress} />
  <CategoryIndicator current={currentCategory} />
  
  <ChatWindow>
    {/* Structured questions appear as chat bubbles */}
    <BotMessage>
      Does the mining operation have a valid exploitation permit?
      <HelpTooltip text={question.help_text} />
    </BotMessage>
    
    <UserResponse type="yes_no">
      <NoButton onClick={() => submitAnswer(false)} />
      <YesButton onClick={() => submitAnswer(true)} />
    </UserResponse>
    
    {/* AI clarification appears inline when triggered */}
    {showAiClarification && (
      <AiClarificationSection>
        <BotMessage variant="ai">
          I need more details about this compliance gap...
        </BotMessage>
        <TextInput onSubmit={submitClarification} />
      </AiClarificationSection>
    )}
  </ChatWindow>
  
  <QuestionCounter current={answered} total={totalQuestions} />
</InterviewChat>
```

### 2. Question Type Components
```javascript
// Handle different question types
const QuestionInput = ({ question, onSubmit }) => {
  switch(question.question_type) {
    case 'yes_no':
      return <YesNoButtons onSelect={onSubmit} />;
    
    case 'scale':
      return <ScaleSlider min={1} max={5} onSelect={onSubmit} />;
    
    case 'multiple_choice':
      return <RadioGroup options={question.options} onSelect={onSubmit} />;
    
    case 'text':
      return <TextArea onSubmit={onSubmit} />;
    
    case 'date':
      return <DatePicker onSelect={onSubmit} />;
    
    case 'number':
      return <NumberInput 
        min={question.validation_rules?.min}
        max={question.validation_rules?.max}
        onSubmit={onSubmit}
      />;
  }
};
```

### 3. AI Clarification Flow
```javascript
// Detect when AI clarification is needed
const handleAnswerSubmit = async (answer) => {
  const response = await submitAnswer(sessionId, questionId, answer);
  
  if (response.needs_ai_clarification) {
    // Show AI thinking animation
    setShowAiThinking(true);
    
    // Get clarification questions
    const clarifications = await getAiClarifications(sessionId);
    
    // Display inline in chat
    setAiQuestions(clarifications.clarification_questions);
    setShowAiSection(true);
  } else {
    // Continue to next question
    setCurrentQuestion(response.next_question);
  }
};
```

### 4. Progress Tracking
```javascript
// Update progress in real-time
useEffect(() => {
  const interval = setInterval(async () => {
    const progress = await getProgress(sessionId);
    setProgress(progress.overall_progress);
    setTimeRemaining(progress.estimated_time_remaining_minutes);
    
    // Show milestone notifications
    if (progress.categories_completed.includes(currentCategory)) {
      showNotification(`✓ ${currentCategory} section complete!`);
    }
  }, 5000);
  
  return () => clearInterval(interval);
}, [sessionId]);
```

### 5. Export and Pipeline Integration
```javascript
const completeInterview = async () => {
  // Get the export
  const exportData = await getExport(sessionId);
  
  // Option 1: Auto-submit to pipeline
  const pipelineResult = await submitToPipeline({
    input_file: exportData,
    framework_files: selectedFrameworks,
    site_name: exportData.session_metadata.site_name
  });
  
  // Option 2: Let user download and manually upload
  downloadJSON(exportData, `interview_${site_name}_${timestamp}.json`);
  
  // Show completion summary
  showCompletionModal({
    score: exportData.compliance_scores,
    gaps: exportData.identified_gaps.slice(0, 5),
    nextSteps: "Upload to /audits endpoint for full analysis"
  });
};
```

## UI/UX Best Practices

### 1. Visual Distinction
- **Structured Questions**: Standard chat bubbles with framework reference
- **AI Clarifications**: Different color/style to indicate AI intervention
- **Critical Questions**: Highlight with warning icon when weight >= 2.5

### 2. Progress Indicators
```css
/* Show different states */
.question-bubble.critical { border-left: 3px solid #ff6b6b; }
.question-bubble.ai-followup { background: linear-gradient(...); }
.progress-bar.category-complete { animation: pulse 1s; }
```

### 3. Smart Defaults
- Auto-save progress every answer
- Allow session pause/resume with session ID
- Pre-fill confidence at 100% for yes answers, 80% for no
- Show estimated time based on 30 seconds per question

### 4. Error Handling
```javascript
// Graceful fallbacks
if (!hasOpenAiKey) {
  // Skip AI clarifications, still functional
  showWarning("AI enhancements unavailable - continuing with structured questions only");
}

if (sessionTimeout) {
  // Auto-save and provide resume code
  const resumeCode = await pauseSession(sessionId);
  showModal(`Session saved. Resume code: ${resumeCode}`);
}
```

## Complete Frontend Example

```javascript
// Main Interview Component
const ComplianceInterview = () => {
  const [session, setSession] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [progress, setProgress] = useState(0);
  const [aiMode, setAiMode] = useState(false);
  const [messages, setMessages] = useState([]);
  
  const startInterview = async (framework, siteInfo) => {
    const response = await fetch('/interview/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ framework, ...siteInfo })
    });
    
    const data = await response.json();
    setSession(data);
    setCurrentQuestion(data.first_question);
    
    // Add welcome message
    addMessage({
      type: 'bot',
      text: `Let's begin the ${framework} compliance assessment. This will take about ${data.estimated_time_minutes} minutes.`
    });
  };
  
  const submitAnswer = async (answer, confidence = 1.0, notes = null) => {
    // Add user message to chat
    addMessage({
      type: 'user',
      content: formatAnswer(currentQuestion.question_type, answer)
    });
    
    // Submit to API
    const response = await fetch(`/interview/${session.session_id}/answer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question_id: currentQuestion.id,
        answer_value: answer,
        confidence,
        notes
      })
    });
    
    const data = await response.json();
    
    // Check for AI clarification need
    if (data.needs_ai_clarification && currentQuestion.weight >= 2.5) {
      setAiMode(true);
      addMessage({
        type: 'bot',
        variant: 'ai',
        text: 'I need to understand this compliance gap better. Let me ask a few clarifying questions...'
      });
      
      // Get and display AI questions
      const aiQuestions = await getAiClarifications(session.session_id);
      handleAiQuestions(aiQuestions);
    } else {
      // Continue to next question
      setCurrentQuestion(data.next_question);
      setProgress(data.progress);
      
      if (data.session_complete) {
        completeInterview();
      }
    }
  };
  
  return (
    <div className="interview-container">
      <ProgressHeader progress={progress} session={session} />
      
      <ChatInterface 
        messages={messages}
        currentQuestion={currentQuestion}
        onAnswer={submitAnswer}
        aiMode={aiMode}
      />
      
      <QuestionInputPanel
        question={currentQuestion}
        onSubmit={submitAnswer}
        disabled={aiMode}
      />
    </div>
  );
};
```

## Testing the Integration

### Test Scenarios
1. **Happy Path**: Answer all questions with "Yes" - should complete quickly
2. **AI Triggers**: Answer "No" to permits/safety questions - should trigger AI
3. **Mixed Responses**: Combination of yes/no/scale answers
4. **Session Recovery**: Pause and resume using session ID
5. **Export Validation**: Ensure export contains AI clarifications

### API Test Commands
```bash
# Start session
curl -X POST http://localhost:9999/interview/start \
  -H "Content-Type: application/json" \
  -d '{"framework":"DRC_Mining_Code","site_name":"Test Site","auditor_name":"Tester"}'

# Submit answer triggering AI
curl -X POST http://localhost:9999/interview/{session_id}/answer \
  -H "Content-Type: application/json" \
  -d '{"question_id":"drc_001","answer_value":false,"notes":"No permit"}'
```

## Support & Troubleshooting

### Common Issues
1. **AI not triggering**: Check question weight >= 2.5 and answer is "no"
2. **Session timeout**: Sessions expire after 1 hour of inactivity
3. **Export incomplete**: Ensure all required questions are answered
4. **API key issues**: AI features degrade gracefully without valid key

### Contact
For API issues or feature requests, create an issue on the GitHub repository.