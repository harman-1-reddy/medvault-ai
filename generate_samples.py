import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

OUT_DIR = os.path.join(os.path.dirname(__file__), "sample_reports")
os.makedirs(OUT_DIR, exist_ok=True)

def create_sample_pdf(filename: str, title: str, patient_info: str, rows: list, notes: str):
    filepath = os.path.join(OUT_DIR, filename)
    doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    story = [
        Paragraph(f"<b>{title}</b>", styles['Heading1']),
        Paragraph(patient_info.replace("\n", "<br/>"), styles['Normal']),
        Spacer(1, 15),
        Paragraph("<b>LABORATORY TEST RESULTS & REFERENCE INTERVALS</b>", styles['Heading2'])
    ]

    table_data = [["Test Name", "Result", "Units", "Reference Range", "Flag"]]
    table_data.extend(rows)

    t = Table(table_data, colWidths=[180, 70, 70, 130, 60])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#94A3B8')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>CLINICAL NOTES & ALERTS:</b>", styles['Heading3']))
    story.append(Paragraph(notes.replace("\n", "<br/>"), styles['Normal']))

    doc.build(story)
    print(f"Generated sample PDF: {filepath}")

# 1. Sarah Jenkins CMP PDF
create_sample_pdf(
    "Comprehensive_Metabolic_Panel_Aug2026.pdf",
    "METRO CLINICAL DIAGNOSTICS LABORATORY",
    "Patient: Sarah Jenkins | DOB: 1974-04-12 | MRN: 489102-SJ\nCollection Date: 2026-08-20 07:45 AM | Ordering Dr: Jennifer Lin, MD",
    [
        ["Fasting Blood Glucose", "145.0", "mg/dL", "70.0 - 99.0", "HIGH"],
        ["Hemoglobin A1c (HbA1c)", "7.2", "%", "4.0 - 5.6", "HIGH"],
        ["Serum Creatinine", "1.4", "mg/dL", "0.6 - 1.2", "HIGH"],
        ["eGFR (Estimated GFR)", "54.0", "mL/min", "> 60.0", "LOW"],
        ["Potassium", "4.8", "mEq/L", "3.5 - 5.0", "NORMAL"],
        ["Total Cholesterol", "182.0", "mg/dL", "125.0 - 200.0", "NORMAL"],
        ["Microalbumin / Creatinine", "42.0", "mg/g", "< 30.0", "HIGH"]
    ],
    "Patient chart notes prior adverse reaction: developed acute erythematous urticaria (rash) following oral Penicillin antibiotic course in 2023.\nNote decreased eGFR compared to May 2026 baseline. Advise monitoring renal clearance."
)

# 2. Robert Vance Lipids PDF
create_sample_pdf(
    "Cardiac_Lipid_Panel_Sep2026.pdf",
    "QUEST CARDIOVASCULAR DIAGNOSTICS",
    "Patient: Robert Vance | DOB: 1965-02-14 | MRN: 902144-RV\nCollection Date: 2026-09-02 08:15 AM | Ordering Dr: Marcus Brody, MD",
    [
        ["Total Cholesterol", "212.0", "mg/dL", "125.0 - 200.0", "HIGH"],
        ["LDL Cholesterol", "135.0", "mg/dL", "< 100.0", "HIGH"],
        ["HDL Cholesterol", "46.0", "mg/dL", "> 40.0", "NORMAL"],
        ["Triglycerides", "175.0", "mg/dL", "< 150.0", "HIGH"],
        ["High-Sensitivity CRP (hs-CRP)", "3.4", "mg/L", "< 1.0", "HIGH"]
    ],
    "Statin adherence noted. Comparison to prior year indicates positive response (LDL reduction from 182 mg/dL to 135 mg/dL).\nElevated hs-CRP warrants continued cardiovascular risk monitoring."
)

# 3. Elena Rostova Thyroid PDF
create_sample_pdf(
    "Thyroid_Ferritin_Workup_Sep2026.pdf",
    "APEX ENDOCRINE & HEMATOLOGY LABS",
    "Patient: Elena Rostova | DOB: 1992-07-22 | MRN: 110294-ER\nCollection Date: 2026-09-04 09:30 AM | Ordering Dr: Sarah Al-Mansoor, MD",
    [
        ["TSH (Thyroid Stimulating)", "6.4", "uIU/mL", "0.4 - 4.0", "HIGH"],
        ["Free T4", "0.75", "ng/dL", "0.8 - 1.8", "LOW"],
        ["Ferritin", "11.5", "ng/mL", "15.0 - 150.0", "LOW"],
        ["Hemoglobin", "10.9", "g/dL", "12.0 - 16.0", "LOW"]
    ],
    "Lab findings demonstrate microcytic iron deficiency profile concurrently with mild subclinical hypothyroidism.\nRecommend comprehensive iron panel follow-up and clinical endocrinology review."
)
print("All sample PDF files generated!")
