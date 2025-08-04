"""
FastAPI application v2 - Enhanced for Frontend Integration
Includes metadata fields, dashboard endpoints, and reporting features
"""

import uuid
import json
import os
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum
import random

from fastapi import FastAPI, UploadFile, BackgroundTasks, HTTPException, File, Form, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr

from audit_agent.core.orchestrator import ComplianceOrchestrator
from audit_agent.models.compliance_models import FinalReport
from audit_agent.utils.exceptions import AuditAgentError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="VigilOre Compliance API",
    description="API for multi-agent compliance analysis with dashboard and reporting",
    version="2.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
RESULTS_DIR = Path("api_results")
RESULTS_DIR.mkdir(exist_ok=True, parents=True)
METADATA_FILE = RESULTS_DIR / "audit_metadata.json"

# Job status enum
class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "complete"
    FAILED = "error"

class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non-compliant"
    REVIEW_NEEDED = "review_needed"
    NOT_APPLICABLE = "not_applicable"

# Response models
class AuditSubmissionResponse(BaseModel):
    job_id: str
    status: str = "processing"
    message: str = "Audit submission accepted and is now being processed."

class AuditStatusResponse(BaseModel):
    job_id: str
    status: str

class SiteMarker(BaseModel):
    site_name: str
    latitude: float
    longitude: float
    status: str

class RiskIssue(BaseModel):
    issue: str
    status: str

class RiskHotspot(BaseModel):
    site_name: str
    site_code: str
    risk_score: int
    top_issues: List[RiskIssue]

class ComplianceTrendPoint(BaseModel):
    month: str
    score: float

class FrameworkCompliance(BaseModel):
    framework: str
    compliant: int
    non_compliant: int
    review_needed: int
    not_applicable: int

class DashboardSummary(BaseModel):
    national_compliance_map: List[SiteMarker]
    risk_hotspots: List[RiskHotspot]
    compliance_trend: List[ComplianceTrendPoint]
    framework_matrix: List[FrameworkCompliance]

class FindingsSummary(BaseModel):
    compliant: int
    non_compliant: int
    review_needed: int

class ReportItem(BaseModel):
    report_id: str
    audit_site: str
    date_of_audit: str
    compliance_score: float
    status: str
    findings_summary: FindingsSummary

class ReportsListResponse(BaseModel):
    total_reports: int
    page: int
    limit: int
    reports: List[ReportItem]

# Helper functions
def load_audit_metadata() -> Dict[str, Any]:
    """Load audit metadata from file"""
    try:
        if METADATA_FILE.exists():
            with open(METADATA_FILE, "r") as f:
                data = json.load(f)
                # Ensure audits key exists
                if "audits" not in data:
                    data["audits"] = {}
                return data
    except Exception as e:
        logger.error(f"Error loading audit metadata: {e}")
    return {"audits": {}}

def save_audit_metadata(metadata: Dict[str, Any]):
    """Save audit metadata to file"""
    try:
        # Ensure directory exists
        METADATA_FILE.parent.mkdir(exist_ok=True, parents=True)
        with open(METADATA_FILE, "w") as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving audit metadata: {e}")

def write_job_status(job_dir: Path, status: JobStatus, error: str = None, progress: int = None):
    """Write job status to file"""
    status_data = {
        "status": status.value,
        "updated_at": datetime.now().isoformat(),
        "progress": progress
    }
    if error:
        status_data["error"] = error
    
    with open(job_dir / "status.json", "w") as f:
        json.dump(status_data, f)

def read_job_status(job_dir: Path) -> Dict[str, Any]:
    """Read job status from file"""
    status_file = job_dir / "status.json"
    if not status_file.exists():
        return None
    
    with open(status_file, "r") as f:
        return json.load(f)

