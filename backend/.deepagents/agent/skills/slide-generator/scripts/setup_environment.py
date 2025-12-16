import os
from datetime import datetime
from zoneinfo import ZoneInfo

def setup_folders():
    jst = ZoneInfo('Asia/Tokyo')
    date_str = datetime.now(jst).strftime('%Y-%m-%d_%H%M%S')
    base_path = f"/workspace/app/flow/slide-generator/{date_str}"
    os.makedirs(base_path, exist_ok=True)    
    print(f"Created directory: {base_path}")

    return base_path

if __name__ == "__main__":
    setup_folders()