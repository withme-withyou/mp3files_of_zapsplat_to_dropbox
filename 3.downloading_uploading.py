import requests
from bs4 import BeautifulSoup
import csv
import os
import time
import re
import random
import json
import pandas as pd
import sys

def load_config(config_file):
    with open(config_file, 'r') as file:
        return json.load(file)

file_index = 0
total_count = 0
uul_order = 0
iitem_order = 0

# Load configuration from JSON file
config = load_config('config.json')

# Access the values
json_file_path = config['json_file_path']
dropbox_base_path = config['dropbox_base_path']
ACCESS_TOKEN = config['access_token']
zapsplat_username = config['zapsplat_username']
zapsplat_password = config['zapsplat_password']
should_download_list = config['should_download_list']
download_failed_log = config['download_failed_log']
uploading_success_log = config['uploading_success_log']
uploading_failed_log = config['uploading_failed_log']
# Define the directory for the log file
log_folder = config['log_folder']
# ===================== log part =======================================================
# Log file path
log_file_name = config['log_file_path']
log_file_path = os.path.join(log_folder, log_file_name)

# Create the log folder if it doesn't exist
os.makedirs(log_folder, exist_ok=True)

# Read last processed orders from the log file
if os.path.exists(log_file_path):
    with open(log_file_path, 'r') as log_file:
        last_ul_order, last_item_order = map(int, log_file.read().strip().split(','))
else:
    last_ul_order, last_item_order = 0, 0  # Start fresh if log file doesn't exist
# ==========================================================================================

# Function to generate a 12-digit random number
def generate_random_12_digit_number():
    return ''.join([str(random.randint(0, 9)) for _ in range(12)])

def calculate_pages(count, per_page):
    quotient, remainder = divmod(count, per_page)
    return quotient + 1 if remainder != 0 else quotient

def sanitize_name(name):
    return re.sub(r'\W+', '-', name).strip('-')

def check_string_in_json(file_path, search_string):
    # Load the JSON data
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    # Check if the search string is in the JSON data
    return any(search_string in sfx for sfx in data)

def check_string_in_column_by_index(file_path, column_index, special_string):
    file_path = os.path.join(log_folder, file_path)
    # Check if the CSV file exists; if not, create it
    if not os.path.isfile(file_path):
        # Create a blank CSV file with a header
        with open(file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Sub Category","Folder Name","File Name","Number"])  # Adjust headers as needed
        print(f"Created empty CSV file: {file_path}")

    # Read the CSV file into a DataFrame
    df = pd.read_csv(file_path)

    # Check if the specified column index is valid
    if column_index < 0 or column_index >= len(df.columns):
        raise ValueError(f"Column index {column_index} is out of bounds.")

    # Check if the special string exists in the specified column
    contains_special_string = df.iloc[:, column_index].astype(str).str.contains(special_string).any()

    return contains_special_string

def get_unique_folder_name(access_token, path, folder_name_base):
    url = "https://api.dropboxapi.com/2/files/list_folder"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {"path": path}
    r = requests.post(url, headers=headers, data=json.dumps(data))
    if r.status_code == 401:  # Unauthorized, likely due to expired access token
            print("[ERROR] Access token expired or unauthorized. Stopping script.")
            with open(log_file_path, 'w') as log_file:
                log_file.write(f"{uul_order},{iitem_order}")
            sys.exit(1)  # Stop the script
    if r.status_code == 200:
        existing_folders = {entry['name'] for entry in r.json()['entries'] if entry['.tag'] == 'folder'}
        new_folder_name = folder_name_base
        index = 1
        while new_folder_name in existing_folders:
            new_folder_name = f"{folder_name_base}-{index}"
            index += 1
        return new_folder_name
    else:
        url = "https://api.dropboxapi.com/2/files/create_folder_v2"
        data = {"path": path}
        r = requests.post(url, headers=headers, data=json.dumps(data))
        return folder_name_base
 
    
def write_log_info(sub_category, folder_name, file_name, number, csv_file):
    
    # Create the folder if it doesn't exist
    os.makedirs(log_folder, exist_ok=True)
    
    # Construct the full path for the CSV file
    csv_file = os.path.join(log_folder, csv_file)

    file_exists = os.path.isfile(csv_file)
    with open(csv_file, "a", newline="") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Sub Category", "Folder Name", "File Name", "Number"])
        writer.writerow([sub_category, folder_name, file_name, number])

def upload_file_to_dropbox(file_data, dropbox_path, sub_category, folder_name, file_name, number):
    global file_index  # Declare file_index as global
    global total_count  # Declare total_count as global
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
        file_index += 1
        response = requests.post(url, headers=headers, data=file_data)
        if response.status_code == 401:  # Unauthorized, likely due to expired access token
            print("[ERROR] Access token expired or unauthorized. Stopping script.")
            with open(log_file_path, 'w') as log_file:
                log_file.write(f"{uul_order},{iitem_order}")
            sys.exit(1)  # Stop the script
        if response.status_code == 200:
            print(f"File {file_index}: {dropbox_path} - Upload successful")
            write_log_info(sub_category, folder_name, file_name, number, uploading_success_log)
        else:
            print(f"File {file_index}: {dropbox_path} - Upload failed. Error: {response.text}")
            write_log_info(sub_category, folder_name, file_name, number, uploading_failed_log)
    except Exception as e:
        print(f"File {file_index}: {dropbox_path} - Upload failed. Error: {e}")
        write_log_info(sub_category, folder_name, file_name, number, uploading_failed_log)

# Login URL and credentials
login_url = "https://www.zapsplat.com/login/"
login_payload = {
    "log": zapsplat_username,
    "pwd": zapsplat_password,
    "submit": "",
    "redirect_to": "https://www.zapsplat.com/wp-admin/",
    "testcookie": "1"
}

# Create a session object
s = requests.Session()

# Define headers for login
login_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'en-US,en;q=0.9,ko;q=0.8',
    'Content-Type': 'application/x-www-form-urlencoded'
}

