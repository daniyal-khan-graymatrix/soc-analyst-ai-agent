import csv
import json
import os

def csv_to_json(csv_filepath, json_filepath=None):
    """
    Converts a CSV file to a list of JSON (dicts).
    Optionally saves to a JSON file if json_filepath is provided.

    Returns:
        List[dict]: Parsed rows as dictionaries
    """
    data = []

    try:
        with open(csv_filepath, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                cleaned_row = {k.strip(): v.strip() for k, v in row.items()}
                data.append(cleaned_row)
    except Exception as e:
        print(f"Error reading CSV {csv_filepath}: {e}")
        return []

    # If saving to JSON
    if json_filepath:
        try:
            os.makedirs(os.path.dirname(json_filepath), exist_ok=True)
            with open(json_filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(data, jsonfile, indent=4)
        except Exception as e:
            print(f"Error writing JSON {json_filepath}: {e}")

    return data
