import argparse
import json
import os
from datetime import datetime

def load_history(history_path):
    if os.path.exists(history_path):
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"processed_files": [], "last_updated": None}
    return {"processed_files": [], "last_updated": None}

def save_history(history_path, history):
    history["last_updated"] = datetime.now().isoformat()
    # Ensure processed_files is a list and sorted for consistency
    history["processed_files"] = sorted(list(set(history.get("processed_files", []))))
    
    # Create directory for history file if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(history_path)), exist_ok=True)
    
    with open(history_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def get_files(log_dir):
    files = []
    if not os.path.exists(log_dir):
        return []
        
    for root, _, filenames in os.walk(log_dir):
        for filename in filenames:
            # Skip hidden files
            if not filename.startswith('.'):
                files.append(os.path.abspath(os.path.join(root, filename)))
    return files

def main():
    parser = argparse.ArgumentParser(description="Manage log files for persona updates.")
    parser.add_argument("--log-dir", required=True, help="Directory containing log files")
    parser.add_argument("--history-file", required=True, help="JSON file to store processing history")
    parser.add_argument("--action", choices=["check", "mark"], required=True, help="Action: 'check' for new files, 'mark' to update history")
    parser.add_argument("--files", nargs="*", help="Specific files to mark as processed (absolute paths)")
    
    args = parser.parse_args()
    
    history = load_history(args.history_file)
    processed_set = set(history.get("processed_files", []))
    
    if args.action == "check":
        all_files = get_files(args.log_dir)
        new_files = [f for f in all_files if f not in processed_set]
        
        result = {
            "status": "success",
            "new_files_count": len(new_files),
            "new_files": new_files,
            "processed_count": len(processed_set),
            "total_files_in_dir": len(all_files)
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    elif args.action == "mark":
        files_to_mark = args.files
        
        # If no specific files provided, mark ALL currently new files found in log-dir
        if not files_to_mark:
            all_files = get_files(args.log_dir)
            files_to_mark = [f for f in all_files if f not in processed_set]
            
        count = 0
        current_processed = history.get("processed_files", [])
        
        for f in files_to_mark:
            abs_path = os.path.abspath(f)
            if abs_path not in processed_set:
                current_processed.append(abs_path)
                processed_set.add(abs_path) # Update set to prevent duplicates in this loop
                count += 1
        
        history["processed_files"] = current_processed
        save_history(args.history_file, history)
        
        print(json.dumps({
            "status": "success", 
            "marked_count": count,
            "message": f"{count} files marked as processed.",
            "total_processed": len(history["processed_files"])
        }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
