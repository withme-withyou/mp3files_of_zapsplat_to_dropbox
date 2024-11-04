import os
import csv
import requests
import json
import sys



# Dropbox API access token
ACCESS_TOKEN = "sl.B_w6oi3DILwKsAW83DTUR3Xt9gqbai-6UEV2gyLViTMoltsBlF10PA0gv_PWyEZ67qKjFqJIyNkPowESFa2Vgs_WHQCLfS628lAvggHs2TQ-Xu_9vK-MekQFLcnBZ9CBQx1mJRvOPGTQXHOHDamm"

# Progress log file
PROGRESS_LOG_FILE = "upload_progress.log"

# Function to log the current progress
def log_progress(local_file_path):
    with open(PROGRESS_LOG_FILE, "w") as log_file:
        log_file.write(local_file_path)

# Function to read the last progress from the log file
def read_progress():
    if os.path.exists(PROGRESS_LOG_FILE):
        with open(PROGRESS_LOG_FILE, "r") as log_file:
            return log_file.readline().strip()
    return None

# Function to create a folder in Dropbox
def create_dropbox_folder(path, error_log):
    url = "https://api.dropboxapi.com/2/files/create_folder_v2"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "path": path,
        "autorename": False
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 401:  # Unauthorized, likely due to expired access token
        print("[ERROR] Access token expired or unauthorized. Stopping script.")
        sys.exit(1)  # Stop the script
    if response.status_code != 200 and response.status_code != 409:  # 409 means folder already exists
        error_log.append((path, "Failed to create folder", response.text))
        print(f"[ERROR] Failed to create folder: {path}. Error: {response.text}")

# Function to upload a file to Dropbox
def upload_file_to_dropbox(local_file_path, dropbox_path, file_index, error_log):
    url = "https://content.dropboxapi.com/2/files/upload"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/octet-stream",
        "Dropbox-API-Arg": json.dumps({
            "path": dropbox_path,
            "mode": "add",
            "autorename": True,
            "mute": False
        })
    }
    try:
        with open(local_file_path, "rb") as file_data:
            response = requests.post(url, headers=headers, data=file_data)
        if response.status_code == 401:  # Unauthorized, likely due to expired access token
            print("[ERROR] Access token expired or unauthorized. Stopping script.")
            sys.exit(1)  # Stop the script
        if response.status_code == 200:
            print(f"File {file_index}: {local_file_path} - Upload successful")
            log_progress(local_file_path)  # Log the progress
        else:
            print(f"File {file_index}: {local_file_path} - Upload failed. Error: {response.text}")
            error_log.append((file_index, local_file_path, response.text))
    except Exception as e:
        print(f"File {file_index}: {local_file_path} - Upload failed. Error: {e}")
        error_log.append((file_index, local_file_path, str(e)))

# Function to traverse the local directory, create folders, and upload files
def traverse_and_upload(local_path, dropbox_base_path):
    file_index = 1
    error_log = []

    last_uploaded_file = read_progress()  # Read last uploaded file from the log
    skip = last_uploaded_file is not None

    for root, dirs, files in os.walk(local_path):
        for file in files:

            if file.endswith(".mp3"):
                local_file_path = os.path.join(root, file)

                # If skipping files until the last uploaded one is found
                if skip:
                    if local_file_path == last_uploaded_file:
                        skip = False  # Stop skipping once we reach the last uploaded file
                    continue

                # Get the base name of the file (without extension)
                base_name = os.path.splitext(file)[0]
                
                # Construct the folder path and file path in Dropbox
                dropbox_folder_path = f"{dropbox_base_path}/{base_name}"
                dropbox_file_path = f"{dropbox_folder_path}/{file}"
                
                # Create the folder in Dropbox
                create_dropbox_folder(dropbox_folder_path, error_log)
                
                # Upload the .mp3 file to Dropbox
                upload_file_to_dropbox(local_file_path, dropbox_file_path, file_index, error_log)
                
                file_index += 1

    # Log errors to a CSV file
    if error_log:
        with open("upload_errors.csv", "w", newline="") as error_file:
            writer = csv.writer(error_file)
            writer.writerow(["File Index", "File Path", "Error Message"])
            writer.writerows(error_log)
        print(f"[INFO] Errors logged to upload_errors.csv")

# Replace with your local base folder path and Dropbox base path
local_base_path = r"C:\Users\Administrator\Pictures\updater\Sound Effects"  # Local directory path
dropbox_base_path = "/SFX 6"  # Dropbox base path where all files will be uploaded

# Start the folder creation and file upload process
traverse_and_upload(local_base_path, dropbox_base_path)
