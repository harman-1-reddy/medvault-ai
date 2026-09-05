import re
import uuid
import os
from typing import List, Tuple, Optional, Dict, Any
from pypdf import PdfReader
from models import LabTest, ReferenceRange, RangeStatus, ProvenanceSource, MedicalReport

KNOWN_PANELS = {
    "Metabolic & Glucose": [
        "glucose", "fasting blood glucose", "fbs", "hba1c", "glycated hemoglobin", "calcium", 
        "sodium", "potassium", "chloride", "carbon dioxide", "bicarbonate"
    ],
    "Lipid Profile": [
        "cholesterol", "total cholesterol", "hdl", "hdl cholesterol", "ldl", "ldl cholesterol", 
        "triglycerides", "vldl"
    ],
    "Renal & Kidney Function": [
        "creatinine", "serum creatinine", "bun", "blood urea nitrogen", "egfr", "uric acid", "microalbumin"
    ],
    "Complete Blood Count (CBC)": [
        "hemoglobin", "wbc", "white blood cell", "rbc", "red blood cell", "platelets", 
        "hematocrit", "mcv", "mch", "mchc"
    ],
    "Thyroid & Endocrine": [
        "tsh", "thyroid stimulating hormone", "thyroid stimulating", "free t3", "free t4", "total t3", "total t4"
    ],
    "Iron & Anemia Workup": [
        "ferritin", "serum iron", "tibc", "transferrin saturation"
    ],
    "Liver Function Panel": [
        "alt", "ast", "alkaline phosphatase", "total bilirubin", "direct bilirubin", "albumin"
    ]
}

def determine_category(test_name: str) -> str:
    lower_name = test_name.lower().strip()
    for category, keywords in KNOWN_PANELS.items():
        for kw in keywords:
            if kw in lower_name:
                return category
    return "Diagnostic Chemistry"

def parse_reference_range(range_str: str) -> ReferenceRange:
    if not range_str or range_str.strip().lower() in ["none", "n/a", "-", "nil", "not provided"]:
        return ReferenceRange(is_present_in_source=False, text="Not provided in report")

    clean = range_str.strip()
    
    # Range formats like "70 - 99", "70.0 to 99.0", "70.0-99.0"
    hyphen_match = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(?:-|to)\s*([0-9]+(?:\.[0-9]+)?)', clean, re.IGNORECASE)
    if hyphen_match:
        low = float(hyphen_match.group(1))
        high = float(hyphen_match.group(2))
        return ReferenceRange(low=low, high=high, text=clean, is_present_in_source=True)

    # Less than formats like "< 200", "<= 100", "<5.7"
    less_match = re.search(r'(?:<|<=|less than)\s*([0-9]+(?:\.[0-9]+)?)', clean, re.IGNORECASE)
    if less_match:
        high = float(less_match.group(1))
        return ReferenceRange(low=0.0, high=high, text=clean, is_present_in_source=True)

    # Greater than formats like "> 60", ">= 60", ">60"
    greater_match = re.search(r'(?:>|>=|greater than)\s*([0-9]+(?:\.[0-9]+)?)', clean, re.IGNORECASE)
    if greater_match:
        low = float(greater_match.group(1))
        return ReferenceRange(low=low, high=99999.0, text=clean, is_present_in_source=True)

    return ReferenceRange(is_present_in_source=True, text=clean)

def evaluate_status(value: float, ref_range: ReferenceRange) -> RangeStatus:
    if not ref_range.is_present_in_source:
        return RangeStatus.RANGE_NOT_PROVIDED
    
    if ref_range.low is not None and value < ref_range.low:
        return RangeStatus.LOW
    if ref_range.high is not None and value > ref_range.high:
        return RangeStatus.HIGH
    if ref_range.low is not None or ref_range.high is not None:
        return RangeStatus.NORMAL
    
    return RangeStatus.RANGE_NOT_PROVIDED

def extract_text_from_pdf(filepath: str) -> List[Tuple[int, str]]:
    """Returns a list of (page_number, page_text)"""
    pages_data = []
    try:
        reader = PdfReader(filepath)
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            pages_data.append((i + 1, text))
    except Exception as e:
        pages_data.append((1, f"Error extracting PDF: {str(e)}"))
    return pages_data

