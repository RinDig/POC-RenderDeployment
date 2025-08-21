# Multi-User Support Implementation Guide

## Overview
This guide provides a complete, step-by-step implementation plan to transform the VigilOre API from a single-user, in-memory system to a production-ready, multi-user platform with database persistence and true background processing.

## Current Issues to Solve
1. **Single User Limitation**: All data stored in memory (`app.state`)
2. **Blocking Processing**: API becomes unresponsive during pipeline processing
3. **Data Loss**: Sessions and jobs lost on server restart
4. **No Concurrency**: Can't handle multiple simultaneous users
5. **Mock Data Inaccessible**: All endpoints blocked during audit processing

## Solution Architecture

### Core Components
1. **PostgreSQL Database**: Persistent storage for sessions and jobs
2. **Threading/Celery**: True background processing
3. **Hybrid Storage**: Database with in-memory fallback
4. **Feature Flags**: Gradual migration without breaking changes

---

## Phase 1: Database Setup

### 1.1 Create PostgreSQL on Render

**Via Render Dashboard:**
```
1. Navigate to Dashboard → New → PostgreSQL
2. Configure:
   - Name: vigilore-db
   - Database: vigilore_prod
   - User: vigilore_user
   - Region: Same as your web service (e.g., Oregon)
   - PostgreSQL Version: 16
   - Plan: Starter ($7/month)
   - Storage: 1 GB
3. Click "Create Database"
4. Wait for status to show "Available"
```

### 1.2 Update Dependencies

**Add to `requirements.txt`:**
```python
# Database
sqlalchemy>=2.0.0
asyncpg>=0.29.0           # Async PostgreSQL driver
alembic>=1.13.0           # Database migrations
python-dotenv>=1.0.0      # Environment management

# Background Processing (Phase 2)
celery[redis]>=5.3.0      # Optional: for production-grade queuing
redis>=5.0.0              # Optional: for caching
```

### 1.3 Update Render Configuration

**Update `render.yaml`:**
```yaml
services:
  - type: web
    name: vigilore-compliance-api
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn api_v2:app --host 0.0.0.0 --port $PORT --workers 2
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: OPENAI_API_KEY
        sync: false  # Set in dashboard
      - key: DATABASE_URL
        fromDatabase:
          name: vigilore-db
          property: connectionString
      - key: USE_DATABASE
        value: "true"  # Feature flag
      - key: WEB_CONCURRENCY
        value: "2"     # Number of workers

databases:
  - name: vigilore-db
    databaseName: vigilore_prod
    user: vigilore_user
    plan: starter
```

---

## Phase 2: Database Models

### 2.1 Create Database Models

**Create `audit_agent/database/models.py`:**
```python
"""
Database models that mirror existing Pydantic models
Ensures compatibility with existing code
"""
from sqlalchemy import Column, String, JSON, DateTime, Float, Text, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class InterviewSessionDB(Base):
    """Database model for interview sessions"""
    __tablename__ = "interview_sessions"
    
    # Primary key
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic info
    framework = Column(String(100), nullable=False, index=True)
    site_name = Column(String(255), nullable=False)
    site_code = Column(String(100))
    operator = Column(String(255))
    auditor_name = Column(String(255), nullable=False)
    auditor_email = Column(String(255))
    language = Column(String(10), default='en')
    status = Column(String(50), default='in_progress', index=True)
    
    # Complex data as JSONB for flexibility
    answers = Column(JSONB, default=list)
    metadata = Column(JSONB, default=dict)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Progress tracking
    total_questions = Column(Integer, default=0)
    progress_percentage = Column(Float, default=0.0)
    categories_completed = Column(JSONB, default=list)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_session_status', 'status'),
        Index('idx_session_framework', 'framework'),
        Index('idx_session_auditor', 'auditor_email'),
    )

class AuditJobDB(Base):
    """Database model for audit jobs"""
    __tablename__ = "audit_jobs"
    
    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(String(50), unique=True, index=True)  # e.g., REP-2024-0001
    status = Column(String(50), default='pending', index=True)
    
    # Metadata as JSONB
    metadata = Column(JSONB, default=dict)
    
    # Store entire report as JSONB
    report_data = Column(JSONB)
    
    # File references
    excel_path = Column(String(500))
    json_path = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime)
    
    # Progress tracking
    progress = Column(Integer, default=0)
    error_message = Column(Text)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_job_status', 'status'),
        Index('idx_job_created', 'created_at'),
    )

class MockReportDB(Base):
    """Store mock reports in database for persistence"""
    __tablename__ = "mock_reports"
    
    id = Column(Integer, primary_key=True)
    report_id = Column(String(50), unique=True)
    report_data = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 2.2 Create Database Connection Manager

**Create `audit_agent/database/connection.py`:**
```python
"""
Database connection management with fallback to in-memory storage
"""
import os
from typing import Optional, AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

