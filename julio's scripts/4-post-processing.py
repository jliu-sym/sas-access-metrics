import pandas as pd
import matplotlib.pyplot as plt
import sys

def clean_raw_data(LOGDATE, SITE_TIME_ZONE):
    dbsre = pd.read_csv(f'disabled_by_sre-{LOGDATE}.log',sep=' ', names=["timestamp","botid"])
    data = pd.read_csv(f'sto_reasons_raw_{LOGDATE}.csv', names=["date","time","botid","access_location","structure_access","sto_reason","last_location_time","gate_close_time"])
    data = data.dropna()
    
    data["sto_time_local"] = data["date"] + "T" + data["time"]
    data["sto_time_local"] = pd.to_datetime(data["sto_time_local"])
    dbsre["timestamp"] = pd.to_datetime(dbsre["timestamp"])
    
    data_sort1 = data.sort_values(by=["botid","sto_time_local"], ascending = [True,True])
    
    data_sort1["deltaT"] = data_sort1.groupby("botid")["sto_time_local"].diff().fillna(pd.Timedelta(seconds=0))
    
    data_sort1['remove'] = (
        # Delta is less than 1.5 minutes
        (data_sort1['deltaT'] < pd.Timedelta(minutes=1.5)) &    
        # Same reason as the previous row
        (data_sort1['sto_reason'] == data_sort1['sto_reason'].shift()) &
        # Same Id as the previous row
        (data_sort1['botid'] == data_sort1['botid'].shift())
    )
        
    data_cleaned = data_sort1[~data_sort1['remove']].drop(columns=['remove'])
    data_cleaned = data_cleaned.drop(["deltaT", "date", "time"],axis=1)
    
    # Extract year
    year = data["sto_time_local"].dt.year.iloc[0]
    
    # Convert gate closure times to datetimes
    data_cleaned.loc[data_cleaned['gate_close_time'] != '-', 'gate_close_UTC'] = pd.to_datetime(
        data_cleaned.loc[data_cleaned['gate_close_time'] != '-', 'gate_close_time'].str.replace(
            r'(\d{2}:\d{2}:\d{2})\[(\d{2}-[a-zA-Z]{3})\]', fr'\2-{year} \1', regex=True), format='%d-%b-%Y %H:%M:%S')
    
    data_cleaned.loc[data_cleaned['last_location_time'] != '-', 'last_location_UTC'] = pd.to_datetime(
        data_cleaned.loc[data_cleaned['last_location_time'] != '-', 'last_location_time'].str.replace(
            r'(\d{2}:\d{2}:\d{2})\[(\d{2}-[a-zA-Z]{3})\]', fr'\2-{year} \1', regex=True), format='%d-%b-%Y %H:%M:%S')
    
    # Convert gate_close and last_location times from UTC time to local time
    data_cleaned["gate_close_local"] = data_cleaned["gate_close_UTC"] + pd.Timedelta(hours=int(SITE_TIME_ZONE))
    data_cleaned["last_location_local"] = data_cleaned["last_location_UTC"] + pd.Timedelta(hours=int(SITE_TIME_ZONE))
    
    # Convert sto_time from local time to UTC time
    data_cleaned["sto_time_UTC"] = data_cleaned["sto_time_local"] - pd.Timedelta(hours=int(SITE_TIME_ZONE))
  
    # Flag initialization
    data_cleaned['disabled_by_sre'] = False
    data_cleaned['gate_deltas'] = ''
    
    # Iterate through each row in df1 where 'reason' is 'aisle' or 'drive'
    for idx, row in data_cleaned[data_cleaned['sto_reason'].isin(['0x60000(Failed_to_localize)'])].iterrows():
        id_value = row['botid']
        gate_time = row['gate_close_local']
        
        matching_rows = dbsre[dbsre['botid'] == id_value]
        
        deltas = []
        for timestamp2 in matching_rows['timestamp']:
            delta = (gate_time - timestamp2).total_seconds()
            if delta > 0 and delta <= 120:
                deltas.append(delta)
        data_cleaned.at[idx,'gate_deltas'] = str(deltas)
        
        # Check the timestamp condition
        disable_flag = any(
            (gate_time - timestamp).total_seconds() <= 30 and (gate_time - timestamp).total_seconds() > 0
            for timestamp in matching_rows['timestamp']
        )
        
        # Set the disable flag in df1
        data_cleaned.at[idx, 'disabled_by_sre'] = disable_flag
    
    data_cleaned = data_cleaned.drop(["gate_close_time", "gate_deltas", "last_location_time"],axis=1)
    
    data_cleaned = data_cleaned.sort_values(by="sto_time_local", ascending=True)
    data_cleaned["sto_time_local"]=data_cleaned["sto_time_local"].dt.strftime('%Y-%m-%d %H:%M:%S')
    data_cleaned["sto_time_UTC"]=data_cleaned["sto_time_UTC"].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    columns_order = ['botid', 'access_location', 'structure_access', 'sto_reason', 'last_location_UTC',
                     'gate_close_UTC', 'sto_time_UTC', 'last_location_local', 'gate_close_local', 
                     'sto_time_local', 'disabled_by_sre']
    
    data_cleaned = data_cleaned[columns_order]
    
    return data_cleaned


