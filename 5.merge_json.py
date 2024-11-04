import os
import json

def merge_json_files(input_folder, output_folder, output_filename_base):
    merged_data = []

    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Iterate over all JSON files in the input folder
    for filename in os.listdir(input_folder):
        if filename.endswith(".json"):
            file_path = os.path.join(input_folder, filename)
            
            # Read each JSON file
            with open(file_path, 'r', encoding='utf-8') as file:
                try:
                    data = json.load(file)
                    # Ensure the file contains a list
                    if isinstance(data, list):
                        # Append the list data to the merged_data list
                        merged_data.extend(data)
                    else:
                        print(f"Skipping {filename} because it's not a list.")
                except json.JSONDecodeError as e:
                    print(f"Error decoding {filename}: {e}")

    # Count the total number of elements in the merged list
    total_elements = len(merged_data)

    # Construct the output file name to include the total element count
    output_filename = f"{output_filename_base}_{total_elements}_elements.json"
    output_file_path = os.path.join(output_folder, output_filename)

    # Write the merged list data to the output file
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        json.dump(merged_data, output_file, indent=4)

    print(f"Merged JSON saved to {output_file_path}")


# Specify the input folder containing JSON files, output folder, and output file name
input_folder = "exported_folders"
output_folder = "merged_jsons"
output_filename = "sfx_1_2_3_4_5_6.json"

# Call the function to merge JSON files and save in the output folder
merge_json_files(input_folder, output_folder, output_filename)
