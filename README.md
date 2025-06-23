# LWJGL3ify Installer for Prism Launcher

A Qt GUI application to easily install lwjgl3ify mod on Prism Launcher instances.

## Features

- Browse and select Prism Launcher instances folder
- List all available instances by name
- Download the latest lwjgl3ify release automatically
- Extract and install into selected instance with progress tracking
- User-friendly GUI with step-by-step process

## Requirements

- Python 3.7+
- PyQt6 or PyQt5
- requests library

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install PyQt6 requests
```

If PyQt6 is not available, you can use PyQt5:
```bash
pip install PyQt5 requests
```

## Usage

1. Run the installer:
```bash
python lwjgl3ify_installer.py
```

2. Click "Browse Instances Folder" and select your Prism Launcher instances directory
   - On Linux: Usually `~/.local/share/PrismLauncher/instances`
   - On Windows: Usually `%APPDATA%\PrismLauncher\instances`
   - On macOS: Usually `~/Library/Application Support/PrismLauncher/instances`

3. Select an instance from the list

4. Click "Download and Install LWJGL3ify" to automatically download the latest version and install it

## How it works

1. The application scans the selected instances folder for subdirectories containing `instance.cfg` files
2. It reads the instance names from these configuration files
3. When installing, it downloads the latest lwjgl3ify release from GitHub
4. The JAR file is extracted (as it's essentially a ZIP file) into the selected instance folder
5. All files are overwritten if they already exist

## Troubleshooting

- **"No instances found"**: Make sure you've selected the correct instances folder
- **Download fails**: Check your internet connection and firewall settings
- **Extraction fails**: Ensure the instance folder is writable and not locked by Prism Launcher

## What is lwjgl3ify?

lwjgl3ify is a mod that updates LWJGL (Lightweight Java Game Library) from version 2 to version 3 in Minecraft, providing better performance and compatibility with modern systems.

Project repository: https://github.com/GTNewHorizons/lwjgl3ify 