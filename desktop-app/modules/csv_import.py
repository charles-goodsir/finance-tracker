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
        title.setStyleSheet("color: white; padding: 10px;")
        layout.addWidget(title)

        # File selection
        file_frame = QFrame()
        file_frame.setStyleSheet(
            """
            QFrame {
                background-color: #2d3748;
                border: 2px solid #4a5568;
                border-radius: 8px;
                padding: 10px;
            }
        """
        )
        file_layout = QHBoxLayout()
        file_frame.setLayout(file_layout)

        csv_label = QLabel("📄 CSV File:")
        csv_label.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
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

        account_frame = QFrame()
        account_frame.setStyleSheet(
            """
            QFrame {
                background-color: #2d3748;
                border: 2px solid #4a5568;
                border-radius: 8px;
                padding: 10px;
                margin-top: 10px;
            }
        """
        )
        account_layout = QHBoxLayout()
        account_frame.setLayout(account_layout)

        account_label = QLabel("🏦 Select Account:")
        account_label.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        account_layout.addWidget(account_label)

        self.account_selector = QComboBox()
        self.account_selector.setStyleSheet(
            """
            QComboBox {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                min-width: 200px;
        }
        QComboBox: focus {
            border-color: #2196F3;
        }
    """
        )

        from modules.accounts import ACCOUNT_TYPES

        for account_id, account_info in ACCOUNT_TYPES.items():
            self.account_selector.addItem(
                f"{account_info['icon']} {account_info['name']}", account_id
            )

        account_layout.addWidget(self.account_selector)
        account_layout.addStretch()

        layout.addWidget(account_frame)

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
                background-color: #666;
                border: 2px solid #666;
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
            selected_account = self.account_selector.currentData()

            import requests

            with open(file_path, "rb") as f:
                files = {"file": f}
                data = {"user_id": "user1", "account": selected_account}
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
            # Format date nicely
            date_str = tx.get("date", "")
            if date_str:
                from datetime import datetime

                try:
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    formatted_date = dt.strftime("%d %b %Y")  # e.g., "04 Sep 2025"
                except:
                    formatted_date = date_str[:10]  # Fallback to YYYY-MM-DD
            else:
                formatted_date = "No date"

            self.results_text.append(
                f"[{formatted_date}] {tx['description']} → {tx['category']} (${tx['amount']})"
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

    def commit_transactions(self):
        """Commit pending transactions to database"""
        if not hasattr(self, "pending_transactions") or not self.pending_transactions:
            QMessageBox.warning(
                self.parent, "No Transactions", "No transactions to commit!"
            )
            return

        # Ask for confirmation
        reply = QMessageBox.question(
            self.parent,
            "Confirm Commit",
            f"Commit {len(self.pending_transactions)} transactions to AWS?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Call API client to commit transactions
            self.commit_button.setEnabled(False)
            self.commit_button.setText("⏳ Committing...")

            # Use QTimer to avoid blocking the UI
            QTimer.singleShot(
                0, lambda: self.do_commit_transactions(self.pending_transactions)
            )

    def do_commit_transactions(self, transactions):
        """Actually commit the transactions"""
        import requests

        try:
            payload = {"transactions": transactions}

            response = requests.post(
                f"{self.api.aws_api_url}/transaction/commit-bulk",
                json=payload,
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                QMessageBox.information(
                    self.parent,
                    "Success",
                    f"✅ Committed {result['saved']} transactions!\n"
                    f"Failed: {len(result['failed'])}",
                )
                self.results_text.append(
                    f"\n✅ Committed {result['saved']} transactions!"
                )
                self.pending_transactions = []
                self.commit_button.hide()
            else:
                QMessageBox.critical(
                    self.parent, "Error", f"Commit failed: {response.text}"
                )

        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"Commit error: {str(e)}")
        finally:
            self.commit_button.setEnabled(True)
            self.commit_button.setText("💾 Commit Transactions")
