from typing import Dict
from models import (
    PatientRecord, PatientIntake, MedicalReport, LabTest, ReferenceRange, 
    RangeStatus, ProvenanceSource, Medication, Allergy, AuditEntry
)
from analyzer import detect_inconsistencies, compute_longitudinal_trends, generate_patient_summary, generate_physician_summary

def get_sarah_jenkins_record() -> PatientRecord:
    intake = PatientIntake(
        age=52,
        sex="Female",
        symptoms=["Persistent fatigue", "Frequent urination", "Occasional morning dizziness"],
        conditions=["Hypertension"],
        medications=[
            Medication(name="Lisinopril", dosage="10mg once daily", frequency="Morning", source=ProvenanceSource.USER_INTAKE),
            Medication(name="Metformin", dosage="500mg twice daily", frequency="With meals", source=ProvenanceSource.USER_INTAKE),
            Medication(name="Ibuprofen", dosage="400mg as needed", frequency="PRN joint pain", source=ProvenanceSource.USER_INTAKE)
        ],
        allergies=[],
        notes="Patient provided intake on hospital registration tablet.",
        provenance=ProvenanceSource.USER_INTAKE
    )

    prior_labs = [
        LabTest(
            id="t-prev-1",
            name="Fasting Blood Glucose",
            category="Metabolic & Glucose",
            value=128.0,
            unit="mg/dL",
            reference_range=ReferenceRange(low=70.0, high=99.0, text="70.0 - 99.0", is_present_in_source=True),
            status=RangeStatus.HIGH,
            confidence=0.98,
            source_snippet="Fasting Blood Glucose: 128.0 mg/dL (Ref: 70.0 - 99.0)",
            source_file="Lab_Report_May2026.pdf",
            page_number=1,
            verified=True,
            verified_by="Dr. M. Patel"
        ),
        LabTest(
            id="t-prev-2",
            name="Hemoglobin A1c (HbA1c)",
            category="Metabolic & Glucose",
            value=6.5,
            unit="%",
            reference_range=ReferenceRange(low=4.0, high=5.6, text="4.0 - 5.6", is_present_in_source=True),
            status=RangeStatus.HIGH,
            confidence=0.98,
            source_snippet="Hemoglobin A1c: 6.5 % (Ref: 4.0 - 5.6)",
            source_file="Lab_Report_May2026.pdf",
            page_number=1,
            verified=True,
            verified_by="Dr. M. Patel"
        ),
        LabTest(
            id="t-prev-3",
            name="Serum Creatinine",
            category="Renal & Kidney Function",
            value=1.1,
            unit="mg/dL",
            reference_range=ReferenceRange(low=0.6, high=1.2, text="0.6 - 1.2", is_present_in_source=True),
            status=RangeStatus.NORMAL,
            confidence=0.95,
            source_snippet="Serum Creatinine: 1.1 mg/dL (Ref: 0.6 - 1.2)",
            source_file="Lab_Report_May2026.pdf",
            page_number=1,
            verified=True
        ),
        LabTest(
            id="t-prev-4",
            name="eGFR (Estimated GFR)",
            category="Renal & Kidney Function",
            value=68.0,
            unit="mL/min",
            reference_range=ReferenceRange(low=60.0, high=99999.0, text="> 60.0", is_present_in_source=True),
            status=RangeStatus.NORMAL,
            confidence=0.95,
            source_snippet="eGFR: 68.0 mL/min (Ref: > 60.0)",
            source_file="Lab_Report_May2026.pdf",
            page_number=1,
            verified=True
        ),
        LabTest(
            id="t-prev-5",
            name="Total Cholesterol",
            category="Lipid Profile",
            value=195.0,
            unit="mg/dL",
            reference_range=ReferenceRange(low=125.0, high=200.0, text="125.0 - 200.0", is_present_in_source=True),
            status=RangeStatus.NORMAL,
            confidence=0.95,
            source_snippet="Total Cholesterol: 195.0 mg/dL (Ref: 125.0 - 200.0)",
            source_file="Lab_Report_May2026.pdf",
            page_number=1,
            verified=True
        )
    ]

    current_labs = [
        LabTest(
            id="t-curr-1",
            name="Fasting Blood Glucose",
            category="Metabolic & Glucose",
            value=145.0,
            unit="mg/dL",
            reference_range=ReferenceRange(low=70.0, high=99.0, text="70.0 - 99.0", is_present_in_source=True),
            status=RangeStatus.HIGH,
            confidence=0.97,
            source_snippet="Fasting Blood Glucose       145.0     mg/dL     70.0 - 99.0  [H]",
            source_file="Comprehensive_Metabolic_Panel_Aug2026.pdf",
            page_number=1,
            verified=False
        ),
        LabTest(
            id="t-curr-2",
            name="Hemoglobin A1c (HbA1c)",
            category="Metabolic & Glucose",
            value=7.2,
            unit="%",
            reference_range=ReferenceRange(low=4.0, high=5.6, text="4.0 - 5.6", is_present_in_source=True),
            status=RangeStatus.HIGH,
            confidence=0.96,
            source_snippet="Hemoglobin A1c (HbA1c)       7.2      %         4.0 - 5.6    [H]",
            source_file="Comprehensive_Metabolic_Panel_Aug2026.pdf",
            page_number=1,
            verified=False
        ),
        LabTest(
            id="t-curr-3",
            name="Serum Creatinine",
            category="Renal & Kidney Function",
            value=1.4,
            unit="mg/dL",
            reference_range=ReferenceRange(low=0.6, high=1.2, text="0.6 - 1.2", is_present_in_source=True),
            status=RangeStatus.HIGH,
            confidence=0.95,
            source_snippet="Serum Creatinine            1.4       mg/dL     0.6 - 1.2    [H]",
            source_file="Comprehensive_Metabolic_Panel_Aug2026.pdf",
            page_number=1,
            verified=False
        ),
        LabTest(
            id="t-curr-4",
            name="eGFR (Estimated GFR)",
            category="Renal & Kidney Function",
            value=54.0,
            unit="mL/min",
            reference_range=ReferenceRange(low=60.0, high=99999.0, text="> 60.0", is_present_in_source=True),
            status=RangeStatus.LOW,
            confidence=0.95,
            source_snippet="eGFR (Estimated GFR)        54.0      mL/min    > 60.0       [L]",
            source_file="Comprehensive_Metabolic_Panel_Aug2026.pdf",
            page_number=1,
            verified=False
        ),
        LabTest(
            id="t-curr-5",
            name="Potassium",
            category="Metabolic & Glucose",
            value=4.8,
            unit="mEq/L",
            reference_range=ReferenceRange(low=3.5, high=5.0, text="3.5 - 5.0", is_present_in_source=True),
            status=RangeStatus.NORMAL,
            confidence=0.95,
            source_snippet="Potassium                   4.8       mEq/L     3.5 - 5.0",
            source_file="Comprehensive_Metabolic_Panel_Aug2026.pdf",
            page_number=1,
            verified=True,
            verified_by="Auto-validated"
        ),
        LabTest(
            id="t-curr-6",
            name="Total Cholesterol",
            category="Lipid Profile",
            value=182.0,
            unit="mg/dL",
            reference_range=ReferenceRange(low=125.0, high=200.0, text="125.0 - 200.0", is_present_in_source=True),
            status=RangeStatus.NORMAL,
            confidence=0.94,
            source_snippet="Total Cholesterol           182.0     mg/dL     125.0 - 200.0",
            source_file="Comprehensive_Metabolic_Panel_Aug2026.pdf",
            page_number=2,
            verified=False
        ),
        LabTest(
            id="t-curr-7",
            name="Microalbumin / Creatinine Ratio",
            category="Renal & Kidney Function",
            value=42.0,
            unit="mg/g",
            reference_range=ReferenceRange(low=0.0, high=30.0, text="< 30.0", is_present_in_source=True),
            status=RangeStatus.HIGH,
            confidence=0.91,
            source_snippet="Microalbumin / Creatinine   42.0      mg/g      < 30.0       [H]",
            source_file="Comprehensive_Metabolic_Panel_Aug2026.pdf",
            page_number=2,
            verified=False
        )
    ]

    report_aug = MedicalReport(
        id="rep-sarah-aug2026",
        filename="Comprehensive_Metabolic_Panel_Aug2026.pdf",
        report_date="2026-08-20",
        lab_name="Metro Clinical Diagnostics Laboratory",
        category="Metabolic & Renal Comprehensive Panel",
        raw_text="""METRO CLINICAL DIAGNOSTICS LABORATORY
Accreditation #8921-A | CLIA ID: 36D098231
PATIENT: Sarah Jenkins | DOB: 1974-04-12 | MRN: 489102-SJ
ORDERING PHYSICIAN: Dr. Jennifer Lin, MD
COLLECTION DATE: 2026-08-20 07:45 AM | REPORT DATE: 2026-08-20 02:30 PM

PANEL: COMPREHENSIVE METABOLIC & RENAL PROFILE
TEST NAME                  RESULT    UNITS      REFERENCE INTERVAL   FLAG
-------------------------------------------------------------------------
Fasting Blood Glucose       145.0     mg/dL      70.0 - 99.0          HIGH
Hemoglobin A1c (HbA1c)       7.2      %          4.0 - 5.6            HIGH
Serum Creatinine            1.4       mg/dL      0.6 - 1.2            HIGH
eGFR (Estimated GFR)        54.0      mL/min     > 60.0               LOW
Potassium                   4.8       mEq/L      3.5 - 5.0            NORMAL
Total Cholesterol           182.0     mg/dL      125.0 - 200.0        NORMAL
Microalbumin / Creatinine   42.0      mg/g       < 30.0               HIGH

CLINICAL NOTES & ALERTS:
- Patient chart notes prior adverse reaction: developed acute erythematous urticaria (rash) following oral Penicillin antibiotic course in 2023.
- Note decreased eGFR compared to May 2026 baseline. Advise monitoring renal clearance.""",
        tests=current_labs
    )

    reports = [report_aug]
    conflicts = detect_inconsistencies(intake, current_labs, reports)
    trends = compute_longitudinal_trends(prior_labs, current_labs, prev_date="2026-05-10", curr_date="2026-08-20")
    patient_summary, questions = generate_patient_summary(intake, current_labs, trends, conflicts)
    physician_summary = generate_physician_summary("Sarah Jenkins", intake, current_labs, trends, conflicts)

    return PatientRecord(
        patient_id="p-sarah-jenkins",
        name="Sarah Jenkins",
        intake=intake,
        reports=reports,
        current_labs=current_labs,
        previous_labs=prior_labs,
        trends=trends,
        conflicts=conflicts,
        summary_patient=patient_summary,
        summary_physician=physician_summary,
        questions_for_doctor=questions,
        audit_log=[
            AuditEntry(action="INTAKE_INGESTED", actor="Patient Self-Service Tablet", details="Completed demographics, medications, and symptom intake"),
            AuditEntry(action="REPORT_EXTRACTED", actor="MedVault Parser Engine", details="Extracted 7 lab tests and 2 clinical alerts from Comprehensive_Metabolic_Panel_Aug2026.pdf"),
            AuditEntry(action="CONFLICTS_IDENTIFIED", actor="MedVault Rule Engine", details="Flagged undisclosed Penicillin allergy and NSAID/eGFR renal warning")
        ]
    )

