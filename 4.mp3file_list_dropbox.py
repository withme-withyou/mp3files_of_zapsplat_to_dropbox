import requests
import json
import os

# Dropbox API URLs
list_folder_url = "https://api.dropboxapi.com/2/files/list_folder"
continue_url = "https://api.dropboxapi.com/2/files/list_folder/continue"

# Set up authorization headers
headers = {
    "Authorization": "Bearer sl.B_w6oi3DILwKsAW83DTUR3Xt9gqbai-6UEV2gyLViTMoltsBlF10PA0gv_PWyEZ67qKjFqJIyNkPowESFa2Vgs_WHQCLfS628lAvggHs2TQ-Xu_9vK-MekQFLcnBZ9CBQx1mJRvOPGTQXHOHDamm",
    "Content-Type": "application/json"
}

# Function to list all subfolders with error handling
def list_all_folders(folder_path):
    subfolders = []

    try:
        # Initial request to list folders
        data = {"path": folder_path, "recursive": False}
        response = requests.post(list_folder_url, headers=headers, data=json.dumps(data))
        
        # Check if the response is unauthorized (401 error)
        if response.status_code == 401:
            raise Exception("API access token has expired or is invalid.")
        
        result = response.json()

        # Collect subfolder names from the first request
        entries = result.get('entries', [])
        subfolders.extend([entry['name'] for entry in entries if entry['.tag'] == 'folder'])

        # Continue fetching more data if "has_more" is true
        has_more = result.get('has_more', False)
        cursor = result.get('cursor', '')

        while has_more:
            data = {"cursor": cursor}
            response = requests.post(continue_url, headers=headers, data=json.dumps(data))

            # Check again for 401 errors during pagination
            if response.status_code == 401:
                raise Exception("API access token has expired or is invalid.")
            
            result = response.json()

            # Collect subfolder names from the current response
            entries = result.get('entries', [])
            subfolders.extend([entry['name'] for entry in entries if entry['.tag'] == 'folder'])

            # Update the cursor and check if more data is available
            cursor = result.get('cursor', '')
            has_more = result.get('has_more', False)
        
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

    return subfolders

# Function to save the subfolders list as a JSON file
def save_subfolders_as_json(folder_path, subfolders):
    save_folder = "exported_folders"
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    # Extract folder name from the path (root is treated as "root")
    folder_name = "root" if folder_path == "" else os.path.basename(folder_path.strip('/'))

    # Create the filename as "foldername_subfoldercount.json"
    filename = f"{folder_name}_{len(subfolders)}_subfolders.json"
    file_path = os.path.join(save_folder, filename)

    # Save the subfolders list as a JSON file
    with open(file_path, 'w') as json_file:
        json.dump(subfolders, json_file, indent=4)

    print(f"Subfolder list saved as {file_path}")

# Specify the folder path to list subfolders (for root, use an empty string "")
folder_path = "/SFX 6"

# Call the function to list all subfolders
subfolder_names = list_all_folders(folder_path)

# Save the subfolders list as a JSON file
if subfolder_names:
    save_subfolders_as_json(folder_path, subfolder_names)
