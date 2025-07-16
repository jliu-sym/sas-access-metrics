import pandas as pd

def compute_transition_deltas(transitions_csv, output_csv='transition_deltas.csv'):
    # Load the parsed transitions file
    df = pd.read_csv(transitions_csv, parse_dates=[
        'OPEN to REQUESTED',
        'REQUESTED to CLOSED',
        'CLOSED_EMPTY to ACCESS_GRANTED_EMPTY',
        'REQUESTED to ACCESS_GRANTED_EMPTY', 'CLOSED to ACCESS_GRANTED_EMPTY', # These are illegal transitions?
        'PREPARING to SAFE_ACCESS_GRANTED',
        'CLOSED to PREPARING'
    ])

    output_rows = []
    for idx, row in df.iterrows():
        location = row['Location']
        t_request = row['OPEN to REQUESTED']

        # 1. Time from request to gate closed
        t_closed = row['REQUESTED to CLOSED']
        delta_closed = (t_closed - t_request).total_seconds() if pd.notnull(t_closed) else None

        # 2. Time from request till access granted empty
        t_access_empty = row['CLOSED_EMPTY to ACCESS_GRANTED_EMPTY']
        delta_access_empty = (t_access_empty - t_request).total_seconds() if pd.notnull(t_access_empty) else None

        # 3. Time from request till bots are localized
        t_localized_bots = row['CLOSED to PREPARING']
        delta_localized_bots = (t_localized_bots - t_request).total_seconds() if pd.notnull(t_localized_bots) else None

        # 4. Time from request till safe access granted
        t_safe_access = row['PREPARING to SAFE_ACCESS_GRANTED']
        delta_safe_access = (t_safe_access - t_request).total_seconds() if pd.notnull(t_safe_access) else None

        # Date/Hour/Minute for request start
        request_start_short = t_request.strftime('%Y-%m-%d %H:%M') if pd.notnull(t_request) else None

        output_rows.append({
            'Location': location,
            'Request Start (YYYY-MM-DD HH:MM)': request_start_short,       
            'Time from Request to Gate Closed (s)': delta_closed,
            'Time from Request to Bots Localized (s)': delta_localized_bots,
            'Time from Request to Safe Access Granted (s)': delta_safe_access,
            'Time from Request to Access Granted via "empty button" (s)': delta_access_empty
        })

    output_df = pd.DataFrame(output_rows)
    output_df.to_csv(output_csv, index=False)
    return output_csv
    print(output_df)
