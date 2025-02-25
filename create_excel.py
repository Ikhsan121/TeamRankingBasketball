import csv
import os
import pandas as pd


def create_excel(csv_file_path, final_data):
    # Open the CSV file in write mode
    with open(csv_file_path, 'w', newline='') as csv_file:
        # Create a CSV writer
        csv_writer = csv.writer(csv_file)
        # Write each list in the main list as a separate row in the CSV file
        csv_writer.writerows(final_data)
    df = pd.read_csv(csv_file_path)
    df.insert(0, 'Game#', [i // 2 + 1 for i in range(len(df))])
    df.to_excel(f'{csv_file_path.split(".")[0]}.xlsx', index=False)
    # delete csv file
    # Check if the file exists before attempting to delete it
    if os.path.exists(csv_file_path):
        # Delete the file
        os.remove(csv_file_path)
