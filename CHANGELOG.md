# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2025-07-16
### Added
- Navigation support for browsing nested folders and returning to previous directory
- Inline comments for clarity on all functions and significant logic blocks
- `simulate_cli_upload()` function to run CLI commands visibly in CMD using `subprocess`

### Changed
- Replaced `pyautogui` automation with more reliable and readable `subprocess`-based execution
- Improved folder selection UI: displays date-modified, handles invalid inputs more gracefully
- Robust VIN detection with general `W[A-Z0-9]{16}` pattern (instead of fixed `WA1ZZZ...`)
- Modularized main logic into cleanly separated helper functions

### Fixed
- Edge case where folder name format (AU, Description, Location) was not properly validated
- Avoided script failure when required trace files are missing by adding retry logic

---

## [1.0.0] - Initial version
- Simple folder selection and file extraction
- Used `pyautogui` to automate CLI command typing
- Performed VIN and timestamp insertion into JSON