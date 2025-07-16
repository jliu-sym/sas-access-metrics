import pandas as pd
import matplotlib.pyplot as plt

def plot_histograms(delta_csv, png_out):
    df = pd.read_csv(delta_csv)
    delta_cols = [col for col in df.columns if '(s)' in col]  # works for all types

    # Identify rows by type
    is_driveway = df['Location'].str.startswith("Driveway")
    is_aisle = df['Location'].str.startswith("Aisle")
    is_level = df['Location'].str.startswith("Level")

    n_cols = len(delta_cols)
    fig, axs = plt.subplots(3, n_cols, figsize=(6 * n_cols, 15))  # 3 rows now

    if n_cols == 1:
        axs = axs.reshape(3, 1)  # Always 3 rows

    for i, col in enumerate(delta_cols):
        # Plot for Driveway (row 0)
        driveway_data = pd.to_numeric(df.loc[is_driveway, col], errors='coerce').dropna()
        axs[0, i].hist(driveway_data, bins=30, alpha=0.7, edgecolor='black')
        axs[0, i].set_title(f'Driveway: {col}', fontsize=10)
        axs[0, i].set_xlabel('Seconds')
        axs[0, i].set_ylabel('Count')

        # Plot for Aisle (row 1)
        aisle_data = pd.to_numeric(df.loc[is_aisle, col], errors='coerce').dropna()
        axs[1, i].hist(aisle_data, bins=30, alpha=0.7, edgecolor='black')
        axs[1, i].set_title(f'Aisle: {col}', fontsize=10)
        axs[1, i].set_xlabel('Seconds')
        axs[1, i].set_ylabel('Count')

        # Plot for Level (row 2)
        level_data = pd.to_numeric(df.loc[is_level, col], errors='coerce').dropna()
        axs[2, i].hist(level_data, bins=30, alpha=0.7, edgecolor='black')
        axs[2, i].set_title(f'Level: {col}', fontsize=10)
        axs[2, i].set_xlabel('Seconds')
        axs[2, i].set_ylabel('Count')

    plt.tight_layout()
    plt.savefig(png_out)
    plt.show()
