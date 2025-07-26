import sys
import os
import json
import hashlib
import zipfile
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog, QTextEdit, QProgressBar,
    QStackedWidget, QFrame, QScrollArea, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QSplitter
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QPalette, QColor, QPixmap, QPainter, QIcon


class FileProcessor(QThread):
    """Worker thread for file processing operations"""
    progress_updated = Signal(int)
    status_updated = Signal(str)
    finished_signal = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, operation, folder_path=None, json_data=None, zip_path=None):
        super().__init__()
        self.operation = operation
        self.folder_path = folder_path
        self.json_data = json_data
        self.zip_path = zip_path

    def run(self):
        try:
            if self.operation == "scan_folder":
                result = self.scan_folder()
            elif self.operation == "compare_versions":
                result = self.compare_versions()
            elif self.operation == "create_zip":
                result = self.create_zip()
            elif self.operation == "equalize":
                result = self.equalize_versions()
            else:
                result = {}
            
            self.finished_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))

    def scan_folder(self):
        """Scan folder and generate hash data"""
        if not self.folder_path or not os.path.exists(self.folder_path):
            raise Exception("Invalid folder path")
        
        file_data = []
        total_files = sum(len(files) for _, _, files in os.walk(self.folder_path))
        processed = 0
        
        self.status_updated.emit("Scanning files...")
        
        for root, dirs, files in os.walk(self.folder_path):
            for file in files:
                try:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, self.folder_path)
                    
                    # Calculate MD5 hash
                    hash_md5 = hashlib.md5()
                    with open(file_path, "rb") as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hash_md5.update(chunk)
                    
                    file_data.append({
                        "fileName": relative_path.replace(os.sep, '/'),
                        "hash": hash_md5.hexdigest()
                    })
                    
                    processed += 1
                    progress = int((processed / total_files) * 100)
                    self.progress_updated.emit(progress)
                    self.status_updated.emit(f"Processing: {relative_path}")
                    
                except Exception as e:
                    # Continue processing other files if one fails
                    print(f"Error processing {file}: {e}")
                    continue
        
        return {"files": file_data}

    def compare_versions(self):
        """Compare two versions and generate conversion data"""
        to_version_data = self.json_data["to_version"]
        from_version_data = self.json_data["from_version"]
        
        to_files = {item["fileName"]: item["hash"] for item in to_version_data["files"]}
        from_files = {item["fileName"]: item["hash"] for item in from_version_data["files"]}
        
        convert_data = []
        
        # Check files that need to be copied (missing or different hash)
        for filename, hash_value in to_files.items():
            if filename not in from_files or from_files[filename] != hash_value:
                convert_data.append({
                    "filename": filename,
                    "status": "copy"
                })
        
        # Check files that need to be moved (exist in from but not in to)
        for filename in from_files:
            if filename not in to_files:
                convert_data.append({
                    "filename": filename,
                    "status": "move"
                })
        
        return {"convert_data": convert_data}

    def create_zip(self):
        """Create ZIP file with files marked for copying"""
        convert_data = self.json_data["convert_data"]
        to_folder = self.json_data["to_folder"]
        
        files_to_zip = [item for item in convert_data if item["status"] == "copy"]
        
        if not files_to_zip:
            return {"zip_path": None, "message": "No files to zip"}
        
        zip_path = os.path.join(os.path.dirname(to_folder), "version_update.zip")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for i, item in enumerate(files_to_zip):
                file_path = os.path.join(to_folder, item["filename"].replace('/', os.sep))
                if os.path.exists(file_path):
                    zipf.write(file_path, item["filename"])
                
                progress = int(((i + 1) / len(files_to_zip)) * 100)
                self.progress_updated.emit(progress)
                self.status_updated.emit(f"Adding to ZIP: {item['filename']}")
        
        return {"zip_path": zip_path}

    def equalize_versions(self):
        """Extract ZIP and move extra files"""
        convert_data = self.json_data["convert_data"]
        from_folder = self.json_data["from_folder"]
        zip_path = self.zip_path
        
        # Extract ZIP files
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(from_folder)
        
        # Move extra files
        extra_files_dir = os.path.join(from_folder, "ExtraFiles_VersionEqualizer")
        os.makedirs(extra_files_dir, exist_ok=True)
        
        moved_files = []
        for item in convert_data:
            if item["status"] == "move":
                source_path = os.path.join(from_folder, item["filename"].replace('/', os.sep))
                if os.path.exists(source_path):
                    dest_path = os.path.join(extra_files_dir, item["filename"].replace('/', os.sep))
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    shutil.move(source_path, dest_path)
                    moved_files.append(item["filename"])
        
        return {"moved_files": moved_files}


