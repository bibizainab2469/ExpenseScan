import json
from datetime import datetime

AUDIT_FILE = "audit_log.json"

def log_entry(action, data):
    log = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "data": data
    }
    
    try:
        with open(AUDIT_FILE, "r") as f:
            logs = json.load(f)
    except:
        logs = []
    
    logs.append(log)
    
    with open(AUDIT_FILE, "w") as f:
        json.dump(logs, f, indent=2)
    
    print(f"[AUDIT] {log['timestamp']} - {action}")