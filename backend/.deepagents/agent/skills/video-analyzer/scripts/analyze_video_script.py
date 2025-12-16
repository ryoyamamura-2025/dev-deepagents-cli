import argparse
import json
import os
from datetime import datetime
import time

def generate_dummy_data(title, mode):
    base_data = {
        "video_title": title,
        "mode": mode,
        "timestamp": datetime.now().isoformat()
    }

    if mode == "summary":
        base_data["summary"] = f"This is a dummy summary for video '{title}'. The video discusses key topics regarding AI and automation."
    
    elif mode == "manual":
        base_data["steps"] = [
            {"step": 1, "description": "Open the application."},
            {"step": 2, "description": f"Load the video file: {title}."},
            {"step": 3, "description": "Click the 'Analyze' button."},
            {"step": 4, "description": "Wait for processing to complete."}
        ]
        
    elif mode == "questions":
        base_data["questions"] = [
            {"q": "What is the main topic of the video?", "a": "The main topic is strictly confidential (Dummy answer)."},
            {"q": "How long is the video?", "a": "10 minutes and 30 seconds."},
            {"q": "What tool is recommended?", "a": "The 'Video Analyzer' tool."}
        ]
    else:
        base_data["error"] = "Unknown mode"
        
    return base_data

def main():
    parser = argparse.ArgumentParser(description="Analyze video (Script Pattern)")
    parser.add_argument("--title", required=True, help="Video title (e.g., test.mp4)")
    parser.add_argument("--mode", required=True, choices=["summary", "manual", "questions"], help="Analysis mode")
    
    args = parser.parse_args()
    
    print(f"Starting analysis for {args.title} in {args.mode} mode...")
    # Simulate processing time
    time.sleep(2)
    
    # Generate data
    data = generate_dummy_data(args.title, args.mode)
    
    # Setup output path
    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output_dir = f"/workspace/app/flow/video-analyzer/{timestamp_str}"
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, "result.json")
    
    # Write to file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print(f"Analysis completed successfully.")
    print(f"Output saved to: {output_file}")

if __name__ == "__main__":
    main()
