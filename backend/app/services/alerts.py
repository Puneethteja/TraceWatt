from ..db import insert_alert

def handle_alert_transition(detection, old_risk=None, old_cause=None, is_simulation=False):
    # Determine if we should alert
    should_alert = False
    
    if is_simulation:
        # Every simulation run generates/updates an alert for visibility
        should_alert = True
    elif detection.risk_level == "High" and old_risk != "High":
        should_alert = True
    elif detection.risk_level == "High" and old_risk == "High" and old_cause != detection.cause:
        should_alert = True
    elif detection.risk_level in ["High", "Medium"] and old_risk not in ["High", "Medium"]:
        should_alert = True
        
    if should_alert:
        insert_alert(detection)