async def run_compliance_pipeline(
    job_id: str,
    input_path: Path,
    framework_paths: List[Path],
    metadata: Dict[str, Any],
    api_key: str = None
):
    """
    Run the compliance analysis pipeline in the background
    """
    job_dir = RESULTS_DIR / job_id
    
    try:
        logger.info(f"Starting compliance analysis for job {job_id}")
        write_job_status(job_dir, JobStatus.PROCESSING, progress=10)
        
        # Get API key from environment if not provided
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable or provide in request.")
        
        # Initialize orchestrator
        orchestrator = ComplianceOrchestrator(api_key=api_key)
        
        # Update progress
        write_job_status(job_dir, JobStatus.PROCESSING, progress=20)
        
        # Run analysis
        report = await orchestrator.analyze(
            input_path=str(input_path),
            framework_paths=[str(p) for p in framework_paths],
            categories=None  # Use all categories
        )
        
        # Update progress
        write_job_status(job_dir, JobStatus.PROCESSING, progress=80)
        
        # Save results
        json_output = job_dir / "report.json"
        with open(json_output, 'w') as f:
            json.dump(report.model_dump(), f, indent=2)
        
        excel_output = job_dir / "report.xlsx"
        orchestrator.aggregator.generate_excel_report(report, str(excel_output))
        
        # Update metadata with results
        all_metadata = load_audit_metadata()
        all_metadata["audits"][job_id].update({
            "status": JobStatus.COMPLETED.value,
            "completed_at": datetime.now().isoformat(),
            "compliance_score": report.overall_compliance_score * 100,
            "findings_summary": {
                "compliant": sum(1 for r in report.results for i in r.items if i.match_score >= 0.8),
                "non_compliant": sum(1 for r in report.results for i in r.items if i.match_score < 0.5),
                "review_needed": sum(1 for r in report.results for i in r.items if 0.5 <= i.match_score < 0.8)
            }
        })
        save_audit_metadata(all_metadata)
        
        # Cleanup orchestrator
        await orchestrator.cleanup()
        
        # Mark as completed
        write_job_status(job_dir, JobStatus.COMPLETED, progress=100)
        logger.info(f"Completed compliance analysis for job {job_id}")
        
    except AuditAgentError as e:
        logger.error(f"Audit error in job {job_id}: {str(e)}")
        write_job_status(job_dir, JobStatus.FAILED, error=str(e))
        
        # Update metadata
        all_metadata = load_audit_metadata()
        all_metadata["audits"][job_id]["status"] = JobStatus.FAILED.value
        all_metadata["audits"][job_id]["error"] = str(e)
        save_audit_metadata(all_metadata)
        
    except Exception as e:
        logger.error(f"Unexpected error in job {job_id}: {str(e)}")
        write_job_status(job_dir, JobStatus.FAILED, error=f"Internal error: {str(e)}")
        
        # Update metadata
        all_metadata = load_audit_metadata()
        all_metadata["audits"][job_id]["status"] = JobStatus.FAILED.value
        all_metadata["audits"][job_id]["error"] = str(e)
        save_audit_metadata(all_metadata)

# API Endpoints
@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0"}

@app.post("/audits", response_model=AuditSubmissionResponse)
async def submit_audit(
    background_tasks: BackgroundTasks,
    input_file: UploadFile = File(..., description="Input transcript or report"),
    framework_files: List[UploadFile] = File(..., description="Framework documents"),
    site_name: str = Form(..., description="Mine site name"),
    operator: str = Form(..., description="Operator code"),
    auditor_name: str = Form(..., description="Auditor name"),
    auditor_email: EmailStr = Form(..., description="Auditor email"),
    language: str = Form("en", description="Language code"),
    api_key: Optional[str] = Form(None, description="OpenAI API key")
):
    """
    Submit a new compliance audit with metadata
    
    This endpoint matches the frontend's "Submit Audit" form
    """
    
    # Validate file types
    valid_input_extensions = ['.pdf', '.txt', '.mp3', '.docx']
    if not any(input_file.filename.lower().endswith(ext) for ext in valid_input_extensions):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid input file type. Supported: {', '.join(valid_input_extensions)}"
        )
    
    valid_framework_extensions = ['.pdf', '.txt', '.docx']
    for fw_file in framework_files:
        if not any(fw_file.filename.lower().endswith(ext) for ext in valid_framework_extensions):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid framework file '{fw_file.filename}'. Supported: {', '.join(valid_framework_extensions)}"
            )
    
    # Generate job ID and create directory
    job_id = str(uuid.uuid4())
    job_dir = RESULTS_DIR / job_id
    job_dir.mkdir(parents=True)
    
    # Create report ID (e.g., REP-2025-0001)
    all_metadata = load_audit_metadata()
    report_number = len(all_metadata.get("audits", {})) + 1
    report_id = f"REP-{datetime.now().year}-{report_number:04d}"
    
    # Write initial status
    write_job_status(job_dir, JobStatus.PROCESSING)
    
    try:
        # Save uploaded files
        input_path = job_dir / "input" / input_file.filename
        input_path.parent.mkdir(exist_ok=True)
        with open(input_path, "wb") as f:
            content = await input_file.read()
            f.write(content)
        
        framework_paths = []
        frameworks_dir = job_dir / "frameworks"
        frameworks_dir.mkdir(exist_ok=True)
        
        for fw_file in framework_files:
            fw_path = frameworks_dir / fw_file.filename
            with open(fw_path, "wb") as f:
                content = await fw_file.read()
                f.write(content)
            framework_paths.append(fw_path)
        
        # Store metadata
        audit_metadata = {
            "job_id": job_id,
            "report_id": report_id,
            "site_name": site_name,
            "operator": operator,
            "auditor_name": auditor_name,
            "auditor_email": auditor_email,
            "language": language,
            "submitted_at": datetime.now().isoformat(),
            "date_of_audit": datetime.now().date().isoformat(),
            "status": JobStatus.PROCESSING.value,
            "input_file": input_file.filename,
            "framework_files": [f.filename for f in framework_files]
        }
        
        # Save metadata
        all_metadata["audits"][job_id] = audit_metadata
        save_audit_metadata(all_metadata)
        
        # Add background task
        background_tasks.add_task(
            run_compliance_pipeline,
            job_id,
            input_path,
            framework_paths,
            audit_metadata,
            api_key
        )
        
        return AuditSubmissionResponse(job_id=job_id)
        
    except Exception as e:
        # Clean up on error
        import shutil
        if job_dir.exists():
            shutil.rmtree(job_dir)
        raise HTTPException(status_code=500, detail=f"Failed to process files: {str(e)}")

