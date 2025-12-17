import sys
import json
import argparse
import itertools
import random

def generate_cohort(config_json, count):
    """
    Generate a cohort list based on dimensions, then randomly sample N subjects.
    """
    try:
        data = json.loads(config_json)
    except json.JSONDecodeError:
        print("Error: Invalid JSON string provided.")
        sys.exit(1)

    theme = data.get("theme", "General Inquiry")
    regions = data.get("regions", ["Japan", "US", "EU"])
    industries = data.get("industries", ["General"])
    roles = data.get("roles", ["User"])

    # 1. Generate ALL possible combinations (Cartesian product)
    combinations = list(itertools.product(regions, industries, roles))
    
    # 2. Shuffle to ensure random selection
    random.shuffle(combinations)
    
    # 3. Slice the list to the requested count (safe even if combinations < count)
    selected_combinations = combinations[:count]
    
    cohort_list = []
    for i, (reg, ind, role) in enumerate(selected_combinations):
        subject = {
            "id": f"subject_{i+1:02d}", # e.g., subject_01
            "theme": theme,
            "region": reg,
            "industry": ind,
            "role": role,
            # Create a filename friendly string
            "filename_base": f"{i+1:02d}_{reg}_{ind}_{role}".lower().replace(" ", "_").replace("/", "-")
        }
        cohort_list.append(subject)

    # Output the list as JSON string
    print(json.dumps(cohort_list, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate Ethnography Cohort')
    parser.add_argument('--config', type=str, required=True, 
                        help='JSON string containing definitions.')
    parser.add_argument('--count', type=int, default=10, 
                        help='Number of subjects to randomly select.')
    
    args = parser.parse_args()
    generate_cohort(args.config, args.count)