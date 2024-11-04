import requests
from bs4 import BeautifulSoup
import csv
import os
import time
import re
import random

valid_categories = [
    "Animal", "Bell", "Cartoon", "Emergency", "Explosions", "Fantasy", "Foley", "Food and Drink", 
    "Horror", "Hospital", "Household", "Human", "Impacts", "Industrial", "Lab", "Leisure", 
    "Multimedia and UI", "Musical", "Nature", "Office", "Public Places", "Science Fiction", 
    "Sound Design", "Sport", "Technology", "Vehicles", "Warfare"
]

total_count = 0
# Function to generate a 12-digit random number
def generate_random_12_digit_number():
    return ''.join([str(random.randint(0, 9)) for _ in range(12)])

def calculate_pages(count, per_page):
    quotient, remainder = divmod(count, per_page)
    return quotient + 1 if remainder != 0 else quotient

def sanitize_name(name):
    return re.sub(r'\W+', '-', name).strip('-')

def write_incomplete_info(sub_category, folder_name, file_name, number):
    with open("incomplete_files.csv", "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([sub_category, folder_name, file_name, number])



# Login URL and credentials
login_url = "https://www.zapsplat.com/login/"
login_payload = {
    "log": "Sourav2024",
    "pwd": "Sourav2024",
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
            if ul_order != 8:
                continue  # Skip ul elements with order less than 5
            time.sleep(3)
            cat_items = ul.find_all('li', class_='cat-item')
            for item_order, item in enumerate(cat_items, start=1):
                # if item_order <= 13:
                #     continue  # Skip ul elements with order less than 5
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
                                    
                                    # ===================================================================
                                    # Get the div with class 'download-links'
                                    download_links_div = block.find('div', class_='download-links')
                                    if download_links_div:
                                        a_tags = download_links_div.find_all('a', id=True)
                                        for a in a_tags:
                                            id_value = a.get('id', '')
                                            if id_value.startswith('alink'):
                                                number = id_value.replace('alink', '')
                                                
                                    # ===================================================================
                                            # Create directory structure
                                            base_directory = os.path.join("Sound Effects", sub_category)
                                            os.makedirs(base_directory, exist_ok=True)
                                            
                                            # Generate unique folder name
                                            folder_name = title_clean
                                            folder_path = os.path.join(base_directory, folder_name)
                                            unique_index = 1
                                            while os.path.exists(folder_path):
                                                folder_name = f"{title_clean}-{unique_index}"
                                                folder_path = os.path.join(base_directory, folder_name)
                                                unique_index += 1
                                            
                                            # Create folder for the mp3 file
                                            os.makedirs(folder_path, exist_ok=True)
                                            file_name = f"{folder_name}.mp3"
                                            
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
                                                        
                                                        file_path = os.path.join(folder_path, file_name)
                                                        
                                                        with open(file_path, "wb") as file:
                                                            file.write(download_response.content)
                                                        print(f"File {index}: Downloaded and saved as {file_path}")
                                                    except requests.RequestException as e:
                                                        print(f"Failed to download file from {download_link}: {e}")
                                                        write_incomplete_info(sub_category, folder_name, file_name, number)
                                                    except IOError as e:
                                                        print(f"Failed to save file {file_path}: {e}")
                                                        write_incomplete_info(sub_category, folder_name, file_name, number)
                                                else:
                                                    print("Status is not 1. No download link provided.")
                                                    write_incomplete_info(sub_category, folder_name, file_name, number)
                                            except requests.RequestException as e:
                                                print(f"Error with AJAX request for ID {number}: {e}")
                                                write_incomplete_info(sub_category, folder_name, file_name, number)
                                except Exception as e:
                                    print(f"Error processing block: {e}")
                                    write_incomplete_info(sub_category, sub_category, folder_name, file_name, number)

                        # Sleep for a short time to avoid overloading the server
                        time.sleep(0.1)

    else:
        print("Failed to retrieve the categories page.")
else:
    print("Failed to login.")
