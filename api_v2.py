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
    REVIEW_NEEDED = "review-needed"
    NOT_APPLICABLE = "not-applicable"

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
    site_code: str
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
    site_code: Optional[str] = None
    date_of_audit: str
    compliance_score: float
    status: str
    findings_summary: FindingsSummary
    auditor_name: Optional[str] = None
    frameworks: Optional[List[str]] = []

class ReportsListResponse(BaseModel):
    total_reports: int
    page: int
    limit: int
    reports: List[ReportItem]

# Helper functions
def generate_mock_reports() -> List[Dict[str, Any]]:
    """Generate mock audit reports for demo purposes"""
    mock_reports = [
        {
            "job_id": "mock-001",
            "report_id": "REP-2024-0001",
            "site_name": "Kinshasa Mining Complex",
            "site_code": "KIN-001",
            "operator": "Congo Mining Corp",
            "auditor_name": "Jean-Pierre Mbala",
            "auditor_email": "jp.mbala@audit.cg",
            "date_of_audit": "2024-11-15",
            "status": "complete",
            "compliance_score": 45.2,
            "compliance_status": "non-compliant",
            "findings_summary": {"compliant": 12, "non_compliant": 18, "review_needed": 5},
            "framework_files": ["ISO_14001_2015.pdf", "VPSHR_2020.pdf"]
        },
        {
            "job_id": "mock-002",
            "report_id": "REP-2024-0002",
            "site_name": "Lubumbashi Copper Mine",
            "site_code": "LBM-004",
            "operator": "Sangha Resources Ltd",
            "auditor_name": "Marie Kouassi",
            "auditor_email": "m.kouassi@compliance.cg",
            "date_of_audit": "2024-11-20",
            "status": "complete",
            "compliance_score": 82.7,
            "compliance_status": "compliant",
            "findings_summary": {"compliant": 28, "non_compliant": 3, "review_needed": 4},
            "framework_files": ["DRC_Mining_Code_2018.pdf"]
        },
        {
            "job_id": "mock-003",
            "report_id": "REP-2024-0003",
            "site_name": "Mbuji-Mayi Diamond",
            "site_code": "MJM-025",
            "operator": "Alima Gold International",
            "auditor_name": "Pierre Makaya",
            "auditor_email": "p.makaya@goldaudit.cg",
            "date_of_audit": "2024-11-25",
            "status": "complete",
            "compliance_score": 38.5,
            "compliance_status": "non-compliant",
            "findings_summary": {"compliant": 8, "non_compliant": 22, "review_needed": 8},
            "framework_files": ["ISO_45001_2018.pdf", "ISO_14001_2015.pdf"]
        },
        {
            "job_id": "mock-004",
            "report_id": "REP-2024-0004",
            "site_name": "Kolwezi Cobalt Mine",
            "site_code": "KWZ-012",
            "operator": "Forest Mining Solutions",
            "auditor_name": "Sarah Ndongo",
            "auditor_email": "s.ndongo@forestaudit.cg",
            "date_of_audit": "2024-12-01",
            "status": "complete",
            "compliance_score": 67.3,
            "compliance_status": "review-needed",
            "findings_summary": {"compliant": 15, "non_compliant": 7, "review_needed": 12},
            "framework_files": ["VPSHR_2020.pdf", "DRC_Mining_Code_2018.pdf"]
        },
        {
            "job_id": "mock-005",
            "report_id": "REP-2024-0005",
            "site_name": "Tenke Fungurume",
            "site_code": "TFM-061",
            "operator": "Quarry Operations CG",
            "auditor_name": "Jean-Pierre Mbala",
            "auditor_email": "jp.mbala@audit.cg",
            "date_of_audit": "2024-12-05",
            "status": "complete",
            "compliance_score": 51.8,
            "compliance_status": "non-compliant",
            "findings_summary": {"compliant": 11, "non_compliant": 16, "review_needed": 9},
            "framework_files": ["ISO_14001_2015.pdf"]
        },
        {
            "job_id": "mock-006",
            "report_id": "REP-2024-0006",
            "site_name": "Goma Mining Site",
            "site_code": "GOM-007",
            "operator": "Ouesso Mining Corp",
            "auditor_name": "Emmanuel Tchissambou",
            "auditor_email": "e.tchissambou@ouessoaudit.cg",
            "date_of_audit": "2024-12-08",
            "status": "complete",
            "compliance_score": 78.9,
            "compliance_status": "compliant",
            "findings_summary": {"compliant": 25, "non_compliant": 5, "review_needed": 6},
            "framework_files": ["ISO_45001_2018.pdf", "VPSHR_2020.pdf"]
        },
        {
            "job_id": "mock-007",
            "report_id": "REP-2024-0007",
            "site_name": "Bukavu Tin Mine",
            "site_code": "BKV-008",
            "operator": "Niari Valley Resources",
            "auditor_name": "Claudine Moukoko",
            "auditor_email": "c.moukoko@niariaudit.cg",
            "date_of_audit": "2024-12-10",
            "status": "complete",
            "compliance_score": 42.1,
            "compliance_status": "non-compliant",
            "findings_summary": {"compliant": 10, "non_compliant": 20, "review_needed": 10},
            "framework_files": ["DRC_Mining_Code_2018.pdf", "ISO_14001_2015.pdf"]
        },
        {
            "job_id": "mock-008",
            "report_id": "REP-2024-0008",
            "site_name": "Kananga Diamond Mine",
            "site_code": "KNG-002",
            "operator": "Coastal Mining Industries",
            "auditor_name": "François Malonga",
            "auditor_email": "f.malonga@coastalaudit.cg",
            "date_of_audit": "2024-12-12",
            "status": "complete",
            "compliance_score": 89.3,
            "compliance_status": "compliant",
            "findings_summary": {"compliant": 32, "non_compliant": 2, "review_needed": 3},
            "framework_files": ["ISO_14001_2015.pdf", "ISO_45001_2018.pdf"]
        },
        {
            "job_id": "mock-009",
            "report_id": "REP-2024-0009",
            "site_name": "Mbandaka Forest Mine",
            "site_code": "MBD-019",
            "operator": "Diamond Extraction Ltd",
            "auditor_name": "Marie Kouassi",
            "auditor_email": "m.kouassi@compliance.cg",
            "date_of_audit": "2024-12-14",
            "status": "complete",
            "compliance_score": 63.7,
            "compliance_status": "review-needed",
            "findings_summary": {"compliant": 18, "non_compliant": 9, "review_needed": 11},
            "framework_files": ["VPSHR_2020.pdf"]
        },
        {
            "job_id": "mock-010",
            "report_id": "REP-2024-0010",
            "site_name": "Tshikapa Mine",
            "site_code": "TSH-031",
            "operator": "Iron Ore Congo SA",
            "auditor_name": "Robert Nganga",
            "auditor_email": "r.nganga@ironaudit.cg",
            "date_of_audit": "2024-12-16",
            "status": "complete",
            "compliance_score": 75.4,
            "compliance_status": "compliant",
            "findings_summary": {"compliant": 22, "non_compliant": 6, "review_needed": 7},
            "framework_files": ["DRC_Mining_Code_2018.pdf"]
        },
        {
            "job_id": "mock-011",
            "report_id": "REP-2024-0011",
            "site_name": "Kipushi Zinc Mine",
            "site_code": "KPS-013",
            "operator": "Bauxite Mining Group",
            "auditor_name": "Sarah Ndongo",
            "auditor_email": "s.ndongo@forestaudit.cg",
            "date_of_audit": "2024-12-18",
            "status": "complete",
            "compliance_score": 55.2,
            "compliance_status": "review-needed",
            "findings_summary": {"compliant": 14, "non_compliant": 13, "review_needed": 10},
            "framework_files": ["ISO_14001_2015.pdf", "ISO_45001_2018.pdf"]
        },
        {
            "job_id": "mock-012",
            "report_id": "REP-2024-0012",
            "site_name": "Kamoa Copper Project",
            "site_code": "KMP-055",
            "operator": "Copper Resources International",
            "auditor_name": "Jean-Baptiste Kaya",
            "auditor_email": "jb.kaya@copperaudit.cg",
            "date_of_audit": "2024-12-20",
            "status": "complete",
            "compliance_score": 83.6,
            "compliance_status": "compliant",
            "findings_summary": {"compliant": 29, "non_compliant": 4, "review_needed": 5},
            "framework_files": ["VPSHR_2020.pdf", "DRC_Mining_Code_2018.pdf"]
        },
        {
            "job_id": "mock-013",
            "report_id": "REP-2024-0013",
            "site_name": "Kamoto Underground",
            "site_code": "KMT-078",
            "operator": "Forest Concessions Ltd",
            "auditor_name": "Pierre Makaya",
            "auditor_email": "p.makaya@goldaudit.cg",
            "date_of_audit": "2024-12-22",
            "status": "complete",
            "compliance_score": 71.8,
            "compliance_status": "review-needed",
            "findings_summary": {"compliant": 20, "non_compliant": 8, "review_needed": 8},
            "framework_files": ["ISO_14001_2015.pdf"]
        },
        {
            "job_id": "mock-014",
            "report_id": "REP-2024-0014",
            "site_name": "Mutanda Mining",
            "site_code": "MTD-084",
            "operator": "Phosphate Mining Congo",
            "auditor_name": "Claudine Moukoko",
            "auditor_email": "c.moukoko@niariaudit.cg",
            "date_of_audit": "2024-12-24",
            "status": "complete",
            "compliance_score": 58.9,
            "compliance_status": "review-needed",
            "findings_summary": {"compliant": 16, "non_compliant": 12, "review_needed": 14},
            "framework_files": ["DRC_Mining_Code_2018.pdf", "ISO_45001_2018.pdf"]
        },
        {
            "job_id": "mock-015",
            "report_id": "REP-2024-0015",
            "site_name": "Mongbwalu Gold",
            "site_code": "MGB-118",
            "operator": "Zinc Extraction Industries",
            "auditor_name": "Emmanuel Tchissambou",
            "auditor_email": "e.tchissambou@ouessoaudit.cg",
            "date_of_audit": "2024-12-26",
            "status": "complete",
            "compliance_score": 39.7,
            "compliance_status": "non-compliant",
            "findings_summary": {"compliant": 9, "non_compliant": 21, "review_needed": 7},
            "framework_files": ["ISO_14001_2015.pdf", "VPSHR_2020.pdf", "ISO_45001_2018.pdf"]
        }
    ]
    return mock_reports

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
        if job_id in all_metadata.get("audits", {}):
            # Determine compliance status based on score
            compliance_score = report.overall_compliance_score * 100
            if compliance_score >= 80:
                compliance_status = "compliant"
            elif compliance_score >= 60:
                compliance_status = "review-needed"
            else:
                compliance_status = "non-compliant"
            
            all_metadata["audits"][job_id].update({
                "status": JobStatus.COMPLETED.value,
                "completed_at": datetime.now().isoformat(),
                "compliance_score": compliance_score,
                "compliance_status": compliance_status,
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
        if job_id in all_metadata.get("audits", {}):
            all_metadata["audits"][job_id]["status"] = JobStatus.FAILED.value
            all_metadata["audits"][job_id]["error"] = str(e)
            save_audit_metadata(all_metadata)
        
    except Exception as e:
        logger.error(f"Unexpected error in job {job_id}: {str(e)}")
        write_job_status(job_dir, JobStatus.FAILED, error=f"Internal error: {str(e)}")
        
        # Update metadata
        all_metadata = load_audit_metadata()
        if job_id in all_metadata.get("audits", {}):
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
    site_code: Optional[str] = Form(None, description="Mine site code"),
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
            "site_code": site_code,
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
        
        return AuditSubmissionResponse(
            job_id=job_id,
            status="processing",
            message=f"Audit submission accepted. Report ID: {report_id}"
        )
        
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
    
    # Mock data for POC demonstration - this serves as baseline data
    # Real user-submitted audits will be added to this data
    mock_sites = [
        {"name": "Kinshasa Mining Complex", "code": "KIN-001", "lat": -4.3276, "lng": 15.3136, "status": "non-compliant"},
        {"name": "Lubumbashi Copper Mine", "code": "LBM-004", "lat": -11.6640, "lng": 27.4792, "status": "compliant"},
        {"name": "Kolwezi Cobalt Mine", "code": "KWZ-012", "lat": -10.7143, "lng": 25.4666, "status": "review-needed"},
        {"name": "Goma Mining Site", "code": "GOM-007", "lat": -1.6784, "lng": 29.2308, "status": "compliant"},
        {"name": "Kisangani Gold Mine", "code": "KIS-003", "lat": 0.5152, "lng": 25.1919, "status": "not-applicable"},
        {"name": "Bukavu Tin Mine", "code": "BKV-008", "lat": -2.5083, "lng": 28.8428, "status": "non-compliant"},
        {"name": "Matadi Iron Ore", "code": "MAT-015", "lat": -5.8167, "lng": 13.4833, "status": "review-needed"},
        {"name": "Kananga Diamond Mine", "code": "KNG-002", "lat": -5.8965, "lng": 22.4178, "status": "compliant"},
        {"name": "Mbandaka Forest Mine", "code": "MBD-019", "lat": 0.0486, "lng": 18.2603, "status": "review-needed"},
        {"name": "Mbuji-Mayi Diamond", "code": "MJM-025", "lat": -6.1361, "lng": 23.5891, "status": "non-compliant"},
        {"name": "Tshikapa Mine", "code": "TSH-031", "lat": -6.4167, "lng": 20.8, "status": "compliant"},
        {"name": "Likasi Copper Mine", "code": "LKS-047", "lat": -10.9813, "lng": 26.7384, "status": "not-applicable"},
        {"name": "Kipushi Zinc Mine", "code": "KPS-013", "lat": -11.7608, "lng": 27.2434, "status": "review-needed"},
        {"name": "Kamoa Copper Project", "code": "KMP-055", "lat": -10.9739, "lng": 25.3908, "status": "compliant"},
        {"name": "Tenke Fungurume", "code": "TFM-061", "lat": -10.6167, "lng": 26.2167, "status": "non-compliant"},
        {"name": "Kamoto Underground", "code": "KMT-078", "lat": -10.7215, "lng": 25.3996, "status": "compliant"},
        {"name": "Mutanda Mining", "code": "MTD-084", "lat": -10.7645, "lng": 25.5798, "status": "review-needed"},
        {"name": "Ruashi Mining", "code": "RSH-092", "lat": -11.6178, "lng": 27.5693, "status": "not-applicable"},
        {"name": "Kibali Gold Mine", "code": "KBL-103", "lat": 2.7619, "lng": 30.3822, "status": "compliant"},
        {"name": "Mongbwalu Gold", "code": "MGB-118", "lat": 1.9500, "lng": 29.9500, "status": "non-compliant"},
    ]
    
    # Start with mock sites
    all_sites = mock_sites.copy()
    existing_codes = {site["code"] for site in mock_sites}
    
    # Add real audit data if available (avoiding duplicates)
    for audit_id, audit in audits.items():
        if audit.get("status") == JobStatus.COMPLETED.value:
            site_code = audit.get("site_code")
            if site_code and site_code not in existing_codes:
                # Determine compliance status based on score
                score = audit.get("compliance_score", 0)
                if score >= 80:
                    status = "compliant"
                elif score >= 60:
                    status = "review-needed"
                else:
                    status = "non-compliant"
                
                # Add real audit site (you'd need to add lat/lng in real implementation)
                all_sites.append({
                    "name": audit.get("site_name", "Unknown Site"),
                    "code": site_code,
                    "lat": -4.0 + random.uniform(-7, 7),  # Random lat for DRC demo
                    "lng": 23.0 + random.uniform(-10, 10),  # Random lng for DRC demo
                    "status": status
                })
                existing_codes.add(site_code)
    
    # Create site markers from combined data
    national_compliance_map = [
        SiteMarker(
            site_name=site["name"],
            site_code=site["code"],
            latitude=site["lat"],
            longitude=site["lng"],
            status=site["status"]
        ) for site in all_sites
    ]
    
    # Risk hotspots mock data
    risk_hotspots = [
        RiskHotspot(
            site_name="Kinshasa Mining Complex",
            site_code="BZV-001",
            risk_score=92,
            top_issues=[
                RiskIssue(issue="Safety Protocol Violations (ISO 45001:6.1)", status="non-compliant"),
                RiskIssue(issue="Environmental Impact Assessment Missing (ISO 14001:4.3)", status="non-compliant")
            ]
        ),
        RiskHotspot(
            site_name="Sangha River Mine",
            site_code="SRM-004", 
            risk_score=67,
            top_issues=[
                RiskIssue(issue="Worker Training Documentation (VPSHR 3.A.2)", status="review-needed"),
                RiskIssue(issue="Equipment Maintenance Logs (DRC 8.2.B)", status="review-needed")
            ]
        ),
        RiskHotspot(
            site_name="Alima Gold Mine",
            site_code="AGM-025",
            risk_score=88,
            top_issues=[
                RiskIssue(issue="Waste Management Violations (ISO 14001:8.1)", status="non-compliant"),
                RiskIssue(issue="Community Engagement Records Missing (VPSHR 1.C.4)", status="non-compliant")
            ]
        ),
        RiskHotspot(
            site_name="Pool Region Quarry",
            site_code="PRQ-061",
            risk_score=79,
            top_issues=[
                RiskIssue(issue="Blast Zone Safety Protocols (DRC 5.3.A)", status="non-compliant"),
                RiskIssue(issue="Dust Control Measures Inadequate (ISO 14001:6.2)", status="review-needed")
            ]
        ),
        RiskHotspot(
            site_name="Niari Valley Mine",
            site_code="NVM-008",
            risk_score=85,
            top_issues=[
                RiskIssue(issue="Water Quality Testing Overdue (ISO 14001:9.1)", status="non-compliant"),
                RiskIssue(issue="Emergency Response Plan Outdated (ISO 45001:8.2)", status="review-needed")
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
    order: str = Query("desc", description="Sort order (asc/desc)"),
    site_name: Optional[str] = Query(None, description="Filter by site name"),
    site_code: Optional[str] = Query(None, description="Filter by site code"),
    status: Optional[str] = Query(None, description="Filter by compliance status"),
    min_score: Optional[float] = Query(None, ge=0, le=100, description="Minimum compliance score"),
    max_score: Optional[float] = Query(None, ge=0, le=100, description="Maximum compliance score"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    auditor_name: Optional[str] = Query(None, description="Filter by auditor name"),
    framework: Optional[str] = Query(None, description="Filter by framework")
):
    """
    Get paginated list of audit reports
    
    Returns a list of all submitted audits for the Reports table
    """
    
    # Load all audits from metadata
    metadata = load_audit_metadata()
    real_audits = list(metadata.get("audits", {}).values())
    
    # Combine mock reports with real audits
    mock_reports = generate_mock_reports()
    all_audits = mock_reports + real_audits
    
    # Include all audits - both completed and processing
    # Processing audits will have limited data but should still appear in the list
    filtered_audits = all_audits.copy()
    
    # Apply filters
    if site_name:
        filtered_audits = [a for a in filtered_audits if site_name.lower() in a.get("site_name", "").lower()]
    
    if site_code:
        filtered_audits = [a for a in filtered_audits if a.get("site_code", "") == site_code]
    
    if status:
        filtered_audits = [a for a in filtered_audits if a.get("compliance_status", "") == status]
    
    if min_score is not None:
        filtered_audits = [a for a in filtered_audits if a.get("compliance_score", 0) >= min_score]
    
    if max_score is not None:
        filtered_audits = [a for a in filtered_audits if a.get("compliance_score", 100) <= max_score]
    
    if start_date:
        filtered_audits = [a for a in filtered_audits if a.get("date_of_audit", "") >= start_date]
    
    if end_date:
        filtered_audits = [a for a in filtered_audits if a.get("date_of_audit", "") <= end_date]
    
    if auditor_name:
        filtered_audits = [a for a in filtered_audits if auditor_name.lower() in a.get("auditor_name", "").lower()]
    
    if framework:
        filtered_audits = [a for a in filtered_audits if framework.lower() in str(a.get("framework_files", [])).lower()]
    
    # Sort audits
    if sort_by == "date_of_audit":
        filtered_audits.sort(key=lambda x: x.get("date_of_audit", ""), reverse=(order == "desc"))
    elif sort_by == "compliance_score":
        filtered_audits.sort(key=lambda x: x.get("compliance_score", 0), reverse=(order == "desc"))
    elif sort_by == "site_name":
        filtered_audits.sort(key=lambda x: x.get("site_name", ""), reverse=(order == "desc"))
    
    # Calculate pagination
    total_reports = len(filtered_audits)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_audits = filtered_audits[start_idx:end_idx]
    
    # Format reports
    reports = []
    for audit in paginated_audits:
        # For processing audits, use default values
        audit_status = audit.get("status", "unknown")
        if audit_status == JobStatus.PROCESSING.value:
            # Processing audits don't have scores yet
            compliance_score = 0
            findings_summary = FindingsSummary(
                compliant=0,
                non_compliant=0,
                review_needed=0
            )
        else:
            compliance_score = round(audit.get("compliance_score", 0), 1)
            findings_summary = FindingsSummary(
                compliant=audit.get("findings_summary", {}).get("compliant", 0),
                non_compliant=audit.get("findings_summary", {}).get("non_compliant", 0),
                review_needed=audit.get("findings_summary", {}).get("review_needed", 0)
            )
        
        reports.append(ReportItem(
            report_id=audit.get("report_id", "Unknown"),
            audit_site=audit.get("site_name", "Unknown Site"),
            site_code=audit.get("site_code"),
            date_of_audit=audit.get("date_of_audit", datetime.now().date().isoformat()),
            compliance_score=compliance_score,
            status=audit_status,
            findings_summary=findings_summary,
            auditor_name=audit.get("auditor_name"),
            frameworks=audit.get("framework_files", [])
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
    
    # Check if it's a mock report first
    mock_reports = generate_mock_reports()
    mock_report = next((r for r in mock_reports if r.get("report_id") == report_id), None)
    
    if mock_report:
        # Generate mock detailed report with improved structure
        compliance_score = mock_report.get("compliance_score", 0)
        site_name = mock_report.get("site_name")
        
        # Convert executive summary to markdown format with emphasis on numbers
        executive_summary = f"""## Compliance Assessment Summary

**Site:** {site_name}  
**Overall Compliance Score:** **{compliance_score}%**  
**Status:** {mock_report.get('compliance_status').upper()}

### Key Findings:
- **{mock_report.get('findings_summary', {}).get('compliant', 0)}** compliant items
- **{mock_report.get('findings_summary', {}).get('non_compliant', 0)}** non-compliant items  
- **{mock_report.get('findings_summary', {}).get('review_needed', 0)}** items requiring review

### Risk Assessment:
Total potential financial exposure identified: **$50,000**"""
        
        # Structure critical actions with id, priority, and description
        critical_actions = [
            {
                "id": "action_001",
                "priority": "critical",
                "description": "Implement integrated alarm system across main gate"
            },
            {
                "id": "action_002",
                "priority": "critical",
                "description": "Close perimeter segregating gaps"
            },
            {
                "id": "action_003",
                "priority": "medium",
                "description": "Upload induction logbook template & train supervisors"
            },
            {
                "id": "action_004",
                "priority": "low",
                "description": "Provide proof of transparent production reporting"
            }
        ]
        
        # Separate financial exposure structure
        financial_exposure = {
            "totalExposure": "$50,000",
            "violations": [
                {
                    "code": "7.1.A",
                    "description": "Administrative/procedural noncompliance",
                    "maxExposure": "$12,500"
                },
                {
                    "code": "9.2.B",
                    "description": "Unauthorized processing/transformation",
                    "maxExposure": "$25,000"
                },
                {
                    "code": "8.4.C",
                    "description": "Theft, concealment of minerals",
                    "maxExposure": "$12,500"
                }
            ]
        }
        
        return {
            "metadata": mock_report,
            "timestamp": datetime.now().isoformat(),
            "frameworks": mock_report.get("framework_files", []),
            "overall_compliance_score": compliance_score / 100,
            "executive_summary": executive_summary,
            "criticalActions": critical_actions,
            "financialExposure": financial_exposure
        }
    
    # Find the real audit with this report_id
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
    
    # Check if audit is still processing
    if audit.get("status") == JobStatus.PROCESSING.value:
        # Return a processing status response
        return {
            "metadata": audit,
            "status": "processing",
            "message": "Report is still being processed. Please check back later.",
            "timestamp": audit.get("submitted_at", datetime.now().isoformat()),
            "frameworks": audit.get("framework_files", []),
            "overall_compliance_score": 0,
            "executive_summary": "## Compliance Assessment In Progress\n\nThe audit is currently being analyzed. Results will be available shortly.",
            "criticalActions": [],
            "financialExposure": {
                "totalExposure": "$0.00",
                "violations": []
            }
        }
    
    # Check if audit failed
    if audit.get("status") == JobStatus.FAILED.value:
        error_msg = audit.get("error", "An error occurred during processing")
        return {
            "metadata": audit,
            "status": "error",
            "error": error_msg,
            "timestamp": audit.get("submitted_at", datetime.now().isoformat()),
            "frameworks": audit.get("framework_files", []),
            "overall_compliance_score": 0,
            "executive_summary": f"## Compliance Assessment Failed\n\nError: {error_msg}",
            "criticalActions": [],
            "financialExposure": {
                "totalExposure": "$0.00",
                "violations": []
            }
        }
    
    # Load the full report for completed audits
    json_path = RESULTS_DIR / job_id / "report.json"
    
    if not json_path.exists():
        # This shouldn't happen for completed audits, but handle gracefully
        raise HTTPException(status_code=404, detail="Report data not found")
    
    try:
        with open(json_path, "r") as f:
            report_data = json.load(f)
    except Exception as e:
        logger.error(f"Error loading report data for {report_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading report data: {str(e)}")
    
    try:
        # Process and restructure the report data
        compliance_score = report_data.get("overall_compliance_score", 0) * 100
        site_name = audit.get("site_name", "Unknown Site")
        
        # Count findings by status
        compliant_count = 0
        non_compliant_count = 0
        review_needed_count = 0
        
        for result in report_data.get("results", []):
            for item in result.get("items", []):
                score = item.get("match_score", 0)
                if score >= 0.8:
                    compliant_count += 1
                elif score >= 0.5:
                    review_needed_count += 1
                else:
                    non_compliant_count += 1
        
        # Convert executive summary to markdown if not already
        original_summary = report_data.get("executive_summary", "")
        if not original_summary.startswith("##"):
            executive_summary = f"""## Compliance Assessment Summary

**Site:** {site_name}  
**Overall Compliance Score:** **{compliance_score:.1f}%**  

### Key Findings:
- **{compliant_count}** compliant items
- **{non_compliant_count}** non-compliant items  
- **{review_needed_count}** items requiring review

### Analysis Summary:
{original_summary}

### Risk Assessment:
Total potential financial exposure: **${report_data.get('total_max_penalty_usd', 0):,.2f}**"""
        else:
            executive_summary = original_summary
        
        # Convert critical recommendations to structured actions
        critical_actions = []
        recommendations = report_data.get("critical_recommendations", [])
        for idx, rec in enumerate(recommendations, 1):
            # Skip if recommendation is None or empty
            if not rec:
                continue
                
            # Safely convert to string and determine priority
            rec_str = str(rec)
            rec_lower = rec_str.lower() if rec_str else ""
            
            # Determine priority based on position and content
            if idx <= 2 or "critical" in rec_lower or "immediate" in rec_lower:
                priority = "critical"
            elif idx <= 4 or "high" in rec_lower:
                priority = "high"
            elif "medium" in rec_lower:
                priority = "medium"
            else:
                priority = "low"
            
            critical_actions.append({
                "id": f"action_{idx:03d}",
                "priority": priority,
                "description": rec_str
            })
        
        # Structure financial exposure data
        total_penalty = report_data.get("total_max_penalty_usd", 0)
        financial_exposure = {
            "totalExposure": f"${total_penalty:,.2f}",
            "violations": []
        }
        
        # Extract violations from results
        # Import penalties info for violation descriptions
        from audit_agent.utils.penalties import DRC_MINING_PENALTIES
        
        seen_violations = set()
        violation_penalties = {}  # Track penalties by article for aggregation
        
        try:
            for result in report_data.get("results", []):
                for item in result.get("items", []):
                    # potential_violations is a list of article strings like ["299", "301"]
                    violations = item.get("potential_violations", [])
                    item_penalty = item.get("max_penalty_usd", 0)
                    
                    if violations and item_penalty > 0:
                        # Distribute the penalty across violations for this item
                        penalty_per_violation = item_penalty / len(violations) if len(violations) > 0 else item_penalty
                        
                        for article in violations:
                            if article not in violation_penalties:
                                violation_penalties[article] = 0
                            violation_penalties[article] += penalty_per_violation
            
            # Now create the violations list with descriptions
            for article, total_penalty in violation_penalties.items():
                if total_penalty > 0:
                    # Get description from penalties dictionary
                    description = "Violation"  # Default
                    if article in DRC_MINING_PENALTIES:
                        description = DRC_MINING_PENALTIES[article].violation_description
                    elif article == "7.1.A":
                        description = "Administrative/procedural noncompliance"
                    elif article == "9.2.B":
                        description = "Unauthorized processing/transformation"
                    elif article == "8.4.C":
                        description = "Theft, concealment of minerals"
                    
                    financial_exposure["violations"].append({
                        "code": article,
                        "description": description,
                        "maxExposure": f"${total_penalty:,.2f}"
                    })
                    
        except (TypeError, AttributeError) as e:
            logger.warning(f"Error extracting violations for report {report_id}: {e}")
            # Continue with empty violations list
        
        # Sort violations by amount (highest first)
        financial_exposure["violations"].sort(
            key=lambda x: float(x["maxExposure"].replace("$", "").replace(",", "")),
            reverse=True
        )
    
        # Return restructured report without redundant results
        return {
            "metadata": audit,
            "timestamp": report_data.get("timestamp", datetime.now().isoformat()),
            "frameworks": report_data.get("frameworks", []),
            "overall_compliance_score": report_data.get("overall_compliance_score", 0),
            "executive_summary": executive_summary,
            "criticalActions": critical_actions,
            "financialExposure": financial_exposure
        }
    except Exception as e:
        logger.error(f"Error processing report {report_id}: {e}")
        # Return a minimal valid response on error
        return {
            "metadata": audit,
            "timestamp": datetime.now().isoformat(),
            "frameworks": audit.get("framework_files", []),
            "overall_compliance_score": 0,
            "executive_summary": "## Error Processing Report\n\nAn error occurred while processing the report data. Please try again or contact support.",
            "criticalActions": [],
            "financialExposure": {
                "totalExposure": "$0.00",
                "violations": []
            },
            "error": str(e)
        }

@app.get("/reports/{report_id}/findings")
async def get_report_findings(report_id: str):
    """
    Get all findings for a specific report
    
    Returns findings with nested structure: results > categories > items
    """
    
    # Check if it's a mock report first
    mock_reports = generate_mock_reports()
    mock_report = next((r for r in mock_reports if r.get("report_id") == report_id), None)
    
    if mock_report:
        # Generate mock findings with nested structure
        return {
            "report_id": report_id,
            "results": [
                {
                    "category": "Environmental",
                    "framework": mock_report.get("framework_files", ["ISO_14001_2015.pdf"])[0],
                    "overall_score": 0.65,
                    "items": [
                        {
                            "finding_id": f"FIND-{report_id}-0001",
                            "question": "Is there an established environmental management system?",
                            "input_statement": "Partial implementation observed",
                            "framework_ref": "ISO 14001:4.4",
                            "match_score": 0.6,
                            "compliance_level": "Medium",
                            "status": "review-needed",
                            "gap": "Documentation incomplete",
                            "recommendation": "Complete EMS documentation",
                            "potential_violations": [],
                            "max_penalty_usd": 0
                        },
                        {
                            "finding_id": f"FIND-{report_id}-0002",
                            "question": "Are waste management procedures documented and followed?",
                            "input_statement": "No waste management system in place",
                            "framework_ref": "ISO 14001:8.1",
                            "match_score": 0.2,
                            "compliance_level": "Low",
                            "status": "non-compliant",
                            "gap": "Critical waste management gaps",
                            "recommendation": "Implement waste management system immediately",
                            "potential_violations": [
                                {"code": "7.1.A", "description": "Environmental violations", "max_penalty_usd": 25000}
                            ],
                            "max_penalty_usd": 25000
                        }
                    ]
                },
                {
                    "category": "Safety",
                    "framework": "ISO_45001_2018.pdf",
                    "overall_score": 0.45,
                    "items": [
                        {
                            "finding_id": f"FIND-{report_id}-0003",
                            "question": "Are safety protocols properly implemented?",
                            "input_statement": "Safety measures are in place and functional",
                            "framework_ref": "ISO 45001:6.1",
                            "match_score": 0.85,
                            "compliance_level": "High",
                            "status": "compliant",
                            "gap": "",
                            "recommendation": "Continue current safety practices",
                            "potential_violations": [],
                            "max_penalty_usd": 0
                        }
                    ]
                }
            ]
        }
    
    # For real audits, load the report data
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
    
    # Check if audit is still processing or failed
    if audit.get("status") in [JobStatus.PROCESSING.value, JobStatus.FAILED.value]:
        # Return empty findings for processing/failed audits
        return {
            "report_id": report_id,
            "status": audit.get("status"),
            "results": []
        }
    
    # Load the full report
    json_path = RESULTS_DIR / job_id / "report.json"
    
    if not json_path.exists():
        # This shouldn't happen for completed audits, but handle gracefully
        raise HTTPException(status_code=404, detail="Report data not found")
    
    with open(json_path, "r") as f:
        report_data = json.load(f)
    
    # Structure findings with nested categories and add compliance_level
    results = []
    finding_counter = 0
    
    for result in report_data.get("results", []):
        category_items = []
        for item in result.get("items", []):
            finding_counter += 1
            match_score = item.get("match_score", 0)
            
            # Determine compliance level and status
            if match_score >= 0.8:
                compliance_level = "High"
                status = "compliant"
            elif match_score >= 0.5:
                compliance_level = "Medium"
                status = "review-needed"
            else:
                compliance_level = "Low"
                status = "non-compliant"
            
            # Ensure questions are in English (basic check and translation for common cases)
            question = item.get("question", "")
            if any(french_word in question.lower() for french_word in ["est-ce", "avez-vous", "êtes-vous", "sont"]):
                # This is likely French, use the English version from framework_ref or provide generic
                question = f"Compliance check for {item.get('framework_ref', 'requirement')}"
            
            category_items.append({
                "finding_id": f"FIND-{report_id}-{finding_counter:04d}",
                "question": question,
                "input_statement": item.get("input_statement"),
                "framework_ref": item.get("framework_ref"),
                "match_score": match_score,
                "compliance_level": compliance_level,
                "status": status,
                "gap": item.get("gap", ""),
                "recommendation": item.get("recommendation", ""),
                "potential_violations": item.get("potential_violations", []),
                "max_penalty_usd": item.get("max_penalty_usd", 0)
            })
        
        results.append({
            "category": result.get("category"),
            "framework": result.get("framework"),
            "overall_score": result.get("overall_score", 0),
            "items": category_items
        })
    
    return {
        "report_id": report_id,
        "results": results
    }

@app.get("/reports/{report_id}/findings/{finding_id}")
async def get_specific_finding(report_id: str, finding_id: str):
    """
    Get a specific finding by ID
    
    Returns detailed information about a single compliance finding
    """
    
    # Get all findings for the report
    try:
        findings_response = await get_report_findings(report_id)
    except HTTPException:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Search for the specific finding in the nested structure
    finding = None
    for result in findings_response.get("results", []):
        for item in result.get("items", []):
            if item.get("finding_id") == finding_id:
                finding = item.copy()
                finding["category"] = result.get("category")
                finding["framework"] = result.get("framework")
                break
        if finding:
            break
    
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    # Add additional context for the specific finding
    finding["report_id"] = report_id
    
    # The compliance_level is already included from the findings endpoint
    # Add detailed analysis based on the finding data
    finding["detailed_analysis"] = {
        "compliance_level": finding.get("compliance_level", "Unknown"),
        "priority": "Critical" if finding["max_penalty_usd"] > 100000 else 
                   "High" if finding["max_penalty_usd"] > 50000 else 
                   "Medium" if finding["max_penalty_usd"] > 10000 else "Low",
        "requires_immediate_action": finding["match_score"] < 0.5 and finding["max_penalty_usd"] > 50000
    }
    
    return finding

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