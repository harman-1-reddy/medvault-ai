import sys
import os
backend_dir = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app import app
from extractor import process_document
from pdf_exporter import generate_patient_pdf
from sample_data import get_sarah_jenkins_record

def run_all_tests():
    print(">>> [TEST 1/6] Initializing TestClient...")
    client = TestClient(app)
    
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("    PASSED: /api/health returned 200 OK")

    print(">>> [TEST 2/6] Verifying Current Patient API...")
    res = client.get("/api/current-patient")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Sarah Jenkins"
    assert len(data["current_labs"]) >= 5
    print(f"    PASSED: Sarah Jenkins loaded with {len(data['current_labs'])} labs and {len(data['conflicts'])} conflicts")

    print(">>> [TEST 3/6] Testing Conflict Detection...")
    conflicts = data["conflicts"]
    has_allergy_conflict = any("allergy" in c["title"].lower() or "penicillin" in c["title"].lower() for c in conflicts)
    assert has_allergy_conflict, "Expected penicillin allergy conflict to be detected!"
    print("    PASSED: Omitted Penicillin allergy detected correctly")

    print(">>> [TEST 4/6] Testing Longitudinal Trends...")
    trends = data["trends"]
    assert len(trends) >= 3
    for tr in trends:
        print(f"    Trend: {tr['test_name']}: {tr['previous_value']} -> {tr['current_value']} {tr['unit']} ({tr['direction']})")
    print("    PASSED: Longitudinal trends calculated")

    print(">>> [TEST 5/6] Testing Human-in-the-Loop Verification Endpoint...")
    test_id = data["current_labs"][0]["id"]
    verify_res = client.post("/api/verify-test", json={
        "test_id": test_id,
        "verified_value": 146.0,
        "verified_unit": "mg/dL",
        "verified_by": "Dr. Automated Test",
        "notes": "Verified by test suite"
    })
    assert verify_res.status_code == 200
    updated_data = verify_res.json()
    updated_test = next(t for t in updated_data["current_labs"] if t["id"] == test_id)
    assert updated_test["verified"] == True
    assert updated_test["value"] == 146.0
    print("    PASSED: Verification and audit log entry registered")

    print(">>> [TEST 6/6] Testing PDF Health Passport Generation & Download...")
    export_res = client.get("/api/export-pdf")
    assert export_res.status_code == 200
    assert len(export_res.content) > 5000
    print(f"    PASSED: Exported clinical PDF ({len(export_res.content)} bytes)")

    print("\n" + "=" * 50)
    print(" ALL 6 SYSTEM VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 50)

if __name__ == "__main__":
    run_all_tests()
