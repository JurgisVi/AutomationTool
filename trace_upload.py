import os
import re
import json
import subprocess
from bs4 import BeautifulSoup

# === CONFIGURATION ===
base_trace_path = "D:/logs"  # Base folder where all trace folders are located
cli_tool_path = "C:/path/to/gmdm_companion_cli"  # <-- Adjust to your actual CLI path

# === FUNCTIONS ===

def list_trace_folders(base_path):
    folders = []
    for entry in os.listdir(base_path):
        folder_path = os.path.join(base_path, entry)
        if os.path.isdir(folder_path):
            files = os.listdir(folder_path)
            if any(f.endswith(".log") for f in files) and any(f.endswith(".html") for f in files) and any(f.endswith(".json") for f in files):
                folders.append(entry)
    return folders

def get_log_time(log_path):
    with open(log_path, 'r', encoding='utf-8') as file:
        for line in file:
            match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', line)
            if match:
                return match.group()
    return None

def get_vin_from_html(html_path):
    with open(html_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
        vin_match = re.search(r'WA1ZZZ[A-Z0-9]{11}', soup.text)
        return vin_match.group() if vin_match else None

def update_json(json_path, vin, timestamp, au_number, description):
    with open(json_path, 'r+', encoding='utf-8') as file:
        data = json.load(file)
        data['vin'] = vin
        data['timestamp'] = timestamp
        data['au_number'] = au_number
        data['description'] = description
        file.seek(0)
        json.dump(data, file, indent=4)
        file.truncate()

def run_upload_commands(cli_path, trace_path):
    os.chdir(cli_path)
    subprocess.run([
        "gmdm_companion_cli.exe",
        "store-explore",
        "get-stats",
        "--data-pool-id", "wus2-se-cariad-speedboats"
    ], shell=True)
    subprocess.run([
        "gmdm_companion_cli.exe",
        "store-explore",
        "push-folder",
        f"--folder-path={trace_path}"
    ], shell=True)

# === MAIN EXECUTION ===

print("🔍 Searching for available trace folders...\n")
trace_folders = list_trace_folders(base_trace_path)

if not trace_folders:
    print("❌ No valid trace folders found in:", base_trace_path)
    exit()

# Display options
for i, folder in enumerate(trace_folders, start=1):
    print(f"{i}. {folder}")

choice = input("\nEnter the number of the trace folder to upload: ")
try:
    selected_folder = trace_folders[int(choice)-1]
except (IndexError, ValueError):
    print("❌ Invalid selection.")
    exit()

trace_folder = os.path.join(base_trace_path, selected_folder)
log_file = next((os.path.join(trace_folder, f) for f in os.listdir(trace_folder) if f.endswith(".log")), None)
html_file = next((os.path.join(trace_folder, f) for f in os.listdir(trace_folder) if f.endswith(".html")), None)
json_file = next((os.path.join(trace_folder, f) for f in os.listdir(trace_folder) if f.endswith(".json")), None)

print("\n📂 Selected trace folder:", selected_folder)

timestamp = get_log_time(log_file)
vin = get_vin_from_html(html_file)

if not timestamp or not vin:
    print("❌ Could not extract timestamp or VIN.")
    exit()

au_number = input("Enter AU number: ").strip()
description = input("Enter test drive description (e.g. CN26.2_VR41.7SP1_ADAS_R3_SW_Approval_drive): ").strip()

print("\n📝 Updating metadata JSON...")
update_json(json_file, vin, timestamp, au_number, description)

print("🚀 Uploading trace using CLI tool...")
run_upload_commands(cli_tool_path, trace_folder)

print("✅ Trace upload completed successfully.")
