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
            "site_name": "Brazzaville Mining Complex",
            "site_code": "BZV-001",
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
            "site_name": "Sangha River Mine",
            "site_code": "SRM-004",
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
            "site_name": "Alima Gold Mine",
            "site_code": "AGM-025",
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
            "site_name": "Kabo Forest Mine",
            "site_code": "KFM-012",
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
            "site_name": "Pool Region Quarry",
            "site_code": "PRQ-061",
            "operator": "Quarry Operations CG",
            "auditor_name": "Jean-Pierre Mbala",
            "auditor_email": "jp.mbala@audit.cg",
            "date_of_audit": "2024-12-05",
            "status": "complete",
            "compliance_score": 51.8,
            "compliance_status": "non-compliant",
            "findings_summary": {"compliant": 11, "non_compliant": 16, "review_needed": 9},
            "framework_files": ["ISO_14001_2015.pdf"]
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
    
    # Mock data for POC demonstration - this serves as baseline data
    # Real user-submitted audits will be added to this data
    mock_sites = [
        {"name": "Brazzaville Mining Complex", "code": "BZV-001", "lat": -4.2634, "lng": 15.2429, "status": "non-compliant"},
        {"name": "Sangha River Mine", "code": "SRM-004", "lat": -0.8317, "lng": 17.6856, "status": "compliant"},
        {"name": "Kabo Forest Mine", "code": "KFM-012", "lat": -2.154, "lng": 16.1624, "status": "review-needed"},
        {"name": "Ouesso Mining Site", "code": "OMS-007", "lat": -1.8312, "lng": 14.7218, "status": "compliant"},
        {"name": "Likouala Copper Mine", "code": "LCM-003", "lat": -3.7056, "lng": 17.8914, "status": "not-applicable"},
        {"name": "Niari Valley Mine", "code": "NVM-008", "lat": -2.9456, "lng": 13.1738, "status": "non-compliant"},
        {"name": "Cuvette Basin Mine", "code": "CBM-015", "lat": -1.2046, "lng": 16.8974, "status": "review-needed"},
        {"name": "Pointe-Noire Coastal Mine", "code": "PNC-002", "lat": -4.7727, "lng": 11.8638, "status": "compliant"},
        {"name": "Impfondo Diamond Mine", "code": "IDM-019", "lat": -0.6134, "lng": 16.2456, "status": "review-needed"},
        {"name": "Alima Gold Mine", "code": "AGM-025", "lat": -3.1542, "lng": 15.8745, "status": "non-compliant"},
        {"name": "Dolisie Iron Ore", "code": "DIO-031", "lat": -2.4892, "lng": 12.9834, "status": "compliant"},
        {"name": "Bomassa Timber Mine", "code": "BTM-047", "lat": -1.5628, "lng": 18.1456, "status": "not-applicable"},
        {"name": "Mayombe Bauxite", "code": "MBX-013", "lat": -4.1234, "lng": 13.5678, "status": "review-needed"},
        {"name": "Plateaux Copper Mine", "code": "PCM-055", "lat": -0.9876, "lng": 15.4321, "status": "compliant"},
        {"name": "Pool Region Quarry", "code": "PRQ-061", "lat": -3.8765, "lng": 14.2109, "status": "non-compliant"},
        {"name": "Mambili Forest Concession", "code": "MFC-078", "lat": -1.3456, "lng": 17.289, "status": "compliant"},
        {"name": "Odzala Phosphate Mine", "code": "OPM-084", "lat": -2.789, "lng": 16.5432, "status": "review-needed"},
        {"name": "Kouilou Salt Works", "code": "KSW-092", "lat": -4.5432, "lng": 12.3456, "status": "not-applicable"},
        {"name": "Equateur Limestone", "code": "ELS-103", "lat": -1.7654, "lng": 14.9876, "status": "compliant"},
        {"name": "Sangha Zinc Mine", "code": "SZM-118", "lat": -3.4567, "lng": 17.1234, "status": "non-compliant"},
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
                    "lat": -2.5 + random.uniform(-2, 2),  # Random lat for demo
                    "lng": 15.5 + random.uniform(-3, 3),  # Random lng for demo
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
            site_name="Brazzaville Mining Complex",
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
    
    # Filter only completed audits
    filtered_audits = [a for a in all_audits if a.get("status") in [JobStatus.COMPLETED.value, "complete"]]
    
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
        reports.append(ReportItem(
            report_id=audit.get("report_id", "Unknown"),
            audit_site=audit.get("site_name", "Unknown Site"),
            site_code=audit.get("site_code"),
            date_of_audit=audit.get("date_of_audit", datetime.now().date().isoformat()),
            compliance_score=round(audit.get("compliance_score", 0), 1),
            status=audit.get("status", "unknown"),
            findings_summary=FindingsSummary(
                compliant=audit.get("findings_summary", {}).get("compliant", 0),
                non_compliant=audit.get("findings_summary", {}).get("non_compliant", 0),
                review_needed=audit.get("findings_summary", {}).get("review_needed", 0)
            ),
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
        # Generate mock detailed report
        return {
            "metadata": mock_report,
            "timestamp": datetime.now().isoformat(),
            "frameworks": mock_report.get("framework_files", []),
            "overall_compliance_score": mock_report.get("compliance_score", 0) / 100,
            "results": [
                {
                    "category": "Environmental",
                    "framework": mock_report.get("framework_files", ["ISO_14001_2015.pdf"])[0],
                    "overall_score": 0.65,
                    "items": [
                        {
                            "question": "Environmental management system established?",
                            "input_statement": "Partial implementation observed",
                            "framework_ref": "ISO 14001:4.4",
                            "match_score": 0.6,
                            "gap": "Documentation incomplete",
                            "recommendation": "Complete EMS documentation",
                            "potential_violations": [],
                            "max_penalty_usd": 0
                        }
                    ],
                    "total_max_penalty_usd": 0
                }
            ],
            "executive_summary": f"Compliance audit for {mock_report.get('site_name')} shows {mock_report.get('compliance_status')} status.",
            "critical_recommendations": ["Address safety protocol gaps", "Update environmental assessments"],
            "total_max_penalty_usd": 50000,
            "penalty_summary": {"DRC_Mining_Code": 50000}
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
    
    # Load the full report
    json_path = RESULTS_DIR / job_id / "report.json"
    
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Report data not found")
    
    with open(json_path, "r") as f:
        report_data = json.load(f)
    
    # Add metadata to the report
    report_data["metadata"] = audit
    
    return report_data

@app.get("/reports/{report_id}/findings")
async def get_report_findings(report_id: str):
    """
    Get all findings for a specific report
    
    Returns a list of all compliance findings from the report
    """
    
    # First get the full report
    try:
        report = await get_report_details(report_id)
    except HTTPException:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Extract all findings (ComplianceItems) from the report
    findings = []
    finding_id = 0
    
    for result in report.get("results", []):
        for item in result.get("items", []):
            finding_id += 1
            findings.append({
                "finding_id": f"FIND-{report_id}-{finding_id:04d}",
                "category": result.get("category"),
                "framework": result.get("framework"),
                "question": item.get("question"),
                "input_statement": item.get("input_statement"),
                "framework_ref": item.get("framework_ref"),
                "match_score": item.get("match_score"),
                "status": "compliant" if item.get("match_score", 0) >= 0.8 else 
                         "review-needed" if item.get("match_score", 0) >= 0.5 else "non-compliant",
                "gap": item.get("gap"),
                "recommendation": item.get("recommendation"),
                "potential_violations": item.get("potential_violations", []),
                "max_penalty_usd": item.get("max_penalty_usd", 0)
            })
    
    return {
        "report_id": report_id,
        "total_findings": len(findings),
        "findings": findings
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
    
    # Find the specific finding
    finding = next(
        (f for f in findings_response["findings"] if f["finding_id"] == finding_id),
        None
    )
    
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    # Add additional context for the specific finding
    finding["report_id"] = report_id
    finding["detailed_analysis"] = {
        "compliance_level": "High" if finding["match_score"] >= 0.8 else 
                            "Medium" if finding["match_score"] >= 0.5 else "Low",
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