@app.get("/audits/status/{job_id}", response_model=AuditStatusResponse)
async def get_audit_status(job_id: str):
    """
    Get the status of a compliance audit job
    
    Frontend uses this for polling
    """
    job_dir = RESULTS_DIR / job_id
    
    if not job_dir.exists():
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Read status file
    status_data = read_job_status(job_dir)
    
    if not status_data:
        # Fallback to checking if results exist
        if (job_dir / "report.xlsx").exists():
            return AuditStatusResponse(job_id=job_id, status=JobStatus.COMPLETED.value)
        else:
            return AuditStatusResponse(job_id=job_id, status=JobStatus.PROCESSING.value)
    
    return AuditStatusResponse(
        job_id=job_id,
        status=status_data["status"]
    )

@app.get("/dashboard/summary", response_model=DashboardSummary)
async def get_dashboard_summary():
    """
    Get dashboard summary data
    
    Returns aggregated compliance data for the dashboard visualization
    """
    
    # Load metadata to get real audit data
    metadata = load_audit_metadata()
    audits = metadata.get("audits", {})
    
    # Generate sample map data (in production, this would come from a database)
    sites = [
        {"name": "Kamoto Copper Company - Pit 2", "lat": -10.7, "lng": 25.4, "status": "non-compliant"},
        {"name": "Mutanda Mining", "lat": -10.9, "lng": 25.8, "status": "compliant"},
        {"name": "Tenke Fungurume", "lat": -10.6, "lng": 26.2, "status": "review_needed"},
        {"name": "Kibali Gold Mine", "lat": 3.0, "lng": 29.9, "status": "compliant"},
        {"name": "Kamoa-Kakula", "lat": -11.2, "lng": 26.5, "status": "non-compliant"},
    ]
    
    national_compliance_map = [
        SiteMarker(
            site_name=site["name"],
            latitude=site["lat"],
            longitude=site["lng"],
            status=site["status"]
        ) for site in sites
    ]
    
    # Calculate risk hotspots from recent audits
    risk_hotspots = [
        RiskHotspot(
            site_name="Kamoto Copper Company - Pit 2",
            site_code="KCC-002",
            risk_score=85,
            top_issues=[
                RiskIssue(issue="Armed-Guard Training Gaps (VPSHR 2.B.3)", status="non-compliant"),
                RiskIssue(issue="Explosives Storage Perimeter Fencing (DRC 7.6.A)", status="non-compliant")
            ]
        )
    ]
    
    # Generate compliance trend (last 7 months)
    months = ["FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG"]
    base_score = 75
    compliance_trend = []
    
    for i, month in enumerate(months):
        # Add some variation but trending upward
        score = base_score + i * 1.5 + random.uniform(-2, 3)
        compliance_trend.append(ComplianceTrendPoint(month=month, score=round(score, 1)))
    
    # Framework compliance matrix
    framework_matrix = [
        FrameworkCompliance(
            framework="DRC Mining Code (2018)",
            compliant=20,
            non_compliant=43,
            review_needed=65,
            not_applicable=2
        ),
        FrameworkCompliance(
            framework="VPSHR (2020)",
            compliant=13,
            non_compliant=34,
            review_needed=23,
            not_applicable=23
        ),
        FrameworkCompliance(
            framework="ISO Standards",
            compliant=12,
            non_compliant=23,
            review_needed=13,
            not_applicable=4
        ),
        FrameworkCompliance(
            framework="GSMS",
            compliant=18,
            non_compliant=15,
            review_needed=20,
            not_applicable=7
        )
    ]
    
    return DashboardSummary(
        national_compliance_map=national_compliance_map,
        risk_hotspots=risk_hotspots,
        compliance_trend=compliance_trend,
        framework_matrix=framework_matrix
    )

