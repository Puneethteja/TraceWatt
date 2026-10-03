from ..db import insert_alert

def handle_alert_transition(detection, old_risk, old_cause=None):
    # Determine if we should alert
    should_alert = False
    
    if detection.risk_level == "High" and old_risk != "High":
        should_alert = True
    elif detection.risk_level == "High" and old_risk == "High" and old_cause != detection.cause:
        should_alert = True
        
    if should_alert:
        insert_alert(detection)
