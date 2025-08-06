import csv
import json
from collections import defaultdict

# Define only the columns to include in the output
FIELDS_TO_KEEP = [
    "column_name",
    "is_nullable",
    "data_type",
    "is_partitioning_column",
    "column_description"
]

def csv_to_filtered_json(csv_file_path, json_file_path=None):
    table_dict = defaultdict(lambda: {"columns": []})

    with open(csv_file_path, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            table_name = row.get("table_name", "").strip()
            if not table_name:
                continue  # Skip rows without a valid table_name

            # Filter only desired fields, skip missing ones gracefully
            column_info = {
                field: row.get(field, "").strip() for field in FIELDS_TO_KEEP if field in row
            }

            table_dict[table_name]["columns"].append(column_info)

    result = dict(table_dict)

    if json_file_path:
        with open(json_file_path, 'w', encoding='utf-8') as out_f:
            json.dump(result, out_f, indent=2)

    return result

# Example usage
csv_path = 'wau dictionary - results-20250730-231659.csv'
json_output = csv_to_filtered_json(csv_path, "table_dictionary.json")
print(json.dumps(json_output, indent=2))

