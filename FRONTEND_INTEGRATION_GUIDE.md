# Frontend Integration Guide - Interview System

## Overview
The VigilOre API now includes a comprehensive interview system that allows structured compliance assessments through guided questionnaires. This guide explains how to integrate the interview functionality into your frontend application.

## Key Features
- Framework-specific compliance interviews (DRC Mining Code, ISO 14001/45001, VPSHR)
- 70+ questions per framework organized by category
- Smart follow-up questions based on answers
- AI-powered clarifications for critical compliance gaps
- Progress tracking and session management
- Export to JSON for full compliance pipeline processing

## API Endpoints

### 1. Start Interview Session
```http
POST /interview/start
Content-Type: application/json

{
  "framework": "DRC_Mining_Code_2018",  // Required
  "site_name": "Kibali Gold Mine",      // Required
  "site_code": "KBL-001",               // Optional
  "operator": "AngloGold Ashanti",      // Optional
  "auditor_name": "John Smith",         // Required
  "auditor_email": "john@example.com",  // Required
  "categories": ["Permits", "Safety"]   // Optional - null for all categories
}

Response:
{
  "session_id": "uuid-string",
  "framework": "DRC_Mining_Code_2018",
  "total_questions": 45,
  "categories": ["Permits", "Safety"],
  "status": "active",
  "next_question": { ... }
}
```

### 2. Get Next Question
```http
GET /interview/{session_id}/question

Response:
{
  "question": {
    "id": "permits_q1",
    "category": "Permits",
    "question_text": "Does the operation have a valid mining permit?",
    "question_type": "yes_no",  // yes_no, scale, text, number, date, multiple_choice, multi_select
    "help_text": "Check for current mining license issued by authorities",
    "required": true,
    "weight": 3.0,  // 1.0-3.0, higher = more critical
    "options": [],  // For multiple choice questions
    "validation_rules": {},
    "framework_ref": "Article 5"
  },
  "progress": {
    "current": 5,
    "total": 45,
    "percentage": 11.1
  }
}
```

### 3. Submit Answer
```http
POST /interview/{session_id}/answer
Content-Type: application/x-www-form-urlencoded

question_id=permits_q1&
answer=yes&
confidence=0.95&
notes=Permit valid until 2025

Response:
{
  "success": true,
  "next_question": { ... },  // null if interview complete
  "session_complete": false,
  "validation_error": null,
  "follow_up_triggered": false
}
```

### 4. Get Interview Progress
```http
GET /interview/{session_id}/progress

Response:
{
  "session_id": "uuid-string",
  "status": "active",
  "progress_percentage": 55.5,
  "answered_questions": 25,
  "total_questions": 45,
  "categories_progress": [
    {
      "category": "Permits",
      "completion_percentage": 100.0,
      "answered_questions": 10,
      "total_questions": 10
    },
    {
      "category": "Safety",
      "completion_percentage": 30.0,
      "answered_questions": 3,
      "total_questions": 10
    }
  ]
}
```

### 5. Export Interview Results
```http
GET /interview/{session_id}/export

Response:
{
  "session_id": "uuid-string",
  "framework": "DRC_Mining_Code_2018",
  "site_info": { ... },
  "answers": [ ... ],
  "compliance_scores": {
    "Permits": 0.85,
    "Safety": 0.72,
    "Environmental": 0.91
  },
  "identified_gaps": [
    "Missing environmental impact assessment update",
    "Safety training records incomplete"
  ],
  "recommendations": [
    "Update EIA within 30 days",
    "Complete safety training for all operators"
  ],
  "export_timestamp": "2024-01-15T10:30:00Z"
}
```

### 6. Pause/Resume Session
```http
POST /interview/{session_id}/pause

Response:
{
  "success": true,
  "session_id": "uuid-string",
  "can_resume": true,
  "expires_at": "2024-01-20T10:30:00Z"  // Sessions expire after 7 days
}
```

### 7. Get Available Frameworks
```http
GET /interview/frameworks

Response:
{
  "frameworks": [
    {
      "id": "DRC_Mining_Code_2018",
      "display_name": "DRC Mining Code",
      "categories": ["Permits", "Environmental", "Safety", "Community", "Financial"],
      "total_questions": 72
    },
    {
      "id": "ISO_14001_2015",
      "display_name": "ISO 14001 Environmental Management",
      "categories": ["Planning", "Implementation", "Monitoring", "Review"],
      "total_questions": 68
    }
  ]
}
```

