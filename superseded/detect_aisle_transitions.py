# Step 2: Process filtered log to extract transitions from all-zero to something with 1

import csv
import re

filtered_input = 'intermediate_filtered_log.csv'
final_output = 'filtered_log_aisle_key_transitions.csv'

zones = ['Z1', 'Z2', 'Z3']
prev_req_bits = {zone: None for zone in zones}
has_seen_valid_zero = {zone: False for zone in zones}  # New flag per zone
capture_next_key = {zone: False for zone in zones}

filtered_lines = []

with open(filtered_input, 'r') as f:
    reader = csv.reader(f)
    next(reader)  # Skip header

    for row in reader:
        line = row[0]
        for zone in zones:
            req_tag = f"{zone} aisle req"
            key_tag = f"{zone} aisle key"

            if req_tag in line:
                match = re.search(rf'{re.escape(req_tag)}\s+(.*)', line)
                if match:
                    bit_string = match.group(1).replace(' ', '')

                    # If it's the very first req and contains '1', ignore
                    if prev_req_bits[zone] is None:
                        prev_req_bits[zone] = bit_string
                        if '1' not in bit_string:
                            has_seen_valid_zero[zone] = True
                        continue

                    if bit_string != prev_req_bits[zone]:
                        # Only count transition if we’ve previously seen a valid all-zero state
                        if has_seen_valid_zero[zone] and '1' in bit_string:
                            filtered_lines.append([line.strip()])
                            capture_next_key[zone] = True
                        # Update state and track if it’s a new zero
                        if '1' not in bit_string:
                            has_seen_valid_zero[zone] = True
                        prev_req_bits[zone] = bit_string

            elif key_tag in line and capture_next_key[zone]:
                filtered_lines.append([line.strip()])
                capture_next_key[zone] = False

# Write to final CSV
with open(final_output, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Log Entry'])
    writer.writerows(filtered_lines)

print(f"Aisle 0→1 transitions written to {final_output}")