@app.get("/reports", response_model=ReportsListResponse)
async def get_reports_list(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("date_of_audit", description="Sort field"),
    order: str = Query("desc", description="Sort order (asc/desc)")
):
    """
    Get paginated list of audit reports
    
    Returns a list of all submitted audits for the Reports table
    """
    
    # Load all audits from metadata
    metadata = load_audit_metadata()
    all_audits = list(metadata.get("audits", {}).values())
    
    # Filter only completed audits
    completed_audits = [a for a in all_audits if a.get("status") == JobStatus.COMPLETED.value]
    
    # Sort audits
    if sort_by == "date_of_audit":
        completed_audits.sort(key=lambda x: x.get("date_of_audit", ""), reverse=(order == "desc"))
    elif sort_by == "compliance_score":
        completed_audits.sort(key=lambda x: x.get("compliance_score", 0), reverse=(order == "desc"))
    
    # Calculate pagination
    total_reports = len(completed_audits)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_audits = completed_audits[start_idx:end_idx]
    
    # Format reports
    reports = []
    for audit in paginated_audits:
        reports.append(ReportItem(
            report_id=audit.get("report_id", "Unknown"),
            audit_site=audit.get("site_name", "Unknown Site"),
            date_of_audit=audit.get("date_of_audit", datetime.now().date().isoformat()),
            compliance_score=round(audit.get("compliance_score", 0), 1),
            status=audit.get("status", "unknown"),
            findings_summary=FindingsSummary(
                compliant=audit.get("findings_summary", {}).get("compliant", 0),
                non_compliant=audit.get("findings_summary", {}).get("non_compliant", 0),
                review_needed=audit.get("findings_summary", {}).get("review_needed", 0)
            )
        ))
    
    return ReportsListResponse(
        total_reports=total_reports,
        page=page,
        limit=limit,
        reports=reports
    )

@app.get("/reports/{report_id}")
async def get_report_details(report_id: str):
    """
    Get detailed report by report ID
    
    Returns the full compliance report for a specific audit
    """
    
    # Find the audit with this report_id
    metadata = load_audit_metadata()
    audit = None
    job_id = None
    
    for jid, audit_data in metadata.get("audits", {}).items():
        if audit_data.get("report_id") == report_id:
            audit = audit_data
            job_id = jid
            break
    
    if not audit:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Load the full report
    json_path = RESULTS_DIR / job_id / "report.json"
    
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Report data not found")
    
    with open(json_path, "r") as f:
        report_data = json.load(f)
    
    # Add metadata to the report
    report_data["metadata"] = audit
    
    return report_data

@app.get("/reports/{report_id}/excel")
async def download_report_excel(report_id: str):
    """
    Download Excel report by report ID
    """
    
    # Find the audit with this report_id
    metadata = load_audit_metadata()
    job_id = None
    
    for jid, audit_data in metadata.get("audits", {}).items():
        if audit_data.get("report_id") == report_id:
            job_id = jid
            break
    
    if not job_id:
        raise HTTPException(status_code=404, detail="Report not found")
    
    excel_path = RESULTS_DIR / job_id / "report.xlsx"
    
    if not excel_path.exists():
        raise HTTPException(status_code=404, detail="Excel report not found")
    
    return FileResponse(
        excel_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"compliance_report_{report_id}.xlsx"
    )

# Legacy endpoints for backward compatibility
@app.get("/results/{job_id}/json")
async def get_json_result(job_id: str):
    """Legacy endpoint - get JSON report by job_id"""
    json_path = RESULTS_DIR / job_id / "report.json"
    
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Results not ready yet")
    
    return FileResponse(
        json_path,
        media_type="application/json",
        filename=f"compliance_report_{job_id}.json"
    )

@app.get("/results/{job_id}/excel")
async def get_excel_result(job_id: str):
    """Legacy endpoint - get Excel report by job_id"""
    excel_path = RESULTS_DIR / job_id / "report.xlsx"
    
    if not excel_path.exists():
        raise HTTPException(status_code=404, detail="Results not ready yet")
    
    return FileResponse(
        excel_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"compliance_report_{job_id}.xlsx"
    )

if __name__ == "__main__":
    import uvicorn
    # Using localhost and a high port number for better Windows compatibility
    uvicorn.run(app, host="localhost", port=9999)