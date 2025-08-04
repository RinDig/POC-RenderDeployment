# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VigilOre Compliance API - A multi-agent system for automated compliance analysis against various regulatory frameworks. The system processes audit documents and compares them against compliance frameworks to generate detailed reports.

## Key Commands

### Running the API
```bash
# Development
uvicorn api_v2:app --reload --host localhost --port 9999

# Production (uses environment PORT)
uvicorn api_v2:app --host 0.0.0.0 --port $PORT
```

### Installing Dependencies
```bash
pip install -r requirements-api.txt
```

### Environment Variables
- `OPENAI_API_KEY` - Required for LLM operations (can also be passed via API)
- `PORT` - Port for production deployment (defaults to environment variable)

## Architecture Overview

### Multi-Agent System
The compliance analysis uses a multi-agent architecture with specialized agents:

1. **Orchestrator** (`audit_agent/core/orchestrator.py`)
   - Coordinates all agents
   - Manages the analysis pipeline
   - Handles agent lifecycle and cleanup

2. **Input Parser Agent** (`audit_agent/agents/input_parser.py`)
   - Processes various input formats (PDF, TXT, DOCX, MP3)
   - Extracts compliance-related statements
   - Categorizes content for analysis

3. **Framework Loader Agent** (`audit_agent/agents/framework_loader.py`)
   - Loads regulatory framework documents
   - Extracts relevant requirements by category
   - Maintains a framework cache for efficiency

4. **Comparator Agent** (`audit_agent/agents/comparator.py`)
   - Compares input statements against framework requirements
   - Calculates compliance scores
   - Identifies gaps and generates recommendations
   - Calculates potential financial penalties

5. **Aggregator Agent** (`audit_agent/agents/aggregator.py`)
   - Consolidates results from all comparisons
   - Generates executive summaries
   - Creates final reports in JSON and Excel formats

### API Layer
The FastAPI application (`api_v2.py`) provides:
- REST endpoints for audit submission and retrieval
- Dashboard data aggregation endpoints
- Background task processing for long-running analyses
- CORS support for frontend integration

### Data Models
Pydantic models (`audit_agent/models/compliance_models.py`) ensure type safety:
- `ParsedInput/ParsedStatement` - Structured input data
- `FrameworkExtract/FrameworkClause` - Framework requirements
- `ComplianceItem/ComparisonResult` - Analysis results
- `FinalReport` - Complete compliance report with financial exposure

## Key Implementation Details

- **Async Processing**: All agents use async/await for concurrent operations
- **Client Pool**: OpenAI clients are managed via a pool for resource efficiency
- **Error Handling**: Custom exceptions with retry logic for API calls
- **File Storage**: Results stored in `api_results/{job_id}/` directories
- **Metadata Tracking**: Audit metadata stored in `api_results/audit_metadata.json`

## Deployment

The application is configured for deployment on Render.com:
- See `render.yaml` for service configuration
- `Procfile` defines the web process command
- Requires Python 3.11+ runtime