import os
import gzip
import shutil

# Set the folder containing .gz files
folder = r'raw logs'  # Change to your folder name or path if needed

for filename in os.listdir(folder):
    if filename.endswith('.gz'):
        gz_path = os.path.join(folder, filename)
        out_path = os.path.join(folder, filename[:-3])  # Remove .gz extension

        # Only extract if the uncompressed file doesn't already exist
        if not os.path.exists(out_path):
            print(f'Extracting {gz_path}...')
            with gzip.open(gz_path, 'rb') as f_in:
                with open(out_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            print(f'Skipping {out_path} (already exists)')

print('Done extracting all .gz files.')
