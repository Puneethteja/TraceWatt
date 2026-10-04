import io
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

def render_report(case, consumer, baseline, readings=None) -> bytes:
    """
    Renders a valid, professional PDF investigation report for a consumer case.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
        title="TraceWatt Investigation Report"
    )
    doc.pageCompression = 0

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=10
    )
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=8,
        spaceAfter=5
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )
    bold_style = ParagraphStyle(
        'BoldDark',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    evidence_style = ParagraphStyle(
        'EvidenceItem',
        parent=body_style,
        leftIndent=12,
        spaceAfter=3,
        textColor=colors.HexColor('#1e293b')
    )
    counter_style = ParagraphStyle(
        'CounterItem',
        parent=body_style,
        leftIndent=12,
        spaceAfter=3,
        textColor=colors.HexColor('#059669')
    )

    story = []

    # Title & Metadata Header
    story.append(Paragraph("TraceWatt Investigation Report", title_style))
    gen_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    story.append(Paragraph(
        f"Confidential Utility Investigation Dossier &middot; Generated {gen_time} &middot; TraceWatt AI Engine",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#cbd5e1'), spaceAfter=10))

    # Safe attribute extractors
    cid = getattr(consumer, "id", None) or (consumer.get("id") if isinstance(consumer, dict) else "Unknown")
    cat = getattr(consumer, "category", None) or (consumer.get("category") if isinstance(consumer, dict) else "General")
    feeder = getattr(consumer, "feeder_id", None) or (consumer.get("feeder_id") if isinstance(consumer, dict) else "N/A")
    transformer = getattr(consumer, "transformer_id", None) or (consumer.get("transformer_id") if isinstance(consumer, dict) else "N/A")
    meter_id = f"MTR-{str(cid).replace('SYN_', '').replace('CONS-', '')}"

    status = getattr(case, "status", None) or (case.get("status") if isinstance(case, dict) else "New")
    risk = getattr(case, "risk_level", None) or (case.get("risk_level") if isinstance(case, dict) else "Low")
    cause = getattr(case, "cause", None) or (case.get("cause") if isinstance(case, dict) else "Normal Pattern")
    score = getattr(case, "anomaly_score", None) if not isinstance(case, dict) else case.get("anomaly_score")
    conf = getattr(case, "confidence", None) if not isinstance(case, dict) else case.get("confidence")
    loss = getattr(case, "estimated_loss", None) if not isinstance(case, dict) else case.get("estimated_loss")
    priority = getattr(case, "priority", None) if not isinstance(case, dict) else case.get("priority")
    flagged = getattr(case, "first_flagged_at", None) if not isinstance(case, dict) else case.get("first_flagged_at")
    action = getattr(case, "recommended_action", None) or (case.get("recommended_action") if isinstance(case, dict) else "None")
    note = getattr(case, "note", None) or (case.get("note") if isinstance(case, dict) else "")

    risk_color = '#dc2626' if str(risk).lower() == 'high' else ('#d97706' if str(risk).lower() == 'medium' else '#059669')

    # Section 1: Consumer & Grid Identity
    story.append(Paragraph("1. Consumer & Smart Meter Identity", h2_style))
    id_data = [
        [Paragraph("Consumer ID:", bold_style), Paragraph(str(cid), body_style),
         Paragraph("Smart Meter ID:", bold_style), Paragraph(meter_id, body_style)],
        [Paragraph("Category / Tariff:", bold_style), Paragraph(str(cat).title(), body_style),
         Paragraph("Time Window:", bold_style), Paragraph("120-Day Ingestion Window", body_style)],
        [Paragraph("Grid Feeder:", bold_style), Paragraph(str(feeder), body_style),
         Paragraph("Substation Transformer:", bold_style), Paragraph(str(transformer), body_style)],
    ]
    id_table = Table(id_data, colWidths=[110, 160, 130, 140])
    id_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#f1f5f9')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(id_table)
    story.append(Spacer(1, 8))

    # Calculate Historical vs Actual Consumption Comparison
    base_vals = [
        float(b.get("expected_kwh", b.get("baseline_kwh", 10.5)) if isinstance(b, dict) else getattr(b, "expected_kwh", getattr(b, "baseline_kwh", 10.5)))
        for b in (baseline or [])
    ]
    avg_base = sum(base_vals) / len(base_vals) if base_vals else 10.5

    actual_vals = []
    if readings:
        for r in readings:
            v = r.get("kwh") if isinstance(r, dict) else getattr(r, "kwh", None)
            if v is not None:
                actual_vals.append(float(v))
    avg_actual = sum(actual_vals) / len(actual_vals) if actual_vals else avg_base
    recent_actual = sum(actual_vals[-14:]) / len(actual_vals[-14:]) if len(actual_vals) >= 14 else avg_actual

    diff_kwh = recent_actual - avg_base
    deviation_pct = (diff_kwh / avg_base) * 100 if avg_base > 0 else 0

    if recent_actual < 0.1 and avg_base > 2.0:
        pattern = "Zero Flatline (Sensor Inactive or Complete Bypass)"
    elif deviation_pct < -35:
        pattern = "Abrupt Step Down (Suspected Shunt/Tamper)"
    elif deviation_pct > 35:
        pattern = "Elevated Abnormal Draw (Unregistered Load)"
    elif abs(deviation_pct) <= 15:
        pattern = "Stable Periodic Tracking (Normal Profile)"
    else:
        pattern = "Seasonal / Moderate Load Variance"

    # Section 2: Historical vs. Current Consumption & Behavioural Analysis
    story.append(Paragraph("2. Historical vs. Current Consumption & Behavioural Pattern", h2_style))
    comp_data = [
        [Paragraph("Historical Expected Baseline:", bold_style), Paragraph(f"{avg_base:.2f} kWh / day", body_style),
         Paragraph("Current Observed Consumption:", bold_style), Paragraph(f"{recent_actual:.2f} kWh / day", body_style)],
        [Paragraph("Consumption Deviation:", bold_style), Paragraph(f"<b><font color='{risk_color}'>{deviation_pct:+.1f}% ({diff_kwh:+.2f} kWh)</font></b>", body_style),
         Paragraph("Behavioural Pattern:", bold_style), Paragraph(f"<b>{pattern}</b>", body_style)],
    ]
    comp_table = Table(comp_data, colWidths=[160, 110, 150, 120])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#f1f5f9')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(comp_table)
    story.append(Spacer(1, 8))

    # Section 3: Anomaly Assessment
    story.append(Paragraph("3. Loss Assessment & Diagnosis", h2_style))
    score_str = f"{float(score):.2f}" if score is not None else "—"
    conf_str = f"{float(conf)*100:.1f}%" if conf is not None else "—"
    loss_str = f"₹{float(loss):,.2f}" if loss is not None else "₹0.00"
    prio_str = f"{float(priority):.2f}" if priority is not None else "—"
    flagged_str = flagged.strftime('%Y-%m-%d %H:%M') if isinstance(flagged, datetime) else str(flagged or "Recent")

    assess_data = [
        [Paragraph("Risk Classification:", bold_style), Paragraph(f"<b><font color='{risk_color}'>{str(risk).upper()}</font></b>", body_style),
         Paragraph("Investigation Status:", bold_style), Paragraph(str(status), body_style)],
        [Paragraph("Attributed Cause:", bold_style), Paragraph(f"<b>{cause}</b>", body_style),
         Paragraph("First Flagged:", bold_style), Paragraph(flagged_str, body_style)],
        [Paragraph("Anomaly Score:", bold_style), Paragraph(score_str, body_style),
         Paragraph("Model Confidence:", bold_style), Paragraph(conf_str, body_style)],
        [Paragraph("Estimated Financial Loss:", bold_style), Paragraph(f"<b>{loss_str}</b>", body_style),
         Paragraph("Priority Score:", bold_style), Paragraph(prio_str, body_style)],
    ]
    assess_table = Table(assess_data, colWidths=[120, 150, 130, 140])
    assess_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#f1f5f9')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(assess_table)
    story.append(Spacer(1, 8))

    # Parse Evidence & Counter-Evidence
    def _parse_list(val):
        if not val:
            return []
        if isinstance(val, list):
            return val
        if isinstance(val, str):
            try:
                parsed = json.loads(val)
                if isinstance(parsed, list):
                    return parsed
                return [val]
            except Exception:
                return [val]
        return [str(val)]

    evidence_list = _parse_list(getattr(case, "evidence", None) if not isinstance(case, dict) else case.get("evidence"))
    counter_list = _parse_list(getattr(case, "counter_evidence", None) if not isinstance(case, dict) else case.get("counter_evidence"))

    # Section 4: Evidence
    story.append(Paragraph("4. Supporting Evidence (Why Flagged)", h2_style))
    if evidence_list:
        for item in evidence_list:
            story.append(Paragraph(f"&bull;&nbsp; {item}", evidence_style))
    else:
        story.append(Paragraph("No direct anomaly indicators noted.", body_style))
    story.append(Spacer(1, 6))

    # Section 5: Counter-Evidence
    story.append(Paragraph("5. Counter-Evidence (Why Not Alternative Causes)", h2_style))
    if counter_list:
        for item in counter_list:
            story.append(Paragraph(f"&check;&nbsp; {item}", counter_style))
    else:
        story.append(Paragraph("No counter-evidence evaluated.", body_style))
    story.append(Spacer(1, 6))

    # Section 6: Recommended Action
    story.append(Paragraph("6. Recommended Action for Field Inspection", h2_style))
    action_box = [
        [Paragraph(f"<b>Recommended Action:</b> {action}", body_style)],
    ]
    if note:
        action_box.append([Paragraph(f"<b>Investigator Notes:</b> {note}", body_style)])
    action_table = Table(action_box, colWidths=[540])
    action_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(action_table)
    story.append(Spacer(1, 8))

    # Section 7: Baseline Telemetry Profile
    if baseline:
        story.append(Paragraph("7. Historical Baseline Profile (Recent Excerpt)", h2_style))
        b_rows = [[Paragraph("Timestamp", bold_style), Paragraph("Expected Consumption (kWh)", bold_style)]]
        for b in baseline[:5]:
            ts_val = b.get("ts") if isinstance(b, dict) else getattr(b, "ts", "")
            if isinstance(ts_val, datetime):
                ts_str = ts_val.strftime("%Y-%m-%d %H:%M")
            else:
                ts_str = str(ts_val)
            kwh_val = (
                b.get("expected_kwh", b.get("baseline_kwh", ""))
                if isinstance(b, dict)
                else getattr(b, "expected_kwh", getattr(b, "baseline_kwh", ""))
            )
            kwh_str = f"{float(kwh_val):.2f} kWh" if kwh_val != "" and kwh_val is not None else "—"
            b_rows.append([Paragraph(ts_str, body_style), Paragraph(kwh_str, body_style)])
        
        b_table = Table(b_rows, colWidths=[270, 270])
        b_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(b_table)

    doc.build(story)
    return buffer.getvalue()
