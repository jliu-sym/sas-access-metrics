import pandas as pd
import matplotlib.pyplot as plt

def plot_histograms(delta_csv, png_out):
    df = pd.read_csv(delta_csv)
    delta_cols = [col for col in df.columns if 'Time from Request' in col and '(s)' in col]

    # Identify rows
    is_driveway = df['Location'].str.startswith("Driveway")
    is_aisle = df['Location'].str.startswith("Aisle")

    n_cols = len(delta_cols)
    fig, axs = plt.subplots(2, n_cols, figsize=(6 * n_cols, 10))  # 2 rows

    if n_cols == 1:
        axs = axs.reshape(2, 1)  # Always 2 rows

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

    plt.tight_layout()
    plt.savefig(png_out)
    plt.show()
