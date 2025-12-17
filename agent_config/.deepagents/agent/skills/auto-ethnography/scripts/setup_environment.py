import os
from datetime import datetime
from zoneinfo import ZoneInfo

def setup_folders():
    jst = ZoneInfo('Asia/Tokyo')
    date_str = datetime.now(jst).strftime('%Y-%m-%d_%H%M%S')
    base_path = f"/workspace/app/flow/ethnography-research/{date_str}"
    
    subdirs = ["interview_logs", "interview_reports"]
    
    for subdir in subdirs:
        path = os.path.join(base_path, subdir)
        os.makedirs(path, exist_ok=True)
        print(f"Created directory: {path}")
    
    return base_path

if __name__ == "__main__":
    setup_folders()