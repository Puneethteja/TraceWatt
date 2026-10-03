def render_report(case, consumer, baseline) -> bytes:
    report_text = f"""
    TraceWatt Investigation Report
    ==============================
    
    Consumer ID: {consumer.id}
    Category: {consumer.category}
    Feeder: {consumer.feeder_id}
    Transformer: {consumer.transformer_id}
    
    Case Details:
    -------------
    Status: {case.status}
    Risk Level: {case.risk_level}
    Cause: {case.cause}
    Anomaly Score: {case.anomaly_score}
    Confidence: {case.confidence}
    First Flagged: {case.first_flagged_at}
    Last Updated: {case.last_updated_at}
    
    Investigation Notes:
    --------------------
    {case.note or 'No notes provided.'}
    
    Evidence:
    ---------
    {case.evidence or 'None'}
    
    Counter-Evidence:
    -----------------
    {case.counter_evidence or 'None'}
    
    Recommended Action:
    -------------------
    {case.recommended_action or 'None'}
    
    Baseline Data (First 5 records):
    --------------------------------
"""
    if baseline:
        for b in baseline[:5]:
<<<<<<< HEAD
            ts_val = b.get("ts") if isinstance(b, dict) else getattr(b, "ts", "")
            kwh_val = (
                b.get("expected_kwh", b.get("baseline_kwh", ""))
                if isinstance(b, dict)
                else getattr(b, "expected_kwh", getattr(b, "baseline_kwh", ""))
            )
            report_text += f"    {ts_val}: {kwh_val} kWh\n"
=======
            ts = b.get('ts') if isinstance(b, dict) else b.ts
            kwh = b.get('expected_kwh') if isinstance(b, dict) else b.expected_kwh
            report_text += f"    {ts}: {kwh} kWh\n"
>>>>>>> 533fc623c44f4b3e0f731bea39c6c27377d94866
        if len(baseline) > 5:
            report_text += "    ... and more\n"
    else:
        report_text += "    No baseline data available.\n"
        
    # Returning as utf-8 encoded bytes. 
    # In a real environment, you'd use reportlab or fpdf here to generate a valid PDF byte stream.
    return report_text.encode('utf-8')
