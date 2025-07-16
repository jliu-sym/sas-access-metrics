import csv
from datetime import datetime
from collections import defaultdict

input_filename = 'filtered_log_transitions.csv'
output_filename = 'event_timing.csv'

TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f%z"
zones = ['Z1', 'Z2', 'Z3']

def flatten(s):
    return "".join(s.strip().split())

# Per zone: (zone, idx) => time
req_start = defaultdict(dict)    # driveways
door_end = defaultdict(dict)
state_c = defaultdict(dict)
prev_req = {}
prev_door = {}
prev_state = {}

# Level events (global, not per zone)
level_req_start = {}
level_key_end = {}
prev_level_req = None
prev_level_key = None

# Aisle events (per zone)
aisle_req_start = defaultdict(dict)
aisle_key_end = defaultdict(dict)
prev_aisle_req = {}
prev_aisle_key = {}

with open(input_filename, 'r') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        # Zones (driveway, aisle)
        for zone in zones:
            # Driveway Request
            req_tag = f"{zone} dwy req"
            if req_tag in line:
                ts = datetime.strptime(line.split()[0], TIME_FORMAT)
                bits = flatten(line.split(req_tag)[-1])
                if prev_req.get(zone):
                    for i, (before, after) in enumerate(zip(prev_req[zone], bits)):
                        if before == "0" and after == "1":
                            req_start[zone][i] = ts
                prev_req[zone] = bits

            # Driveway Door
            door_tag = f"{zone} dwy door"
            if door_tag in line:
                ts = datetime.strptime(line.split()[0], TIME_FORMAT)
                bits = flatten(line.split(door_tag)[-1])
                if prev_door.get(zone):
                    for i, (before, after) in enumerate(zip(prev_door[zone], bits)):
                        if before == "1" and after == "0":
                            door_end[zone][i] = ts
                prev_door[zone] = bits

            # Driveway State
            state_tag = f"{zone} dwy state"
            if state_tag in line:
                ts = datetime.strptime(line.split()[0], TIME_FORMAT)
                chars = flatten(line.split(state_tag)[-1])
                if prev_state.get(zone):
                    for i, (before, after) in enumerate(zip(prev_state[zone], chars)):
                        if before != "C" and after == "C":
                            state_c[zone][i] = ts
                prev_state[zone] = chars

            # Aisle Request
            aisle_req_tag = f"{zone} aisle req"
            if aisle_req_tag in line:
                ts = datetime.strptime(line.split()[0], TIME_FORMAT)
                bits = flatten(line.split(aisle_req_tag)[-1])
                if prev_aisle_req.get(zone):
                    for i, (before, after) in enumerate(zip(prev_aisle_req[zone], bits)):
                        if before == "0" and after == "1":
                            aisle_req_start[zone][i] = ts
                prev_aisle_req[zone] = bits

            # Aisle Key
            aisle_key_tag = f"{zone} aisle key"
            if aisle_key_tag in line:
                ts = datetime.strptime(line.split()[0], TIME_FORMAT)
                bits = flatten(line.split(aisle_key_tag)[-1])
                if prev_aisle_key.get(zone):
                    for i, (before, after) in enumerate(zip(prev_aisle_key[zone], bits)):
                        if before == "1" and after == "0":
                            aisle_key_end[zone][i] = ts
                prev_aisle_key[zone] = bits

        # LEVEL section (not per zone)
        if "level req" in line:
            ts = datetime.strptime(line.split()[0], TIME_FORMAT)
            bits = flatten(line.split("level req")[-1])
            bits = bits[:10]  # ignore trailing bits (1 0)
            if prev_level_req:
                for i, (before, after) in enumerate(zip(prev_level_req, bits)):
                    if before == "0" and after == "1":
                        level_req_start[i] = ts
            prev_level_req = bits

        elif "level key" in line:
            ts = datetime.strptime(line.split()[0], TIME_FORMAT)
            bits = flatten(line.split("level key")[-1])
            bits = bits[:10]
            if prev_level_key:
                for i, (before, after) in enumerate(zip(prev_level_key, bits)):
                    if before == "1" and after == "0":
                        level_key_end[i] = ts
            prev_level_key = bits

# Write output CSV
with open(output_filename, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Type', 'Position', 'Start_Time', 'Req_to_Door_s', 'Req_to_C_s', 'Req_to_Key_s'])
    # Driveways
    for zone in zones:
        for i in sorted(req_start[zone]):
            t_req = req_start[zone][i]
            t_door = door_end[zone].get(i)
            t_c = state_c[zone].get(i)
            req_to_door = (t_door - t_req).total_seconds() if t_door else ""
            req_to_c = (t_c - t_req).total_seconds() if t_c else ""
            start_time_str = t_req.isoformat() if t_req else ""
            writer.writerow(['Driveway', f"{zone}-{i+1}", start_time_str, req_to_door, req_to_c, ""])
    # Levels
    for i in sorted(level_req_start):
        t_req = level_req_start[i]
        t_key = level_key_end.get(i)
        req_to_key = (t_key - t_req).total_seconds() if t_key else ""
        start_time_str = t_req.isoformat() if t_req else ""
        writer.writerow(['Level', f"{i+1}", start_time_str, "", "", req_to_key])
    # Aisles
    for zone in zones:
        for i in sorted(aisle_req_start[zone]):
            t_req = aisle_req_start[zone][i]
            t_key = aisle_key_end[zone].get(i)
            req_to_key = (t_key - t_req).total_seconds() if t_key else ""
            start_time_str = t_req.isoformat() if t_req else ""
            writer.writerow(['Aisle', f"{zone}-{i+1}", start_time_str, "", "", req_to_key])

print(f"✅ Done! Results written to '{output_filename}'")
