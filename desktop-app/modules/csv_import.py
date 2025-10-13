from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
import requests


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

        # Note: Results area is dynamically created when importing
        # We don't create a results_text widget anymore since we use tables

    def load_categories(self):
        """Load available categories from API"""
        # Define comprehensive fallback categories
        fallback_categories = [
            "Income",
            "Payment",
            "Cash Withdrawal",
            "Groceries",
            "Dining Out",
            "Transportation",
            "Bills & Utilities",
            "Entertainment",
            "Healthcare",
            "Shopping",
            "Insurance",
            "Travel",
            "Transfers",
            "Credit Card Payments",
            "Uncategorized",
        ]

        try:
            if hasattr(self.api, "aws_api_url"):
                response = requests.get(
                    f"{self.api.aws_api_url}/categories", timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    api_categories = [cat["name"] for cat in data.get("categories", [])]

                    # If API returns categories, merge with fallback to ensure we have all
                    if api_categories:
                        # Combine API categories with fallback, removing duplicates
                        all_categories = list(
                            dict.fromkeys(api_categories + fallback_categories)
                        )
                        return all_categories
        except Exception as e:
            print(f"Failed to load categories: {e}")

        # Use fallback categories
        return fallback_categories

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
            # Send Telegram notification for CSV import
            if self.api and hasattr(self.api, "telegram"):
                summary = result.get("summary", {})
                account = self.account_selector.currentData()
                self.api.telegram.notify_csv_import(
                    summary.get("total", 0), summary.get("auto-classified", 0), account
                )

            self.show_import_results(result)
        else:
            QMessageBox.critical(self.parent, "Error", result)

        self.import_button.setEnabled(True)

    def show_import_results(self, result):
        """Show import results in an interactive table"""
        from datetime import datetime

        # Clear previous results
        if hasattr(self, "results_text") and self.results_text is not None:
            try:
                self.results_text.setParent(None)
                self.results_text.deleteLater()
            except:
                pass
            self.results_text = None

        if hasattr(self, "results_table") and self.results_table is not None:
            try:
                self.results_table.setParent(None)
                self.results_table.deleteLater()
            except:
                pass
            self.results_table = None

        if hasattr(self, "summary_label") and self.summary_label is not None:
            try:
                self.summary_label.setParent(None)
                self.summary_label.deleteLater()
            except:
                pass
            self.summary_label = None

        if hasattr(self, "filter_frame") and self.filter_frame is not None:
            try:
                self.filter_frame.setParent(None)
                self.filter_frame.deleteLater()
            except:
                pass
            self.filter_frame = None

        # Store pending transactions
        self.pending_transactions = result["transactions"]
        summary = result["summary"]

        # Debug: Check if account field is present
        if self.pending_transactions:
            print(
                f"DEBUG: First transaction account field: {self.pending_transactions[0].get('account', 'MISSING')}"
            )

        # Recalculate summary based on actual frontend logic
        total = len(self.pending_transactions)
        needs_review_count = 0
        auto_classified_count = 0

        for tx in self.pending_transactions:
            # Get confidence from classification object or top level
            confidence = tx.get("classification", {}).get(
                "confidence", tx.get("confidence", 0.5)
            )
            if confidence < 0.7 or tx.get("category") == "Uncategorized":
                needs_review_count += 1
            else:
                auto_classified_count += 1

        # Create summary label
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet(
            """
            color: white;
            font-size: 14px;
            font-weight: bold;
            padding: 10px;
            background-color: #2d3748;
            border-radius: 5px;
            margin: 10px 0px;
        """
        )

        summary_text = f"📊 Import Results: Total: {total} | ✅ Auto-classified: {auto_classified_count} | ⚠️ Needs Review: {needs_review_count}"
        self.summary_label.setText(summary_text)

        # Insert summary after account selector
        layout = self.parent.layout()
        layout.insertWidget(3, self.summary_label)

        # Load categories for dropdowns
        self.categories = self.load_categories()
        print(f"📋 Loaded {len(self.categories)} categories: {self.categories}")

        # Create interactive table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels(
            ["Status", "Date", "Description", "Amount", "Category", "Confidence"]
        )
        self.results_table.setRowCount(len(self.pending_transactions))

        # Set row height to accommodate dropdown boxes
        self.results_table.verticalHeader().setDefaultSectionSize(45)

        # Style the table
        self.results_table.setStyleSheet(
            """
            QTableWidget {
                background-color: white;
                border: 2px solid #4a5568;
                border-radius: 8px;
                gridline-color: #e2e8f0;
            }
            QTableWidget::item {
                padding: 8px;
                color: #1a202c;
            }
            QHeaderView::section {
                background-color: #4a5568;
                color: white;
                padding: 10px;
                font-weight: bold;
                border: none;
            }
        """
        )

        # Set column widths with stretch for Category column
        header = self.results_table.horizontalHeader()
        self.results_table.setColumnWidth(0, 60)  # Status
        self.results_table.setColumnWidth(1, 100)  # Date
        self.results_table.setColumnWidth(2, 250)  # Description
        self.results_table.setColumnWidth(3, 100)  # Amount
        header.setSectionResizeMode(
            4, QHeaderView.ResizeMode.Stretch
        )  # Category stretches
        self.results_table.setColumnWidth(5, 100)  # Confidence

        # Populate table
        print(f"📊 Processing {len(self.pending_transactions)} transactions...")
        for row_idx, tx in enumerate(self.pending_transactions):
            if row_idx < 3:  # Debug first 3 transactions
                classification = tx.get("classification", {})
                print(
                    f"  Transaction {row_idx}: category='{tx.get('category')}', confidence={classification.get('confidence')}, reason='{classification.get('reason')}'"
                )
            # Format date
            date_str = tx.get("date", "")
            if date_str:
                try:
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    formatted_date = dt.strftime("%d %b")
                except:
                    formatted_date = date_str[:10]
            else:
                formatted_date = "No date"

            # Get confidence from classification object or top level (default 0.5 if not provided)
            confidence = tx.get("classification", {}).get(
                "confidence", tx.get("confidence", 0.5)
            )
            needs_review_flag = (
                confidence < 0.7 or tx.get("category") == "Uncategorized"
            )

            # Status indicator
            status_item = QTableWidgetItem()
            if needs_review_flag:
                status_item.setText("⚠️")
                status_item.setBackground(QColor(255, 243, 205))  # Light yellow
            else:
                status_item.setText("✅")
                status_item.setBackground(QColor(209, 250, 229))  # Light green
            status_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Not editable
            self.results_table.setItem(row_idx, 0, status_item)

            # Date
            date_item = QTableWidgetItem(formatted_date)
            date_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            if needs_review_flag:
                date_item.setBackground(QColor(255, 243, 205))
            self.results_table.setItem(row_idx, 1, date_item)

            # Description
            desc_item = QTableWidgetItem(tx["description"][:50])
            desc_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            if needs_review_flag:
                desc_item.setBackground(QColor(255, 243, 205))
            self.results_table.setItem(row_idx, 2, desc_item)

            # Amount
            amount_item = QTableWidgetItem(f"${tx['amount']}")
            amount_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            if needs_review_flag:
                amount_item.setBackground(QColor(255, 243, 205))
            self.results_table.setItem(row_idx, 3, amount_item)

            # Category dropdown
            category_combo = QComboBox()
            category_combo.addItems(self.categories)
            current_category = tx.get("category", "Uncategorized")

            # Try to find matching category (case-insensitive)
            category_index = -1
            for i, cat in enumerate(self.categories):
                if cat.lower() == current_category.lower():
                    category_index = i
                    break

            if category_index >= 0:
                category_combo.setCurrentIndex(category_index)
                if row_idx < 3:  # Debug first 3
                    print(
                        f"  Row {row_idx}: Set dropdown to index {category_index} = '{self.categories[category_index]}'"
                    )
            else:
                # Category not found, try exact match as fallback
                category_combo.setCurrentText(current_category)
                print(
                    f"Warning: Category '{current_category}' not found in dropdown list. Available: {self.categories}"
                )
            category_combo.setProperty("row", row_idx)  # Store row index
            # Use lambda to pass both the new category and row index
            category_combo.currentTextChanged.connect(
                lambda new_cat, r=row_idx, combo=category_combo: self.on_category_changed(
                    new_cat, r, combo
                )
            )

            # Simple styling - just clear, readable text
            category_combo.setStyleSheet(
                """
                QComboBox {
                    padding: 5px;
                    color: #1a202c;
                    font-size: 14px;
                    background-color: white;
                    border: 1px solid #cbd5e0;
                }
                QComboBox QAbstractItemView {
                    background-color: white;
                    color: #1a202c;
                    selection-background-color: #4299e1;
                }
            """
            )

            self.results_table.setCellWidget(row_idx, 4, category_combo)

            # Confidence
            conf_text = f"{int(confidence * 100)}%"
            if needs_review_flag:
                conf_text += " ⚠️"
            conf_item = QTableWidgetItem(conf_text)
            conf_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            if needs_review_flag:
                conf_item.setBackground(QColor(255, 243, 205))
            self.results_table.setItem(row_idx, 5, conf_item)

        # Add filter buttons
        self.filter_frame = QFrame()
        filter_layout = QHBoxLayout()
        self.filter_frame.setLayout(filter_layout)

        show_all_btn = QPushButton("📋 Show All")
        show_all_btn.clicked.connect(lambda: self.filter_table("all"))
        show_all_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """
        )

        show_review_btn = QPushButton("⚠️ Needs Review Only")
        show_review_btn.clicked.connect(lambda: self.filter_table("review"))
        show_review_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #ffc107;
                color: #1a202c;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """
        )

        filter_layout.addWidget(show_all_btn)
        filter_layout.addWidget(show_review_btn)
        filter_layout.addStretch()

        layout.insertWidget(4, self.filter_frame)
        layout.insertWidget(5, self.results_table)

        # Show/enable commit button
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
            layout.addWidget(self.commit_button)
        else:
            # Re-enable and show the button for subsequent imports
            self.commit_button.setEnabled(True)
            self.commit_button.setVisible(True)

    def on_category_changed(self, new_category, row, combo):
        """Handle category dropdown change"""
        # Get the transaction data
        tx = self.pending_transactions[row]
        original_category = tx.get("category", "Uncategorized")

        # Update the transaction data
        self.pending_transactions[row]["category"] = new_category

        # Track correction for learning if category actually changed
        if original_category != new_category and self.api:
            self.track_correction_for_learning(tx, original_category, new_category)

        # Update status column to show it's been reviewed
        status_item = self.results_table.item(row, 0)
        status_item.setText("✅")
        status_item.setBackground(QColor(209, 250, 229))

        # Update other cells in the row to green to show it's been reviewed
        for col in [1, 2, 3, 5]:
            item = self.results_table.item(row, col)
            if item:
                item.setBackground(QColor(209, 250, 229))

    def filter_table(self, filter_type):
        """Filter table to show all or only needs review"""
        for row in range(self.results_table.rowCount()):
            status_item = self.results_table.item(row, 0)
            if filter_type == "all":
                self.results_table.setRowHidden(row, False)
            elif filter_type == "review":
                # Show only rows with ⚠️
                show_row = status_item.text() == "⚠️"
                self.results_table.setRowHidden(row, not show_row)

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

                # Send enhanced Telegram notification
                if self.api and hasattr(self.api, "telegram"):
                    # Get account from first transaction (they should all be the same)
                    account = (
                        transactions[0].get("account", "main")
                        if transactions
                        else "main"
                    )

                    # Calculate categories summary
                    categories_summary = {}
                    for tx in transactions:
                        category = tx.get("category", "Uncategorized")
                        categories_summary[category] = (
                            categories_summary.get(category, 0) + 1
                        )

                    # Send enhanced notification
                    self.api.telegram.notify_csv_commit(
                        result["saved"], account, categories_summary
                    )

                QMessageBox.information(
                    self.parent,
                    "Success",
                    f"✅ Committed {result['saved']} transactions!\n"
                    f"Failed: {len(result['failed'])}",
                )
                # Clear the pending transactions and hide UI elements
                self.pending_transactions = []
                if hasattr(self, "commit_button") and self.commit_button is not None:
                    try:
                        self.commit_button.hide()
                    except:
                        pass
                if hasattr(self, "results_table") and self.results_table is not None:
                    try:
                        self.results_table.setParent(None)
                        self.results_table.deleteLater()
                    except:
                        pass
                    self.results_table = None
                if hasattr(self, "filter_frame") and self.filter_frame is not None:
                    try:
                        self.filter_frame.setParent(None)
                        self.filter_frame.deleteLater()
                    except:
                        pass
                    self.filter_frame = None
                if hasattr(self, "summary_label") and self.summary_label is not None:
                    try:
                        self.summary_label.setParent(None)
                        self.summary_label.deleteLater()
                    except:
                        pass
                    self.summary_label = None
            else:
                QMessageBox.critical(
                    self.parent, "Error", f"Commit failed: {response.text}"
                )

        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"Commit error: {str(e)}")
        finally:
            self.commit_button.setEnabled(True)
            self.commit_button.setText("💾 Commit Transactions")

    def track_correction_for_learning(self, tx, original_category, corrected_category):
        """Track user correction for learning system"""
        try:
            import requests

            # Get original confidence from classification
            classification = tx.get("classification", {})
            confidence = classification.get("confidence", 0.5)

            # Send correction to learning API
            correction_data = {
                "user_id": "user1",  # Default user ID
                "description": tx.get("description", ""),
                "original_category": original_category,
                "corrected_category": corrected_category,
                "amount": tx.get("amount", 0),
                "confidence": confidence,
            }

            response = requests.post(
                f"{self.api.aws_api_url}/learning/correction",
                json=correction_data,
                timeout=5,
            )

            if response.status_code == 200:
                print(
                    f"🧠 Learning: '{tx.get('description', '')[:30]}...' {original_category} → {corrected_category}"
                )
            else:
                print(f"Learning API error: {response.status_code}")

        except Exception as e:
            print(f"Learning tracking error: {e}")
            # Don't show error to user, learning is optional
