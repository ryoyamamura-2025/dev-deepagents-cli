import argparse
import json
import os
from datetime import datetime
import time
import random

def mock_api_call(endpoint, payload):
    """
    Simulates an HTTP request to an API endpoint.
    """
    print(f"[API] Sending POST request to {endpoint}")
    print(f"[API] Payload: {json.dumps(payload)}")
    
    # Simulate network latency
    time.sleep(1.5)
    
    # Simulate API logic based on payload
    title = payload.get("filename")
    mode = payload.get("mode")
    
    response_data = {
        "status": "success",
        "job_id": f"job-{random.randint(1000, 9999)}",
        "data": {}
    }

    if mode == "summary":
        response_data["data"]["summary"] = f"[API Result] Summary for {title}: The video content was analyzed via API."
    elif mode == "manual":
        response_data["data"]["steps"] = [
            {"step": 1, "description": "API Step 1"},
            {"step": 2, "description": "API Step 2"},
            {"step": 3, "description": "API Step 3"}
        ]
    elif mode == "questions":
        response_data["data"]["questions"] = [
            {"q": "Generated via API?", "a": "Yes."},
            {"q": "Is this real?", "a": "No, it is a mock."}
        ]
    
    return response_data

def main():
    parser = argparse.ArgumentParser(description="Analyze video (API Pattern)")
    parser.add_argument("--title", required=True, help="Video title")
    parser.add_argument("--mode", required=True, choices=["summary", "manual", "questions"], help="Analysis mode")
    
    args = parser.parse_args()
    
    # Define Mock API Endpoint
    api_endpoint = "https://internal-api.example.com/v1/video/analyze"
    
    # Prepare payload
    payload = {
        "filename": args.title,
        "bucket": "gcs-video-bucket-dummy",
        "mode": args.mode
    }
    
    try:
        # Call Mock API
        response = mock_api_call(api_endpoint, payload)
        
        # Process response
        final_output = {
            "source": "api",
            "video_title": args.title,
            "mode": args.mode,
            "api_job_id": response["job_id"],
            "result": response["data"]
        }
        
        # Setup output path
        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        output_dir = f"/workspace/app/flow/video-analyzer/{timestamp_str}"
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, "result.json")
        
        # Write to file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(final_output, f, indent=2, ensure_ascii=False)
            
        print(f"[API] Response received and saved.")
        print(f"Output saved to: {output_file}")
        
    except Exception as e:
        print(f"Error during API call: {e}")

if __name__ == "__main__":
    main()
