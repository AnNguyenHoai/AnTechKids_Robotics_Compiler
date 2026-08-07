"""
RoboStudio Main Window UI – coded manually with PySide6.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QPushButton, QTextEdit, QLabel, QFrame, QMenuBar, QMenu, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QAction, QCursor


class Ui_MainWindow:
    def setupUi(self, MainWindow):
        MainWindow.setWindowTitle("RoboStudio")
        MainWindow.resize(850, 650)

        # Menu Bar
        menubar = QMenuBar(MainWindow)
        MainWindow.setMenuBar(menubar)

        # File menu
        self.file_menu = menubar.addMenu("&File")
        self.file_menu.setObjectName("menuFile")  # <-- ADDED

        # Examples menu
        self.examples_menu = menubar.addMenu("&Examples")

        # Help menu
        help_menu = menubar.addMenu("&Help")
        self.about_action = QAction("About", MainWindow)
        help_menu.addAction(self.about_action)

        # Central widget
        central_widget = QWidget(MainWindow)
        MainWindow.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Code Editor
        self.code_editor = QPlainTextEdit()
        self.code_editor.setPlaceholderText("Paste your RoboSim Python code here...")
        font = QFont("Courier New", 11)
        self.code_editor.setFont(font)
        self.code_editor.setMinimumHeight(250)
        main_layout.addWidget(self.code_editor)

        # Button row
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.compile_button = QPushButton("Compile")
        self.compile_button.setMinimumWidth(100)
        self.compile_button.setEnabled(True)
        button_layout.addWidget(self.compile_button)

        self.open_firmware_button = QPushButton("Open Firmware")
        self.open_firmware_button.setMinimumWidth(100)
        button_layout.addWidget(self.open_firmware_button)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)

        # Build Output
        self.build_output = QTextEdit()
        self.build_output.setReadOnly(True)
        self.build_output.setPlaceholderText("Build output will appear here...")
        font_output = QFont("Courier New", 10)
        self.build_output.setFont(font_output)
        self.build_output.setMinimumHeight(150)
        main_layout.addWidget(self.build_output)

        # Status Bar
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-weight: bold; color: green;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        main_layout.addLayout(status_layout)

        # Store menubar reference for later
        self.menubar = menubar