# Feature flags
USE_DATABASE = os.getenv("USE_DATABASE", "false").lower() == "true"
DATABASE_URL = os.getenv("DATABASE_URL")

# Initialize database connection if available
if USE_DATABASE and DATABASE_URL:
    # Convert to async URL
    if DATABASE_URL.startswith("postgres://"):
        ASYNC_DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://")
    else:
        ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    
    # Create async engine
    engine = create_async_engine(
        ASYNC_DATABASE_URL,
        echo=False,  # Set to True for SQL logging
        pool_size=20,  # Connection pool size
        max_overflow=40,  # Maximum overflow connections
        pool_pre_ping=True,  # Verify connections before using
    )
    
    # Create session factory
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # For synchronous operations (e.g., Celery)
    SYNC_DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://").replace("postgresql://", "postgresql://")
    sync_engine = create_engine(SYNC_DATABASE_URL)
    SyncSessionLocal = sessionmaker(bind=sync_engine)
    
    logger.info("Database connection initialized")
else:
    engine = None
    AsyncSessionLocal = None
    SyncSessionLocal = None
    logger.warning("Database not configured, using in-memory storage")

async def get_db() -> AsyncGenerator[Optional[AsyncSession], None]:
    """
    Database session dependency for FastAPI
    Returns None if database is not configured
    """
    if not AsyncSessionLocal:
        yield None
        return
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

def get_sync_db() -> Session:
    """Get synchronous database session for Celery tasks"""
    if not SyncSessionLocal:
        return None
    
    db = SyncSessionLocal()
    try:
        return db
    finally:
        db.close()

# In-memory storage fallback
class InMemoryStore:
    """
    Fallback storage when database is not available
    Maintains backward compatibility
    """
    def __init__(self):
        self.interview_sessions = {}
        self.audit_jobs = {}
        self.mock_reports = []
    
    async def get_session(self, session_id: str):
        return self.interview_sessions.get(session_id)
    
    async def save_session(self, session_id: str, data: dict):
        self.interview_sessions[session_id] = data
    
    async def get_job(self, job_id: str):
        return self.audit_jobs.get(job_id)
    
    async def save_job(self, job_id: str, data: dict):
        self.audit_jobs[job_id] = data
    
    async def list_sessions(self, limit: int = 100):
        sessions = list(self.interview_sessions.values())
        return sessions[:limit]
    
    async def list_jobs(self, status: str = None, limit: int = 100):
        jobs = list(self.audit_jobs.values())
        if status:
            jobs = [j for j in jobs if j.get('status') == status]
        return jobs[:limit]

# Global in-memory store instance
memory_store = InMemoryStore()
```

### 2.3 Create Database Initialization Script

**Create `audit_agent/database/init_db.py`:**
```python
"""
Initialize database tables
Run this to create all tables in the database
"""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine
from audit_agent.database.models import Base
from audit_agent.database.connection import ASYNC_DATABASE_URL, USE_DATABASE

async def init_database():
    """Create all database tables"""
    if not USE_DATABASE:
        print("Database is not enabled. Set USE_DATABASE=true to enable.")
        return
    
    if not ASYNC_DATABASE_URL:
        print("No DATABASE_URL found. Please configure database connection.")
        return
    
    print(f"Initializing database...")
    
    engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        # Drop all tables (optional, for clean slate)
        # await conn.run_sync(Base.metadata.drop_all)
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    print("Database tables created successfully!")

async def load_mock_data():
    """Load mock reports into database"""
    from audit_agent.database.connection import AsyncSessionLocal
    from audit_agent.database.models import MockReportDB
    import json
    
    # Load mock data from file
    with open('mock_reports_data.json', 'r') as f:
        mock_reports = json.load(f)
    
    async with AsyncSessionLocal() as session:
        for report in mock_reports:
            db_report = MockReportDB(
                report_id=report['report_id'],
                report_data=report
            )
            session.add(db_report)
        
        await session.commit()
        print(f"Loaded {len(mock_reports)} mock reports")

