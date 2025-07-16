import os
import re
import psutil
from bs4 import BeautifulSoup
from datetime import datetime
import string
import ctypes
import subprocess

CURRENT_YEAR = 2025  # Used to format extracted log timestamp

# Detects all external drives (non-C:) connected to the system
def detect_external_drives():
    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for i in range(26):  # Loop through possible drive letters A-Z
        if bitmask & (1 << i):
            drive = f"{string.ascii_uppercase[i]}:/"
            try:
                usage = psutil.disk_usage(drive)
                if usage.total > 0 and not drive.startswith("C:"):
                    drives.append(drive)
            except:
                pass
    return drives

# Navigate through external drive folders and select trace folder
def select_trace_folder():
    while True:
        drives = detect_external_drives()
        if not drives:
            print("No external drives detected.")
            exit()

        print("Available external drives:")
        for i, d in enumerate(drives, 1):
            print(f"{i}. {d}")
        try:
            choice = int(input("Select drive number: "))
            root_path = drives[choice - 1]
            current_path = root_path
        except (ValueError, IndexError):
            print("Invalid drive selection. Try again.")
            continue

        history = []  # Keeps track of folder navigation history

        while True:
            try:
                files = os.listdir(current_path)
                folders = [os.path.join(current_path, f) for f in files if os.path.isdir(os.path.join(current_path, f))]
                log_file = next((f for f in files if f.endswith('.log')), None)
                html_file = next((f for f in files if f.endswith('.html')), None)
                json_file = next((f for f in files if f.endswith('.json')), None)
            except PermissionError:
                print(f"No access to folder: {current_path}")
                if history:
                    current_path = history.pop()
                    continue
                else:
                    break

            # If required trace files are present
            if log_file and html_file and json_file:
                trace_name = os.path.basename(current_path)
                print(f'\nSelected folder: "{trace_name}" contains required trace files.')
                print("Options:")
                print("  [u] Upload this folder")
                print("  [o] Open and browse inside")
                print("  [r] Go back")

                choice = input("Your choice [u/o/r]: ").strip().lower()

                if choice == 'u':
                    return current_path
                elif choice == 'r':
                    if history:
                        current_path = history.pop()
                    else:
                        print("Returning to drive selection...")
                        break
                    continue
                else:
                    pass  # continue browsing into subfolders

            print(f"\nBrowsing: {current_path}")
            if not folders:
                print("No trace_folder detected.")
                choice = input("Press [r] to go back or any other key to retry: ").strip().lower()
                if choice == 'r':
                    if history:
                        current_path = history.pop()
                    else:
                        print("Returning to drive selection...")
                        break
                continue

            # Sort folders by last modified time (descending)
            folders.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            folder_names = [os.path.basename(f) for f in folders]
            max_name_len = max(len(name) for name in folder_names)
            for i, folder_path in enumerate(folders, 1):
                mod_time = os.path.getmtime(folder_path)
                formatted_date = datetime.fromtimestamp(mod_time).strftime("(%m.%d.%y)")
                folder_name = os.path.basename(folder_path)
                print(f"{i:2}. {folder_name:<{max_name_len}}  {formatted_date:>12}")
            print("  To go back press r")

            choice = input("Choose folder to enter: ").strip().lower()
            if choice == 'r':
                if history:
                    current_path = history.pop()
                else:
                    print("Returning to drive selection...")
                    break
                continue
            else:
                try:
                    idx = int(choice)
                    history.append(current_path)
                    current_path = folders[idx - 1]
                except (ValueError, IndexError):
                    print("Invalid selection. Try again.")

# Returns the first file in a folder with a specific extension
def find_file_by_ext(folder, ext):
    log_files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(ext)]
    if not log_files:
        return None
    log_files.sort(key=lambda x: os.path.getctime(x))  # Pick oldest
    return log_files[0]

# Extracts first timestamp fragment from a .log file
def extract_log_time(path):
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            match = re.search(r'\w{3} \d{2} \d{2}:\d{2}:\d{2}', line)
            if match:
                return match.group()
    return None

