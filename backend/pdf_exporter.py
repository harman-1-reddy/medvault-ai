import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from models import PatientRecord, RangeStatus, AlertSeverity

def generate_patient_pdf(record: PatientRecord) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        rightMargin=36, 
        leftMargin=36, 
        topMargin=36, 
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor('#0F766E'),
        alignment=TA_LEFT,
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#475569'),
        spaceAfter=12
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )
    alert_style = ParagraphStyle(
        'AlertText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.HexColor('#B91C1C')
    )
    disclaimer_style = ParagraphStyle(
        'DisclaimerText',
        parent=styles['Italic'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#64748B'),
        alignment=TA_CENTER
    )

    story = []

    # Title Banner
    story.append(Paragraph("MEDVAULT AI — CLINICAL HEALTH PASSPORT", title_style))
    story.append(Paragraph(f"Patient Name: <b>{record.name}</b> | Generated: {record.created_at} | System: MedVault v2.4", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0D9488'), spaceAfter=10))

    # Demographics & Intake
    intake = record.intake
    meds_str = ", ".join([f"{m.name} ({m.dosage})" for m in intake.medications]) if intake.medications else "None reported"
    allergies_str = ", ".join([f"{a.substance}" for a in intake.allergies]) if intake.allergies else "No Known Drug Allergies (NKDA)"
    conditions_str = ", ".join(intake.conditions) if intake.conditions else "None reported"

    intake_data = [
        [Paragraph("<b>Age:</b>", body_style), Paragraph(str(intake.age), body_style), Paragraph("<b>Sex:</b>", body_style), Paragraph(intake.sex, body_style)],
        [Paragraph("<b>Conditions:</b>", body_style), Paragraph(conditions_str, body_style), Paragraph("<b>Allergies:</b>", body_style), Paragraph(allergies_str, body_style)],
        [Paragraph("<b>Active Medications:</b>", body_style), Paragraph(meds_str, body_style), Paragraph("<b>Provenance:</b>", body_style), Paragraph("User-Reported Intake", body_style)]
    ]
    t_intake = Table(intake_data, colWidths=[90, 180, 70, 200])
    t_intake.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_intake)
    story.append(Spacer(1, 10))

    # Safety & Conflict Alerts
    if record.conflicts:
        story.append(Paragraph("DISCREPANCIES & SAFETY FLAGS REQUIRING RECONCILIATION", section_heading))
        alert_rows = [[Paragraph("<b>Severity</b>", body_style), Paragraph("<b>Issue & Description</b>", body_style), Paragraph("<b>Recommended Clinical Action</b>", body_style)]]
        for c in record.conflicts:
            sev_color = colors.HexColor('#EF4444') if c.severity == AlertSeverity.CRITICAL else colors.HexColor('#F59E0B')
            alert_rows.append([
                Paragraph(f"<b>{c.severity.value}</b>", alert_style if c.severity == AlertSeverity.CRITICAL else body_style),
                Paragraph(f"<b>{c.title}</b><br/>{c.description}", body_style),
                Paragraph(c.recommendation, body_style)
            ])
        t_alerts = Table(alert_rows, colWidths=[70, 260, 210])
        t_alerts.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#FEE2E2')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#FCA5A5')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#FECACA')),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_alerts)
        story.append(Spacer(1, 10))

    # Current Lab Results
    story.append(Paragraph("STRUCTURED LABORATORY FINDINGS & PROVENANCE", section_heading))
    lab_rows = [[
        Paragraph("<b>Test Name</b>", body_style),
        Paragraph("<b>Result</b>", body_style),
        Paragraph("<b>Units</b>", body_style),
        Paragraph("<b>Source Ref Interval</b>", body_style),
        Paragraph("<b>Status</b>", body_style),
        Paragraph("<b>Verification</b>", body_style)
    ]]

    for t in record.current_labs:
        ref_text = t.reference_range.text if t.reference_range.is_present_in_source else "Not in report"
        flag_color = colors.HexColor('#DC2626') if t.status == RangeStatus.HIGH else (colors.HexColor('#D97706') if t.status == RangeStatus.LOW else colors.HexColor('#16A34A'))
        status_cell = Paragraph(f"<font color='{flag_color.hexval()}'><b>{t.status.value}</b></font>", body_style)
        verif_text = "Verified" if t.verified else f"{int(t.confidence*100)}% AI"

        lab_rows.append([
            Paragraph(t.name, body_style),
            Paragraph(f"<b>{t.value}</b>", body_style),
            Paragraph(t.unit, body_style),
            Paragraph(ref_text, body_style),
            status_cell,
            Paragraph(verif_text, body_style)
        ])

    t_labs = Table(lab_rows, colWidths=[160, 55, 65, 120, 70, 70])
    t_labs.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#CCFBF1')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#99F6E4')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_labs)
    story.append(Spacer(1, 10))

    # Longitudinal Trends
    if record.trends:
        story.append(Paragraph("LONGITUDINAL COMPARISON (CURRENT VS PRIOR)", section_heading))
        trend_rows = [[
            Paragraph("<b>Test Name</b>", body_style),
            Paragraph("<b>Prior Value</b>", body_style),
            Paragraph("<b>Current Value</b>", body_style),
            Paragraph("<b>Delta (Change)</b>", body_style),
            Paragraph("<b>Trend Direction</b>", body_style)
        ]]
        for tr in record.trends:
            dir_str = f"+{tr.delta} ({tr.direction})" if tr.delta > 0 else f"{tr.delta} ({tr.direction})"
            trend_rows.append([
                Paragraph(tr.test_name, body_style),
                Paragraph(f"{tr.previous_value} {tr.unit}", body_style),
                Paragraph(f"{tr.current_value} {tr.unit}", body_style),
                Paragraph(f"{tr.delta:+.1f} ({tr.delta_percent:+.1f}%)", body_style),
                Paragraph(tr.direction, body_style)
            ])
        t_trends = Table(trend_rows, colWidths=[170, 85, 85, 100, 100])
        t_trends.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_trends)
        story.append(Spacer(1, 10))

    # Patient Summary & Questions
    story.append(Paragraph("PATIENT-FRIENDLY SUMMARY & QUESTIONS FOR HEALTHCARE PROVIDER", section_heading))
    clean_summary = record.summary_patient.replace("### Key Laboratory Observations", "").replace("### Changes Compared to Your Prior Report", "").replace("•", "-").replace("📈", "").replace("📉", "").replace("⚖️", "")
    story.append(Paragraph(clean_summary.replace("\n", "<br/>"), body_style))
    story.append(Spacer(1, 8))

    if record.questions_for_doctor:
        q_lines = "<br/>".join([f"<b>{i+1}.</b> {q}" for i, q in enumerate(record.questions_for_doctor)])
        story.append(Paragraph(f"<b>Suggested Questions to Ask Your Doctor:</b><br/>{q_lines}", body_style))

    # Disclaimer Footer
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#94A3B8'), spaceAfter=6))
    story.append(Paragraph(
        "RESPONSIBLE AI NOTICE: MedVault AI is an assistive administrative organization tool. It does not provide medical diagnoses, treatment decisions, or prescriptions. All extracted laboratory values and ranges must be verified by a licensed medical practitioner.",
        disclaimer_style
    ))

    doc.build(story)
    return buffer.getvalue()