if __name__ == "__main__":
    # Run initialization
    asyncio.run(init_database())
    
    # Optionally load mock data
    # asyncio.run(load_mock_data())
```

---

## Phase 3: Update API Endpoints (Backward Compatible)

### 3.1 Update API with Database Support

**Update `api_v2.py`:**
```python
# Add imports at the top
from typing import Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from audit_agent.database.connection import get_db, memory_store, USE_DATABASE
from audit_agent.database.models import InterviewSessionDB, AuditJobDB

# Add threading for background processing
import threading
from concurrent.futures import ThreadPoolExecutor

# Create thread pool for background tasks
executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="audit-worker")

# Track running jobs
running_jobs = {}  # job_id -> Future

def run_pipeline_in_thread(job_id: str, input_path: Path, framework_paths: List[Path],
                          metadata: Dict, api_key: str):
    """
    Run pipeline in separate thread to avoid blocking
    """
    import asyncio
    
    # Create new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Update status
        if USE_DATABASE:
            from audit_agent.database.connection import get_sync_db
            with get_sync_db() as db:
                job = db.query(AuditJobDB).filter_by(job_id=job_id).first()
                if job:
                    job.status = 'processing'
                    job.progress = 10
                    db.commit()
        
        # Run the async pipeline
        loop.run_until_complete(
            run_compliance_pipeline(job_id, input_path, framework_paths, metadata, api_key)
        )
        
    except Exception as e:
        logger.error(f"Pipeline error for job {job_id}: {e}")
        # Update status to failed
        if USE_DATABASE:
            from audit_agent.database.connection import get_sync_db
            with get_sync_db() as db:
                job = db.query(AuditJobDB).filter_by(job_id=job_id).first()
                if job:
                    job.status = 'failed'
                    job.error_message = str(e)
                    db.commit()
    finally:
        loop.close()
        # Remove from running jobs
        running_jobs.pop(job_id, None)

# Modified submit audit endpoint
@app.post("/audits", response_model=AuditSubmissionResponse)
async def submit_audit(
    background_tasks: BackgroundTasks,  # Keep for compatibility
    input_file: UploadFile = File(...),
    framework_files: List[UploadFile] = File(...),
    site_name: str = Form(...),
    site_code: Optional[str] = Form(None),
    operator: str = Form(...),
    auditor_name: str = Form(...),
    auditor_email: EmailStr = Form(...),
    language: str = Form("en"),
    api_key: Optional[str] = Form(None),
    db: Optional[AsyncSession] = Depends(get_db)  # Database dependency
):
    """
    Submit audit - returns immediately, processes in background
    """
    # ... validation code (same as before) ...
    
    # Generate IDs
    job_id = str(uuid.uuid4())
    report_id = f"REP-{datetime.now().year}-{len(all_metadata.get('audits', {})) + 1:04d}"
    
    # Save files (same as before)
    job_dir = RESULTS_DIR / job_id
    job_dir.mkdir(parents=True)
    # ... save files ...
    
    # Create metadata
    audit_metadata = {
        "job_id": job_id,
        "report_id": report_id,
        "site_name": site_name,
        "site_code": site_code,
        "operator": operator,
        "auditor_name": auditor_name,
        "auditor_email": auditor_email,
        "language": language,
        "submitted_at": datetime.now().isoformat(),
        "status": "processing"
    }
    
    # Save to database if available
    if db and USE_DATABASE:
        db_job = AuditJobDB(
            job_id=job_id,
            report_id=report_id,
            status="processing",
            metadata=audit_metadata,
            created_at=datetime.now()
        )
        db.add(db_job)
        await db.commit()
    else:
        # Fallback to in-memory
        await memory_store.save_job(job_id, audit_metadata)
    
    # Start processing in background thread (NON-BLOCKING!)
    future = executor.submit(
        run_pipeline_in_thread,
        job_id,
        input_path,
        framework_paths,
        audit_metadata,
        api_key
    )
    running_jobs[job_id] = future
    
    # Return immediately - frontend gets response right away
    return AuditSubmissionResponse(
        job_id=job_id,
        status="processing",
        message=f"Audit submission accepted. Report ID: {report_id}"
    )

