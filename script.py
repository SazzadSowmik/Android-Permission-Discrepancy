import os
import subprocess
import json
import xml.etree.ElementTree as ET
from google_play_scraper import permissions

# Paths
APK_FOLDER = './res/apks'
DECOMPILED_FOLDER = './res/decompiled'
MANIFEST_FOLDER = './manifest'

# Ensure folders exist
os.makedirs(DECOMPILED_FOLDER, exist_ok=True)
os.makedirs(MANIFEST_FOLDER, exist_ok=True)

def decompile_apk(apk_path, output_folder):
    """Decompiles the APK using apktool and moves the manifest file."""
    try:
        subprocess.run(['apktool', 'd', apk_path, '-o', output_folder], check=True)
        manifest_source = os.path.join(output_folder, 'AndroidManifest.xml')
        manifest_dest = os.path.join(MANIFEST_FOLDER, os.path.basename(apk_path).replace('.apk', '_manifest.xml'))
        if os.path.exists(manifest_source):
            os.rename(manifest_source, manifest_dest)
            print(f"Manifest file moved to {manifest_dest}")
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

def main():
    # Decompile APKs and extract package name
    for apk_file in os.listdir(APK_FOLDER):
        if apk_file.endswith('.apk'):
            apk_path = os.path.join(APK_FOLDER, apk_file)
            decompiled_path = os.path.join(DECOMPILED_FOLDER, os.path.basename(apk_file).replace('.apk', ''))
            decompile_apk(apk_path, decompiled_path)

            # Extract package name from manifest file
            manifest_file = os.path.join(MANIFEST_FOLDER, os.path.basename(apk_file).replace('.apk', '_manifest.xml'))
            if os.path.exists(manifest_file):
                package_name = extract_package_name(manifest_file)
                if package_name:
                    print(f"Extracted package name: {package_name}")

                    # Get permissions from Google Play Store
                    store_permissions = get_permissions_from_store(package_name)
                    
                    # Save the result
                    store_permissions_file = os.path.join(MANIFEST_FOLDER, f"{package_name}_store_permissions.json")
                    with open(store_permissions_file, 'w') as f:
                        json.dump(store_permissions, f, indent=4)
                    print(f"Permissions saved to {store_permissions_file}")
                else:
                    print(f"Failed to extract package name from {manifest_file}")
            else:
                print(f"Manifest file not found at {manifest_file}")

if __name__ == "__main__":
    main()
