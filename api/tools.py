import json
from typing import Callable
import os

def search_dayne_info(keyword: str, json_file_path="dayne.json"):
    """
    This function is called when user asks information about Dayne.     

    Parameters:
        keyword: Choose from the following options:
                       - "Contact"
                       - "Location"
                       - "LinkedIn"
                       - "GitHub"
                       - "Objectives"
                       - "Education"
                       - "SkillsAndCertifications"
                       - "ProgrammingLanguages"
                       - "SoftwareDevelopment"
                       - "MachineLearning"
                       - "DevOps"
                       - "HardwareDesignAndNetworking"
                       - "Certifications"
                       - "Projects"
                       - "WorkAndVolunteeringExperience"
                       - "ProfessionalRoles"
                       - "Volunteering"
                       - "Leadership"
                       - "AwardsAndHonors"
    json_file_path: Defaults to "dayne.json".

    """
    def search_nested(data, parent_key=None):
        """
        Recursively searches for the keyword in nested dictionaries and lists.

        Args:
            data (dict | list): The data to search within.
            parent_key (str, optional): Key from the parent dictionary.

        Returns:
            list: Matching values associated with the keyword.
        """
        results = []
        if isinstance(data, dict):
            for k, v in data.items():
                if k.lower() == keyword.lower():
                    results.append(v)
                elif isinstance(v, (dict, list)):
                    results.extend(search_nested(v, k))
        elif isinstance(data, list):
            for item in data:
                results.extend(search_nested(item, parent_key))
        return results

    try:
        json_file_path = os.path.join(os.path.dirname(__file__), json_file_path)
        with open(json_file_path, 'r') as file:
            dayne_data = json.load(file)

        # Search for the keyword
        matches = search_nested(dayne_data)

        if matches:
            return f"Information about '{keyword}':\n" + "\n".join([str(match) for match in matches])
        else:
            return f"No information found about '{keyword}' in the data."
    except FileNotFoundError:
        return f"Error: The file '{json_file_path}' was not found."
    except json.JSONDecodeError:
        return f"Error: Failed to parse the file '{json_file_path}' as valid JSON."
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

def search_dayne_info_handler(func: Callable, *args, **kwargs):
    """
    Handler for executing the `search_dayne_info` tool.
    """
    def wrapped():
        return func(*args, **kwargs)
    return wrapped()


if __name__ == "__main__":
    print(search_dayne_info("Github"))
