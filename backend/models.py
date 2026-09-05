from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime

class RangeStatus(str, Enum):
    NORMAL = "NORMAL"
    LOW = "LOW"
    HIGH = "HIGH"
    RANGE_NOT_PROVIDED = "RANGE_NOT_PROVIDED"

class ProvenanceSource(str, Enum):
    USER_INTAKE = "USER_INTAKE"
    EXTRACTED_DOCUMENT = "EXTRACTED_DOCUMENT"
    AI_INFERRED = "AI_INFERRED"

class AlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class ReferenceRange(BaseModel):
    low: Optional[float] = None
    high: Optional[float] = None
    text: Optional[str] = None
    is_present_in_source: bool = False

class LabTest(BaseModel):
    id: str
    name: str
    category: str = "General"
    value: float
    value_text: Optional[str] = None
    unit: str
    reference_range: ReferenceRange
    status: RangeStatus = RangeStatus.NORMAL
    confidence: float = 0.95
    source_snippet: str
    source_file: str = "Intake/Upload"
    page_number: int = 1
    provenance: ProvenanceSource = ProvenanceSource.EXTRACTED_DOCUMENT
    verified: bool = False
    verified_by: Optional[str] = None
    verified_at: Optional[str] = None
    notes: Optional[str] = None

class Medication(BaseModel):
    name: str
    dosage: str
    frequency: Optional[str] = None
    source: ProvenanceSource = ProvenanceSource.USER_INTAKE

class Allergy(BaseModel):
    substance: str
    reaction: Optional[str] = None
    severity: str = "Moderate"
    source: ProvenanceSource = ProvenanceSource.USER_INTAKE

class PatientIntake(BaseModel):
    age: int
    sex: str
    symptoms: List[str] = Field(default_factory=list)
    conditions: List[str] = Field(default_factory=list)
    medications: List[Medication] = Field(default_factory=list)
    allergies: List[Allergy] = Field(default_factory=list)
    notes: Optional[str] = None
    provenance: ProvenanceSource = ProvenanceSource.USER_INTAKE

class MedicalReport(BaseModel):
    id: str
    filename: str
    upload_date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    report_date: str
    lab_name: str = "Clinical Diagnostic Laboratory"
    category: str = "Comprehensive Panel"
    raw_text: str = ""
    tests: List[LabTest] = Field(default_factory=list)

class ConflictAlert(BaseModel):
    id: str
    severity: AlertSeverity = AlertSeverity.WARNING
    title: str
    description: str
    recommendation: str
    source_a: str
    source_b: str

class TrendMetric(BaseModel):
    test_name: str
    unit: str
    previous_date: str
    previous_value: float
    current_date: str
    current_value: float
    delta: float
    delta_percent: float
    direction: str  # "UP", "DOWN", "STABLE"
    status: RangeStatus

class AuditEntry(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    action: str
    actor: str = "User"
    details: str

class PatientRecord(BaseModel):
    patient_id: str
    name: str
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    intake: PatientIntake
    reports: List[MedicalReport] = Field(default_factory=list)
    current_labs: List[LabTest] = Field(default_factory=list)
    previous_labs: List[LabTest] = Field(default_factory=list)
    trends: List[TrendMetric] = Field(default_factory=list)
    conflicts: List[ConflictAlert] = Field(default_factory=list)
    summary_patient: str = ""
    summary_physician: str = ""
    questions_for_doctor: List[str] = Field(default_factory=list)
    audit_log: List[AuditEntry] = Field(default_factory=list)

class VerifyTestRequest(BaseModel):
    test_id: str
    verified_value: Optional[float] = None
    verified_unit: Optional[str] = None
    notes: Optional[str] = None
    verified_by: str = "Clinician / Patient Reviewer"

class IntakeUpdateRequest(BaseModel):
    age: int
    sex: str
    symptoms: List[str]
    conditions: List[str]
    medications: List[Dict[str, str]]
    allergies: List[Dict[str, str]]
