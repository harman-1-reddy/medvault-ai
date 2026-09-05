from typing import List, Dict, Tuple, Optional
import uuid
from models import (
    PatientIntake, MedicalReport, LabTest, ConflictAlert, 
    TrendMetric, RangeStatus, AlertSeverity, ProvenanceSource
)

def detect_inconsistencies(
    intake: PatientIntake, 
    current_labs: List[LabTest], 
    reports: List[MedicalReport]
) -> List[ConflictAlert]:
    """
    Detects clinical conflicts, omissions, and discrepancies between:
    1. Patient-reported intake
    2. Extracted medical reports
    3. Laboratory findings
    """
    conflicts: List[ConflictAlert] = []
    
    intake_conditions_lower = [c.lower() for c in intake.conditions]
    intake_meds_lower = [m.name.lower() for m in intake.medications]
    intake_allergies_lower = [a.substance.lower() for a in intake.allergies]

    # Combine all raw text from reports for provenance checks
    all_report_text = " ".join([r.raw_text.lower() for r in reports])

    # 1. Check for Allergy Discrepancy (e.g., patient omitted allergy or report mentions allergy)
    critical_allergens = ["penicillin", "amoxicillin", "sulfa", "aspirin", "codeine", "latex"]
    for allergen in critical_allergens:
        found_in_reports = allergen in all_report_text
        declared_by_patient = any(allergen in a for a in intake_allergies_lower)
        if found_in_reports and not declared_by_patient:
            conflicts.append(ConflictAlert(
                id=f"conf-{uuid.uuid4().hex[:6]}",
                severity=AlertSeverity.CRITICAL,
                title="Undisclosed Drug Allergy Detected in Source Records",
                description=f"Source records explicitly reference an allergy or sensitivity to '{allergen.title()}', but this was omitted in the current patient intake form.",
                recommendation=f"Confirm with the patient immediately before prescribing or administering {allergen.title()}-class medications.",
                source_a="Medical Report Documentation",
                source_b="Patient Intake (Allergies list: Omitted)"
            ))

    # 2. Check for Medication without Stated Indication/Condition
    med_condition_map = {
        "metformin": ("diabetes", "Type 2 Diabetes"),
        "lisinopril": ("hypertension", "Hypertension / High Blood Pressure"),
        "amlodipine": ("hypertension", "Hypertension / High Blood Pressure"),
        "atorvastatin": ("hyperlipidemia", "Hyperlipidemia / Elevated Cholesterol"),
        "levothyroxine": ("hypothyroid", "Hypothyroidism / Thyroid Condition"),
        "omeprazole": ("gerd", "Acid Reflux / GERD"),
    }
    for med_key, (cond_key, formal_name) in med_condition_map.items():
        if any(med_key in m for m in intake_meds_lower):
            has_condition = any(cond_key in c for c in intake_conditions_lower)
            if not has_condition:
                conflicts.append(ConflictAlert(
                    id=f"conf-{uuid.uuid4().hex[:6]}",
                    severity=AlertSeverity.WARNING,
                    title=f"Medication Prescribed Without Documented Condition ({formal_name})",
                    description=f"Patient intake lists active medication '{med_key.title()}', but '{formal_name}' is not documented in the medical history or existing conditions.",
                    recommendation=f"Clarify if the patient has a formal diagnosis of {formal_name} or is taking {med_key.title()} off-label/prophylactically.",
                    source_a=f"Patient Intake: Medication '{med_key.title()}'",
                    source_b="Patient Intake: Existing Conditions (Not Listed)"
                ))

    # 3. Check for Impaired Kidney Function with Nephrotoxic or Cleared Medications
    egfr_test = next((t for t in current_labs if "egfr" in t.name.lower()), None)
    
    if egfr_test and egfr_test.value < 60:
        nsaids = ["ibuprofen", "naproxen", "meloxicam", "ketorolac", "advil", "aleve"]
        prescribed_nsaids = [m for m in intake_meds_lower if any(n in m for n in nsaids)]
        if prescribed_nsaids:
            nsaid_list_str = ", ".join(prescribed_nsaids).title()
            conflicts.append(ConflictAlert(
                id=f"conf-{uuid.uuid4().hex[:6]}",
                severity=AlertSeverity.CRITICAL,
                title="Potential Renal Contraindication (NSAID + Reduced eGFR)",
                description=f"Lab report indicates reduced eGFR of {egfr_test.value} mL/min (Reference: > 60 mL/min), while patient is actively taking NSAID medication: {nsaid_list_str}.",
                recommendation="Clinician should evaluate stopping or adjusting nephrotoxic NSAIDs to avoid acute kidney injury.",
                source_a=f"Lab Metric: eGFR {egfr_test.value} mL/min ({egfr_test.status.value})",
                source_b=f"Medication Intake: {nsaid_list_str}"
            ))

    # 4. Check for High Fasting Glucose without Documented Diabetes
    glucose_test = next((t for t in current_labs if "glucose" in t.name.lower() or "fbs" in t.name.lower()), None)
    if glucose_test and glucose_test.status == RangeStatus.HIGH and glucose_test.value >= 126:
        if not any("diabetes" in c for c in intake_conditions_lower):
            conflicts.append(ConflictAlert(
                id=f"conf-{uuid.uuid4().hex[:6]}",
                severity=AlertSeverity.INFO,
                title="Elevated Fasting Glucose Exceeding Diagnostic Threshold",
                description=f"Fasting blood glucose is {glucose_test.value} {glucose_test.unit} (Source Range: {glucose_test.reference_range.text}), but Diabetes is not listed in existing patient conditions.",
                recommendation="Recommend repeating fasting blood glucose or ordering a confirmatory Hemoglobin A1c (HbA1c) test.",
                source_a=f"Lab Metric: Glucose {glucose_test.value} {glucose_test.unit}",
                source_b="Patient Intake: Existing Conditions"
            ))

    return conflicts

