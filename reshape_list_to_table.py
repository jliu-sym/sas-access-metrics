import re
import pandas as pd

def reshape_log_to_table(filtered_csv, output_csv='parsed_transitions.csv'):
    # --- Load and Parse ---

    with open(filtered_csv, encoding='utf-8') as f:
        lines = f.readlines()
    if lines[0].strip().lower().startswith("log entry"):
        lines = lines[1:]

    log_pattern = re.compile(
        r'"(?P<timestamp>[\d\-:T\.]+[+-]\d{2}:\d{2}) .*?'
        r'((Driveway (?P<driveway>\d+), Zone (?P<zone>\d+), Cell (?P<cell>\d+))'
        r'|(Aisle (?P<aisle>\d+), Zone (?P<azone>\d+))) '
        r'transitioned from (?P<from_state>\w+) to (?P<to_state>[\w_]+)"'
    )

    entries = []
    for line in lines:
        m = log_pattern.search(line)
        if m:
            timestamp = m.group('timestamp')
            if m.group('driveway'):
                location = f"Driveway {m.group('driveway')}, Zone {m.group('zone')}, Cell {m.group('cell')}"
            elif m.group('aisle'):
                location = f"Aisle {m.group('aisle')}, Zone {m.group('azone')}"
            else:
                continue
            from_state = m.group('from_state')
            to_state = m.group('to_state')
            transition = f"{from_state} to {to_state}"
            entries.append({
                'location': location,
                'timestamp': timestamp,
                'transition': transition
            })

    df = pd.DataFrame(entries)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # --- Main logic: Per-cycle search ---

    transitions_of_interest = [
        # Driveway transitions
        "ACCESS_GRANTED_EMPTY to GATE_CLOSED",
        "ACCESS_GRANTED_EMPTY to OPEN",
        "ACCESS_GRANTED_EMPTY to REQUESTED",
        "BYPASSED to OPEN",
        "BYPASSED to REQUESTED",
        "CLOSED to ACCESS_GRANTED_EMPTY",
        "CLOSED to CLOSED_EMPTY",
        "CLOSED to OPEN",
        "CLOSED to PREPARING",
        "CLOSED_EMPTY to ACCESS_GRANTED_EMPTY",
        "CLOSED_EMPTY to OPEN",
        "GATE_CLOSED to OPEN",
        "OPEN to BYPASSED",
        "OPEN to GATE_CLOSED",
        "OPEN to REQUESTED",
        "PREPARING to SAFE_ACCESS_GRANTED",
        "REQUESTED to ACCESS_GRANTED_EMPTY",
        "REQUESTED to BYPASSED",
        "REQUESTED to CLOSED",
        "REQUESTED to CLOSED_EMPTY",
        "REQUESTED to OPEN",
        "SAFE_ACCESS_GRANTED to OPEN",

        # Aisle transitions (additional transitions)
        "SAFE_ACCESS_GRANTED to REQUESTED",
        "REQUESTED to OPEN",
        "SAFE_ACCESS_GRANTED to GATE_CLOSED",
        "GATE_CLOSED to OPEN",
        "OPEN to CLOSED",
        "CLOSED to SAFE_ACCESS_GRANTED",
        "PREPARING to OPEN",
        "CLOSED to OPEN",
        "PREPARING to GATE_CLOSED",
        "PREPARING to REQUESTED",
        "CLOSED to GATE_CLOSED",
        "CLOSED to REQUESTED"        

        # Not all transitions are shown on the state machine diagram
    ]

    output_rows = []
    for location in df['location'].unique():
        df_loc = df[df['location'] == location].sort_values('timestamp')
        # Find indices of all "OPEN to REQUESTED" events
        open_req_idx = df_loc.index[df_loc['transition'] == "OPEN to REQUESTED"].tolist()
        for i, idx in enumerate(open_req_idx):
            # Define cycle window: start after current "OPEN to REQUESTED", end at next "OPEN to REQUESTED" or end of log
            start_time = df_loc.loc[idx, 'timestamp']
            if i + 1 < len(open_req_idx):
                end_time = df_loc.loc[open_req_idx[i + 1], 'timestamp']
                # Select all rows in (start_time, end_time)
                df_window = df_loc[(df_loc['timestamp'] > start_time) & (df_loc['timestamp'] < end_time)]
            else:
                df_window = df_loc[df_loc['timestamp'] > start_time]

            row = {'Location': location, "OPEN to REQUESTED": start_time}
            for transition in transitions_of_interest:
                if transition == "OPEN to REQUESTED":
                    continue
                t_row = df_window[df_window['transition'] == transition]
                row[transition] = t_row['timestamp'].iloc[0] if not t_row.empty else None
            output_rows.append(row)

    output_df = pd.DataFrame(output_rows)
    columns = ['Location', 'OPEN to REQUESTED'] + [t for t in transitions_of_interest if t != "OPEN to REQUESTED"]
    output_df = output_df[[col for col in columns if col in output_df.columns]]
    output_df.to_csv(output_csv, index=False)
    return output_csv
    print(output_df.head())
