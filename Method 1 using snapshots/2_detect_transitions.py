# Transition detector with 3-part dwy (req, door, state)

import csv
import re

filtered_input = 'intermediate_filtered_log.csv'
final_output = 'filtered_log_transitions.csv'

# Zone-type definitions: (label, req keyword, door keyword, state keyword)
zone_types = [
    ('Z1_aisle',      'Z1 aisle req',   'Z1 aisle key',    None),
    ('Z2_aisle',      'Z2 aisle req',   'Z2 aisle key',    None),
    ('Z3_aisle',      'Z3 aisle req',   'Z3 aisle key',    None),
    ('Z1_dwy',        'Z1 dwy req',     'Z1 dwy door',     'Z1 dwy state'),
    ('Z2_dwy',        'Z2 dwy req',     'Z2 dwy door',     'Z2 dwy state'),
    ('Z3_dwy',        'Z3 dwy req',     'Z3 dwy door',     'Z3 dwy state'),
    ('level',         'level req',      'level key',       None),
]

# Track states
prev_req_bits = {label: None for label, _, _, _ in zone_types}
has_seen_initial = {label: False for label, _, _, _ in zone_types}
has_seen_valid_zero = {label: False for label, _, _, _ in zone_types}
capture_next_door = {label: False for label, _, door, _ in zone_types if door}
capture_next_state = {label: False for label, _, _, state in zone_types if state}

filtered_lines = []

with open(filtered_input, 'r') as f:
    reader = csv.reader(f)
    next(reader)  # Skip header

    for row in reader:
        line = row[0]

        for label, req_tag, door_tag, state_tag in zone_types:
            # Check request
            if req_tag in line:
                match = re.search(rf'{re.escape(req_tag)}\s+(.*)', line)
                if match:
                    bit_string = match.group(1).replace(' ', '')

                    if not has_seen_initial[label]:
                        filtered_lines.append([line.strip()])
                        prev_req_bits[label] = bit_string
                        has_seen_initial[label] = True
                        if '1' not in bit_string:
                            has_seen_valid_zero[label] = True
                        continue

                    if bit_string != prev_req_bits[label]:
                        if has_seen_valid_zero[label] and '1' in bit_string:
                            filtered_lines.append([line.strip()])
                            if door_tag:
                                capture_next_door[label] = True
                            if state_tag:
                                capture_next_state[label] = True
                        if '1' not in bit_string:
                            has_seen_valid_zero[label] = True
                        prev_req_bits[label] = bit_string

            elif door_tag and door_tag in line and capture_next_door.get(label, False):
                filtered_lines.append([line.strip()])
                capture_next_door[label] = False

            elif state_tag and state_tag in line and capture_next_state.get(label, False):
                filtered_lines.append([line.strip()])
                capture_next_state[label] = False

# Write to final CSV
with open(final_output, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Log Entry'])
    writer.writerows(filtered_lines)

print(f"Transitions (aisle, dwy, level) with doors and states written to {final_output}")