def compute_longitudinal_trends(
    previous_labs: List[LabTest], 
    current_labs: List[LabTest],
    prev_date: str = "Prior Record",
    curr_date: str = "Current Record"
) -> List[TrendMetric]:
    """
    Compares historical lab results with current values, calculating delta and direction.
    """
    trends: List[TrendMetric] = []
    prev_map = {t.name.lower().strip(): t for t in previous_labs}

    for curr in current_labs:
        key = curr.name.lower().strip()
        matched_prev = prev_map.get(key)
        
        # Fuzzy match if exact match not found
        if not matched_prev:
            for p_key, p_test in prev_map.items():
                if p_key in key or key in p_key:
                    matched_prev = p_test
                    break

        if matched_prev and matched_prev.value > 0:
            delta = round(curr.value - matched_prev.value, 2)
            pct = round((delta / matched_prev.value) * 100, 1)
            
            if abs(pct) < 1.0:
                direction = "STABLE"
            elif delta > 0:
                direction = "UP"
            else:
                direction = "DOWN"

            trends.append(TrendMetric(
                test_name=curr.name,
                unit=curr.unit,
                previous_date=prev_date,
                previous_value=matched_prev.value,
                current_date=curr_date,
                current_value=curr.value,
                delta=delta,
                delta_percent=pct,
                direction=direction,
                status=curr.status
            ))

    return trends

