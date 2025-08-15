# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VigilOre Compliance API - A multi-agent system for automated compliance analysis against regulatory frameworks. The system processes audit documents (PDF, DOCX, TXT, MP3) and compares them against compliance frameworks to generate detailed reports with scoring, gap analysis, and financial risk assessment.

## Key Commands

### Running the API
```bash
# Development
uvicorn api_v2:app --reload --host localhost --port 9999

# Production (uses environment PORT)
uvicorn api_v2:app --host 0.0.0.0 --port $PORT
```

### Testing
```bash
# Run API tests
python test_api.py

# Basic connectivity test
python simple_api_test.py
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Environment Variables
- `OPENAI_API_KEY` - Required for LLM operations (can also be passed via API)
- `PORT` - Port for production deployment (defaults to environment variable)

## Architecture Overview

### Multi-Agent System
The compliance analysis uses a multi-agent architecture (`audit_agent/`) with specialized agents:

1. **Orchestrator** (`core/orchestrator.py`)
   - Central coordinator managing agent lifecycle
   - Handles pipeline execution flow
   - Manages shared framework cache

2. **Input Parser Agent** (`agents/input_parser.py`)
   - Processes various input formats (PDF, TXT, DOCX, MP3)
   - Extracts compliance-related statements
   - Categorizes content by compliance domains

3. **Framework Loader Agent** (`agents/framework_loader.py`)
   - Loads regulatory framework documents
   - Extracts relevant requirements by category
   - Maintains framework cache for efficiency

4. **Comparator Agent** (`agents/comparator.py`)
   - Compares input statements against framework requirements
   - Calculates compliance scores (0.0-1.0)
   - Identifies gaps and generates recommendations
   - Calculates potential financial penalties

5. **Aggregator Agent** (`agents/aggregator.py`)
   - Consolidates results from all comparisons
   - Generates executive summaries
   - Creates final reports in JSON and Excel formats

### API Layer
The FastAPI application (`api_v2.py`) provides:
- REST endpoints for audit submission and retrieval
- Dashboard data aggregation endpoints
- Background task processing for long-running analyses
- CORS support for frontend integration
- Mock data system with 15 pre-generated reports

### Key API Endpoints
```
POST /audits - Submit compliance audit with metadata
GET /audits/status/{job_id} - Check analysis progress
GET /reports/{report_id} - Retrieve detailed report
GET /reports/{report_id}/excel - Download Excel report
GET /dashboard/summary - Aggregated dashboard data
GET /reports - Paginated reports list with filtering
```

### Data Models
Pydantic models (`audit_agent/models/compliance_models.py`) ensure type safety:
- `ParsedInput/ParsedStatement` - Structured input data
- `FrameworkExtract/FrameworkClause` - Framework requirements
- `ComplianceItem/ComparisonResult` - Analysis results with penalties
- `FinalReport` - Complete compliance report with financial exposure

## Key Implementation Details

### Resource Management
- **Client Pool** (`utils/client_pool.py`): Singleton OpenAI client management
- **Base Agent** (`utils/base_agent.py`): Abstract base class with LLM patterns
- **Framework Cache**: Shared cache prevents redundant processing

### Async Architecture
- All agents use async/await for concurrent operations
- Background task processing via FastAPI BackgroundTasks
- Non-blocking I/O throughout the pipeline

### Error Handling
- Custom exceptions (`utils/exceptions.py`) with specific error types
- Retry logic with tenacity for LLM calls
- Graceful degradation with fallback responses

### File Storage
- Results stored in `api_results/{job_id}/` directories
- Audit metadata tracked in `api_results/audit_metadata.json`
- Excel reports generated with formatted styling

## Deployment

The application is configured for deployment on Render.com:
- `render.yaml` - Service configuration
- `Procfile` - Web process command definition
- Requires Python 3.11+ runtime

## Development Workflow

When modifying the multi-agent system:
1. Review the base agent class for common patterns
2. Maintain async/await consistency
3. Use the client pool for OpenAI operations
4. Ensure proper resource cleanup in agents
5. Update Pydantic models when changing data structures

When adding new API endpoints:
1. Follow existing patterns in `api_v2.py`
2. Use background tasks for long-running operations
3. Update CORS settings if needed
4. Add corresponding mock data if applicable

## Interview System

The system includes a structured compliance interview feature for guided assessments:

### Components
- **Interview Agent** (`audit_agent/agents/interview_agent.py`) - Conducts structured interviews
- **Question Banks** (`audit_agent/data/compliance_questions.py`) - 70+ questions per framework
- **Data Models** (`audit_agent/models/interview_models.py`) - Interview session management
- **Interactive Script** (`run_interview.py`) - Command-line interview interface

### Running an Interview
```bash
# Interactive interview (answers questions yourself)
python run_interview.py

# Test interview (automated)
python test_interview_agent.py
```

### Interview Features
- Framework-specific questions (DRC Mining Code, ISO 14001/45001, VPSHR)
- Smart follow-up questions based on answers
- Answer validation and confidence scoring
- Progress tracking by category
- Export to JSON for pipeline processing
- AI-powered compliance summaries (requires OpenAI API key)

### API Endpoints
- `POST /interview/start` - Start new interview session
- `GET /interview/{session_id}/question` - Get next question
- `POST /interview/{session_id}/answer` - Submit answer
- `GET /interview/{session_id}/progress` - Track progress
- `GET /interview/{session_id}/export` - Export for pipeline
- `POST /interview/{session_id}/pause` - Pause/resume sessions

## Testing Approach

The codebase includes test files for API validation:
- `test_api.py` - Comprehensive API testing
- `simple_api_test.py` - Basic connectivity checks
- `test_interview_agent.py` - Interview system testing
- Mock data system for development testing