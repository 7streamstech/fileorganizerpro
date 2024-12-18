import shutil
import sys
import os
import json
from datetime import datetime
from PyQt5.QtGui import QIcon, QPixmap, QFont, QPalette, QColor
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel,
    QSplashScreen, QMessageBox, QMenuBar, QMainWindow, QAction, QStatusBar, QProgressDialog
)
from PyQt5.QtCore import Qt, QTimer


class FileOrganizerApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Define settings attributes
        self.backup_enabled = False
        self.backup_folder = None
        self.undo_log = []  # In-memory undo log
        self.undo_log_file = "undo_log.json"  # Persistent undo log file

        # Load undo log from file on startup
        self.load_undo_log()

        # Initialize main widget
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)

        # Dynamically locate the icon file based on the executable's location
        base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        icon_path = os.path.join(base_dir, "app_icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print("Icon not found. Using default icon.")

        # Set the window title
        self.setWindowTitle('File Organizer Pro')

        # Adjust the window dimensions
        self.resize(600, 600)
        self.center_window()

        # Apply consistent theming
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#FFFFFF"))  # Clean white background
        self.setPalette(palette)

        # Add a status bar for feedback
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Layout and UI components
        self.layout = QVBoxLayout(self.main_widget)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        # Title label
        self.title_label = QLabel("Welcome to File Organizer Pro")
        self.title_label.setFont(QFont("San Francisco", 20, QFont.Bold))  # Inspired by Apple's typeface
        self.title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.title_label)

        # Subtitle label
        self.subtitle_label = QLabel("The simplest way to organize your files into folders")
        self.subtitle_label.setFont(QFont("San Francisco", 14))
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.subtitle_label)

        # Setup Box
        setup_box = QWidget(self.main_widget)
        setup_layout = QVBoxLayout(setup_box)
        setup_layout.setContentsMargins(10, 10, 10, 10)
        setup_layout.setSpacing(10)
        setup_box.setStyleSheet("border: 1px solid #CCCCCC; border-radius: 5px; background-color: #F9F9F9;")

        setup_label = QLabel("Setup")
        setup_label.setFont(QFont("San Francisco", 14, QFont.Bold))
        setup_label.setAlignment(Qt.AlignCenter)
        setup_layout.addWidget(setup_label)

        # Enable Backup Button
        self.backup_button = QPushButton('Enable Backup')
        self.backup_button.setFont(QFont("San Francisco", 10))
        self.backup_button.setFixedSize(200, 40)
        self.backup_button.setStyleSheet(
            "background-color: #F5B7B1; color: #922B21; border-radius: 5px; border: 1px solid #922B21;"
        )
        self.backup_button.clicked.connect(self.toggle_backup)
        setup_layout.addWidget(self.backup_button, alignment=Qt.AlignCenter)

        # Select Folder Button
        self.select_button = QPushButton('Select Folder')
        self.select_button.setFont(QFont("San Francisco", 12))
        self.select_button.setFixedSize(300, 50)
        self.select_button.setStyleSheet(
            "background-color: #007AFF; color: white; border-radius: 10px; border: 2px solid #007AFF;"
        )
        self.select_button.clicked.connect(self.select_folder)
        setup_layout.addWidget(self.select_button, alignment=Qt.AlignCenter)

        self.layout.addWidget(setup_box, alignment=Qt.AlignTop)

        # Organize Box
        organize_box = QWidget(self.main_widget)
        organize_layout = QVBoxLayout(organize_box)
        organize_layout.setContentsMargins(10, 10, 10, 10)
        organize_layout.setSpacing(10)
        organize_box.setStyleSheet("border: 1px solid #CCCCCC; border-radius: 5px; background-color: #FFFFFF;")

        organize_label = QLabel("Organize Files")
        organize_label.setFont(QFont("San Francisco", 14, QFont.Bold))
        organize_label.setAlignment(Qt.AlignCenter)
        organize_layout.addWidget(organize_label)

        # Organize by Date Modified Button
        self.date_button = QPushButton('Organize by Date Modified')
        self.date_button.setFont(QFont("San Francisco", 12))
        self.date_button.setFixedSize(300, 50)
        self.date_button.setStyleSheet(
            "background-color: #FF9500; color: white; border-radius: 10px;"
        )
        self.date_button.setEnabled(False)
        organize_layout.addWidget(self.date_button, alignment=Qt.AlignCenter)
        self.date_button.clicked.connect(lambda: self.organize_files("date"))

        # Organize by File Extension Button
        self.extension_button = QPushButton('Organize by File Extension')
        self.extension_button.setFont(QFont("San Francisco", 12))
        self.extension_button.setFixedSize(300, 50)
        self.extension_button.setStyleSheet(
            "background-color: #5856D6; color: white; border-radius: 10px;"
        )
        self.extension_button.setEnabled(False)
        organize_layout.addWidget(self.extension_button, alignment=Qt.AlignCenter)
        self.extension_button.clicked.connect(lambda: self.organize_files("extension"))

        # Organize by Size Button
        self.size_button = QPushButton('Organize by File Size')
        self.size_button.setFont(QFont("San Francisco", 12))
        self.size_button.setFixedSize(300, 50)
        self.size_button.setStyleSheet(
            "background-color: #16A085; color: white; border-radius: 10px;"
        )
        self.size_button.setEnabled(False)
        organize_layout.addWidget(self.size_button, alignment=Qt.AlignCenter)
        self.size_button.clicked.connect(lambda: self.organize_files("size"))

        self.layout.addWidget(organize_box, alignment=Qt.AlignTop)

        # Selected Folder Label
        self.selected_folder_label = QLabel("")
        font = QFont("San Francisco", 11)
        font.setItalic(True)  # Apply italic style
        self.selected_folder_label.setFont(font)
        self.selected_folder_label.setStyleSheet("color: #555555; text-align: center;")
        self.selected_folder_label.setAlignment(Qt.AlignCenter)
        self.selected_folder_label.setWordWrap(True)
        self.selected_folder_label.hide()  # Initially hidden
        self.layout.addWidget(self.selected_folder_label)

        # Initialize menu bar
        self.init_menu_bar()

    def init_menu_bar(self):
        """Initialize the menu bar with Settings and Help menus."""
        menu_bar = QMenuBar(self)

        # Settings menu
        settings_menu = menu_bar.addMenu("Settings")

        # Undo organization action
        undo_action = QAction("Undo Organization", self)
        undo_action.setEnabled(bool(self.undo_log))  # Enable only if undo log exists
        undo_action.triggered.connect(self.undo_organization)
        self.undo_files_action = undo_action  # Reference for enabling/disabling
        settings_menu.addAction(undo_action)

        # Help menu
        help_menu = menu_bar.addMenu("Help")

        # How to Use
        how_to_action = QAction("How to Use", self)
        how_to_action.triggered.connect(self.show_how_to_use)
        help_menu.addAction(how_to_action)

        # About
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        self.setMenuBar(menu_bar)

    def center_window(self):
        """Center the application window on the screen."""
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def toggle_backup(self):
        """Enable or disable the backup feature."""
        self.backup_enabled = not self.backup_enabled
        if self.backup_enabled:
            self.backup_button.setText("Disable Backup")
            self.backup_button.setStyleSheet(
                "background-color: #C0392B; color: white; border-radius: 5px; border: 1px solid #922B21;"
            )  # Dark red for active state
            self.status_bar.showMessage("Backup enabled")
        else:
            self.backup_button.setText("Enable Backup")
            self.backup_button.setStyleSheet(
                "background-color: #F5B7B1; color: #922B21; border-radius: 5px; border: 1px solid #922B21;"
            )  # Light red for default state
            self.status_bar.showMessage("Backup disabled")

    # Full code continues with organize_files, undo_organization, and other methods.

    def select_folder(self):
        """Allow the user to select a folder."""
        folder = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder:
            self.folder_path = folder
            self.selected_folder_label.setText(f"Selected folder: {folder}")
            self.selected_folder_label.show()  # Display the folder path
            self.date_button.setEnabled(True)
            self.extension_button.setEnabled(True)
            self.size_button.setEnabled(True)
            self.status_bar.showMessage(f"Folder selected: {folder}")

    def organize_files(self, method):
        """Organize files based on the chosen method with progress animation."""
        try:
            # Gather files to organize
            files = [f for f in os.listdir(self.folder_path) if os.path.isfile(os.path.join(self.folder_path, f))]
            total_files = len(files)

            if total_files == 0:
                QMessageBox.information(
                    self,
                    "No Files Found",
                    "No files were found to organize in the selected folder."
                )
                return

            # Initialize the progress dialog
            progress_dialog = QProgressDialog("Organizing files...", "Cancel", 0, 100, self)
            progress_dialog.setWindowModality(Qt.WindowModal)
            progress_dialog.setWindowTitle("Progress")
            progress_dialog.setValue(0)

            undo_entry = []

            for i, filename in enumerate(files):
                file_path = os.path.join(self.folder_path, filename)

                if method == "date":
                    last_modified = os.path.getmtime(file_path)
                    date_folder = os.path.join(self.folder_path, self.get_date_folder(last_modified))
                    os.makedirs(date_folder, exist_ok=True)
                    shutil.move(file_path, os.path.join(date_folder, filename))
                    undo_entry.append((os.path.join(date_folder, filename), file_path))
                elif method == "extension":
                    file_extension = filename.split('.')[-1]
                    folder_path = os.path.join(self.folder_path, file_extension)
                    os.makedirs(folder_path, exist_ok=True)
                    shutil.move(file_path, os.path.join(folder_path, filename))
                    undo_entry.append((os.path.join(folder_path, filename), file_path))
                elif method == "size":
                    size_category = self.get_size_category(file_path)
                    size_folder = os.path.join(self.folder_path, size_category)
                    os.makedirs(size_folder, exist_ok=True)
                    shutil.move(file_path, os.path.join(size_folder, filename))
                    undo_entry.append((os.path.join(size_folder, filename), file_path))

                # Update progress
                progress_dialog.setValue(int((i + 1) / total_files * 100))
                if progress_dialog.wasCanceled():
                    QMessageBox.warning(self, "Cancelled", "File organization was cancelled.")
                    return

            self.undo_log = undo_entry
            progress_dialog.setValue(100)  # Ensure progress completes
            self.status_bar.showMessage("Files organized successfully!")
            QMessageBox.information(self, "Success", "Files organized successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def get_date_folder(self, timestamp):
        """Generate a folder path based on a timestamp."""
        dt = datetime.fromtimestamp(timestamp)
        return os.path.join(str(dt.year), dt.strftime("%B"))  # e.g., "2023/December"

    def get_size_category(self, file_path):
        """Categorize a file based on its size."""
        size_in_bytes = os.path.getsize(file_path)
        if size_in_bytes < 1024:  # Less than 1 KB
            return "Small Files"
        elif size_in_bytes < 1024 * 1024:  # Less than 1 MB
            return "Medium Files"
        else:  # Larger than 1 MB
            return "Large Files"

    def undo_organization(self):
        """Undo the last file organization."""
        if not self.undo_log:
            QMessageBox.information(
                self,
                "Undo Not Available",
                "No organization actions to undo."
            )
            return

        try:
            for src, dst in self.undo_log:
                shutil.move(src, dst)
            self.undo_log = []
            self.undo_files_action.setEnabled(False)
            self.status_bar.showMessage("Undo completed.")
            QMessageBox.information(self, "Undo Complete", "Undo completed successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def save_undo_log(self):
        """Save the undo log to a file."""
        with open(self.undo_log_file, "w") as file:
            json.dump(self.undo_log, file)

    def load_undo_log(self):
        """Load the undo log from a file."""
        if os.path.exists(self.undo_log_file):
            with open(self.undo_log_file, "r") as file:
                self.undo_log = json.load(file)

    def show_how_to_use(self):
        """Display a simple guide on how to use the app."""
        QMessageBox.information(
            self,
            "How to Use",
            "1. Select a folder to organize.\n"
            "2. Choose an organization method (Date, Extension, or Size).\n"
            "3. Optional: Enable backups for safety.\n"
            "4. Use 'Undo Organization' if needed."
        )

    def show_about(self):
        """Display information about the app."""
        QMessageBox.information(
            self,
            "About",
            "File Organizer Pro v1.8.3\n"
            "Developed by 7 Streams Tech.\n"
            "Contact: support@7streamstech.com"
        )


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Create splash screen
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    splash_path = os.path.join(base_dir, "splash_screen.png")
    if os.path.exists(splash_path):
        pixmap = QPixmap(splash_path).scaled(500, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        splash = QSplashScreen(pixmap, Qt.WindowStaysOnTopHint)
        splash.show()
        QTimer.singleShot(3000, splash.close)

    # Launch app
    window = FileOrganizerApp()
    QTimer.singleShot(3000, window.show)
    sys.exit(app.exec_())