class StyledButton(QPushButton):
    """Custom styled button with hover effects"""
    def __init__(self, text, primary=False):
        super().__init__(text)
        self.primary = primary
        self.setMinimumHeight(45)
        self.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        self.apply_style()

    def apply_style(self):
        if self.primary:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #4A9EFF, stop:1 #2E7BFF);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #5BADFF, stop:1 #3F8CFF);
                    transform: translateY(-1px);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #3F8CFF, stop:1 #1E6AFF);
                }
                QPushButton:disabled {
                    background: #3A3A3A;
                    color: #666;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: #3A3A3A;
                    color: #E0E0E0;
                    border: 1px solid #555;
                    border-radius: 8px;
                    padding: 12px 24px;
                }
                QPushButton:hover {
                    background: #454545;
                    border-color: #666;
                }
                QPushButton:pressed {
                    background: #2F2F2F;
                }
                QPushButton:disabled {
                    background: #2A2A2A;
                    color: #555;
                    border-color: #444;
                }
            """)


class HomePage(QWidget):
    """Main home page with navigation options"""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(40)
        layout.setContentsMargins(60, 60, 60, 60)

        # Title
        title = QLabel("VersionEqualizer")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        title.setStyleSheet("color: #4A9EFF; margin-bottom: 20px;")
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Match software versions across different systems")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Segoe UI", 14))
        subtitle.setStyleSheet("color: #B0B0B0; margin-bottom: 40px;")
        layout.addWidget(subtitle)

        # Buttons container
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setSpacing(30)

        # Checker button
        checker_btn = StyledButton("🔍 Checker", primary=True)
        checker_btn.setMinimumSize(200, 80)
        checker_btn.clicked.connect(lambda: self.main_window.show_page("checker"))
        buttons_layout.addWidget(checker_btn)

        # Match button
        match_btn = StyledButton("🔄 Match", primary=True)
        match_btn.setMinimumSize(200, 80)
        match_btn.clicked.connect(lambda: self.main_window.show_page("match"))
        buttons_layout.addWidget(match_btn)

        layout.addWidget(buttons_container)
        layout.addStretch()
        self.setLayout(layout)


class CheckerPage(QWidget):
    """Checker page with To Version and From Version options"""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.to_version_data = None
        self.from_version_data = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # Header
        header_layout = QHBoxLayout()
        back_btn = StyledButton("← Back")
        back_btn.clicked.connect(lambda: self.main_window.show_page("home"))
        header_layout.addWidget(back_btn)
        header_layout.addStretch()

        title = QLabel("Version Checker")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #4A9EFF;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Content area
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setSpacing(30)

        # To Version section
        to_version_frame = self.create_version_frame("To Version", "to_version")
        content_layout.addWidget(to_version_frame)

        # From Version section
        from_version_frame = self.create_version_frame("From Version", "from_version")
        content_layout.addWidget(from_version_frame)

        layout.addWidget(content_widget)

        # Progress area
        self.progress_widget = QWidget()
        progress_layout = QVBoxLayout(self.progress_widget)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #555;
                border-radius: 8px;
                text-align: center;
                background: #2A2A2A;
                color: white;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4A9EFF, stop:1 #2E7BFF);
                border-radius: 6px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #B0B0B0; padding: 10px;")
        progress_layout.addWidget(self.status_label)
        
        self.progress_widget.hide()
        layout.addWidget(self.progress_widget)

        # Compare button
        self.compare_btn = StyledButton("Proceed to Check", primary=True)
        self.compare_btn.clicked.connect(self.compare_versions)
        self.compare_btn.setEnabled(False)
        layout.addWidget(self.compare_btn)

        self.setLayout(layout)

    def create_version_frame(self, title, version_type):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: #2A2A2A;
                border: 1px solid #444;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(20)

        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #4A9EFF; border: none;")
        layout.addWidget(title_label)

        if version_type == "to_version":
            # Folder selection
            select_btn = StyledButton("Select Folder")
            select_btn.clicked.connect(self.select_to_version_folder)
            layout.addWidget(select_btn)

            self.to_folder_label = QLabel("No folder selected")
            self.to_folder_label.setStyleSheet("color: #B0B0B0; border: none; padding: 10px;")
            self.to_folder_label.setWordWrap(True)
            layout.addWidget(self.to_folder_label)

        else:
            # JSON file selection
            json_btn = StyledButton("Load JSON File")
            json_btn.clicked.connect(self.load_from_version_json)
            layout.addWidget(json_btn)

            self.json_file_label = QLabel("No JSON file loaded")
            self.json_file_label.setStyleSheet("color: #B0B0B0; border: none; padding: 10px;")
            self.json_file_label.setWordWrap(True)
            layout.addWidget(self.json_file_label)

            # Folder selection
            folder_btn = StyledButton("Select Folder")
            folder_btn.clicked.connect(self.select_from_version_folder)
            layout.addWidget(folder_btn)

            self.from_folder_label = QLabel("No folder selected")
            self.from_folder_label.setStyleSheet("color: #B0B0B0; border: none; padding: 10px;")
            self.from_folder_label.setWordWrap(True)
            layout.addWidget(self.from_folder_label)

        layout.addStretch()
        return frame

    def select_to_version_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select To Version Folder")
        if folder:
            self.to_folder_label.setText(f"Selected: {folder}")
            self.scan_to_version_folder(folder)

    def scan_to_version_folder(self, folder_path):
        self.progress_widget.show()
        self.progress_bar.setValue(0)
        self.status_label.setText("Scanning to version folder...")

        self.worker = FileProcessor("scan_folder", folder_path=folder_path)
        self.worker.progress_updated.connect(self.progress_bar.setValue)
        self.worker.status_updated.connect(self.status_label.setText)
        self.worker.finished_signal.connect(self.on_to_version_scanned)
        self.worker.error_signal.connect(self.show_error)
        self.worker.start()

    def on_to_version_scanned(self, result):
        self.to_version_data = result
        self.progress_widget.hide()
        
        # Save JSON file
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save To Version JSON", "to_version.json", "JSON files (*.json)"
        )
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "Success", f"To Version data saved to {file_path}")
        
        self.check_ready_state()

    def load_from_version_json(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load From Version JSON", "", "JSON files (*.json)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.to_version_data = json.load(f)
                self.json_file_label.setText(f"Loaded: {os.path.basename(file_path)}")
                self.check_ready_state()
            except Exception as e:
                self.show_error(f"Error loading JSON: {str(e)}")

    def select_from_version_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select From Version Folder")
        if folder:
            self.from_folder_label.setText(f"Selected: {folder}")
            self.scan_from_version_folder(folder)

    def scan_from_version_folder(self, folder_path):
        self.progress_widget.show()
        self.progress_bar.setValue(0)
        self.status_label.setText("Scanning from version folder...")

        self.worker = FileProcessor("scan_folder", folder_path=folder_path)
        self.worker.progress_updated.connect(self.progress_bar.setValue)
        self.worker.status_updated.connect(self.status_label.setText)
        self.worker.finished_signal.connect(self.on_from_version_scanned)
        self.worker.error_signal.connect(self.show_error)
        self.worker.start()

    def on_from_version_scanned(self, result):
        self.from_version_data = result
        self.progress_widget.hide()
        self.check_ready_state()

    def check_ready_state(self):
        if self.to_version_data and self.from_version_data:
            self.compare_btn.setEnabled(True)

    def compare_versions(self):
        if not self.to_version_data or not self.from_version_data:
            return

        self.progress_widget.show()
        self.progress_bar.setValue(0)
        self.status_label.setText("Comparing versions...")

        compare_data = {
            "to_version": self.to_version_data,
            "from_version": self.from_version_data
        }

        self.worker = FileProcessor("compare_versions", json_data=compare_data)
        self.worker.finished_signal.connect(self.on_comparison_finished)
        self.worker.error_signal.connect(self.show_error)
        self.worker.start()

    def on_comparison_finished(self, result):
        self.progress_widget.hide()
        
        convert_data = result["convert_data"]
        
        # Save convert.json
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Conversion Data", "convert.json", "JSON files (*.json)"
        )
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(convert_data, f, indent=2, ensure_ascii=False)
            
            # Show results
            copy_count = len([item for item in convert_data if item["status"] == "copy"])
            move_count = len([item for item in convert_data if item["status"] == "move"])
            
            QMessageBox.information(
                self, "Comparison Complete",
                f"Files to copy: {copy_count}\n"
                f"Files to move: {move_count}\n\n"
                f"Conversion data saved to {file_path}"
            )

    def show_error(self, error_message):
        self.progress_widget.hide()
        QMessageBox.critical(self, "Error", error_message)


class MatchPage(QWidget):
    """Match page with Prepare and Equalize options"""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # Header
        header_layout = QHBoxLayout()
        back_btn = StyledButton("← Back")
        back_btn.clicked.connect(lambda: self.main_window.show_page("home"))
        header_layout.addWidget(back_btn)
        header_layout.addStretch()

        title = QLabel("Version Matcher")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #4A9EFF;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Content area
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setSpacing(30)

        # Prepare section
        prepare_frame = self.create_prepare_frame()
        content_layout.addWidget(prepare_frame)

        # Equalize section
        equalize_frame = self.create_equalize_frame()
        content_layout.addWidget(equalize_frame)

        layout.addWidget(content_widget)

        # Progress area
        self.progress_widget = QWidget()
        progress_layout = QVBoxLayout(self.progress_widget)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #555;
                border-radius: 8px;
                text-align: center;
                background: #2A2A2A;
                color: white;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4A9EFF, stop:1 #2E7BFF);
                border-radius: 6px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #B0B0B0; padding: 10px;")
        progress_layout.addWidget(self.status_label)
        
        self.progress_widget.hide()
        layout.addWidget(self.progress_widget)

        self.setLayout(layout)

    def create_prepare_frame(self):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: #2A2A2A;
                border: 1px solid #444;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(20)

        # Title
        title_label = QLabel("📦 Prepare")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #4A9EFF; border: none;")
        layout.addWidget(title_label)

        # Convert JSON selection
        json_btn = StyledButton("Select convert.json")
        json_btn.clicked.connect(self.select_convert_json)
        layout.addWidget(json_btn)

        self.convert_json_label = QLabel("No JSON file selected")
        self.convert_json_label.setStyleSheet("color: #B0B0B0; border: none; padding: 10px;")
        self.convert_json_label.setWordWrap(True)
        layout.addWidget(self.convert_json_label)

        # To Version folder selection
        folder_btn = StyledButton("Select To Version Folder")
        folder_btn.clicked.connect(self.select_to_folder)
        layout.addWidget(folder_btn)

        self.to_folder_label = QLabel("No folder selected")
        self.to_folder_label.setStyleSheet("color: #B0B0B0; border: none; padding: 10px;")
        self.to_folder_label.setWordWrap(True)
        layout.addWidget(self.to_folder_label)

        # Create ZIP button
        self.create_zip_btn = StyledButton("Create ZIP Package", primary=True)
        self.create_zip_btn.clicked.connect(self.create_zip_package)
        self.create_zip_btn.setEnabled(False)
        layout.addWidget(self.create_zip_btn)

        layout.addStretch()
        return frame

    def create_equalize_frame(self):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: #2A2A2A;
                border: 1px solid #444;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(20)

        # Title
        title_label = QLabel("⚖️ Equalize")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #4A9EFF; border: none;")
        layout.addWidget(title_label)

        # Convert JSON selection
        eq_json_btn = StyledButton("Select convert.json")
        eq_json_btn.clicked.connect(self.select_equalize_json)
        layout.addWidget(eq_json_btn)

        self.eq_json_label = QLabel("No JSON file selected")
        self.eq_json_label.setStyleSheet("color: #B0B0B0; border: none; padding: 10px;")
        self.eq_json_label.setWordWrap(True)
        layout.addWidget(self.eq_json_label)

        # ZIP file selection
        zip_btn = StyledButton("Select ZIP File")
        zip_btn.clicked.connect(self.select_zip_file)
        layout.addWidget(zip_btn)

        self.zip_file_label = QLabel("No ZIP file selected")
        self.zip_file_label.setStyleSheet("color: #B0B0B0; border: none; padding: 10px;")
        self.zip_file_label.setWordWrap(True)
        layout.addWidget(self.zip_file_label)

        # From Version folder selection
        from_folder_btn = StyledButton("Select From Version Folder")
        from_folder_btn.clicked.connect(self.select_from_folder)
        layout.addWidget(from_folder_btn)

        self.from_folder_label = QLabel("No folder selected")
        self.from_folder_label.setStyleSheet("color: #B0B0B0; border: none; padding: 10px;")
        self.from_folder_label.setWordWrap(True)
        layout.addWidget(self.from_folder_label)

        # Equalize button
        self.equalize_btn = StyledButton("Start Equalization", primary=True)
        self.equalize_btn.clicked.connect(self.start_equalization)
        self.equalize_btn.setEnabled(False)
        layout.addWidget(self.equalize_btn)

        layout.addStretch()
        return frame

    def select_convert_json(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select convert.json", "", "JSON files (*.json)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.prepare_convert_data = json.load(f)
                self.convert_json_label.setText(f"Selected: {os.path.basename(file_path)}")
                self.check_prepare_ready()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading JSON: {str(e)}")

    def select_to_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select To Version Folder")
        if folder:
            self.prepare_to_folder = folder
            self.to_folder_label.setText(f"Selected: {folder}")
            self.check_prepare_ready()

    def check_prepare_ready(self):
        if hasattr(self, 'prepare_convert_data') and hasattr(self, 'prepare_to_folder'):
            self.create_zip_btn.setEnabled(True)

    def create_zip_package(self):
        self.progress_widget.show()
        self.progress_bar.setValue(0)
        self.status_label.setText("Creating ZIP package...")

        zip_data = {
            "convert_data": self.prepare_convert_data,
            "to_folder": self.prepare_to_folder
        }

        self.worker = FileProcessor("create_zip", json_data=zip_data)
        self.worker.progress_updated.connect(self.progress_bar.setValue)
        self.worker.status_updated.connect(self.status_label.setText)
        self.worker.finished_signal.connect(self.on_zip_created)
        self.worker.error_signal.connect(self.show_error)
        self.worker.start()

    def on_zip_created(self, result):
        self.progress_widget.hide()
        if result.get("zip_path"):
            QMessageBox.information(
                self, "ZIP Created",
                f"ZIP package created successfully!\n\n"
                f"Location: {result['zip_path']}\n\n"
                f"Send this ZIP file to the From Version user."
            )
        else:
            QMessageBox.information(
                self, "No Files to Package",
                result.get("message", "No files need to be packaged.")
            )

    def select_equalize_json(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select convert.json", "", "JSON files (*.json)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.equalize_convert_data = json.load(f)
                self.eq_json_label.setText(f"Selected: {os.path.basename(file_path)}")
                self.check_equalize_ready()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading JSON: {str(e)}")

    def select_zip_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select ZIP File", "", "ZIP files (*.zip)"
        )
        if file_path:
            self.equalize_zip_path = file_path
            self.zip_file_label.setText(f"Selected: {os.path.basename(file_path)}")
            self.check_equalize_ready()

    def select_from_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select From Version Folder")
        if folder:
            self.equalize_from_folder = folder
            self.from_folder_label.setText(f"Selected: {folder}")
            self.check_equalize_ready()

    def check_equalize_ready(self):
        if (hasattr(self, 'equalize_convert_data') and 
            hasattr(self, 'equalize_zip_path') and 
            hasattr(self, 'equalize_from_folder')):
            self.equalize_btn.setEnabled(True)

    def start_equalization(self):
        self.progress_widget.show()
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting equalization...")

        equalize_data = {
            "convert_data": self.equalize_convert_data,
            "from_folder": self.equalize_from_folder
        }

        self.worker = FileProcessor(
            "equalize", 
            json_data=equalize_data, 
            zip_path=self.equalize_zip_path
        )
        self.worker.progress_updated.connect(self.progress_bar.setValue)
        self.worker.status_updated.connect(self.status_label.setText)
        self.worker.finished_signal.connect(self.on_equalization_finished)
        self.worker.error_signal.connect(self.show_error)
        self.worker.start()

    def on_equalization_finished(self, result):
        self.progress_widget.hide()
        moved_files = result.get("moved_files", [])
        
        if moved_files:
            QMessageBox.information(
                self, "Equalization Complete",
                f"Equalization completed successfully!\n\n"
                f"Files extracted from ZIP and {len(moved_files)} extra files "
                f"moved to ExtraFiles_VersionEqualizer folder."
            )
        else:
            QMessageBox.information(
                self, "Equalization Complete",
                "Equalization completed successfully!\n\n"
                "Files extracted from ZIP. No extra files to move."
            )

    def show_error(self, error_message):
        self.progress_widget.hide()
        QMessageBox.critical(self, "Error", error_message)


class MainWindow(QMainWindow):
    """Main application window"""
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.apply_dark_theme()

    def init_ui(self):
        self.setWindowTitle("VersionEqualizer")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        # Create stacked widget for page navigation
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Create pages
        self.home_page = HomePage(self)
        self.checker_page = CheckerPage(self)
        self.match_page = MatchPage(self)

        # Add pages to stack
        self.stacked_widget.addWidget(self.home_page)
        self.stacked_widget.addWidget(self.checker_page)
        self.stacked_widget.addWidget(self.match_page)

        # Show home page initially
        self.show_page("home")

    def show_page(self, page_name):
        """Navigate to specified page"""
        page_mapping = {
            "home": 0,
            "checker": 1,
            "match": 2
        }
        
        if page_name in page_mapping:
            self.stacked_widget.setCurrentIndex(page_mapping[page_name])

    def apply_dark_theme(self):
        """Apply beautiful dark theme to the application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1E1E1E;
                color: #E0E0E0;
            }
            
            QWidget {
                background-color: #1E1E1E;
                color: #E0E0E0;
                font-family: 'Segoe UI', sans-serif;
            }
            
            QLabel {
                color: #E0E0E0;
                background: transparent;
            }
            
            QTextEdit {
                background-color: #2A2A2A;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 12px;
                color: #E0E0E0;
                font-size: 11pt;
            }
            
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            
            QScrollBar:vertical {
                background: #2A2A2A;
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background: #4A4A4A;
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #5A5A5A;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            
            QTableWidget {
                background-color: #2A2A2A;
                border: 1px solid #444;
                border-radius: 8px;
                gridline-color: #444;
                color: #E0E0E0;
            }
            
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #333;
            }
            
            QTableWidget::item:selected {
                background-color: #4A9EFF;
                color: white;
            }
            
            QHeaderView::section {
                background-color: #333;
                color: #E0E0E0;
                padding: 10px;
                border: none;
                border-right: 1px solid #444;
                font-weight: bold;
            }
            
            QMessageBox {
                background-color: #2A2A2A;
                color: #E0E0E0;
            }
            
            QMessageBox QPushButton {
                background-color: #4A9EFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                min-width: 80px;
            }
            
            QMessageBox QPushButton:hover {
                background-color: #5BADFF;
            }
            
            QFileDialog {
                background-color: #1E1E1E;
                color: #E0E0E0;
            }
        """)


class VersionEqualizerApp:
    """Main application class"""
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("VersionEqualizer")
        self.app.setApplicationVersion("1.0")
        
        # Set application icon (you can add an icon file)
        # self.app.setWindowIcon(QIcon("icon.ico"))
        
        self.main_window = MainWindow()

    def run(self):
        """Run the application"""
        self.main_window.show()
        return self.app.exec()


def main():
    """Main entry point"""
    try:
        app = VersionEqualizerApp()
        sys.exit(app.run())
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()