# Modified interview start endpoint
@app.post("/interview/start")
async def start_interview(
    request: InterviewStartRequest,
    db: Optional[AsyncSession] = Depends(get_db)
):
    """
    Start interview session - works with or without database
    """
    # Create agent (existing logic)
    if not hasattr(app.state, 'interview_agents'):
        app.state.interview_agents = {}
    
    if request.framework not in app.state.interview_agents:
        agent = InterviewAgent(request.framework, api_key=os.getenv("OPENAI_API_KEY"))
        app.state.interview_agents[request.framework] = agent
    else:
        agent = app.state.interview_agents[request.framework]
    
    # Start session
    session = agent.start_session(
        site_name=request.site_name,
        site_code=request.site_code,
        operator=request.operator,
        auditor_name=request.auditor_name,
        auditor_email=request.auditor_email,
        language=request.language,
        categories=request.categories
    )
    
    # Save to database if available
    if db and USE_DATABASE:
        db_session = InterviewSessionDB(
            session_id=session.session_id,
            framework=request.framework,
            site_name=request.site_name,
            site_code=request.site_code,
            operator=request.operator,
            auditor_name=request.auditor_name,
            auditor_email=request.auditor_email,
            language=request.language,
            status="in_progress",
            total_questions=session.total_questions,
            answers=[]
        )
        db.add(db_session)
        await db.commit()
    else:
        # Fallback to in-memory
        await memory_store.save_session(session.session_id, session.model_dump())
    
    # Get first question
    first_question = agent.get_next_question(session.session_id)
    
    # Return same format - frontend unchanged
    return {
        "session": session,
        "first_question": first_question,
        "total_questions": session.total_questions,
        "categories": get_categories_for_framework(request.framework)
    }

# Modified dashboard endpoint - always accessible
@app.get("/dashboard/summary", response_model=DashboardSummary)
async def get_dashboard_summary(db: Optional[AsyncSession] = Depends(get_db)):
    """
    Get dashboard summary - works even during processing
    """
    # Load mock data (always available)
    mock_reports = load_mock_reports()
    
    # Include real data if database available
    all_reports = mock_reports.copy()
    
    if db and USE_DATABASE:
        # Get completed reports from database
        result = await db.execute(
            select(AuditJobDB).where(AuditJobDB.status == "complete").limit(100)
        )
        db_jobs = result.scalars().all()
        
        for job in db_jobs:
            if job.report_data:
                all_reports.append({
                    "report_id": job.report_id,
                    "site_name": job.metadata.get("site_name"),
                    "compliance_score": job.report_data.get("overall_compliance_score", 0) * 100,
                    "status": job.status,
                    "date_of_audit": job.created_at.isoformat()
                })
    
    # Generate dashboard data from all reports
    # ... (rest of dashboard logic) ...
    
    return DashboardSummary(
        national_compliance_map=site_markers,
        risk_hotspots=risk_hotspots,
        compliance_trend=compliance_trend,
        framework_matrix=framework_compliance
    )

# Add new endpoint to check job status
@app.get("/audits/status/{job_id}")
async def get_audit_status(job_id: str, db: Optional[AsyncSession] = Depends(get_db)):
    """
    Check audit job status - always responsive
    """
    # Check if job is currently running
    if job_id in running_jobs:
        future = running_jobs[job_id]
        if future.running():
            return {"job_id": job_id, "status": "processing", "progress": 50}
    
    # Check database
    if db and USE_DATABASE:
        result = await db.execute(
            select(AuditJobDB).where(AuditJobDB.job_id == job_id)
        )
        job = result.scalar_one_or_none()
        if job:
            return {
                "job_id": str(job.job_id),
                "status": job.status,
                "progress": job.progress,
                "report_id": job.report_id,
                "error": job.error_message
            }
    
    # Check in-memory
    job_data = await memory_store.get_job(job_id)
    if job_data:
        return job_data
    
    # Check file system (backward compatibility)
    job_dir = RESULTS_DIR / job_id
    if job_dir.exists():
        status = read_job_status(job_dir)
        return {"job_id": job_id, "status": status.get("status", "unknown")}
    
    raise HTTPException(status_code=404, detail="Job not found")
