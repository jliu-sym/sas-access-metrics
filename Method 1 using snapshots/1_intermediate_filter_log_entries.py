# Goal is to extract this
# Log Entry
# 2025-07-09T03:56:54.082-04:00 botguardian2 <info> mast  39647 #6009 _siomon_  level req    0000000000 1 0
# 2025-07-09T03:56:54.083-04:00 botguardian2 <info> mast  39648 #6010 _siomon_  level key    1111111111
# 2025-07-09T03:56:54.083-04:00 botguardian2 <info> mast  39651 #6011 _siomon_  Z1 aisle req    0000000000 0000000000 0000000000 0000000000 0000000001 0000000011 0000000000 0000000000 0000000000 0000000000 0000000000 0000000000 0000000000 0000000000 000
# 2025-07-09T03:56:54.083-04:00 botguardian2 <info> mast  39653 #6013 _siomon_  Z1 aisle key    1111111111 1111111111 1111111111 1111111111 1111111111 1111111111 1111111111 1111111111 1111111111 1111111111 1111111111 1111111111 1111111111 1111111111 111

# Step 1: Filter raw log to only relevant Z1-Z3 aisle req/key entries

import csv
import re

# log_file = 'scpu.log'
log_file = 'scpu-20250710.log'
filtered_output = 'intermediate_filtered_log.csv'

include_keywords = [
    "Z1 aisle req", "Z1 aisle key",
    "Z1 dwy req", "Z1 dwy door", "Z1 dwy state",
    "Z2 aisle req", "Z2 aisle key",
    "Z2 dwy req", "Z2 dwy door", "Z2 dwy state",
    "Z3 aisle req", "Z3 aisle key",
    "Z3 dwy req", "Z3 dwy door", "Z3 dwy state",
    "level req", "level key"
]

exclude_phrases = [
    "bot id requested",
    "requested to renew lease",
    "Accountant requested codeplate",
    "Vendor-Class-ID requested",
    "Options requested",
    "SafetyTimeManager",
    "_botLift_", "Botlift",
    "Unsafe level",
    "Unsafe cell"
]

include_pattern = re.compile(r'\b(?:' + '|'.join(re.escape(k) for k in include_keywords) + r')\b', re.IGNORECASE)
exclude_pattern = re.compile(r'|'.join(re.escape(p) for p in exclude_phrases), re.IGNORECASE)

filtered_lines = []
with open(log_file, 'r') as f:
    for line in f:
        line_lower = line.lower()
        if include_pattern.search(line) and not exclude_pattern.search(line_lower):
            # Clean the hostname: botguardianX.mservices.xxx06020-c.sxxxxxxx → botguardianX
            cleaned_line = re.sub(r'(\bbotguardian\d+)\.mservices\.[^\s]+', r'\1', line.strip())
            filtered_lines.append([cleaned_line])

with open(filtered_output, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Log Entry'])
    writer.writerows(filtered_lines)

print(f"Filtered entries written to {filtered_output}")
