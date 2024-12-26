import json

def get_background():
    # Path to your JSON file
    json_file_path = 'src2/dayne.json'

    # Open and load the JSON file
    with open(json_file_path, 'r') as file:
        resume_data = json.load(file)

    return resume_data


