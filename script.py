import os
import subprocess
import json
import xml.etree.ElementTree as ET
import csv
import shutil
from google_play_scraper import permissions

# Paths
APK_FOLDER = './res/apks'
DECOMPILED_FOLDER = './res/decompiled'
MANIFEST_FOLDER = './manifest'
CSV_FILE = './permissions_summary.csv'

# Ensure folders exist
os.makedirs(DECOMPILED_FOLDER, exist_ok=True)
os.makedirs(MANIFEST_FOLDER, exist_ok=True)

def decompile_apk(apk_path, output_folder):
    """Decompiles the APK using apktool and moves the manifest file."""
    try:
        subprocess.run(['apktool', 'd', apk_path, '-o', output_folder], check=True)
        manifest_source = os.path.join(output_folder, 'AndroidManifest.xml')
        if os.path.exists(manifest_source):
            print(f"Manifest file found: {manifest_source}")
        else:
            print(f"Manifest file not found in {manifest_source}")
    except subprocess.CalledProcessError as e:
        print(f"Error during decompilation: {e}")

def get_permissions_from_store(package_name):
    """Fetch permissions from Google Play Store using google-play-scraper."""
    try:
        result = permissions(package_name, lang='en', country='us')
        return result
    except Exception as e:
        print(f"Error fetching permissions: {e}")
        return {}

def extract_package_name(manifest_file):
    """Extracts the package name from the AndroidManifest.xml file."""
    try:
        tree = ET.parse(manifest_file)
        root = tree.getroot()
        package_name = root.attrib.get('package')
        return package_name
    except Exception as e:
        print(f"Error parsing manifest file: {e}")
        return None

def count_permissions_in_manifest(manifest_file):
    """Count unique permissions in the manifest file, handling namespace issues."""
    try:
        tree = ET.parse(manifest_file)
        root = tree.getroot()
        
        # Extract the correct Android namespace
        android_ns = 'http://schemas.android.com/apk/res/android'
        permissions = set()
        
        # Iterate through all 'uses-permission' tags and count unique permissions
        for elem in root.iter('uses-permission'):
            perm = elem.attrib.get(f'{{{android_ns}}}name')
            if perm:
                permissions.add(perm)
        
        return len(permissions)
    except Exception as e:
        print(f"Error counting permissions in manifest: {e}")
        return 0

def count_unique_permissions_in_json(json_data):
    """Count unique permissions from the description JSON."""
    unique_permissions = set()
    for category in json_data.values():
        for perm in category:
            unique_permissions.add(perm)
    return len(unique_permissions)

def delete_decompiled_folder(folder_path):
    """Deletes the decompiled folder after processing."""
    try:
        shutil.rmtree(folder_path)
        print(f"Deleted folder: {folder_path}")
    except Exception as e:
        print(f"Error deleting folder: {e}")

def main():
    # Prepare CSV file for writing results
    with open(CSV_FILE, mode='w', newline='') as csv_file:
        fieldnames = ['App Name', 'Manifest Permission Count', 'Description Permission Count']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        # Process each APK
        for apk_file in os.listdir(APK_FOLDER):
            if apk_file.endswith('.apk'):
                apk_path = os.path.join(APK_FOLDER, apk_file)
                app_name = os.path.basename(apk_file).replace('.apk', '')

                # Create subfolder for each app
                app_folder = os.path.join(MANIFEST_FOLDER, app_name)
                os.makedirs(app_folder, exist_ok=True)
                decompiled_path = os.path.join(DECOMPILED_FOLDER, app_name)

                # Decompile APK and move manifest file
                decompile_apk(apk_path, decompiled_path)

                # Move manifest file to app subfolder
                manifest_file_source = os.path.join(decompiled_path, 'AndroidManifest.xml')
                manifest_file_dest = os.path.join(app_folder, 'AndroidManifest.xml')

                if os.path.exists(manifest_file_source):
                    os.rename(manifest_file_source, manifest_file_dest)
                    print(f"Manifest file moved to {manifest_file_dest}")
                else:
                    print(f"Manifest file not found in {manifest_file_source}")

                # Extract package name from manifest file
                if os.path.exists(manifest_file_dest):
                    package_name = extract_package_name(manifest_file_dest)
                    if package_name:
                        print(f"Extracted package name: {package_name}")

                        # Count permissions in manifest file
                        manifest_permission_count = count_permissions_in_manifest(manifest_file_dest)

                        # Get permissions from Google Play Store and count unique permissions
                        store_permissions = get_permissions_from_store(package_name)
                        description_permission_count = count_unique_permissions_in_json(store_permissions)

                        # Save permissions JSON to app folder
                        store_permissions_file = os.path.join(app_folder, f"{package_name}_store_permissions.json")
                        with open(store_permissions_file, 'w') as f:
                            json.dump(store_permissions, f, indent=4)
                        print(f"Permissions saved to {store_permissions_file}")

                        # Write to CSV
                        writer.writerow({
                            'App Name': app_name,
                            'Manifest Permission Count': manifest_permission_count,
                            'Description Permission Count': description_permission_count
                        })
                    else:
                        print(f"Failed to extract package name from {manifest_file_dest}")
                else:
                    print(f"Manifest file not found at {manifest_file_dest}")

                # Delete the decompiled folder after processing
                delete_decompiled_folder(decompiled_path)

if __name__ == "__main__":
    main()