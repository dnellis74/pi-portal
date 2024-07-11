import csv
import json
import sys
from datetime import datetime

def csv_to_json(csv_file_path, json_file_path):
    # List to store the data
    data = []

    # Read the CSV file
    try:
        with open(csv_file_path, 'r') as csv_file:
            print(f"Starting reader '{csv_file_path}'.")
            csv_reader = csv.DictReader(csv_file)
            print(f"Finished reader '{csv_file_path}'.")
            n = 1
            for row in csv_reader:
                n = n + 1
                # Add a new row
                new_row = {
                    "updated": "7/3/2024",
                    "count_by_state": n,
                    "State": "California",
                    "epa_region": 9,
                    "Regulation": row["Regulation"],
                    "Description": row["Rules"],
                    "Link": row["Regulatory Text"],
                    "Timing": row["OriginalAdoptionDate"],
                    "Addt. Notes 1": "",
                    "Addt. Notes 2": "",
                    "Tags": row["Pollutants"]
                }
                data.append(new_row)
    except FileNotFoundError:
        print(f"Error: CSV file '{csv_file_path}' not found.")
        sys.exit(1)
    except csv.Error as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)

    # Transform the data
    transformed_data = {
        "data": data,
        "metadata": {
            "record_count": len(data),
            "source_file": csv_file_path,
            "date_processed": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }

    # Write the transformed data to a JSON file
    try:
        with open(json_file_path, 'w') as json_file:
            json.dump(transformed_data, json_file, indent=4)
        print(f"JSON data has been written to {json_file_path}")
    except IOError:
        print(f"Error: Unable to write to file '{json_file_path}'.")
        sys.exit(1)

if __name__ == "__main__":









    if len(sys.argv) != 3:
        print("Usage: python script.py <input_csv_file> <output_json_file>")
        sys.exit(1)

    input_csv = sys.argv[1]
    output_json = sys.argv[2]

    csv_to_json(input_csv, output_json)