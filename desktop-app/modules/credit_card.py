from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import requests


class CreditCardWidget(QFrame):
    """Reusable credit card management widget"""

    def __init__(self, api_client=None):
        super().__init__()
        self.api = api_client
        self.credit_limit = 4000.00  # Default, will be updated from snapshots
        self.setup_ui()

    def setup_ui(self):
        """Setup the credit card UI"""
        self.setStyleSheet(
            """
            QFrame {
                background-color: #2d3748;
                border: 2px solid #9333ea;
                border-radius: 10px;
                margin: 5px;
                padding: 15px;
            }
        """
        )

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header
        header = QLabel("💳 Credit Card Management")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setStyleSheet(
            "color: #9333ea; border: none; padding: 0; margin-bottom: 10px;"
        )
        layout.addWidget(header)

        # Balance Overview
        balance_frame = QFrame()
        balance_frame.setStyleSheet(
            "QFrame { background-color: #1a202c; border: 1px solid #4a5568; border-radius: 8px; padding: 15px; }"
        )
        balance_layout = QVBoxLayout()
        balance_frame.setLayout(balance_layout)

        # Current Balance
        balance_row = QHBoxLayout()
        balance_label = QLabel("Current Balance Owed:")
        balance_label.setStyleSheet(
            "color: white; font-weight: bold; border: none; padding: 0;"
        )
        self.balance_value = QLabel("$0.00")
        self.balance_value.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.balance_value.setStyleSheet("color: #ef4444; border: none; padding: 0;")
        balance_row.addWidget(balance_label)
        balance_row.addStretch()
        balance_row.addWidget(self.balance_value)
        balance_layout.addLayout(balance_row)

        # Available Credit
        available_row = QHBoxLayout()
        available_label = QLabel("Available Credit:")
        available_label.setStyleSheet("color: white; border: none; padding: 0;")
        self.available_value = QLabel("$0.00")
        self.available_value.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.available_value.setStyleSheet("color: #10b981; border: none; padding: 0;")
        available_row.addWidget(available_label)
        available_row.addStretch()
        available_row.addWidget(self.available_value)
        balance_layout.addLayout(available_row)

        # Credit Utilization
        util_label = QLabel("Credit Utilization:")
        util_label.setStyleSheet(
            "color: white; border: none; padding: 0; margin-top: 10px;"
        )
        balance_layout.addWidget(util_label)

        # Progress bar for utilization
        self.utilization_bar = QProgressBar()
        self.utilization_bar.setRange(0, 100)
        self.utilization_bar.setValue(0)
        self.utilization_bar.setTextVisible(True)
        self.utilization_bar.setFormat("%p%")
        self.utilization_bar.setStyleSheet(
            """
            QProgressBar {
                border: 2px solid #4a5568;
                border-radius: 5px;
                text-align: center;
                background-color: #1a202c;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #10b981;
                border-radius: 3px;
            }
        """
        )
        balance_layout.addWidget(self.utilization_bar)

        self.utilization_status = QLabel("✅ Excellent utilization!")
        self.utilization_status.setStyleSheet(
            "color: #10b981; font-size: 12px; border: none; padding: 0; margin-top: 5px;"
        )
        balance_layout.addWidget(self.utilization_status)

        layout.addWidget(balance_frame)

        # Monthly Activity
        activity_frame = QFrame()
        activity_frame.setStyleSheet(
            "QFrame { background-color: #1a202c; border: 1px solid #4a5568; border-radius: 8px; padding: 15px; }"
        )
        activity_layout = QVBoxLayout()
        activity_frame.setLayout(activity_layout)

        activity_title = QLabel("📊 This Month's Activity")
        activity_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        activity_title.setStyleSheet(
            "color: #9333ea; border: none; padding: 0; margin-bottom: 10px;"
        )
        activity_layout.addWidget(activity_title)

        # Charges this month
        charges_row = QHBoxLayout()
        charges_label = QLabel("Charges:")
        charges_label.setStyleSheet("color: white; border: none; padding: 0;")
        self.charges_value = QLabel("$0.00")
        self.charges_value.setStyleSheet(
            "color: #ef4444; font-weight: bold; border: none; padding: 0;"
        )
        charges_row.addWidget(charges_label)
        charges_row.addStretch()
        charges_row.addWidget(self.charges_value)
        activity_layout.addLayout(charges_row)

        # Payments this month
        payments_row = QHBoxLayout()
        payments_label = QLabel("Payments:")
        payments_label.setStyleSheet("color: white; border: none; padding: 0;")
        self.payments_value = QLabel("$0.00")
        self.payments_value.setStyleSheet(
            "color: #10b981; font-weight: bold; border: none; padding: 0;"
        )
        payments_row.addWidget(payments_label)
        payments_row.addStretch()
        payments_row.addWidget(self.payments_value)
        activity_layout.addLayout(payments_row)

        # Net change
        net_row = QHBoxLayout()
        net_label = QLabel("Net Change:")
        net_label.setStyleSheet(
            "color: white; font-weight: bold; border: none; padding: 0; margin-top: 5px;"
        )
        self.net_value = QLabel("$0.00")
        self.net_value.setStyleSheet(
            "color: white; font-weight: bold; border: none; padding: 0; margin-top: 5px;"
        )
        net_row.addWidget(net_label)
        net_row.addStretch()
        net_row.addWidget(self.net_value)
        activity_layout.addLayout(net_row)

        layout.addWidget(activity_frame)

        # Quick Actions
        actions_layout = QHBoxLayout()

        self.view_transactions_btn = QPushButton("📋 View Transactions")
        self.view_transactions_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #9333ea;
                color: white;
                border: none;
                padding: 10px 15px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #7e22ce;
            }
            QPushButton:pressed {
                background-color: #6b21a8;
            }
        """
        )

        self.payment_history_btn = QPushButton("💰 Payment History")
        self.payment_history_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 10px 15px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
        """
        )

        actions_layout.addWidget(self.view_transactions_btn)
        actions_layout.addWidget(self.payment_history_btn)

        layout.addLayout(actions_layout)

        # Status message
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(
            "color: white; font-size: 12px; border: none; padding: 5px; margin-top: 10px;"
        )
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

    def update_data(self, balance_owed, credit_limit=4000):
        """Update credit card data"""
        self.credit_limit = credit_limit
        available = credit_limit - balance_owed
        utilization = (balance_owed / credit_limit * 100) if credit_limit > 0 else 0

        # Update balance
        self.balance_value.setText(f"${balance_owed:.2f}")
        self.available_value.setText(f"${available:.2f} / ${credit_limit:.2f}")

        # Update utilization bar
        self.utilization_bar.setValue(int(utilization))

        # Update utilization status with color
        if utilization < 10:
            self.utilization_status.setText("✅ Excellent utilization!")
            self.utilization_status.setStyleSheet(
                "color: #10b981; font-size: 12px; border: none; padding: 0; margin-top: 5px;"
            )
            self.utilization_bar.setStyleSheet(
                """
                QProgressBar {
                    border: 2px solid #4a5568;
                    border-radius: 5px;
                    text-align: center;
                    background-color: #1a202c;
                    color: white;
                    font-weight: bold;
                }
                QProgressBar::chunk {
                    background-color: #10b981;
                    border-radius: 3px;
                }
            """
            )
        elif utilization < 30:
            self.utilization_status.setText("✅ Good utilization")
            self.utilization_status.setStyleSheet(
                "color: #10b981; font-size: 12px; border: none; padding: 0; margin-top: 5px;"
            )
            self.utilization_bar.setStyleSheet(
                """
                QProgressBar {
                    border: 2px solid #4a5568;
                    border-radius: 5px;
                    text-align: center;
                    background-color: #1a202c;
                    color: white;
                    font-weight: bold;
                }
                QProgressBar::chunk {
                    background-color: #3b82f6;
                    border-radius: 3px;
                }
            """
            )
        elif utilization < 50:
            self.utilization_status.setText("⚠️ Moderate utilization")
            self.utilization_status.setStyleSheet(
                "color: #f59e0b; font-size: 12px; border: none; padding: 0; margin-top: 5px;"
            )
            self.utilization_bar.setStyleSheet(
                """
                QProgressBar {
                    border: 2px solid #4a5568;
                    border-radius: 5px;
                    text-align: center;
                    background-color: #1a202c;
                    color: white;
                    font-weight: bold;
                }
                QProgressBar::chunk {
                    background-color: #f59e0b;
                    border-radius: 3px;
                }
            """
            )
        else:
            self.utilization_status.setText("⚠️ High utilization - consider paying down")
            self.utilization_status.setStyleSheet(
                "color: #ef4444; font-size: 12px; border: none; padding: 0; margin-top: 5px;"
            )
            self.utilization_bar.setStyleSheet(
                """
                QProgressBar {
                    border: 2px solid #4a5568;
                    border-radius: 5px;
                    text-align: center;
                    background-color: #1a202c;
                    color: white;
                    font-weight: bold;
                }
                QProgressBar::chunk {
                    background-color: #ef4444;
                    border-radius: 3px;
                }
            """
            )

    def update_monthly_activity(self, charges, payments):
        """Update this month's activity"""
        self.charges_value.setText(f"${charges:.2f}")
        self.payments_value.setText(f"${payments:.2f}")

        net = charges - payments
        self.net_value.setText(f"${abs(net):.2f}")

        if net > 0:
            self.net_value.setStyleSheet(
                "color: #ef4444; font-weight: bold; border: none; padding: 0; margin-top: 5px;"
            )
        elif net < 0:
            self.net_value.setStyleSheet(
                "color: #10b981; font-weight: bold; border: none; padding: 0; margin-top: 5px;"
            )
        else:
            self.net_value.setStyleSheet(
                "color: white; font-weight: bold; border: none; padding: 0; margin-top: 5px;"
            )

    def load_from_aws(self):
        """Load credit card data from AWS"""
        if not self.api:
            self.show_status("⚠️ API not configured", "#f59e0b")
            return

        try:
            # Get latest snapshot for current balance
            response = requests.get(
                f"{self.api.aws_api_url}/snapshots/list?user_id=user1&limit=1",
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                snapshots = data.get("snapshots", [])

                if snapshots:
                    latest = snapshots[0]
                    balance_owed = latest.get("credit", 0.0)
                    self.update_data(balance_owed, self.credit_limit)

                    # Get this month's activity
                    self.load_monthly_activity()

                    self.show_status("✅ Loaded credit card data", "#10b981")
                else:
                    self.show_status("⚠️ No snapshot data found", "#f59e0b")
            else:
                self.show_status(f"❌ Error: {response.status_code}", "#ef4444")

        except Exception as e:
            self.show_status(f"❌ Error: {str(e)}", "#ef4444")
            print(f"Error loading credit card data: {e}")

    def load_monthly_activity(self):
        """Load this month's charges and payments"""
        if not self.api:
            return

        try:
            from datetime import datetime

            # Get current month
            now = datetime.utcnow()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            # Get all transactions for this month with credit account
            response = requests.get(
                f"{self.api.aws_api_url}/transactions?user_id=user1&limit=500",
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                transactions = data.get("items", [])

                # Filter for credit card transactions this month
                charges = 0.0
                payments = 0.0

                for tx in transactions:
                    tx_date = tx.get("date", "")[:10]  # Get date part only
                    account = tx.get("account", "")
                    amount = float(tx.get("amount", 0))
                    category = tx.get("category", "")

                    # Check if in current month and credit account
                    if (
                        tx_date >= month_start.strftime("%Y-%m-%d")
                        and account == "credit"
                    ):
                        if amount < 0:
                            charges += abs(amount)
                        elif category == "Credit Card Payments":
                            payments += amount

                self.update_monthly_activity(charges, payments)

        except Exception as e:
            print(f"Error loading monthly activity: {e}")

    def show_status(self, message, color):
        """Show status message"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet(
            f"color: {color}; font-size: 12px; border: none; padding: 5px; margin-top: 10px;"
        )
