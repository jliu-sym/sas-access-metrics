import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_access_granted_timeline(transitions_csv, png_out):
    # Load CSV
    df = pd.read_csv(transitions_csv)

    # Parse all relevant columns as datetime
    for col in ['OPEN to REQUESTED', 'REQUESTED to CLOSED', 'CLOSED to PREPARING', 'PREPARING to SAFE_ACCESS_GRANTED']:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    # Drop rows with any NaN in required transitions
    required_cols = ['OPEN to REQUESTED', 'REQUESTED to CLOSED', 'CLOSED to PREPARING', 'PREPARING to SAFE_ACCESS_GRANTED']
    clean_df = df.dropna(subset=required_cols).copy()

    # Sort by request time
    clean_df = clean_df.sort_values('OPEN to REQUESTED').reset_index(drop=True)

    # Compute the duration in seconds for each stage
    part1 = (clean_df['REQUESTED to CLOSED'] - clean_df['OPEN to REQUESTED']).dt.total_seconds()
    part2 = (clean_df['CLOSED to PREPARING'] - clean_df['REQUESTED to CLOSED']).dt.total_seconds()
    part3 = (clean_df['PREPARING to SAFE_ACCESS_GRANTED'] - clean_df['CLOSED to PREPARING']).dt.total_seconds()

    N = len(clean_df)
    y_pos = np.arange(N)

    plt.figure(figsize=(10, max(4, N//3)))

    plt.barh(y_pos, part1, color='tab:blue', edgecolor='k', label='Requested → Gate Closed')
    plt.barh(y_pos, part2, left=part1, color='tab:orange', edgecolor='k', label='Gate Closed → Preparing')
    plt.barh(y_pos, part3, left=part1+part2, color='tab:green', edgecolor='k', label='Preparing → Safe Access Granted')

    plt.xlim([0, 1200])  # Limit x-axis to 1200 sec

    # Label y-axis as location and request time
    labels = clean_df['Location'] + ' | ' + clean_df['OPEN to REQUESTED'].dt.strftime('%Y-%m-%d %H:%M')
    plt.yticks(y_pos, labels)
    plt.xlabel('Seconds')
    plt.title('Time to Safe Access Granted (Stacked per Transition)')
    plt.legend(loc='upper right')
    plt.tight_layout()
    plt.savefig(png_out)
    plt.show()

# Usage:
# plot_access_granted_timeline("YOUR_CSV.csv", "output.png")
