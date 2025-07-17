import csv
import re
import os

def extract_and_filter_logs(log_files, output_csv='filtered_log_transitionStates.csv'):
    """
    Takes a list of log file paths and writes a single filtered CSV.
    """
    include_keywords = [
        "LockedSetSafetyIOContext",
        "LockedSetSafeAccessState"
    ]
    exclude_phrases = [
        # "Driveway",
        # "Level", 
        # "Aisle", 
        "bot id requested", "requested to renew lease",
        "Accountant requested codeplate", "Vendor-Class-ID requested", "Options requested",
        "SafetyTimeManager", "_botLift_", "Botlift", "Unsafe level", "Unsafe cell"
    ]

    include_pattern = re.compile(r'\b(?:' + '|'.join(re.escape(k) for k in include_keywords) + r')\b', re.IGNORECASE)
    exclude_pattern = re.compile(r'|'.join(re.escape(p) for p in exclude_phrases), re.IGNORECASE)

    filtered_lines = []
    for log_file in log_files:
        with open(log_file, 'r') as f:
            for line in f:
                line_lower = line.lower()
                if include_pattern.search(line) and not exclude_pattern.search(line_lower):
                    cleaned_line = re.sub(r'(\bbotguardian\d+)\.mservices\.[^\s]+', r'\1', line.strip())
                    filtered_lines.append([cleaned_line])
        print(f"Filtered log written from {log_file}")

    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Log Entry'])
        writer.writerows(filtered_lines)
    print(f"Filtered log written to {output_csv} ({len(filtered_lines)} lines)")
    return output_csv
