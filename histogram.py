import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

def plot_histograms(delta_csv, png_out):
    df = pd.read_csv(delta_csv)
    delta_cols = [col for col in df.columns if '(s)' in col]

    # Identify rows by type
    is_driveway = df['Location'].str.startswith("Driveway")
    is_aisle = df['Location'].str.startswith("Aisle")
    is_level = df['Location'].str.startswith("Level")

    n_cols = len(delta_cols)
    fig, axs = plt.subplots(3, n_cols, figsize=(6 * n_cols, 15))
    if n_cols == 1:
        axs = axs.reshape(3, 1)

    # Define bins: 0, 60, ..., 1200 sec, and a final [1200, inf)
    bin_edges = np.append(np.arange(0, 1200 + 60, 60), [np.inf])  # 0,60,...,1200, inf

    # Labels for each bin (0, 1, 2, ..., 19, '>20')
    labels = [str(i) for i in range(20)] + ['>20']

    for i, col in enumerate(delta_cols):
        for row, (selector, label) in enumerate(zip([is_driveway, is_aisle, is_level], 
                                                    ['Driveway', 'Aisle', 'Level'])):
            data = pd.to_numeric(df.loc[selector, col], errors='coerce').dropna()
            data = data[np.isfinite(data)]

            if len(data) == 0:
                axs[row, i].set_visible(False)
                continue

            # Plot histogram, also get n (counts) and _, bins
            n, bins, patches = axs[row, i].hist(data, bins=bin_edges, alpha=0.7, edgecolor='black')
            # axs[row, i].set_title(f'{label}: {col}', fontsize=10)
            axs[row, i].set_title(f'{label}: {col.replace("(s)", "")}', fontsize=10)

            axs[row, i].set_xlabel('Minutes')
            axs[row, i].set_ylabel('Count')
            axs[row, i].set_xticks(bin_edges[:-1])
            axs[row, i].set_xticklabels(labels, rotation=45)
            axs[row, i].set_xlim([0, 1260])
            
            for count, patch in zip(n, patches):
                x = patch.get_x() + patch.get_width() / 2
                y = patch.get_height()
                axs[row, i].annotate(
                    f'{int(count)}',
                    xy=(x, y),
                    xytext=(0, 3), textcoords='offset points',
                    ha='center', va='bottom',
                    fontsize=8, color='black'
                )
            # Annotate count above last bin (the outlier bin)
            outlier_count = int(n[-1])
            axs[row, i].annotate(
                f'{outlier_count}', 
                xy=(bin_edges[-2] + 30, n[-1]),  # Middle of last bin
                xytext=(0, 3), textcoords='offset points',
                ha='center', va='bottom', fontsize=8, color='black'
            )

            if len(data) == 0:
                axs[row, i].set_visible(False)
                continue

            # Plot histogram as before ...
            n, bins, patches = axs[row, i].hist(data, bins=bin_edges, alpha=0.7, edgecolor='black')
            # [other code here...]

            # --- Calculate stats (all in seconds)
            avg = np.mean(data)
            median = np.median(data)
            p95 = np.percentile(data, 95)
            p99 = np.percentile(data, 99)

            # --- Format as text
            stats_text = (
                f'Avg: {avg:.1f}s\n'
                f'Median: {median:.1f}s\n'
                f'P95: {p95:.1f}s\n'
                f'P99: {p99:.1f}s'
            )
            # --- Display in upper right of plot
            axs[row, i].text(
                0.98, 0.95, stats_text,
                transform=axs[row, i].transAxes,
                fontsize=8, va='top', ha='right',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.6, edgecolor='gray')
            )


    plt.tight_layout()
    plt.savefig(png_out)
    plt.show()
