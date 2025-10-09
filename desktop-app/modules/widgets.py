from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class StatCard(QFrame):
    """Reusable stat card widget"""

    def __init__(self, title, value, color, icon="💰"):
        super().__init__()
        self.setup_ui(title, value, color, icon)

    def setup_ui(self, title, value, color, icon):
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: #2d3748;
                border: 2px solid {color};
                border-radius: 10px;
                margin: 5px;
            }}
        """
        )

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title
        title_label = QLabel(f"{icon} {title}")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {color}; padding: 10px 5px 5px 5px;")
        layout.addWidget(title_label)

        # Value
        self.value_label = QLabel(value)
        self.value_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet(f"color: {color}; padding: 5px;")
        layout.addWidget(self.value_label)

    def update_value(self, new_value):
        self.value_label.setText(new_value)


class AccountCard(QFrame):
    """Reusable account card widget"""

    def __init__(self, account_id, account_info):
        super().__init__()
        self.account_id = account_id
        self.setup_ui(account_info)

    def setup_ui(self, account_info):
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: white;
                border: 3px solid {account_info['color']};
                border-radius: 10px;
                margin: 5px;
                padding: 15px;
            }}
        """
        )

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Account name
        self.name_label = QLabel(f"{account_info['icon']} {account_info['name']}")
        self.name_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.name_label.setStyleSheet(f"color: {account_info['color']};")
        layout.addWidget(self.name_label)

        # Balance
        self.balance_label = QLabel("Balance: $0.00")
        self.balance_label.setFont(QFont("Arial", 12))
        self.balance_label.setStyleSheet("color: #666;")
        layout.addWidget(self.balance_label)

        # Transaction count
        self.count_label = QLabel("Transactions: 0")
        self.count_label.setFont(QFont("Arial", 10))
        self.count_label.setStyleSheet("color: #999;")
        layout.addWidget(self.count_label)

    def update_balance(self, balance):
        self.balance_label.setText(f"Balance: ${balance:.2f}")

    def update_transaction_count(self, count):
        self.count_label.setText(f"Transactions: {count}")


class StyledTableWidget(QTableWidget):
    """Reusable styled table widget"""

    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setup_ui(columns)

    def setup_ui(self, columns):
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        self.setAlternatingRowColors(True)
        self.setStyleSheet(
            """
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                gridline-color: #e0e0e0;
                selection-background-color: #e3f2fd;
            }
            QTableWidget::item {
                padding: 10px;
                border: none;
                color: #333;
                background-color: white;
                font-size: 13px;
            }
            QTableWidget::item:alternate {
                background-color: #f8f9fa;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 12px;
                border: none;
                font-weight: bold;
                color: #333;
                font-size: 14px;
                border-bottom: 2px solid #ddd;
            }
            QHeaderView::section:vertical {
                font-size: 12px;
                font-weight: bold;
                color: #333;
                background-color: #f0f0f0;
                padding: 8px;
            }
        """
        )

        # Make table stretch
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