```

---

## Phase 4: Optional Celery Integration (Production)

### 4.1 Create Celery Tasks

**Create `audit_agent/tasks.py`:**
```python
"""
Celery tasks for distributed background processing
"""
from celery import Celery
import os
import asyncio
from datetime import datetime
from audit_agent.core.orchestrator import ComplianceOrchestrator
from audit_agent.database.models import AuditJobDB
from audit_agent.database.connection import get_sync_db

# Configure Celery
celery_app = Celery(
    'vigilore',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
)

# Configure Celery settings
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max per task
    task_soft_time_limit=25 * 60,  # Soft limit at 25 minutes
)

@celery_app.task(name='process_audit', bind=True)
def process_audit_task(self, job_id: str, input_path: str, 
                       framework_paths: list, metadata: dict, api_key: str):
    """
    Process audit in Celery worker
    """
    # Update task state
    self.update_state(state='PROCESSING', meta={'progress': 10})
    
    # Run async code in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Update database status
        db = get_sync_db()
        if db:
            job = db.query(AuditJobDB).filter_by(job_id=job_id).first()
            if job:
                job.status = 'processing'
                job.progress = 20
                db.commit()
        
        # Run orchestrator
        orchestrator = ComplianceOrchestrator(api_key=api_key)
        report = loop.run_until_complete(
            orchestrator.analyze(input_path, framework_paths)
        )
        
        self.update_state(state='PROCESSING', meta={'progress': 80})
        
        # Save results
        if db and job:
            job.status = 'complete'
            job.report_data = report.model_dump()
            job.completed_at = datetime.now()
            job.progress = 100
            db.commit()
        
        return {
            "status": "complete",
            "job_id": job_id,
            "report_id": metadata.get('report_id')
        }
        
    except Exception as e:
        # Update failure status
        if db:
            job = db.query(AuditJobDB).filter_by(job_id=job_id).first()
            if job:
                job.status = 'failed'
                job.error_message = str(e)
                db.commit()
        
        raise  # Re-raise for Celery error handling
        
    finally:
        loop.close()
        if db:
            db.close()

# Start worker with:
# celery -A audit_agent.tasks worker --loglevel=info
```

### 4.2 Add Redis Service

**Update `render.yaml` for Celery:**
```yaml
services:
  - type: web
    name: vigilore-api
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn api_v2:app --host 0.0.0.0 --port $PORT --workers 2
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: vigilore-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: vigilore-cache
          property: connectionString

  # Celery worker service
  - type: worker
    name: vigilore-worker
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: celery -A audit_agent.tasks worker --loglevel=info
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: vigilore-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: vigilore-cache
          property: connectionString

databases:
  - name: vigilore-db
    plan: starter

services:
  - type: redis
    name: vigilore-cache
    plan: starter  # $10/month
```

---

## Phase 5: Local Development Setup

### 5.1 Create Local Environment

**Create `.env` file:**
```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/vigilore_dev
USE_DATABASE=true

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=your-key-here

# Development
DEBUG=true
```

### 5.2 Docker Compose for Local Development

**Create `docker-compose.yml`:**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: vigilore_dev
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  app:
    build: .
    ports:
      - "9999:9999"
    environment:
      DATABASE_URL: postgresql://postgres:password@postgres:5432/vigilore_dev
      REDIS_URL: redis://redis:6379/0
      USE_DATABASE: "true"
    depends_on:
      - postgres
      - redis
    command: uvicorn api_v2:app --reload --host 0.0.0.0 --port 9999

  worker:
    build: .
    environment:
      DATABASE_URL: postgresql://postgres:password@postgres:5432/vigilore_dev
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    command: celery -A audit_agent.tasks worker --loglevel=info

volumes:
  postgres_data:
```

### 5.3 Initialize Local Database

```bash
# Start services
docker-compose up -d postgres redis

# Initialize database
python -m audit_agent.database.init_db

# Run development server
uvicorn api_v2:app --reload --host localhost --port 9999

# Optional: Start Celery worker
celery -A audit_agent.tasks worker --loglevel=info
```

---

## Deployment Steps

### Step 1: Prepare Code
```bash
# 1. Update requirements.txt with new dependencies
# 2. Create database models and connection files
# 3. Update api_v2.py with new code
# 4. Test locally
```

### Step 2: Deploy to Render
```bash
# 1. Commit and push changes
git add .
git commit -m "Add multi-user support with database and background processing"
git push

# 2. Render will auto-deploy
```

