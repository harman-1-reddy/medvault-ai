import os
import shutil
import uuid
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import Response, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from models import (
    PatientRecord, PatientIntake, MedicalReport, LabTest, 
    VerifyTestRequest, IntakeUpdateRequest, AuditEntry, RangeStatus, ProvenanceSource
)
from extractor import process_document, evaluate_status
from analyzer import (
    detect_inconsistencies, compute_longitudinal_trends, 
    generate_patient_summary, generate_physician_summary
)
from pdf_exporter import generate_patient_pdf
from sample_data import SAMPLE_DATABASE, get_sarah_jenkins_record

app = FastAPI(title="MedVault AI API", version="2.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active state in-memory database
CURRENT_RECORD: PatientRecord = get_sarah_jenkins_record()

# Handle Vercel / serverless writable directory (/tmp)
if os.environ.get("VERCEL"):
    UPLOAD_DIR = "/tmp/uploads"
else:
    UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/api/health")
def health():
    return {"status": "online", "system": "MedVault Clinical Intelligence Engine", "version": "2.4.0", "deployment": "Vercel Serverless Ready"}

@app.get("/api/sample-personas")
def list_sample_personas():
    return [
        {
            "id": "sarah-jenkins",
            "name": "Sarah Jenkins",
            "condition_focus": "Type 2 Diabetes, Hypertension & Renal Risk",
            "highlights": "Longitudinal glucose/HbA1c trends, Penicillin allergy omission, NSAID eGFR contraindication"
        },
        {
            "id": "robert-vance",
            "name": "Robert Vance",
            "condition_focus": "Cardiovascular & Lipid Panel Follow-up",
            "highlights": "Elevated LDL & hs-CRP, Positive medication response comparison, Statin tracking"
        },
        {
            "id": "elena-rostova",
            "name": "Elena Rostova",
            "condition_focus": "Endocrine & Iron Deficiency Workup",
            "highlights": "Subclinical hypothyroidism, Ferritin & Hemoglobin microcytosis, Strict reference-range provenance"
        }
    ]

@app.post("/api/load-sample/{persona_id}")
def load_sample_persona(persona_id: str):
    global CURRENT_RECORD
    from sample_data import get_sarah_jenkins_record, get_robert_vance_record, get_elena_rostova_record
    
    if persona_id == "sarah-jenkins":
        CURRENT_RECORD = get_sarah_jenkins_record()
    elif persona_id == "robert-vance":
        CURRENT_RECORD = get_robert_vance_record()
    elif persona_id == "elena-rostova":
        CURRENT_RECORD = get_elena_rostova_record()
    else:
        raise HTTPException(status_code=404, detail="Persona not found")
        
    return CURRENT_RECORD

@app.get("/api/current-patient")
def get_current_patient():
    return CURRENT_RECORD

@app.post("/api/intake")
def update_intake(req: IntakeUpdateRequest):
    global CURRENT_RECORD
    from models import Medication, Allergy
    
    meds = [Medication(name=m.get("name", ""), dosage=m.get("dosage", ""), frequency=m.get("frequency", "")) for m in req.medications if m.get("name")]
    allergies = [Allergy(substance=a.get("substance", ""), reaction=a.get("reaction", ""), severity=a.get("severity", "Moderate")) for a in req.allergies if a.get("substance")]

    CURRENT_RECORD.intake.age = req.age
    CURRENT_RECORD.intake.sex = req.sex
    CURRENT_RECORD.intake.symptoms = req.symptoms
    CURRENT_RECORD.intake.conditions = req.conditions
    CURRENT_RECORD.intake.medications = meds
    CURRENT_RECORD.intake.allergies = allergies

    CURRENT_RECORD.conflicts = detect_inconsistencies(
        CURRENT_RECORD.intake, 
        CURRENT_RECORD.current_labs, 
        CURRENT_RECORD.reports
    )
    CURRENT_RECORD.summary_patient, CURRENT_RECORD.questions_for_doctor = generate_patient_summary(
        CURRENT_RECORD.intake, CURRENT_RECORD.current_labs, CURRENT_RECORD.trends, CURRENT_RECORD.conflicts
    )
    CURRENT_RECORD.summary_physician = generate_physician_summary(
        CURRENT_RECORD.name, CURRENT_RECORD.intake, CURRENT_RECORD.current_labs, CURRENT_RECORD.trends, CURRENT_RECORD.conflicts
    )
    
    CURRENT_RECORD.audit_log.insert(0, AuditEntry(
        action="INTAKE_MODIFIED",
        actor="Clinician / Patient Intake Portal",
        details="Updated demographics, conditions, medications, or allergies"
    ))

    return CURRENT_RECORD

@app.post("/api/upload-report")
async def upload_medical_report(file: UploadFile = File(...)):
    global CURRENT_RECORD
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    report = process_document(file_path, filename=file.filename)
    
    if not report.tests:
        return JSONResponse(status_code=400, content={"error": "No laboratory test values could be parsed from the uploaded document."})

    if CURRENT_RECORD.current_labs:
        CURRENT_RECORD.previous_labs = CURRENT_RECORD.current_labs

    CURRENT_RECORD.current_labs = report.tests
    CURRENT_RECORD.reports.append(report)

    if CURRENT_RECORD.previous_labs:
        CURRENT_RECORD.trends = compute_longitudinal_trends(
            CURRENT_RECORD.previous_labs, 
            CURRENT_RECORD.current_labs,
            prev_date="Prior Session",
            curr_date=report.report_date
        )

    CURRENT_RECORD.conflicts = detect_inconsistencies(
        CURRENT_RECORD.intake, 
        CURRENT_RECORD.current_labs, 
        CURRENT_RECORD.reports
    )

    CURRENT_RECORD.summary_patient, CURRENT_RECORD.questions_for_doctor = generate_patient_summary(
        CURRENT_RECORD.intake, CURRENT_RECORD.current_labs, CURRENT_RECORD.trends, CURRENT_RECORD.conflicts
    )
    CURRENT_RECORD.summary_physician = generate_physician_summary(
        CURRENT_RECORD.name, CURRENT_RECORD.intake, CURRENT_RECORD.current_labs, CURRENT_RECORD.trends, CURRENT_RECORD.conflicts
    )

    CURRENT_RECORD.audit_log.insert(0, AuditEntry(
        action="DOCUMENT_UPLOADED",
        actor="User Upload Interface",
        details=f"Uploaded and parsed '{file.filename}': extracted {len(report.tests)} structured test findings"
    ))

    return CURRENT_RECORD

@app.post("/api/verify-test")
def verify_test(req: VerifyTestRequest):
    global CURRENT_RECORD
    found = False
    
    for t in CURRENT_RECORD.current_labs:
        if t.id == req.test_id:
            old_val = t.value
            if req.verified_value is not None:
                t.value = req.verified_value
                t.status = evaluate_status(t.value, t.reference_range)
            if req.verified_unit:
                t.unit = req.verified_unit
            if req.notes:
                t.notes = req.notes
            
            t.verified = True
            t.verified_by = req.verified_by
            t.confidence = 1.0
            found = True
            
            CURRENT_RECORD.audit_log.insert(0, AuditEntry(
                action="TEST_VERIFIED_HUMAN",
                actor=req.verified_by,
                details=f"Verified metric '{t.name}' (Value adjusted: {old_val} -> {t.value} {t.unit})"
            ))
            break

    if not found:
        raise HTTPException(status_code=404, detail="Test record not found")

    CURRENT_RECORD.summary_patient, CURRENT_RECORD.questions_for_doctor = generate_patient_summary(
        CURRENT_RECORD.intake, CURRENT_RECORD.current_labs, CURRENT_RECORD.trends, CURRENT_RECORD.conflicts
    )
    CURRENT_RECORD.summary_physician = generate_physician_summary(
        CURRENT_RECORD.name, CURRENT_RECORD.intake, CURRENT_RECORD.current_labs, CURRENT_RECORD.trends, CURRENT_RECORD.conflicts
    )

    return CURRENT_RECORD

@app.get("/api/export-pdf")
def export_pdf():
    pdf_bytes = generate_patient_pdf(CURRENT_RECORD)
    filename = f"MedVault_Report_{CURRENT_RECORD.name.replace(' ', '_')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# Static frontend files mount (for local runs)
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
