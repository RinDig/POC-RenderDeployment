"""
Simple API test - no dependencies required
"""

import urllib.request
import json

API_URL = "https://vigilore-api.onrender.com"

print("=== Testing VigilOre API ===\n")

# Test 1: Health Check
print("1. Testing API Health Check...")
try:
    response = urllib.request.urlopen(f"{API_URL}/")
    data = json.loads(response.read().decode())
    print(f"[SUCCESS] API is live!")
    print(f"   Status: {data['status']}")
    print(f"   Version: {data['version']}")
except Exception as e:
    print(f"[FAILED] Health check failed: {e}")

# Test 2: Check endpoints
print("\n2. Testing API Endpoints...")
endpoints = [
    "/docs",  # FastAPI documentation
    "/dashboard/summary",  # Dashboard data
    "/reports?page=1&limit=5"  # Reports list
]

for endpoint in endpoints:
    try:
        response = urllib.request.urlopen(f"{API_URL}{endpoint}")
        print(f"[SUCCESS] {endpoint} - Status: {response.status}")
    except Exception as e:
        print(f"[FAILED] {endpoint} - Error: {e}")

print("\n=== For Your Frontend Developer ===")
print(f"\nAPI Base URL: {API_URL}")
print("\nKey endpoints:")
print("- POST /audits - Submit new audit")
print("- GET /audits/status/{job_id} - Check progress")
print("- GET /reports/{report_id} - Get JSON report")
print("- GET /reports/{report_id}/excel - Download Excel")
print("- GET /dashboard/summary - Dashboard data")
print("- GET /reports - List all reports")
print("\nNo authentication required - just use the endpoints directly!")
print("\nAPI Documentation: https://vigilore-api.onrender.com/docs")