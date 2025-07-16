import re
import pandas as pd

def reshape_log_to_table(filtered_csv, output_csv='parsed_transitions.csv'):
    # --- Load and Parse ---

    with open(filtered_csv, encoding='utf-8') as f:
        lines = f.readlines()
    if lines[0].strip().lower().startswith("log entry"):
        lines = lines[1:]

    log_pattern = re.compile(
        r'^"?'  # Optional starting quote
        r'(?P<timestamp>[\d\-:T\.]+[+-]\d{2}:\d{2}) .*?'
        r'((Driveway (?P<driveway>\d+), Zone (?P<zone>\d+), Cell (?P<cell>\d+))'
        r'|(Aisle (?P<aisle>\d+), Zone (?P<azone>\d+))'
        r'|(Level (?P<level>\d+))) '
        r'transitioned from (?P<from_state>\w+) to (?P<to_state>[\w_]+)'
        r'"?$'   # Optional ending quote
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
            elif m.group('level'):
                location = f"Level {m.group('level')}"
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

        "SAFE_ACCESS_GRANTED to REQUESTED",
        "SAFE_ACCESS_GRANTED to GATE_CLOSED",
        "OPEN to CLOSED",
        "CLOSED to SAFE_ACCESS_GRANTED",
        "PREPARING to OPEN",
        "PREPARING to GATE_CLOSED",
        "PREPARING to REQUESTED",
        "CLOSED to GATE_CLOSED",
        "CLOSED to REQUESTED",

        "OPEN to PREPARING"
    
        # Not all transitions are shown on the state machine diagram
    ]

    output_rows = []
    for location in df['location'].unique():
        df_loc = df[df['location'] == location].sort_values('timestamp')
        # Determine cycle start transition
        if location.startswith("Level"):
            cycle_start = "OPEN to CLOSED"
        else:
            cycle_start = "OPEN to REQUESTED"

        # Find indices of all cycle starts
        cycle_start_idx = df_loc.index[df_loc['transition'] == cycle_start].tolist()
        # For each cycle window...
        for i, idx in enumerate(cycle_start_idx):
            start_time = df_loc.loc[idx, 'timestamp']
            if i + 1 < len(cycle_start_idx):
                end_time = df_loc.loc[cycle_start_idx[i + 1], 'timestamp']
                df_window = df_loc[(df_loc['timestamp'] >= start_time) & (df_loc['timestamp'] < end_time)]
            else:
                df_window = df_loc[df_loc['timestamp'] >= start_time]

            row = {'Location': location, 'Cycle Start': start_time}
            for transition in transitions_of_interest:
                t_row = df_window[df_window['transition'] == transition]
                row[transition] = t_row['timestamp'].iloc[0] if not t_row.empty else None
            output_rows.append(row)

    output_df = pd.DataFrame(output_rows)
    columns = ['Location', 'Cycle Start'] + [t for t in transitions_of_interest]
    output_df = output_df[[col for col in columns if col in output_df.columns]]

    output_df.to_csv(output_csv, index=False)
    return output_csv
    print(output_df.head())