## Frontend Implementation Flow

### 1. Interview Setup Screen
```javascript
// Fetch available frameworks
const frameworks = await fetch('/interview/frameworks').then(r => r.json());

// User selects framework and enters site info
const sessionData = {
  framework: selectedFramework,
  site_name: siteNameInput,
  auditor_name: auditorNameInput,
  auditor_email: auditorEmailInput,
  categories: selectedCategories  // null for all
};

// Start interview
const session = await fetch('/interview/start', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(sessionData)
}).then(r => r.json());

// Store session_id for subsequent calls
localStorage.setItem('interview_session_id', session.session_id);
```

### 2. Question Display Component
```javascript
function QuestionDisplay({ question, onAnswer }) {
  const renderInput = () => {
    switch(question.question_type) {
      case 'yes_no':
        return (
          <div>
            <button onClick={() => onAnswer('yes')}>Yes</button>
            <button onClick={() => onAnswer('no')}>No</button>
          </div>
        );
      
      case 'scale':
        return (
          <input 
            type="range" 
            min="1" 
            max="5" 
            onChange={(e) => onAnswer(e.target.value)}
          />
        );
      
      case 'multiple_choice':
        return (
          <select onChange={(e) => onAnswer(e.target.value)}>
            {question.options.map(opt => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        );
      
      case 'text':
        return (
          <textarea 
            placeholder="Enter your answer"
            onBlur={(e) => onAnswer(e.target.value)}
          />
        );
      
      // Add other types...
    }
  };

  return (
    <div className="question-container">
      <div className="question-header">
        <span className="category">{question.category}</span>
        <span className="reference">{question.framework_ref}</span>
        {question.weight >= 2.5 && <span className="critical">CRITICAL</span>}
      </div>
      
      <h3>{question.question_text}</h3>
      
      {question.help_text && (
        <p className="help-text">{question.help_text}</p>
      )}
      
      {renderInput()}
      
      {question.required && (
        <p className="required-indicator">* Required question</p>
      )}
    </div>
  );
}
```

### 3. Answer Submission with Confidence
```javascript
async function submitAnswer(questionId, answer, confidence = 1.0, notes = '') {
  const formData = new FormData();
  formData.append('question_id', questionId);
  formData.append('answer', answer);
  formData.append('confidence', confidence);
  if (notes) formData.append('notes', notes);

  const response = await fetch(`/interview/${sessionId}/answer`, {
    method: 'POST',
    body: formData
  }).then(r => r.json());

  if (response.validation_error) {
    // Show error to user
    showError(response.validation_error);
    return false;
  }

  if (response.next_question) {
    // Load next question
    setCurrentQuestion(response.next_question);
  } else if (response.session_complete) {
    // Show completion screen
    showCompletionScreen();
  }

  return true;
}
```

