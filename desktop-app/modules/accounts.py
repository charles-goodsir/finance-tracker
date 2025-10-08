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
    def __init__(self, parent_widget):
        self.parent = parent_widget
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.parent.setLayout(layout)

        # Title
        title = QLabel("🏦 Account Management")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #333; padding: 10px;")
        layout.addWidget(title)

        # Account cards
        accounts_layout = QGridLayout()

        for i, (account_id, account_info) in enumerate(ACCOUNT_TYPES.items()):
            card = AccountCard(account_id, account_info)
            accounts_layout.addWidget(card, i // 2, i % 2)

        layout.addLayout(accounts_layout)

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
