import pandas as pd
import matplotlib.pyplot as plt

def plot_histograms(delta_csv, png_out):
    # Load the transition deltas data
    df = pd.read_csv(delta_csv)

    # Automatically select columns that are numeric deltas (time columns)
    delta_cols = [col for col in df.columns if 'Time from Request' in col and '(s)' in col]

    fig, axs = plt.subplots(1, len(delta_cols), figsize=(6 * len(delta_cols), 5))  # scale width by # of plots

    if len(delta_cols) == 1:
        axs = [axs]  # Make it iterable for a single column

    for i, col in enumerate(delta_cols):
        data = pd.to_numeric(df[col], errors='coerce').dropna()
        axs[i].hist(data, bins=30, alpha=0.7, edgecolor='black')
        axs[i].set_title(col, fontsize=10)
        axs[i].set_xlabel('Seconds')
        axs[i].set_ylabel('Count')

    plt.tight_layout()
    plt.savefig(png_out)
    plt.show()