# Extracts VIN (starting with 'W') from HTML file
def extract_vin(path):
    with open(path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
        match = re.search(r'W[A-Z0-9]{16}', soup.text)
        return match.group() if match else None

# Convert timestamp from log to ISO 8601 format
def format_to_iso8601(log_fragment):
    dt_obj = datetime.strptime(f"{CURRENT_YEAR} {log_fragment}", "%Y %b %d %H:%M:%S")
    return dt_obj.strftime("%Y-%m-%dT%H:%M:%S.000Z")

# Updates several fields in JSON trace metadata
def update_fields(json_path, iso_timestamp, full_folder_name, au_number, vin):
    with open(json_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace all required fields using regex substitution
    content = re.sub(r'"date_created"\s*:\s*".*?"', f'"date_created": "{iso_timestamp}"', content)
    content = re.sub(r'"record_date"\s*:\s*".*?"', f'"record_date": "{iso_timestamp}"', content)
    content = re.sub(r'"record_city"\s*:\s*".*?"', f'"record_city": "{full_folder_name.split(",")[-1].strip()}"', content)
    content = re.sub(r'"description"\s*:\s*".*?"', f'"description": "{full_folder_name}"', content)
    content = re.sub(r'"group_vehicle_number"\s*:\s*".*?"', f'"group_vehicle_number": "{au_number}"', content)
    content = re.sub(r'"vehicle_designation"\s*:\s*".*?"', f'"vehicle_designation": "{au_number}"', content)
    content = re.sub(r'"vin"\s*:\s*"W[A-Z0-9]{16}"', f'"vin": "{vin}"', content)

    with open(json_path, 'w', encoding='utf-8') as f:
        f.write(content)

# Builds and runs the CLI commands for ingestion and stats
def simulate_cli_upload(trace_folder):
    cli_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gmdm_companion_cli_4.3.0")
    stats_command = 'gmdm_companion_cli store-explore get-stats --data-pool-id wus2-se-cariad-speedboats'
    ingest_command = f'gmdm_companion_cli store-explore ingest -s "{trace_folder}"'

    # Opens a new visible cmd window and runs both commands
    full_cmd = (
        f'start cmd /K "cd /d {cli_dir} && '
        f'echo {cli_dir}^>{stats_command} && {stats_command} && '
        f'echo {cli_dir}^>{ingest_command} && {ingest_command}"'
    )
    print("CLI path being used:", cli_dir)
    print("Exists?", os.path.exists(cli_dir))
    subprocess.run(full_cmd, shell=True)

# Main script logic — selects folder, updates metadata, and runs upload
def main():
    while True:
        trace_folder = select_trace_folder()
        log_file = find_file_by_ext(trace_folder, ".log")
        html_file = find_file_by_ext(trace_folder, ".html")
        json_file = find_file_by_ext(trace_folder, ".json")

        if not all([log_file, html_file, json_file]):
            print("Required files not found in the folder.")
            retry = input("Press [r] to reselect folder, or any other key to exit: ").strip().lower()
            if retry == 'r':
                continue
            else:
                return

        raw_time = extract_log_time(log_file)
        vin = extract_vin(html_file)

        if not raw_time or not vin:
            print("Failed to extract timestamp or VIN.")
            retry = input("Press [r] to reselect folder, or any other key to exit: ").strip().lower()
            if retry == 'r':
                continue
            else:
                return

        iso_time = format_to_iso8601(raw_time)
        full_folder_name = os.path.basename(trace_folder)
        folder_parts = full_folder_name.split(",")

        if len(folder_parts) != 3:
            print("Folder name must follow format: AUxxxxx, Description, Location")
            retry = input("Press [r] to reselect folder, or any other key to exit: ").strip().lower()
            if retry == 'r':
                continue
            else:
                return

        au_number = folder_parts[0].strip()
        update_fields(json_file, iso_time, full_folder_name, au_number, vin)

        print("\nMetadata updated successfully:")
        print("   Timestamp:", iso_time)
        print("   VIN:", vin)
        print("   Location:", folder_parts[2].strip())
        print("   Description:", full_folder_name)
        print("   AU Number:", au_number)

        simulate_cli_upload(trace_folder)
        break

# Entry point
if __name__ == "__main__":
    main()
