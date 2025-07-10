
import os
import re
import psutil
from bs4 import BeautifulSoup
from datetime import datetime
import string
import ctypes
import time
import pyautogui

CURRENT_YEAR = 2025

def detect_external_drives():
    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for i in range(26):
        if bitmask & (1 << i):
            drive = f"{string.ascii_uppercase[i]}:/"
            try:
                usage = psutil.disk_usage(drive)
                if usage.total > 0 and not drive.startswith("C:"):
                    drives.append(drive)
            except:
                pass
    return drives

def select_trace_folder():
    while True:
        drives = detect_external_drives()
        if not drives:
            print("No external drives detected.")
            exit()

        print("Available external drives:")
        for i, d in enumerate(drives, start=1):
            print(f"{i}. {d}")
        try:
            choice = int(input("Select drive number: "))
            selected_drive = drives[choice - 1]
        except (ValueError, IndexError):
            print("Invalid drive selection. Try again.")
            continue

        while True:
            folders = [os.path.join(selected_drive, f) for f in os.listdir(selected_drive) if os.path.isdir(os.path.join(selected_drive, f))]
            if not folders:
                print("No folders found on selected drive.")
                break  # go back to drive selection

            folders.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            print("\nFolders on selected drive:")
            max_name_length = max(len(os.path.basename(f)) for f in folders)
            for i, folder_path in enumerate(folders, 1):
                mod_time = os.path.getmtime(folder_path)
                formatted_date = datetime.fromtimestamp(mod_time).strftime("(%m.%d.%y)")
                folder_name = os.path.basename(folder_path)
                print(f"{i:2}. {folder_name.ljust(max_name_length)}  {formatted_date}")

            try:
                folder_choice = int(input("Select the number of the folder to process (0 to reselect drive): "))
                if folder_choice == 0:
                    break  # return to drive selection
                selected_folder = folders[folder_choice - 1]
                print(f"\nYou selected: {selected_folder}")
                return selected_folder
            except (ValueError, IndexError):
                print("Invalid folder selection. Try again.")


def find_file_by_ext(folder, ext):
    log_files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(ext)]
    if not log_files:
        return None
    log_files.sort(key=lambda x: os.path.getctime(x))
    return log_files[0]

def extract_log_time(path):
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            match = re.search(r'\w{3} \d{2} \d{2}:\d{2}:\d{2}', line)
            if match:
                return match.group()
    return None

def extract_vin(path):
    with open(path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
        match = re.search(r'W[A-Z0-9]{16}', soup.text)
        return match.group() if match else None

def format_to_iso8601(log_fragment):
    dt_obj = datetime.strptime(f"{CURRENT_YEAR} {log_fragment}", "%Y %b %d %H:%M:%S")
    return dt_obj.strftime("%Y-%m-%dT%H:%M:%S.000Z")

def update_fields(json_path, iso_timestamp, full_folder_name, au_number, vin):
    with open(json_path, 'r', encoding='utf-8') as f:
        content = f.read()

    content = re.sub(r'"date_created"\s*:\s*".*?"', f'"date_created": "{iso_timestamp}"', content)
    content = re.sub(r'"record_date"\s*:\s*".*?"', f'"record_date": "{iso_timestamp}"', content)
    content = re.sub(r'"record_city"\s*:\s*".*?"', f'"record_city": "{full_folder_name.split(",")[-1].strip()}"', content)
    content = re.sub(r'"description"\s*:\s*".*?"', f'"description": "{full_folder_name}"', content)
    content = re.sub(r'"group_vehicle_number"\s*:\s*".*?"', f'"group_vehicle_number": "{au_number}"', content)
    content = re.sub(r'"vehicle_designation"\s*:\s*".*?"', f'"vehicle_designation": "{au_number}"', content)
    content = re.sub(r'"vin"\s*:\s*"W[A-Z0-9]{16}"', f'"vin": "{vin}"', content)

    with open(json_path, 'w', encoding='utf-8') as f:
        f.write(content)

def simulate_cli_upload(trace_folder):
    cli_dir = r"C:\Users\virbiju\OneDrive - Volkswagen Group of America\Desktop\MDM\gmdm_companion_cli_4.3.0"
    ingest_command = f'gmdm_companion_cli store-explore ingest -s "{trace_folder}"'

    pyautogui.hotkey('win', 'r')
    time.sleep(1)
    pyautogui.write('cmd')
    pyautogui.press('enter')
    time.sleep(2)

    pyautogui.write(f'cd /d "{cli_dir}"')
    pyautogui.press('enter')
    time.sleep(1)

    pyautogui.write('gmdm_companion_cli store-explore get-stats --data-pool-id wus2-se-cariad-speedboats')
    pyautogui.press('enter')
    time.sleep(60)

    pyautogui.write(ingest_command)
    pyautogui.press('enter')

def main():
    trace_folder = select_trace_folder()
    log_file = find_file_by_ext(trace_folder, ".log")
    html_file = find_file_by_ext(trace_folder, ".html")
    json_file = find_file_by_ext(trace_folder, ".json")

    if not all([log_file, html_file, json_file]):
        print("Required files not found in the folder.")
        return

    raw_time = extract_log_time(log_file)
    vin = extract_vin(html_file)

    if not raw_time or not vin:
        print("Failed to extract timestamp or VIN.")
        return

    iso_time = format_to_iso8601(raw_time)
    full_folder_name = os.path.basename(trace_folder)
    folder_parts = full_folder_name.split(",")

    if len(folder_parts) != 3:
        print("Folder name must follow format: AUxxxxx, Description, Location")
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

if __name__ == "__main__":
    main()
