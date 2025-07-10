README - Automated gMDM data set upload application
===================================================

This tool automates the following tasks:

1. Detects external drives (e.g., USB).
2. Lists available folders and prompts user to select one.
3. Extracts:
   - Timestamp from the oldest .log file
   - VIN from the .html diagnostic report
   - AU number, description, and location from folder name
4. Updates the .json metadata file in the selected folder.
5. Launches gmdm_companion_cli for verification and uploading.

----------------------------------------------------
PYTHON INSTALLATION (Windows)
----------------------------------------------------

1. Download Python (e.g. Python 3.10+):
   https://www.python.org/downloads/windows/

2. Run the installer:
   ✔ IMPORTANT: Check **"Add Python to PATH"** at the bottom of the installer window.

3. Choose "Customize Installation" (recommended):
   ✔ Ensure "pip" is selected.
   ✔ Keep default settings and install.

4. After installation, open Command Prompt and check:
       python --version
       pip --version

   Both commands should return version numbers.

If not, verify environment variables are set correctly:
   - Press `Win + S`, type: `environment variables`, hit Enter.
   - Under **System variables**, find and edit `Path`.
   - Add path to Python and Scripts (e.g.):
       C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python310\
       C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python310\Scripts\

----------------------------------------------------
REQUIRED PYTHON LIBRARIES
----------------------------------------------------

Install these libraries before running the script:

    python -m pip install beautifulsoup4
    python -m pip install psutil 
    python -m pip install pyautogui


----------------------------------------------------
HOW TO RUN
----------------------------------------------------

1. Plug in your USB or external drive with trace folders.

2. Double-click the `gMDM_trace_uploader.bat` file,
   or open Command Prompt and run:

       python json_metadata_script.py

3. Follow on-screen instructions:
   - Select external drive
   - Select folder to process

4. The script will:
   - Update the .json file using data from .log and .html
   - Launch CLI tool for authentication
   - Upload the folder via `gmdm_companion_cli`

----------------------------------------------------
CLI REQUIREMENTS
----------------------------------------------------

Folder must exist at:

    C:\Users\jvirb\OneDrive\Desktop\MDM\gmdm_companion_cli_4.3.0

Required contents:
    - gmdm_companion_cli (executable, no .exe needed in script)
    - Internet connection for Azure authentication
    - You will be prompted to log in after launch (60 sec delay built-in)

----------------------------------------------------
FOLDER NAMING FORMAT
----------------------------------------------------

Folder names must follow this exact format:

    AUxxxxxx, Description, Location

Example:

    AU416240118, NAR_CPA_WeekendDrive_Connect, BigSur

The script uses this pattern to extract metadata fields.

----------------------------------------------------
TROUBLESHOOTING
----------------------------------------------------

Ask Jurgis Vi

