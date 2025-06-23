#!/usr/bin/env python3
"""
LWJGL3ify Installer for Prism Launcher
A Qt GUI application to install lwjgl3ify mod on Prism Launcher instances
"""

import sys
import os
import configparser
import requests
import zipfile
import tempfile
from pathlib import Path
from typing import List, Dict, Optional
import json

try:
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                                QWidget, QPushButton, QListWidget, QLabel, QFileDialog, 
                                QMessageBox, QProgressBar, QTextEdit, QListWidgetItem)
    from PyQt6.QtCore import QThread, pyqtSignal, Qt, QSettings
    from PyQt6.QtGui import QFont
except ImportError:
    try:
        from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                                    QWidget, QPushButton, QListWidget, QLabel, QFileDialog, 
                                    QMessageBox, QProgressBar, QTextEdit, QListWidgetItem)
        from PyQt5.QtCore import QThread, pyqtSignal, Qt, QSettings
        from PyQt5.QtGui import QFont
    except ImportError:
        print("Error: PyQt6 or PyQt5 is required. Install with:")
        print("pip install PyQt6")
        print("or")
        print("pip install PyQt5")
        sys.exit(1)


class DownloadThread(QThread):
    """Thread for downloading lwjgl3ify release"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, url, destination):
        super().__init__()
        self.url = url
        self.destination = destination
    
    def run(self):
        try:
            response = requests.get(self.url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(self.destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            self.progress.emit(progress)
            
            self.finished.emit(self.destination)
        except Exception as e:
            self.error.emit(str(e))


class ExtractThread(QThread):
    """Thread for extracting the zip file"""
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, zip_path, destination):
        super().__init__()
        self.zip_path = zip_path
        self.destination = destination
    
    def run(self):
        try:
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                members = zip_ref.namelist()
                total_files = len(members)
                
                for i, member in enumerate(members):
                    zip_ref.extract(member, self.destination)
                    progress = int((i + 1) / total_files * 100)
                    self.progress.emit(progress)
            
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class PrismInstance:
    """Represents a Prism Launcher instance"""
    def __init__(self, path: Path, name: str):
        self.path = path
        self.name = name
    
    def __str__(self):
        return self.name


class LWJGL3ifyInstaller(QMainWindow):
    def __init__(self):
        super().__init__()
        self.instances_folder = None
        self.instances: List[PrismInstance] = []
        self.selected_instance: Optional[PrismInstance] = None
        
        # Initialize settings
        self.settings = QSettings("LWJGL3ifyInstaller", "Settings")
        
        self.init_ui()
        self.load_saved_folder()
        
    def init_ui(self):
        self.setWindowTitle("LWJGL3ify Installer for Prism Launcher")
        self.setGeometry(100, 100, 600, 500)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("LWJGL3ify Installer")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Step 1: Select instances folder
        step1_layout = QHBoxLayout()
        self.folder_label = QLabel("No instances folder selected")
        self.browse_button = QPushButton("Browse Instances Folder")
        self.browse_button.clicked.connect(self.browse_instances_folder)
        step1_layout.addWidget(QLabel("1. "))
        step1_layout.addWidget(self.folder_label)
        step1_layout.addWidget(self.browse_button)
        layout.addLayout(step1_layout)
        
        # Step 2: Instance list
        layout.addWidget(QLabel("2. Select an instance:"))
        self.instance_list = QListWidget()
        self.instance_list.itemClicked.connect(self.on_instance_selected)
        layout.addWidget(self.instance_list)
        
        # Step 3: Install button
        step3_layout = QHBoxLayout()
        step3_layout.addWidget(QLabel("3. "))
        self.install_button = QPushButton("Download and Install LWJGL3ify")
        self.install_button.clicked.connect(self.install_lwjgl3ify)
        self.install_button.setEnabled(False)
        step3_layout.addWidget(self.install_button)
        layout.addLayout(step3_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Log area
        layout.addWidget(QLabel("Log:"))
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)
        
        # Center the window
        self.center_window()
    
    def center_window(self):
        """Center the window on the screen"""
        screen = QApplication.primaryScreen().geometry()
        window = self.geometry()
        self.move(
            (screen.width() - window.width()) // 2,
            (screen.height() - window.height()) // 2
        )
    
    def log(self, message: str):
        """Add message to log"""
        self.log_text.append(message)
        print(message)  # Also print to console
    
    def load_saved_folder(self):
        """Load previously saved instances folder"""
        saved_folder = self.settings.value("instances_folder", "")
        if saved_folder and os.path.exists(saved_folder):
            self.instances_folder = Path(saved_folder)
            self.folder_label.setText(f"Selected: {saved_folder}")
            self.log(f"Loaded saved instances folder: {saved_folder}")
            self.scan_instances()
        else:
            self.log("No saved instances folder found")
    
    def save_folder(self, folder_path: str):
        """Save the instances folder path"""
        self.settings.setValue("instances_folder", folder_path)
        self.log(f"Saved instances folder: {folder_path}")
    
    def browse_instances_folder(self):
        """Browse for Prism Launcher instances folder"""
        # Start from saved folder if it exists, otherwise from home
        start_dir = self.settings.value("instances_folder", os.path.expanduser("~"))
        
        folder = QFileDialog.getExistingDirectory(
            self, 
            "Select Prism Launcher Instances Folder",
            start_dir
        )
        
        if folder:
            self.instances_folder = Path(folder)
            self.folder_label.setText(f"Selected: {folder}")
            self.log(f"Selected instances folder: {folder}")
            self.save_folder(folder)  # Save the folder path
            self.scan_instances()
    
    def scan_instances(self):
        """Scan for instances in the selected folder"""
        if not self.instances_folder:
            return
        
        self.instances.clear()
        self.instance_list.clear()
        
        try:
            for item in self.instances_folder.iterdir():
                if item.is_dir():
                    instance_cfg = item / "instance.cfg"
                    if instance_cfg.exists():
                        instance = self.parse_instance_config(item, instance_cfg)
                        if instance:
                            self.instances.append(instance)
                            list_item = QListWidgetItem(instance.name)
                            list_item.setData(Qt.ItemDataRole.UserRole, instance)
                            self.instance_list.addItem(list_item)
            
            self.log(f"Found {len(self.instances)} instances")
            
        except Exception as e:
            self.log(f"Error scanning instances: {e}")
            QMessageBox.critical(self, "Error", f"Failed to scan instances: {e}")
    
    def parse_instance_config(self, instance_path: Path, config_path: Path) -> Optional[PrismInstance]:
        """Parse instance.cfg file to get instance name"""
        try:
            config = configparser.ConfigParser()
            config.read(config_path)
            
            # Try different sections where name might be stored
            name = None
            for section in config.sections():
                if 'name' in config[section]:
                    name = config[section]['name']
                    break
            
            # If no section found, try reading as key-value pairs without sections
            if not name:
                with open(config_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('name='):
                            name = line.split('=', 1)[1]
                            break
            
            if name:
                return PrismInstance(instance_path, name)
            else:
                # Fallback to folder name
                return PrismInstance(instance_path, instance_path.name)
                
        except Exception as e:
            self.log(f"Error reading config for {instance_path.name}: {e}")
            # Fallback to folder name
            return PrismInstance(instance_path, instance_path.name)
    
    def on_instance_selected(self, item: QListWidgetItem):
        """Handle instance selection"""
        self.selected_instance = item.data(Qt.ItemDataRole.UserRole)
        self.install_button.setEnabled(True)
        self.log(f"Selected instance: {self.selected_instance.name}")
    
    def get_latest_release_url(self) -> Optional[str]:
        """Get the latest lwjgl3ify release download URL"""
        try:
            api_url = "https://api.github.com/repos/GTNewHorizons/lwjgl3ify/releases/latest"
            response = requests.get(api_url)
            response.raise_for_status()
            
            release_data = response.json()
            tag_name = release_data['tag_name']
            
            # Construct the download URL
            download_url = f"https://github.com/GTNewHorizons/lwjgl3ify/releases/download/{tag_name}/lwjgl3ify-{tag_name}-multimc.zip"
            
            self.log(f"Latest version: {tag_name}")
            return download_url
            
        except Exception as e:
            self.log(f"Error getting latest release: {e}")
            # Fallback to the URL provided in the requirements
            return "https://github.com/GTNewHorizons/lwjgl3ify/releases/download/2.1.14/lwjgl3ify-2.1.14-multimc.zip"
    
    def install_lwjgl3ify(self):
        """Download and install lwjgl3ify"""
        if not self.selected_instance:
            QMessageBox.warning(self, "Warning", "Please select an instance first")
            return
        
        self.install_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Get download URL
        download_url = self.get_latest_release_url()
        if not download_url:
            QMessageBox.critical(self, "Error", "Failed to get download URL")
            self.install_button.setEnabled(True)
            self.progress_bar.setVisible(False)
            return
        
        # Create temporary file for download
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, "lwjgl3ify.zip")
        
        self.log(f"Downloading from: {download_url}")
        
        # Start download
        self.download_thread = DownloadThread(download_url, zip_path)
        self.download_thread.progress.connect(self.progress_bar.setValue)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.error.connect(self.on_download_error)
        self.download_thread.start()
    
    def on_download_finished(self, zip_path: str):
        """Handle download completion"""
        self.log("Download completed")
        self.log("Extracting files...")
        
        # Extract to instance folder
        destination = self.selected_instance.path
        
        self.extract_thread = ExtractThread(zip_path, str(destination))
        self.extract_thread.progress.connect(self.progress_bar.setValue)
        self.extract_thread.finished.connect(self.on_extract_finished)
        self.extract_thread.error.connect(self.on_extract_error)
        self.extract_thread.start()
    
    def on_download_error(self, error: str):
        """Handle download error"""
        self.log(f"Download failed: {error}")
        QMessageBox.critical(self, "Download Error", f"Failed to download lwjgl3ify:\n{error}")
        self.install_button.setEnabled(True)
        self.progress_bar.setVisible(False)
    
    def on_extract_finished(self):
        """Handle extraction completion"""
        self.log("Installation completed successfully!")
        QMessageBox.information(self, "Success", "LWJGL3ify has been installed successfully!")
        self.install_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
    
    def on_extract_error(self, error: str):
        """Handle extraction error"""
        self.log(f"Extraction failed: {error}")
        QMessageBox.critical(self, "Extraction Error", f"Failed to extract lwjgl3ify:\n{error}")
        self.install_button.setEnabled(True)
        self.progress_bar.setVisible(False)


def main():
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("LWJGL3ify Installer")
    app.setApplicationVersion("1.0")
    
    # Create and show the main window
    installer = LWJGL3ifyInstaller()
    installer.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 