def extract_tests_from_text(raw_text: str, filename: str = "Uploaded Document", page_num: int = 1) -> List[LabTest]:
    extracted = []
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]

    # Strategy 1: Multi-line table sequence (Name \n Value \n Unit \n RefRange [\n Flag])
    i = 0
    matched_names = set()
    while i < len(lines):
        if i + 3 < len(lines):
            cand_name = lines[i]
            cand_val_str = lines[i+1]
            cand_unit = lines[i+2]
            cand_ref = lines[i+3]

            # Validation checks
            val_match = re.match(r'^[0-9]+(?:\.[0-9]+)?$', cand_val_str)
            if val_match and 2 <= len(cand_name) <= 50 and not any(h in cand_name.lower() for h in ["test name", "patient", "collection", "ordering", "report date", "clinical notes"]):
                try:
                    val = float(cand_val_str)
                    ref_range = parse_reference_range(cand_ref)
                    status = evaluate_status(val, ref_range)
                    cat = determine_category(cand_name)
                    
                    snippet = f"{cand_name}: {val} {cand_unit} (Ref: {cand_ref})"
                    test_obj = LabTest(
                        id=f"test-{uuid.uuid4().hex[:8]}",
                        name=cand_name,
                        category=cat,
                        value=val,
                        unit=cand_unit,
                        reference_range=ref_range,
                        status=status,
                        confidence=0.97 if ref_range.is_present_in_source else 0.88,
                        source_snippet=snippet,
                        source_file=filename,
                        page_number=page_num,
                        provenance=ProvenanceSource.EXTRACTED_DOCUMENT,
                        verified=False
                    )
                    extracted.append(test_obj)
                    matched_names.add(cand_name.lower())

                    # Skip flag if present
                    if i + 4 < len(lines) and lines[i+4].upper() in ['HIGH', 'LOW', 'NORMAL']:
                        i += 5
                    else:
                        i += 4
                    continue
                except ValueError:
                    pass
        i += 1

    # Strategy 2: Single-line tabular lines or colon lines
    table_pattern = re.compile(
        r'^\s*([A-Za-z0-9\(\)\s\/\-\,\.]+?)\s{2,}'+
        r'([0-9]+(?:\.[0-9]+)?)\s*'+
        r'([A-Za-z\%\/\u03bc\d\^\.\-]+)\s*'+
        r'(?:(?:[\:\;\|]\s*)?(?:Ref(?:erence)?\s*(?:Range|Interval)?[\:\s]*)?([<>]?\s*[0-9]+(?:\.[0-9]+)?(?:\s*(?:-|to)\s*[0-9]+(?:\.[0-9]+)?)?))?',
        re.IGNORECASE
    )
    colon_pattern = re.compile(
        r'([A-Za-z0-9\(\)\s\/\-\,\.]+?)\s*:\s*'+
        r'([0-9]+(?:\.[0-9]+)?)\s*'+
        r'([A-Za-z\%\/\u03bc\d\^\.\-]+)?'+
        r'(?:\s*[\(\[]?(?:Ref(?:erence)?\s*(?:Range)?[\:\s]*)?([<>]?\s*[0-9]+(?:\.[0-9]+)?(?:\s*(?:-|to)\s*[0-9]+(?:\.[0-9]+)?)?)[\)\]]?)?',
        re.IGNORECASE
    )

    for line in lines:
        if any(h in line.lower() for h in ["test name", "patient name", "date of test", "laboratory report", "page"]):
            continue

        match = table_pattern.match(line) or colon_pattern.search(line)
        if match:
            name_raw = match.group(1).strip()
            if name_raw.lower() in matched_names:
                continue

            val_str = match.group(2).strip()
            unit_raw = (match.group(3) or "").strip()
            ref_raw = (match.group(4) or "").strip() if len(match.groups()) >= 4 else ""

            if any(term in name_raw.lower() for term in ["mrn", "id", "phone", "dob", "sample", "doctor", "dr.", "date"]):
                continue
            if len(name_raw) < 2 or len(name_raw) > 50:
                continue

            try:
                val = float(val_str)
            except ValueError:
                continue

            ref_range = parse_reference_range(ref_raw)
            status = evaluate_status(val, ref_range)
            cat = determine_category(name_raw)

            test_obj = LabTest(
                id=f"test-{uuid.uuid4().hex[:8]}",
                name=name_raw,
                category=cat,
                value=val,
                unit=unit_raw or "unit",
                reference_range=ref_range,
                status=status,
                confidence=0.96 if ref_range.is_present_in_source else 0.88,
                source_snippet=line,
                source_file=filename,
                page_number=page_num,
                provenance=ProvenanceSource.EXTRACTED_DOCUMENT,
                verified=False
            )
            extracted.append(test_obj)
            matched_names.add(name_raw.lower())

    return extracted

def process_document(filepath: str, filename: str) -> MedicalReport:
    """Processes a PDF or text file and returns a structured MedicalReport."""
    raw_text = ""
    tests: List[LabTest] = []
    report_date = "2026-08-20"

    if filepath.lower().endswith(".pdf"):
        pages = extract_text_from_pdf(filepath)
        for page_num, text in pages:
            raw_text += f"\n--- Page {page_num} ---\n" + text
            page_tests = extract_tests_from_text(text, filename=filename, page_num=page_num)
            tests.extend(page_tests)
    else:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()
        tests = extract_tests_from_text(raw_text, filename=filename, page_num=1)

    date_match = re.search(r'\b(202[0-9]-[0-1][0-9]-[0-3][0-9]|[0-1]?[0-9]\/[0-3]?[0-9]\/202[0-9])\b', raw_text)
    if date_match:
        report_date = date_match.group(1)

    dedup: Dict[str, LabTest] = {}
    for t in tests:
        key = t.name.lower()
        if key not in dedup or t.reference_range.is_present_in_source:
            dedup[key] = t

    report = MedicalReport(
        id=f"rep-{uuid.uuid4().hex[:8]}",
        filename=filename,
        report_date=report_date,
        lab_name="Clinical Diagnostics Diagnostic System",
        category="Comprehensive Multi-Panel Analysis",
        raw_text=raw_text.strip(),
        tests=list(dedup.values())
    )
    return report