def generate_patient_summary(
    intake: PatientIntake, 
    current_labs: List[LabTest], 
    trends: List[TrendMetric],
    conflicts: List[ConflictAlert]
) -> Tuple[str, List[str]]:
    """
    Generates a clear, plain-language patient summary and questions for their doctor.
    Adheres strictly to Responsible AI: avoids diagnosis and treatment recommendations.
    """
    high_tests = [t for t in current_labs if t.status == RangeStatus.HIGH]
    low_tests = [t for t in current_labs if t.status == RangeStatus.LOW]
    normal_tests = [t for t in current_labs if t.status == RangeStatus.NORMAL]

    lines = [
        "Hello! Here is an organized overview of your medical information and recent laboratory tests."
    ]

    # Overview of results
    if high_tests or low_tests:
        abnormal_summary = []
        for t in high_tests:
            ref_str = f" (normal range on report: {t.reference_range.text})" if t.reference_range.is_present_in_source else ""
            abnormal_summary.append(f"• **{t.name}**: {t.value} {t.unit} — Above the reference range{ref_str}")
        for t in low_tests:
            ref_str = f" (normal range on report: {t.reference_range.text})" if t.reference_range.is_present_in_source else ""
            abnormal_summary.append(f"• **{t.name}**: {t.value} {t.unit} — Below the reference range{ref_str}")

        lines.append("\n### Key Laboratory Observations")
        lines.append("Some of your test values fall outside the reference ranges listed on your laboratory report:")
        lines.extend(abnormal_summary)
    else:
        lines.append("\n### Laboratory Observations")
        lines.append("All reported laboratory values with specified reference ranges appear within their standard ranges.")

    if normal_tests:
        sample_names = ", ".join([t.name for t in normal_tests[:3]])
        lines.append(f"\n{len(normal_tests)} other tested metrics (including {sample_names}) were within their normal laboratory reference ranges.")

    # Trends observation
    if trends:
        lines.append("\n### Changes Compared to Your Prior Report")
        for tr in trends:
            arrow = "increased 📈" if tr.direction == "UP" else ("decreased 📉" if tr.direction == "DOWN" else "remained steady ⚖️")
            lines.append(f"• **{tr.test_name}**: {tr.previous_value} → {tr.current_value} {tr.unit} ({arrow} by {abs(tr.delta)} {tr.unit})")

    # Disclaimer
    lines.append("\n> **Important Note:** This summary is for your personal organization only. It does not provide medical diagnoses or prescribe treatment. Always discuss your results with your licensed healthcare provider.")

    # Questions for doctor
    questions = []
    for t in high_tests[:2]:
        questions.append(f"My {t.name} was {t.value} {t.unit}, which is above the laboratory range ({t.reference_range.text}). What does this mean for my routine care?")
    for t in low_tests[:2]:
        questions.append(f"My {t.name} was {t.value} {t.unit}, which is lower than the reference interval. Do we need further testing or dietary changes?")
    if conflicts:
        questions.append("Can we review my allergy and medication list together to ensure our records are completely aligned?")
    if not questions:
        questions.append("Based on my current results, what routine follow-up schedule do you recommend?")

    return "\n".join(lines), questions

def generate_physician_summary(
    patient_name: str,
    intake: PatientIntake, 
    current_labs: List[LabTest], 
    trends: List[TrendMetric],
    conflicts: List[ConflictAlert]
) -> str:
    """
    Generates a structured SOAP-style clinical review for healthcare providers.
    """
    symptoms_str = ", ".join(intake.symptoms) if intake.symptoms else "None reported"
    conditions_str = ", ".join(intake.conditions) if intake.conditions else "None reported"
    meds_str = ", ".join([f"{m.name} ({m.dosage})" for m in intake.medications]) if intake.medications else "None reported"
    
    allergy_items = []
    for a in intake.allergies:
        reaction_text = a.reaction if a.reaction else "unspecified"
        allergy_items.append(f"{a.substance} ({reaction_text})")
    allergies_str = ", ".join(allergy_items) if allergy_items else "NKDA declared"

    lines = [
        "**CLINICAL SUMMARY & RECONCILIATION SHEET**",
        f"**Patient:** {patient_name} | **Age:** {intake.age} | **Sex:** {intake.sex}",
        "",
        "**SUBJECTIVE / PATIENT INTAKE:**",
        f"- **Presenting Symptoms:** {symptoms_str}",
        f"- **Active Conditions:** {conditions_str}",
        f"- **Current Regimen:** {meds_str}",
        f"- **Allergies:** {allergies_str}",
        "",
        "**OBJECTIVE / EXTRACTED LABORATORY METRICS:**"
    ]

    for t in current_labs:
        ref_text = t.reference_range.text if t.reference_range.is_present_in_source else "Range not provided"
        flag = f"[{t.status.value}]" if t.status != RangeStatus.NORMAL else "[NORMAL]"
        verif = "Verified" if t.verified else f"{int(t.confidence*100)}% Conf"
        lines.append(f"- {t.name:30}: {t.value:6.1f} {t.unit:<8} (Ref: {ref_text}) {flag} ({verif})")

    if trends:
        lines.append("\n**LONGITUDINAL DELTA COMPARISON:**")
        for tr in trends:
            lines.append(f"- {tr.test_name}: {tr.previous_value} → {tr.current_value} {tr.unit} (Delta: {tr.delta:+.2f}, {tr.delta_percent:+.1f}%) [{tr.direction}]")

    if conflicts:
        lines.append("\n**DISCREPANCIES & SAFETY FLAGS REQUIRING RECONCILIATION:**")
        for c in conflicts:
            lines.append(f"- [{c.severity.value}] {c.title}: {c.description}")
            lines.append(f"  Action: {c.recommendation}")

    lines.append("\n---\n*Generated by MedVault Clinical Intelligence Engine for human review. Does not replace clinical evaluation.*")
    return "\n".join(lines)
