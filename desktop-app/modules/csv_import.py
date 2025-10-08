from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


class CSVImportModule:
    def __init__(self, parent_widget, api_client, db_manager):
        self.parent = parent_widget
        self.api = api_client
        self.db = db_manager
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.parent.setLayout(layout)

        # Title
        title = QLabel("📁 Smart CSV Import")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #333; padding: 10px;")
        layout.addWidget(title)

        # File selection
        file_frame = QFrame()
        file_frame.setStyleSheet(
            """
            QFrame {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 10px;
            }
        """
        )
        file_layout = QHBoxLayout()
        file_frame.setLayout(file_layout)

        csv_label = QLabel("📄 CSV File:")
        csv_label.setStyleSheet("color: #333; font-weight: bold; font-size: 14px;")
        file_layout.addWidget(csv_label)

        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Select a CSV file...")
        self.file_path_edit.setStyleSheet(
            """
            QLineEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
        """
        )
        file_layout.addWidget(self.file_path_edit)

        browse_btn = QPushButton("📂 Browse")
        browse_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """
        )
        browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_btn)

        layout.addWidget(file_frame)

        # Import button
        self.import_button = QPushButton("🚀 Import with Smart Classification")
        self.import_button.setStyleSheet(
            """
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """
        )
        self.import_button.clicked.connect(self.import_csv)
        layout.addWidget(self.import_button)

        # Results text area
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setStyleSheet(
            """
            QTextEdit {
                background-color: white;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
        """
        )
        layout.addWidget(self.results_text)

    def browse_file(self):
        """Browse for CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent, "Select CSV file", "", "CSV files (*.csv);;All files (*.*)"
        )
        if file_path:
            self.file_path_edit.setText(file_path)

    def import_csv(self):
        """Import CSV file"""
        file_path = self.file_path_edit.text()
        if not file_path:
            QMessageBox.warning(self.parent, "Error", "Please select a file")
            return

        self.import_button.setEnabled(False)

        # Use QTimer to call API in main thread
        QTimer.singleShot(100, lambda: self._do_import(file_path))

    def _do_import(self, file_path):
        """Do the actual import in main thread"""
        try:
            import requests

            with open(file_path, "rb") as f:
                files = {"file": f}
                data = {"user_id": "default"}
                response = requests.post(
                    f"{self.api.aws_api_url}/import-bank-csv",
                    files=files,
                    data=data,
                    timeout=30,
                )

            if response.status_code == 200:
                result = response.json()
                self.on_import_complete(True, result)
            else:
                self.on_import_complete(False, f"Import failed: {response.text}")

        except Exception as e:
            self.on_import_complete(False, f"Import error: {str(e)}")

    def on_import_complete(self, success, result):
        """Handle import completion"""
        if success:
            self.show_import_results(result)
        else:
            QMessageBox.critical(self.parent, "Error", result)

        self.import_button.setEnabled(True)

    def show_import_results(self, result):
        """Show import results"""
        self.results_text.clear()

        summary = result["summary"]
        self.results_text.append("📊 Import Results:")
        self.results_text.append(f"Total: {summary['total']}")
        self.results_text.append(f"Auto-classified: {summary['auto-classified']}")
        self.results_text.append(f"Needs Review: {summary['needs_review']}\n")

        self.results_text.append("💳 Transactions:")
        for tx in result["transactions"]:
            self.results_text.append(
                f"{tx['description']} → {tx['category']} (${tx['amount']})"
            )

        self.pending_transactions = result["transactions"]

        # Add commit button if not exists
        if not hasattr(self, "commit_button"):
            self.commit_button = QPushButton("💾 Commit Transactions")
            self.commit_button.setStyleSheet(
                """
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: bold;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """
            )
            self.commit_button.clicked.connect(self.commit_transactions)
            self.parent.layout().addWidget(self.commit_button)