### 4. Progress Tracking
```javascript
function ProgressBar({ sessionId }) {
  const [progress, setProgress] = useState(null);

  useEffect(() => {
    const fetchProgress = async () => {
      const data = await fetch(`/interview/${sessionId}/progress`)
        .then(r => r.json());
      setProgress(data);
    };

    fetchProgress();
    // Poll every 30 seconds if needed
    const interval = setInterval(fetchProgress, 30000);
    return () => clearInterval(interval);
  }, [sessionId]);

  if (!progress) return <div>Loading...</div>;

  return (
    <div className="progress-container">
      <div className="overall-progress">
        <div className="progress-bar">
          <div 
            className="progress-fill" 
            style={{ width: `${progress.progress_percentage}%` }}
          />
        </div>
        <span>{progress.answered_questions}/{progress.total_questions} questions</span>
      </div>

      <div className="category-breakdown">
        {progress.categories_progress.map(cat => (
          <div key={cat.category} className="category-progress">
            <span>{cat.category}</span>
            <span>{cat.completion_percentage}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### 5. Export and Pipeline Integration
```javascript
async function completeInterview(sessionId) {
  // Get the export
  const exportData = await fetch(`/interview/${sessionId}/export`)
    .then(r => r.json());

  // Show summary to user
  showSummary(exportData);

  // Option to submit to compliance pipeline
  if (confirm('Submit to full compliance analysis?')) {
    const formData = new FormData();
    
    // Convert export to JSON file
    const jsonBlob = new Blob(
      [JSON.stringify(exportData)], 
      { type: 'application/json' }
    );
    formData.append('input_file', jsonBlob, 'interview_export.json');
    
    // Add framework files (you'll need to handle file selection)
    frameworkFiles.forEach(file => {
      formData.append('framework_files', file);
    });
    
    // Add metadata
    formData.append('site_name', exportData.site_info.site_name);
    formData.append('operator', exportData.site_info.operator);
    formData.append('auditor_name', exportData.site_info.auditor_name);
    formData.append('auditor_email', exportData.site_info.auditor_email);
    
    // Submit to pipeline
    const result = await fetch('/audits', {
      method: 'POST',
      body: formData
    }).then(r => r.json());

    // Redirect to report when ready
    window.location.href = `/reports/${result.job_id}`;
  }
}
```

## UI/UX Recommendations

### 1. Question Types Handling
- **Yes/No**: Use clear buttons or toggle switches
- **Scale (1-5)**: Use slider or star rating
- **Multiple Choice**: Dropdown or radio buttons
- **Multi-Select**: Checkboxes with clear selection state
- **Text**: Expandable textarea with character count
- **Number**: Input with validation and min/max indicators
- **Date**: Date picker with format validation

### 2. Critical Questions
- Highlight questions with weight >= 2.5
- Show warning icon for critical compliance areas
- Require confidence rating for important questions
- Prompt for notes/evidence on high-weight items

### 3. Progress Indicators
- Overall progress bar at top
- Category completion badges
- Time estimate remaining
- Question counter (e.g., "Question 15 of 45")

### 4. Save & Resume
- Auto-save after each answer
- "Save and Exit" button for pause functionality
- Resume interview with session ID
- Warning before abandoning incomplete session

### 5. Validation & Feedback
- Real-time validation for answers
- Clear error messages for invalid inputs
- Success confirmation after each answer
- Follow-up question indicators

## Error Handling

```javascript
class InterviewAPI {
  async makeRequest(url, options = {}) {
    try {
      const response = await fetch(url, options);
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Request failed');
      }
      
      return await response.json();
    } catch (error) {
      // Handle network errors
      if (!navigator.onLine) {
        this.saveOffline(url, options);
        throw new Error('Offline - answers will be synced when connected');
      }
      
      // Handle API errors
      if (error.message.includes('session not found')) {
        // Session expired or invalid
        this.handleSessionExpired();
      }
      
      throw error;
    }
  }

  saveOffline(url, data) {
    // Store in localStorage for later sync
    const offline = JSON.parse(localStorage.getItem('offline_answers') || '[]');
    offline.push({ url, data, timestamp: Date.now() });
    localStorage.setItem('offline_answers', JSON.stringify(offline));
  }

  async syncOfflineAnswers() {
    const offline = JSON.parse(localStorage.getItem('offline_answers') || '[]');
    for (const item of offline) {
      try {
        await this.makeRequest(item.url, item.data);
      } catch (e) {
        console.error('Failed to sync:', e);
      }
    }
    localStorage.removeItem('offline_answers');
  }
}
```

## Testing Recommendations

1. **Test Different Question Types**: Ensure all 7 question types render correctly
2. **Session Management**: Test pause/resume functionality
3. **Validation**: Test invalid answers and error handling
4. **Progress Tracking**: Verify accurate progress calculations
5. **Export**: Test JSON export and pipeline submission
6. **Edge Cases**: 
   - Network interruptions
   - Session timeouts
   - Invalid session IDs
   - Concurrent sessions

## Performance Considerations

1. **Lazy Loading**: Load questions one at a time, not entire set
2. **Caching**: Cache framework data and categories locally
3. **Debouncing**: Debounce answer submissions to prevent duplicates
4. **Progress Polling**: Use reasonable intervals (30s) for progress updates
5. **Session Storage**: Store current state in localStorage for recovery

## Security Notes

- Session IDs are UUIDs - store securely
- Validate all inputs client-side before submission
- API handles authentication via environment variables
- No sensitive data in localStorage (only session IDs)
- CORS is configured for your frontend domain

## Support

For questions or issues:
- API Documentation: `/docs` endpoint
- Swagger UI: `/redoc` endpoint
- GitHub Issues: Report bugs or feature requests