# Login to the website
login_response = s.post(login_url, headers=login_headers, data=login_payload)
print(f"Login response status code: {login_response.status_code}")

if login_response.status_code in [200, 302]:  # Check for redirect after login
    print("Login successful!")

    # URL for sound effect categories
    categories_url = "https://www.zapsplat.com/sound-effect-categories/"
    
    # Get the categories page
    categories_response = s.get(categories_url, headers=login_headers)
    print(f"Categories page response status code: {categories_response.status_code}")

    if categories_response.status_code == 200:
        # Parse HTML content
        soup = BeautifulSoup(categories_response.content, 'html.parser')
        
        # Find all ul elements with class 'children'
        children_ul = soup.find_all('ul', class_='children')

        for ul_order, ul in enumerate(children_ul, start=1):
            if ul_order < last_ul_order:  # Skip if less than last processed
                continue
            if ul_order > last_ul_order:
                last_item_order = 0
            print("     ---> current Main Category Index : ", ul_order)
            uul_order = ul_order
            time.sleep(3)
            cat_items = ul.find_all('li', class_='cat-item')
            for item_order, item in enumerate(cat_items, start=1):
                if item_order < last_item_order:  # Skip if less than last processed
                    continue
                print("     ---> current Sub Category Index : ", item_order)
                iitem_order = item_order
                a_tag = item.find('a')
                count_text = item.get_text(strip=True)
                
                # Extract count from the text
                count = count_text.split('(')[-1].split(')')[0]
                # result = count_text.split('(')[0].rstrip()
                
                if a_tag:
                    href = a_tag.get('href')
                    sub_category = a_tag.get_text()
                    # Handle pagination for each category
                    count = int(count)
                    per_page = 20  # Items per page
                    pages = calculate_pages(count, per_page)
                    print(f"\n\n********************************     {sub_category}     ********************************")
                    for page in range(1, pages + 1):
                        # Construct the URL with pagination
                        if page == 1:
                            page_url = href
                        else:
                            page_url = f"{href}page/{page}/?pageCustom={per_page}"

                        # Get the page content
                        page_response = s.get(page_url, headers=login_headers)
                        print(f"\nPage {page} response status code: {page_response.status_code}")

                        if page_response.status_code == 200:
                            # Parse HTML content
                            page_soup = BeautifulSoup(page_response.content, 'html.parser')
                            
                            # Find all div elements with class 'sound-effect-block'
                            sound_effect_blocks = page_soup.find_all('div', class_='sound-effect-block')

                            # Extract IDs and titles from each sound effect block
                            for index, block in enumerate(sound_effect_blocks, start=1):
                                total_count = total_count + 1

                                print(f"     ====================>    total count : {total_count}    <====================     ")

                                try:
                                    # ===================================================================
                                    # Get the h2 tag with class 'sound-effect-title-heading'
                                    h2_tag = block.find('h2', class_='sound-effect-title-heading')
                                    title = h2_tag.get_text(strip=True).lower() if h2_tag else generate_random_12_digit_number()
                                    title_clean = sanitize_name(title)

                                    folder_name = get_unique_folder_name(ACCESS_TOKEN, dropbox_base_path, title_clean)
                                    file_name = f"{folder_name}.mp3"
                                    # Check and print the result
                                    if check_string_in_json(json_file_path, title_clean):
                                        print(f'The string "{title_clean}" is found in the JSON file.')
                                    else:
                                        print(f'**********************>The string "{title_clean}" is NOT found in the JSON file.')

                                        # ===================================================================
                                        # Get the div with class 'download-links'
                                        download_links_div = block.find('div', class_='download-links')
                                        if download_links_div:
                                            a_tags = download_links_div.find_all('a', id=True)
                                            for a in a_tags:
                                                id_value = a.get('id', '')
                                                if id_value.startswith('alink'):
                                                    number = id_value.replace('alink', '')
                                                    if check_string_in_column_by_index(uploading_success_log, 3, number):
                                                        print(f'The string "{number}" is found in the {uploading_success_log} file.')
                                                    else:
                                                        print(f'%%%%%%%%%%%%%%%%%%%%%%%%> The string "{number}" is NOT found in the {uploading_success_log} file.')
                                                        write_log_info(sub_category, folder_name, file_name, number, should_download_list)
                                                        # ===================================================================
                                                                                            
                                                        # ===================================================================
                                                        # Download the WAV file
                                                        ajax_url = "https://www.zapsplat.com/wp-admin/admin-ajax.php"
                                                        ajax_payload = {
                                                            "action": "get_downlink",
                                                            "id": number,
                                                            "soundType": "MP3"
                                                        }

                                                        ajax_headers = {
                                                            "Accept": "application/json, text/javascript, */*; q=0.01",
                                                            "Accept-Encoding": "gzip, deflate, br",
                                                            "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
                                                            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                                                            "Origin": "https://www.zapsplat.com",
                                                            "Referer": page_url,
                                                            "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
                                                            "X-Requested-With": "XMLHttpRequest"
                                                        }
                                                        
                                                        try:
                                                            ajax_response = s.post(ajax_url, headers=ajax_headers, data=ajax_payload, timeout=20)
                                                            ajax_response.raise_for_status()
                                                            ajax_data = ajax_response.json()
                                                            if ajax_data.get('status') == 1:
                                                                download_link = ajax_data.get('downlink')
                                                                
                                                                try:
                                                                    download_response = s.get(download_link, timeout=20)
                                                                    download_response.raise_for_status()
                                                                    # print(download_response.status_code)
                                                                    # time.sleep(10)
                                                                    
                                                                    file_data = download_response.content
                                                                    print(f"Downloading file {file_name} from {download_link}...")
                                                                    upload_file_to_dropbox(file_data, f"{dropbox_base_path}/{folder_name}/{file_name}", sub_category, folder_name, file_name, number)

                                                                except requests.RequestException as e:
                                                                    print(f"Failed to download file from {download_link}: {e}")
                                                                    write_log_info(sub_category, folder_name, file_name, number, download_failed_log)
                                                                except IOError as e:
                                                                    print(f"Failed to save file {dropbox_base_path}/{folder_name}/{file_name}: {e}")
                                                                    write_log_info(sub_category, folder_name, file_name, number, download_failed_log)
                                                            else:
                                                                print("Status is not 1. No download link provided.")
                                                                write_log_info(sub_category, folder_name, file_name, number, download_failed_log)
                                                        except requests.RequestException as e:
                                                            print(f"Error with AJAX request for ID {number}: {e}")
                                                            write_log_info(sub_category, folder_name, file_name, number, download_failed_log)
                                except Exception as e:
                                    print(f"Error processing block: {e}")
                                    write_log_info(sub_category, folder_name, file_name, number, download_failed_log)

                        # Sleep for a short time to avoid overloading the server
                        time.sleep(0.1)

    else:
        print("Failed to retrieve the categories page.")
else:
    print("Failed to login.")
