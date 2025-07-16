# SAS data analysis pipeline
# https://symboticllc.sharepoint.com/:w:/r/Safety%20and%20Compliance/Shared%20Documents/Safe%20Access%20System/SAS%20Design%20and%20Instruction%20Documents/BotGuardian/Safety%20System%20Design/SAS%20theory%20of%20operation/Safety%203.0%20TheoryOfOperations%20-%20gliu_working_20240822.docx?d=w8f249b63963b45a2aaac984e1f135903&csf=1&web=1&e=1LAyux

# step 1:
# filter out rows of the scpu.log containing keywords of access state transitions based on this confluence: https://symbotic.atlassian.net/wiki/spaces/SAS/pages/19759629/ACCESS+STATE+MACHINE

# output a more concise logfile of just access transitions

# step 2:

# tbd
# analyze data structure and attempt to compute dT between transitions of states
# 1_sasAccessTimeDataExtraction.py

import os

from sasAccessTimeDataExtraction import extract_and_filter_logs
from reshape_list_to_table import reshape_log_to_table
from table_access_time import compute_transition_deltas
from histogram import plot_histograms
from AccessGrantedTimeline import plot_access_granted_timeline

def run_combined_pipeline(filtered_csv, base='all_logs'):
    transitions_csv = f"{base}_parsed_transitions.csv"
    deltas_csv = f"{base}_transition_deltas.csv"
    histogram_png = f"{base}_histogram.png"
    timeline_png = f"{base}_access_granted_timeline.png"
    
    reshape_log_to_table(filtered_csv, output_csv=transitions_csv)
    compute_transition_deltas(transitions_csv, output_csv=deltas_csv)
    plot_histograms(deltas_csv, png_out=histogram_png)
    plot_access_granted_timeline(transitions_csv, png_out=timeline_png)

if __name__ == "__main__":
    logfiles = [
                # 'scpu.log',
                'scpu-20250710.log'
                ]
    # Prepend 'raw logs/' to each filename
    logfiles = [os.path.join('raw logs', f) for f in logfiles]

    # filtered_csv = extract_and_filter_logs(logfiles, output_csv='all_logs_filtered.csv')

    filtered_csv = 'all_logs_filtered.csv'

    run_combined_pipeline(filtered_csv, base='all_logs')
