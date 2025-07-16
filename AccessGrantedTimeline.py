import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_access_granted_timeline(transitions_csv, png_out):

    # Load data
    df = pd.read_csv(transitions_csv, parse_dates=[
        'OPEN to REQUESTED',
        'REQUESTED to CLOSED',
        'CLOSED to PREPARING',
        'PREPARING to SAFE_ACCESS_GRANTED'
    ])

    # Filter for cycles where PREPARING to SAFE_ACCESS_GRANTED exists
    valid_cycles = df[~df['PREPARING to SAFE_ACCESS_GRANTED'].isna()].copy()

    # Calculate intervals
    part1 = (valid_cycles['REQUESTED to CLOSED'] - valid_cycles['OPEN to REQUESTED']).dt.total_seconds()
    part2 = (valid_cycles['CLOSED to PREPARING'] - valid_cycles['REQUESTED to CLOSED']).dt.total_seconds()
    part3 = (valid_cycles['PREPARING to SAFE_ACCESS_GRANTED'] - valid_cycles['CLOSED to PREPARING']).dt.total_seconds()

    # Replace negative or missing intervals with zero
    part1 = part1.fillna(0).clip(lower=0)
    part2 = part2.fillna(0).clip(lower=0)
    part3 = part3.fillna(0).clip(lower=0)

    N = len(valid_cycles)
    y_pos = np.arange(N)

    plt.figure(figsize=(10, max(4, N//3)))

    plt.barh(y_pos, part1, color='tab:blue', edgecolor='k', label='Requested → "Symbot Gate" Closed')
    plt.barh(y_pos, part2, left=part1, color='tab:orange', edgecolor='k', label='Closed → Preparing (localization complete)')
    plt.barh(y_pos, part3, left=part1+part2, color='tab:green', edgecolor='k', label='Preparing → Safe Access Granted (door can open)')

    plt.yticks(y_pos, valid_cycles['Location'] + ' | ' + valid_cycles['OPEN to REQUESTED'].dt.strftime('%Y-%m-%d %H:%M'))
    plt.xlabel('Seconds')
    plt.title('Time to Safe Access Granted (Stacked per Transition)')
    plt.legend(loc='upper right')
    plt.tight_layout()
    plt.savefig(png_out)
    plt.show()