def get_robert_vance_record() -> PatientRecord:
    intake = PatientIntake(
        age=61,
        sex="Male",
        symptoms=["Mild shortness of breath with stair climbing", "Heaviness in legs"],
        conditions=["Hyperlipidemia"],
        medications=[
            Medication(name="Atorvastatin", dosage="20mg bedtime", frequency="Once daily", source=ProvenanceSource.USER_INTAKE),
            Medication(name="Aspirin", dosage="81mg daily", frequency="Morning", source=ProvenanceSource.USER_INTAKE)
        ],
        allergies=[
            Allergy(substance="Sulfa drugs", reaction="Hives and facial swelling", severity="Severe", source=ProvenanceSource.USER_INTAKE)
        ],
        notes="Cardiology preventive follow-up visit.",
        provenance=ProvenanceSource.USER_INTAKE
    )

    prior_labs = [
        LabTest(
            id="t-rob-p1",
            name="Total Cholesterol",
            category="Lipid Profile",
            value=268.0,
            unit="mg/dL",
            reference_range=ReferenceRange(low=125.0, high=200.0, text="125.0 - 200.0", is_present_in_source=True),
            status=RangeStatus.HIGH,
            confidence=0.97,
            source_snippet="Total Cholesterol: 268.0 mg/dL",
            source_file="Lipids_Nov2025.pdf"
        ),
        LabTest(
            id="t-rob-p2",
            name="LDL Cholesterol",
            category="Lipid Profile",
            value=182.0,
            unit="mg/dL",
            reference_range=ReferenceRange(low=0.0, high=100.0, text="< 100.0", is_present_in_source=True),
            status=RangeStatus.HIGH,
            confidence=0.96,
            source_snippet="LDL Cholesterol: 182.0 mg/dL",
            source_file="Lipids_Nov2025.pdf"
        ),
        LabTest(
            id="t-rob-p3",
            name="Triglycerides",
            category="Lipid Profile",
            value=240.0,
            unit="mg/dL",
            reference_range=ReferenceRange(low=0.0, high=150.0, text="< 150.0", is_present_in_source=True),
            status=RangeStatus.HIGH,
            confidence=0.95,
            source_snippet="Triglycerides: 240.0 mg/dL",
            source_file="Lipids_Nov2025.pdf"
        )
    ]

    current_labs = [
        LabTest(
            id="t-rob-c1",
            name="Total Cholesterol",
            category="Lipid Profile",
            value=212.0,
            unit="mg/dL",
            reference_range=ReferenceRange(low=125.0, high=200.0, text="125.0 - 200.0", is_present_in_source=True),
            status=RangeStatus.HIGH,
            confidence=0.98,
            source_snippet="Total Cholesterol           212.0     mg/dL     125.0 - 200.0   [H]",
            source_file="Lipid_Panel_Aug2026.pdf"
        ),
        LabTest(
            id="t-rob-c2",
            name="LDL Cholesterol",
            category="Lipid Profile",
            value=135.0,
            unit="mg/dL",
            reference_range=ReferenceRange(low=0.0, high=100.0, text="< 100.0", is_present_in_source=True),
            status=RangeStatus.HIGH,
            confidence=0.97,
            source_snippet="LDL Cholesterol           135.0     mg/dL     < 100.0         [H]",
            source_file="Lipid_Panel_Aug2026.pdf"
        ),
        LabTest(
            id="t-rob-c3",
            name="HDL Cholesterol",
            category="Lipid Profile",
            value=46.0,
            unit="mg/dL",
            reference_range=ReferenceRange(low=40.0, high=99999.0, text="> 40.0", is_present_in_source=True),
            status=RangeStatus.NORMAL,
            confidence=0.96,
            source_snippet="HDL Cholesterol            46.0     mg/dL     > 40.0",
            source_file="Lipid_Panel_Aug2026.pdf"
        ),
        LabTest(
            id="t-rob-c4",
            name="Triglycerides",
            category="Lipid Profile",
            value=175.0,
            unit="mg/dL",
            reference_range=ReferenceRange(low=0.0, high=150.0, text="< 150.0", is_present_in_source=True),
            status=RangeStatus.HIGH,
            confidence=0.95,
            source_snippet="Triglycerides             175.0     mg/dL     < 150.0         [H]",
            source_file="Lipid_Panel_Aug2026.pdf"
        ),
        LabTest(
            id="t-rob-c5",
            name="High-Sensitivity CRP (hs-CRP)",
            category="Diagnostic Chemistry",
            value=3.4,
            unit="mg/L",
            reference_range=ReferenceRange(low=0.0, high=1.0, text="< 1.0", is_present_in_source=True),
            status=RangeStatus.HIGH,
            confidence=0.92,
            source_snippet="High-Sensitivity CRP (hs-CRP) 3.4    mg/L     < 1.0           [H]",
            source_file="Lipid_Panel_Aug2026.pdf"
        )
    ]

    report = MedicalReport(
        id="rep-rob-aug2026",
        filename="Lipid_Panel_Aug2026.pdf",
        report_date="2026-08-18",
        lab_name="Quest Cardiovascular Diagnostics",
        category="Comprehensive Lipid & Inflammatory Marker Panel",
        raw_text="""QUEST CARDIOVASCULAR DIAGNOSTICS
PATIENT: Robert Vance | DOB: 1965-02-14 | MRN: 902144-RV
TEST NAME                  RESULT    UNITS      REFERENCE INTERVAL   FLAG
-------------------------------------------------------------------------
Total Cholesterol           212.0     mg/dL     125.0 - 200.0        HIGH
LDL Cholesterol             135.0     mg/dL     < 100.0              HIGH
HDL Cholesterol              46.0     mg/dL     > 40.0               NORMAL
Triglycerides               175.0     mg/dL     < 150.0              HIGH
High-Sensitivity CRP (hs-CRP) 3.4     mg/L      < 1.0                HIGH
""",
        tests=current_labs
    )

    reports = [report]
    conflicts = detect_inconsistencies(intake, current_labs, reports)
    trends = compute_longitudinal_trends(prior_labs, current_labs, prev_date="2025-11-10", curr_date="2026-08-18")
    patient_summary, questions = generate_patient_summary(intake, current_labs, trends, conflicts)
    physician_summary = generate_physician_summary("Robert Vance", intake, current_labs, trends, conflicts)

    return PatientRecord(
        patient_id="p-robert-vance",
        name="Robert Vance",
        intake=intake,
        reports=reports,
        current_labs=current_labs,
        previous_labs=prior_labs,
        trends=trends,
        conflicts=conflicts,
        summary_patient=patient_summary,
        summary_physician=physician_summary,
        questions_for_doctor=questions,
        audit_log=[
            AuditEntry(action="INTAKE_INGESTED", actor="Self-Service Portal", details="Intake captured with Sulfa allergy and Atorvastatin regimen"),
            AuditEntry(action="TRENDS_COMPUTED", actor="MedVault Longitudinal Engine", details="Significant downward trend observed in LDL (-25.8%) and Total Cholesterol (-20.9%)")
        ]
    )