### Step 3: Initialize Production Database
```bash
# 1. In Render Dashboard, go to your web service
# 2. Click "Shell" tab
# 3. Run:
python -m audit_agent.database.init_db
```

### Step 4: Verify Deployment
```bash
# Test endpoints
curl https://your-app.onrender.com/
curl https://your-app.onrender.com/dashboard/summary
```

---

## Testing Multi-User Support

### Test Concurrent Users
```python
# test_concurrent.py
import asyncio
import aiohttp

async def submit_audit(session, user_id):
    """Submit audit as specific user"""
    url = "http://localhost:9999/audits"
    data = {
        "site_name": f"Test Site {user_id}",
        "operator": f"Operator {user_id}",
        "auditor_name": f"User {user_id}",
        "auditor_email": f"user{user_id}@test.com"
    }
    files = {
        "input_file": open("test.pdf", "rb"),
        "framework_files": open("framework.pdf", "rb")
    }
    
    async with session.post(url, data=data, files=files) as response:
        result = await response.json()
        print(f"User {user_id}: {result['job_id']}")
        return result['job_id']

async def test_concurrent_users():
    """Test multiple users simultaneously"""
    async with aiohttp.ClientSession() as session:
        # Submit 5 audits simultaneously
        tasks = [submit_audit(session, i) for i in range(5)]
        job_ids = await asyncio.gather(*tasks)
        
        # Check dashboard is still accessible
        async with session.get("http://localhost:9999/dashboard/summary") as response:
            assert response.status == 200
            print("Dashboard accessible during processing!")
        
        # Check all job statuses
        for job_id in job_ids:
            async with session.get(f"http://localhost:9999/audits/status/{job_id}") as response:
                status = await response.json()
                print(f"Job {job_id}: {status['status']}")

if __name__ == "__main__":
    asyncio.run(test_concurrent_users())
```

---

## Monitoring and Maintenance

### Database Queries for Monitoring
```sql
-- Check active sessions
SELECT session_id, framework, auditor_name, status, created_at 
FROM interview_sessions 
WHERE status = 'in_progress';

-- Check processing jobs
SELECT job_id, report_id, status, progress, created_at 
FROM audit_jobs 
WHERE status IN ('processing', 'queued');

-- Daily audit statistics
SELECT 
    DATE(created_at) as audit_date,
    COUNT(*) as total_audits,
    AVG(CASE WHEN status = 'complete' THEN 1 ELSE 0 END) as completion_rate
FROM audit_jobs
GROUP BY DATE(created_at)
ORDER BY audit_date DESC;

-- Clean up old incomplete sessions
DELETE FROM interview_sessions 
WHERE status = 'in_progress' 
AND updated_at < NOW() - INTERVAL '7 days';
```

### Render Monitoring
1. **Metrics Dashboard**: Monitor CPU, memory, response times
2. **Logs**: Check for errors in real-time
3. **Alerts**: Set up alerts for high CPU or errors
4. **Auto-scaling**: Configure based on CPU/memory thresholds

---

## Rollback Plan

If issues arise, you can quickly rollback:

### 1. Disable Database (Immediate)
```bash
# In Render environment variables
USE_DATABASE=false
```

### 2. Revert Code (if needed)
```bash
git revert HEAD
git push
```

### 3. Use Previous Threading
```python
# In api_v2.py, comment out new code and use:
background_tasks.add_task(run_compliance_pipeline, ...)
```

---

## Cost Summary

### Monthly Costs on Render
- **Web Service**: Free tier or $7/month (Starter)
- **PostgreSQL**: $7/month (Starter - 1GB)
- **Redis** (optional): $10/month (Starter - 25MB)
- **Worker** (optional): $7/month (if separate)

**Total**: $14-31/month depending on configuration

### Performance Expectations
- **Concurrent Users**: 100+ with Starter plan
- **Audits/Day**: 500-1000 depending on complexity
- **Response Time**: <100ms for API calls
- **Processing Time**: Unchanged (background)

---

## Summary

This implementation provides:
1. ✅ **Multi-user support** with database persistence
2. ✅ **Non-blocking processing** - API always responsive
3. ✅ **Mock data always accessible** during processing
4. ✅ **Backward compatible** - no frontend changes needed
5. ✅ **Gradual migration** - feature flags for safety
6. ✅ **Production ready** - with monitoring and scaling

The hybrid approach ensures zero downtime and safe migration from the current single-user system to a scalable multi-user platform.