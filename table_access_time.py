import pandas as pd

def compute_transition_deltas(transitions_csv, output_csv='transition_deltas.csv'):
    df = pd.read_csv(transitions_csv, parse_dates=True)

    # Parse all columns that look like datetimes
    for col in df.columns:
        if col not in ['Location']:
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass

    output_rows = []
    for idx, row in df.iterrows():
        location = row['Location']
        if location.startswith("Level"):
            t_request = row.get('Cycle Start', None)  # Start from Cycle Start for Level
            t_localized_bots = row.get('CLOSED to PREPARING', None)
            t_safe_access = row.get('PREPARING to SAFE_ACCESS_GRANTED', None)

            delta_closed = None if pd.notnull(t_request) else None
            delta_localized_bots = (t_localized_bots - t_request).total_seconds() if pd.notnull(t_localized_bots) and pd.notnull(t_request) else None
            delta_safe_access = (t_safe_access - t_request).total_seconds() if pd.notnull(t_safe_access) and pd.notnull(t_request) else None
            delta_access_empty = None  # not meaningful for Level

        else:
            t_request = row.get('Cycle Start', None)  # Use Cycle Start for Driveway/Aisle for consistency
            t_closed = row.get('REQUESTED to CLOSED', None)
            t_access_empty = row.get('CLOSED_EMPTY to ACCESS_GRANTED_EMPTY', None)
            t_localized_bots = row.get('CLOSED to PREPARING', None)
            t_safe_access = row.get('PREPARING to SAFE_ACCESS_GRANTED', None)

            delta_closed = (t_closed - t_request).total_seconds() if pd.notnull(t_closed) and pd.notnull(t_request) else None
            delta_access_empty = (t_access_empty - t_request).total_seconds() if pd.notnull(t_access_empty) and pd.notnull(t_request) else None
            delta_localized_bots = (t_localized_bots - t_request).total_seconds() if pd.notnull(t_localized_bots) and pd.notnull(t_request) else None
            delta_safe_access = (t_safe_access - t_request).total_seconds() if pd.notnull(t_safe_access) and pd.notnull(t_request) else None

        request_start_short = pd.to_datetime(t_request).strftime('%Y-%m-%d %H:%M') if pd.notnull(t_request) else None

        output_rows.append({
            'Location': location,
            'Request Start (YYYY-MM-DD HH:MM)': request_start_short,
            'Time from Request to Gate Closed (s)': delta_closed,
            'Time from Request to Localizatoin Complete (s)': delta_localized_bots,
            'Time from Request to Safe Access Granted (s)': delta_safe_access,
            'Time from Request to Access Granted via "empty button" (s)': delta_access_empty
        })

    output_df = pd.DataFrame(output_rows)
    output_df.to_csv(output_csv, index=False)
    return output_csv