def get_elena_rostova_record() -> PatientRecord:
    intake = PatientIntake(
        age=34,
        sex="Female",
        symptoms=["Severe chronic exhaustion", "Cold intolerance", "Hair thinning", "Brain fog"],
        conditions=[],
        medications=[
            Medication(name="Daily Multivitamin", dosage="1 tablet", frequency="Morning", source=ProvenanceSource.USER_INTAKE)
        ],
        allergies=[],
        notes="Referred for unexplained fatigue workup.",
        provenance=ProvenanceSource.USER_INTAKE
    )

    current_labs = [
        LabTest(
            id="t-el-1",
            name="TSH (Thyroid Stimulating Hormone)",
            category="Thyroid & Endocrine",
            value=6.4,
            unit="uIU/mL",
            reference_range=ReferenceRange(low=0.4, high=4.0, text="0.4 - 4.0", is_present_in_source=True),
            status=RangeStatus.HIGH,
            confidence=0.97,
            source_snippet="TSH (Thyroid Stimulating)   6.4       uIU/mL    0.4 - 4.0    [H]",
            source_file="Thyroid_Iron_Panel_Sep2026.pdf"
        ),
        LabTest(
            id="t-el-2",
            name="Free T4",
            category="Thyroid & Endocrine",
            value=0.75,
            unit="ng/dL",
            reference_range=ReferenceRange(low=0.8, high=1.8, text="0.8 - 1.8", is_present_in_source=True),
            status=RangeStatus.LOW,
            confidence=0.96,
            source_snippet="Free T4                     0.75      ng/dL     0.8 - 1.8    [L]",
            source_file="Thyroid_Iron_Panel_Sep2026.pdf"
        ),
        LabTest(
            id="t-el-3",
            name="Ferritin",
            category="Iron & Anemia Workup",
            value=11.5,
            unit="ng/mL",
            reference_range=ReferenceRange(low=15.0, high=150.0, text="15.0 - 150.0", is_present_in_source=True),
            status=RangeStatus.LOW,
            confidence=0.95,
            source_snippet="Ferritin                    11.5      ng/mL     15.0 - 150.0 [L]",
            source_file="Thyroid_Iron_Panel_Sep2026.pdf"
        ),
        LabTest(
            id="t-el-4",
            name="Hemoglobin",
            category="Complete Blood Count (CBC)",
            value=10.9,
            unit="g/dL",
            reference_range=ReferenceRange(low=12.0, high=16.0, text="12.0 - 16.0", is_present_in_source=True),
            status=RangeStatus.LOW,
            confidence=0.96,
            source_snippet="Hemoglobin                  10.9      g/dL      12.0 - 16.0  [L]",
            source_file="Thyroid_Iron_Panel_Sep2026.pdf"
        )
    ]

    report = MedicalReport(
        id="rep-el-sep2026",
        filename="Thyroid_Iron_Panel_Sep2026.pdf",
        report_date="2026-09-01",
        lab_name="Apex Endocrine & Hematology Labs",
        category="Endocrine & Iron Deficiency Evaluation",
        raw_text="""APEX ENDOCRINE & HEMATOLOGY LABS
PATIENT: Elena Rostova | DOB: 1992-07-22 | MRN: 110294-ER
TEST NAME                  RESULT    UNITS      REFERENCE INTERVAL   FLAG
-------------------------------------------------------------------------
TSH (Thyroid Stimulating)   6.4       uIU/mL    0.4 - 4.0            HIGH
Free T4                     0.75      ng/dL     0.8 - 1.8            LOW
Ferritin                    11.5      ng/mL     15.0 - 150.0         LOW
Hemoglobin                  10.9      g/dL      12.0 - 16.0          LOW
""",
        tests=current_labs
    )

    reports = [report]
    conflicts = detect_inconsistencies(intake, current_labs, reports)
    patient_summary, questions = generate_patient_summary(intake, current_labs, [], conflicts)
    physician_summary = generate_physician_summary("Elena Rostova", intake, current_labs, [], conflicts)

    return PatientRecord(
        patient_id="p-elena-rostova",
        name="Elena Rostova",
        intake=intake,
        reports=reports,
        current_labs=current_labs,
        previous_labs=[],
        trends=[],
        conflicts=conflicts,
        summary_patient=patient_summary,
        summary_physician=physician_summary,
        questions_for_doctor=questions,
        audit_log=[
            AuditEntry(action="INTAKE_INGESTED", actor="Patient Intake Tablet", details="Recorded symptoms of extreme fatigue and hair thinning"),
            AuditEntry(action="REPORT_EXTRACTED", actor="MedVault Parser", details="Identified subclinical hypothyroidism indicators and iron deficiency markers")
        ]
    )

SAMPLE_DATABASE: Dict[str, PatientRecord] = {
    "sarah-jenkins": get_sarah_jenkins_record(),
    "robert-vance": get_robert_vance_record(),
    "elena-rostova": get_elena_rostova_record()
}