def save_plot(data_cleaned, LOGDATE):
    data_cleaned.loc[data_cleaned['disabled_by_sre'] == True, 'sto_reason'] = 'Disabled_by_SRE'
    
    data_cleaned['sto_time_local'] = pd.to_datetime(data_cleaned['sto_time_local'])
    data_cleaned['hour_group'] = data_cleaned['sto_time_local'].dt.floor('h')  # Round to the nearest hour
    
    category_counts = data_cleaned.groupby(['hour_group', 'sto_reason'])['botid'].nunique().unstack(fill_value=0)
    
    # Represent 25 hours (3AM to 3AM)
    start_date = data_cleaned['sto_time_local'].min().date()
    start_time = pd.Timestamp(f"{start_date} 03:00:00")
    end_time = start_time + pd.Timedelta(hours=24) 
    category_counts = category_counts.reindex(pd.date_range(start=start_time, end=end_time, freq='h'), fill_value=0)
        
    # Order of categories in the stack
    category_order = ['0x50000(Level_access)', '0xB0000(Bot_in_accessed_DW)', '0x40000(Bot_out_of_comms)', 
                      '0x30000(UNLOCALIZED)', 'Disabled_by_SRE', '0x60000(Failed_to_localize)', '0xD0000(Key/door_breached)'] 
    
    # Color definition by RGB codes
    SYMBOTIC_GREEN = tuple(ch/255 for ch in (120,190,32))
    LIGHT_GRAY = tuple(ch/255 for ch in (200,201,199))
    BRIGHT_BLUE = tuple(ch/255 for ch in (0,63,253))
    SYMBOTIC_GRAY = tuple(ch/255 for ch in (85,86,90))
    BLACK = tuple(ch/255 for ch in (0,0,0))
    DARK_GREEN = tuple(ch/255 for ch in (0,143,56))
    LIGHT_BLUE = tuple(ch/255 for ch in (122,170,253))
    LIGHT_GREEN = tuple(ch/255 for ch in (133,222,56))
    _ORANGE = tuple(ch/255 for ch in (255,153,51))
    _PURPLE = tuple(ch/255 for ch in (153,51,255))
    _RED = tuple(ch/255 for ch in (255,51,51))
    _YELLOW = tuple(ch/255 for ch in (255,255,102))
    
    # Colors for each category
    colors = {'0x50000(Level_access)' : SYMBOTIC_GREEN, '0x60000(Failed_to_localize)' : LIGHT_GRAY, 
              '0x30000(UNLOCALIZED)' : BRIGHT_BLUE, '0xD0000(Key/door_breached)' : SYMBOTIC_GRAY,
              '0xB0000(Bot_in_accessed_DW)' : LIGHT_BLUE, '0x40000(Bot_out_of_comms)' : _YELLOW, 
              'Disabled_by_SRE' : _RED}  
    
    for category in category_order:
        if category not in category_counts.columns:
            category_counts[category] = 0
    
    # Reorder the columns to match the desired stack order
    category_counts = category_counts[category_order]
    
    # Set ticks' fontsize
    plt.rc('xtick', labelsize=30) 
    plt.rc('ytick', labelsize=30)
    
    # Plot with subplots
    fig, ax = plt.subplots(figsize=(48, 24))
    category_counts.plot(kind='bar', stacked=True, color=[colors[c] for c in category_order], ax=ax, width=1.0, edgecolor='black', linewidth=.5)
    
    # Set gridlines
    ax.set_axisbelow(True)
    ax.grid(visible=True, which='major', color='gray', linestyle='--', linewidth=0.3, alpha=1)
    
    # Format the x-axis
    xticks_labels = [(start_time + pd.Timedelta(hours=i)).strftime('%H') for i in range(len(category_counts))]
    ax.set_xticks(range(len(category_counts)))
    ax.set_xticklabels([f"{hour:02d}" for hour in range(3,24)] + [f"{hour:02d}" for hour in range(0,4)], rotation=45, ha='right')
    
    # Add labels and title
    ax.set_xlabel("Site Time (Local)", fontsize=64)
    ax.set_ylabel("Number of Bots", fontsize=64)
    ax.set_title(f"Number of Bots Disabled by Safety per Hour ({LOGDATE})", fontsize=80)
    plt.legend(title="STO Reasons", title_fontsize=40, fontsize=30, loc='upper left', bbox_to_anchor=(1.02, 1), borderaxespad=0)
    
    # Add count to each section of the bars
    for i, bar_group in enumerate(ax.patches):  
        # Bar position and height
        x = bar_group.get_x() + bar_group.get_width() / 2
        y = bar_group.get_y() + bar_group.get_height() / 2
        height = bar_group.get_height()
        if height > 1:  # Only annotate sections greater than 1 (meaning no number = a single bot)
            ax.text(x, y, f"{int(height)}", ha='center', va='center', fontsize=8, color='black')

    plt.tight_layout()
    plt.savefig(f"sto_reasons_chart_{LOGDATE}.png")


def main():
    if len(sys.argv) != 3:
        print("Must input log date (yyyymmdd) and site timezone (-hr)")
    else:
        logdate = sys.argv[1]
        timezone = sys.argv[2]
    
    final_csv_file = clean_raw_data(logdate, timezone)
    print(f"Opening sto_reasons_{logdate}.csv")
    final_csv_file.to_csv(f"sto_reasons_{logdate}.csv", index = False)
    print("Saving plot")
    save_plot(final_csv_file, logdate)
    

if __name__ == '__main__':
    main()
