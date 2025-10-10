from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from .widgets import AccountCard

ACCOUNT_TYPES = {
    "savings": {"name": "Savings Account", "color": "#4CAF50", "icon": "💰"},
    "bills": {"name": "Bills Account", "color": "#FF9800", "icon": "💳"},
    "main": {"name": "Main Account", "color": "#2196F3", "icon": "🏦"},
    "credit": {"name": "Credit Card", "color": "#F44336", "icon": "💳"},
}


class AccountsModule:
    def __init__(self, parent_widget, api_client=None):
        self.parent = parent_widget
        self.api = api_client
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.parent.setLayout(layout)

        # Title
        title = QLabel("🏦 Account Management")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; padding: 10px;")
        layout.addWidget(title)

        # Instructions
        instructions = QLabel("Set your current account balances to track net worth accurately")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setStyleSheet("color: #9CA3AF; padding: 5px; font-size: 12px;")
        layout.addWidget(instructions)

        # Account balance inputs
        for account_key, account_info in ACCOUNT_TYPES.items():
            card_frame = QFrame()
            card_frame.setStyleSheet("""
                QFrame {
                    background-color: #2d3748;
                    border: 2px solid #4a5568;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 5px;
                }
            """)
            
            card_layout = QHBoxLayout()
            card_frame.setLayout(card_layout)
            
            # Account icon and name
            account_label = QLabel(f"{account_info['icon']} {account_info['name']}")
            account_label.setStyleSheet(f"color: white; font-weight: bold; font-size: 14px;")
            card_layout.addWidget(account_label)
            
            card_layout.addStretch()
            
            # Balance input
            balance_input = QLineEdit()
            balance_input.setPlaceholderText("$0.00")
            balance_input.setFixedWidth(150)
            balance_input.setStyleSheet("""
                QLineEdit {
                    background-color: #4a5568;
                    color: white;
                    padding: 8px;
                    border: 1px solid #718096;
                    border-radius: 4px;
                    font-size: 13px;
                }
            """)
            card_layout.addWidget(balance_input)
            
            # Save button
            save_btn = QPushButton("Save")
            save_btn.setFixedWidth(80)
            save_btn.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    padding: 8px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            save_btn.clicked.connect(
                lambda checked, acc=account_key, inp=balance_input: self.save_balance(acc, inp.text())
            )
            card_layout.addWidget(save_btn)
            
            layout.addWidget(card_frame)

        # Account selector for CSV import
        selector_frame = QFrame()
        selector_frame.setStyleSheet(
            """
            QFrame {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 10px;
            }
        """
        )
        selector_layout = QHBoxLayout()
        selector_frame.setLayout(selector_layout)

        selector_layout.addWidget(QLabel("Select Account for Import:"))

        self.account_selector = QComboBox()
        for account_id, account_info in ACCOUNT_TYPES.items():
            self.account_selector.addItem(
                f"{account_info['icon']} {account_info['name']}", account_id
            )
        selector_layout.addWidget(self.account_selector)

        layout.addWidget(selector_frame)

    def get_selected_account(self):
        return self.account_selector.currentData()

    def save_balance(self, account, balance_str):
        """Save account balance to AWS"""
        import requests
        
        if not self.api:
            QMessageBox.warning(
                self.parent,
                "Not Available",
                "Account balance tracking requires API connection"
            )
            return
        
        try:
            # Parse balance
            balance = float(balance_str.replace('$', '').replace(',', '').strip())
            
            # Save to AWS
            response = requests.post(
                f"{self.api.aws_api_url}/accounts/balance",
                json={
                    "user_id": "user1",
                    "account": account,
                    "balance": balance
                },
                timeout=10
            )
            
            if response.status_code == 200:
                QMessageBox.information(
                    self.parent, 
                    "Success", 
                    f"✅ Balance updated for {ACCOUNT_TYPES[account]['name']}"
                )
            else:
                QMessageBox.critical(
                    self.parent, 
                    "Error", 
                    f"Failed to update balance: {response.text}"
                )
        
        except ValueError:
            QMessageBox.warning(
                self.parent,
                "Invalid Input",
                "Please enter a valid number (e.g., 1234.56)"
            )
        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"Error: {str(e)}")
