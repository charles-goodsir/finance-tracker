from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
import requests
from .widgets import StatCard, StyledTableWidget
from .accounts import ACCOUNT_TYPES
from .credit_card import CreditCardWidget
from datetime import datetime



class DashboardModule:
    def __init__(self, parent_widget, db_manager, api_client=None):
        self.parent = parent_widget
        self.db = db_manager
        self.api = api_client
        self.balance_inputs = {}  # store account balance QLineEdits
        self.setup_ui()
        if self.api:
            self.load_net_worth()

    def setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        self.parent.setLayout(main_layout)

        # Header section
        header_frame = QFrame()
        header_frame.setStyleSheet(
            """
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a5568, stop:1 #5a67d8);
                border-radius: 10px;
                margin: 5px;
            }
        """
        )
        header_layout = QVBoxLayout()
        header_frame.setLayout(header_layout)

        # Main title
        title = QLabel("💰 Finance Dashboard")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; padding: 20px;")
        header_layout.addWidget(title)

        # Subtitle
        self.subtitle = QLabel("Track your financial health")
        self.subtitle.setFont(QFont("Arial", 12))
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle.setStyleSheet(
            "color: rgba(255,255,255,0.8); padding-bottom: 10px;"
        )
        header_layout.addWidget(self.subtitle)

        main_layout.addWidget(header_frame)

        # Stats cards layout
        stats_layout = QHBoxLayout()

        self.income_card = StatCard("Income", "$0.00", "#4CAF50", "💰")
        stats_layout.addWidget(self.income_card)

        self.expense_card = StatCard("Expenses", "$0.00", "#F44336", "💸")
        stats_layout.addWidget(self.expense_card)

        self.net_card = StatCard("Net", "$0.00", "#2196F3", "📈")
        stats_layout.addWidget(self.net_card)

        main_layout.addLayout(stats_layout)

        stats_layout_2 = QHBoxLayout()
        self.networth_card = StatCard("Net Worth", "$0.00", "#9C27B0", "💎")
        stats_layout_2.addWidget(self.networth_card)
        self.credit_card = StatCard("Credit %", "0%", "#FF9800", "💳")
        stats_layout_2.addWidget(self.credit_card)
        self.savings_card = StatCard("Savings Rate", "0%", "#00BCD4", "📊")
        stats_layout_2.addWidget(self.savings_card)
        main_layout.addLayout(stats_layout_2)

        # Insights
        insights_frame = QGroupBox("🎯 Quick Insights")
        insights_frame.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 25px;
                padding-top: 10px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 5px 5px 5px 5px;
            }
        """
        )
        insights_layout = QVBoxLayout()
        insights_frame.setLayout(insights_layout)
        self.insights_text = QLabel("Loading insights...")
        self.insights_text.setStyleSheet(
            """
            QLabel {
                padding: 10px;
                background-color: white;
                border-radius: 5px;
                border: 1px solid #ddd;
                font-size: 13px;
                line-height: 1.4;
            }
        """
        )
        self.insights_text.setWordWrap(True)
        insights_layout.addWidget(self.insights_text)
        main_layout.addWidget(insights_frame)

        # Recent transactions preview
        recent_frame = QGroupBox("📋 Recent Transactions")
        recent_frame.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 25px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 5px 5px 5px 5px;
            }
        """
        )
        recent_layout = QVBoxLayout()
        recent_frame.setLayout(recent_layout)
        self.recent_table = StyledTableWidget(["Date", "Description", "Amount", "Category"])
        self.recent_table.setMaximumHeight(200)
        recent_layout.addWidget(self.recent_table)
        main_layout.addWidget(recent_frame)

        # Action buttons
        button_layout = QHBoxLayout()
        refresh_btn = QPushButton("🔄 Refresh Dashboard")
        refresh_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:pressed { background-color: #3d8b40; }
        """
        )
        refresh_btn.clicked.connect(self.refresh_dashboard)
        button_layout.addStretch()
        button_layout.addWidget(refresh_btn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        main_layout.addStretch()

    def refresh_dashboard(self):
        """Refresh dashboard data from AWS for current period"""
        if not self.api:
            self._refresh_local_data()
            return
        refresh_method = {
            "Current Period Stats": self.load_current_period_stats,
            "Net Worth": self.load_networth_data,
            "Credit Utilization": self.load_credit_utilization,
            "Savings Rate": self.load_savings_rate,
            "Quick Insights": self.load_quick_insights,
            "Financial Health": self.load_financial_health,
            "Recent Transactions": self.load_recent_transactions_from_aws,
        }

        for name, method in refresh_method.items():
            try:
                method()
            except Exception as e:
                print(f"Failed to load {name}: {e}")

    def _refresh_local_data(self):
        """Fallback method for local data refresh"""
        transactions = self.db.get_local_transactions()
        self.update_stats(transactions)
        self.update_recent_transactions(transactions)

    def update_stats(self, transactions):
        """Update the stat cards with transaction data"""
        # Exclude these categories from income/expense calculations
        excluded_categories = [
            "Transfers",
            "Payment",
            "Cash Withdrawal",
            "Credit Card Payments",
        ]

        # Filter transactions
        filtered_txs = [
            tx for tx in transactions if tx.get("category") not in excluded_categories
        ]

        income = sum(tx["amount"] for tx in filtered_txs if tx["amount"] > 0)
        expenses = abs(sum(tx["amount"] for tx in filtered_txs if tx["amount"] < 0))
        net = income - expenses

        self.income_card.update_value(f"${income:.2f}")
        self.expense_card.update_value(f"${expenses:.2f}")
        self.net_card.update_value(f"${net:.2f}")

        self.update_account_balances(transactions)

    def update_account_balances(self, transactions):
        """Calculate balances for each account"""
        balances = {account_id: 0 for account_id in ACCOUNT_TYPES.keys()}

        for tx in transactions:
            account = tx.get("account", "main")
            if account in balances:
                balances[account] += tx["amount"]

        # You can display these balances in the accounts module
        print(f"Account Balances: {balances}")

    def update_recent_transactions(self, transactions):
        """Update the recent transactions table"""
        # Show only last 5 transactions
        recent_transactions = transactions[:5]
        self.recent_table.setRowCount(len(recent_transactions))

        for row, tx in enumerate(recent_transactions):
            self.recent_table.setItem(row, 0, QTableWidgetItem(tx["date"]))
            self.recent_table.setItem(row, 1, QTableWidgetItem(tx["description"]))
            self.recent_table.setItem(row, 2, QTableWidgetItem(f"${tx['amount']:.2f}"))

    def load_current_period_stats(self):
        """Load stats for the most recent snapshot period from AWS"""
        import requests
        from datetime import datetime, timedelta

        if not self.api:
            return

        try:
            # First, get the most recent snapshot to determine the period
            response = requests.get(
                f"{self.api.aws_api_url}/snapshots/list?user_id=user1&limit=1",
                timeout=10,
            )

            if response.status_code != 200 or not response.json().get("snapshots"):
                # No snapshots, show all-time stats
                self.update_stats(self.db.get_local_transactions())
                return

            latest_snapshot = response.json()["snapshots"][0]
            end_date = latest_snapshot["snapshot_date"]  # e.g., "2025-10-10"

            # Calculate start date (1 month before)
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            start_dt = end_dt - timedelta(days=30)
            start_date = start_dt.strftime("%Y-%m-%d")

            # Fetch period summary from AWS
            summary_response = requests.get(
                f"{self.api.aws_api_url}/summary/period",
                params={
                    "user_id": "user1",
                    "start_date": start_date,
                    "end_date": end_date,
                },
                timeout=10,
            )

            if summary_response.status_code == 200:
                data = summary_response.json()
                summary = data.get("transaction_based", {})

                # Update cards with current period data
                self.income_card.update_value(f"${summary.get('income', 0):.2f}")
                self.expense_card.update_value(f"${summary.get('spending', 0):.2f}")
                self.net_card.update_value(f"${summary.get('net_savings', 0):.2f}")

                # Update subtitle to show period
                self.subtitle.setText(f"Current Period: {start_date} to {end_date}")
            else:
                print(f"Failed to load period summary: {summary_response.text}")

        except Exception as e:
            print(f"Error loading current period stats: {e}")

    def load_recent_transactions_from_aws(self):
        """Load recent transactions from AWS"""
        import requests

        if not self.api:
            return

        try:
            response = requests.get(
                f"{self.api.aws_api_url}/transactions?user_id=user1&limit=5", timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                transactions = data.get("items", [])
                self.display_recent_transactions_aws(transactions)

        except Exception as e:
            print(f"Error loading recent transactions: {e}")

    def display_recent_transactions_aws(self, transactions):
        """Display recent transactions from AWS format"""
        self.recent_table.setRowCount(len(transactions))

        for row, tx in enumerate(transactions):
            self.recent_table.setItem(row, 0, QTableWidgetItem(tx.get("date", "")))
            self.recent_table.setItem(
                row, 1, QTableWidgetItem(tx.get("description", ""))
            )
            self.recent_table.setItem(
                row, 2, QTableWidgetItem(f"${tx.get('amount', 0):.2f}")
            )
            self.recent_table.setItem(row, 3, QTableWidgetItem(tx.get("category", "")))

    def load_net_worth(self):
        """Load and display net worth from AWS"""
        import requests

        if not self.api:
            return

        try:
            response = requests.get(
                f"{self.api.aws_api_url}/accounts/networth?user_id=user1", timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                print(f"💰 Net Worth: ${data['net_worth']:.2f}")
                print(f"📈 Assets: ${data['total_assets']:.2f}")
                print(f"📉 Liabilities: ${data['total_liabilities']:.2f}")
                print("Account Balances:")
                for account, balance in data["accounts"].items():
                    print(f"  {account}: ${balance:.2f}")

        except Exception as e:
            print(f"Error loading net worth: {e}")

    def load_networth_data(self):
        """Load networth data for the networth card"""
        if not self.api:
            return
        try:
            response = requests.get(
                f"{self.api.aws_api_url}/accounts/networth?user_id=user1", timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                networth = data.get("net_worth", 0)
                self.networth_card.update_value(f"${networth:,.2f}")
        except Exception as e:
            print(f"Error loading net worth: {e}")

    def load_credit_utilization(self):
        """Load credit card utilization"""
        if not self.api:
            return

        try:

            response = requests.get(
                f"{self.api.aws_api_url}/snapshots/list?user_id=user1&limit=1",
                timeout=10,
            )

            if response.status_code == 200:
                snapshots = response.json().get("snapshots", [])
                if snapshots:
                    snapshot = snapshots[0]
                    credit_balance = snapshot.get("credit", 0)
                    credit_limit = 4000

                    if credit_limit > 0:
                        utilization = (abs(credit_balance) / credit_limit) * 100
                        color = (
                            "#4CAF50"
                            if utilization < 30
                            else "#FF9800" if utilization < 50 else "#F44336"
                        )
                        emoji = (
                            "✅"
                            if utilization < 30
                            else "⚠️" if utilization < 50 else "🚨"
                        )
                        self.credit_card.update_value(f"{utilization:.1f}% {emoji}")
                        self.credit_card.setStyleSheet(f"background-color: {color};")
        except Exception as e:
            print(f"Error loading credit utilization: {e}")

    def load_savings_rate(self):
        """Load savings rate from period summary"""
        if not self.api:
            return
        try:
            response = requests.get(
                f"{self.api.aws_api_url}/summary/period?user_id=user1", timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                transaction_data = data.get("transactions_based", {})
                savings_rate = transaction_data.get("savings_rate", 0)

                color = (
                    "#4CAF50"
                    if savings_rate > 20
                    else "#FF9800" if savings_rate > 0 else "#F44336"
                )
                emoji = "🎉" if savings_rate > 20 else "⚠️" if savings_rate > 0 else "🚨"

                self.savings_card.update_value(f"{savings_rate:.1f}% {emoji}")
                self.savings_card.setStyleSheet(f"background-color: {color};")
        except Exception as e:
            print(f"Error loading savings rate: {e}")

    def load_quick_insights(self):
        """Load quick insights from the insights API"""
        if not self.api:
            self.insights_text.setText("API not available")
            return
        try:

            response = requests.get(
                f"{self.api.aws_api_url}/insights?user_id=user1", timeout=10
            )

            if response.status_code != 200:
                self.insights_text.setText("• Server error - try refreshing")
                return
            data = response.json()
            insights = data.get("insights", {})

            insight_sources = [
                ("alerts", 2),
                ("suggestions", 1),
                ("trends", 1),
                ("forecasts", 1),
            ]

            all_insights = [
                insight
                for source, limit in insight_sources
                for insight in insights.get(source, [])[:limit]
            ]

            if all_insights:
                insights_text = "\n".join([f"• {insight}" for insight in all_insights])
                self.insights_text.setText(insights_text)
            else:
                self.insights_text.setText("• No insights available at the moment")
        except requests.exceptions.Timeout:
            self.insights_text.setText("• Request timeout - try again")
        except requests.exceptions.ConnectionError:
            self.insights_text.setText("• Connection error - check network")
        except Exception as e:
            print(f"Error loading insights: {e}")
            self.insights_text.setText("• Unable to load insights")

    def load_financial_health(self):
        """Load financial health score from AWS"""
        if not self.api:
            return
        try:
            response = requests.get(
                f"{self.api.aws_api_url}/insights?user_id=user1", timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                insights = data.get("insights", {})

                health_score = insights.get("health_score", 0)
                health_status = insights.get("health_status", "Unknown")

                print(f"Financial Health: {health_score}/100 ({health_status})")
        except Exception as e:
            print(f"Error loading financial health: {e}")

    def view_credit_transactions(self):
        """Placeholder: open credit transactions (not implemented in dashboard)."""
        print("Dashboard: view_credit_transactions clicked")

    def show_payment_history(self):
        """Placeholder: show payment history (not implemented in dashboard)."""
        print("Dashboard: show_payment_history clicked")

    # --- Snapshot helpers (mirrors AccountsModule minimal behavior) ---
    def show_status(self, message, color):
        """Show status message in the dashboard's status label."""
        if hasattr(self, "status_label"):
            self.status_label.setText(message)
            self.status_label.setStyleSheet(
                f"color: {color}; font-weight: bold; padding: 10px;"
            )

    def save_snapshot(self):
        """Save monthly snapshot of all balances from the dashboard inputs."""
        if not self.api:
            self.show_status("⚠️ API client not configured", "orange")
            return

        balances = {}
        missing = []
        for account_key in ACCOUNT_TYPES.keys():
            balance_widget = self.balance_inputs.get(account_key)
            balance_text = (balance_widget.text() if balance_widget else "").replace("$", "").replace(
                ",", ""
            ).strip()
            if balance_text:
                try:
                    balances[account_key] = float(balance_text)
                except ValueError:
                    missing.append(ACCOUNT_TYPES[account_key]["name"])
            else:
                missing.append(ACCOUNT_TYPES[account_key]["name"])

        if missing:
            self.show_status(f"⚠️ Missing balances: {', '.join(missing)}", "orange")
            return

        snapshot_date = self.snapshot_date.date().toString("yyyy-MM-dd")
        try:
            response = requests.post(
                f"{self.api.aws_api_url}/snapshots/balance",
                json={"user_id": "user1", "snapshot_date": snapshot_date, **balances},
                timeout=10,
            )
            if response.status_code == 200:
                self.show_status(f"✅ Snapshot saved for {snapshot_date}!", "#4CAF50")
                QTimer.singleShot(500, self.load_snapshots)
            else:
                self.show_status(f"❌ Failed: {response.text}", "#F44336")
        except Exception as e:
            self.show_status(f"❌ Error: {str(e)}", "#F44336")

    def load_snapshots(self):
        """Load recent snapshots and display in the table on dashboard."""
        if not self.api:
            return
        try:
            response = requests.get(
                f"{self.api.aws_api_url}/snapshots/list?user_id=user1&limit=12",
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                snapshots = data.get("snapshots", [])
                self.display_snapshots(snapshots)
                self.show_status(f"✅ Loaded {len(snapshots)} snapshots", "#4CAF50")
            else:
                self.show_status("⚠️ No snapshots found", "orange")
        except Exception as e:
            self.show_status(f"❌ Error loading: {str(e)}", "#F44336")

    def display_snapshots(self, snapshots):
        """Render snapshots into the dashboard table."""
        if not hasattr(self, "snapshots_table"):
            return
        self.snapshots_table.setRowCount(len(snapshots))
        for row, snapshot in enumerate(snapshots):
            self.snapshots_table.setItem(row, 0, QTableWidgetItem(snapshot.get("snapshot_date", "")))
            self.snapshots_table.setItem(row, 1, QTableWidgetItem(f"${snapshot.get('savings', 0):.2f}"))
            self.snapshots_table.setItem(row, 2, QTableWidgetItem(f"${snapshot.get('bills', 0):.2f}"))
            self.snapshots_table.setItem(row, 3, QTableWidgetItem(f"${snapshot.get('main', 0):.2f}"))
            self.snapshots_table.setItem(row, 4, QTableWidgetItem(f"${snapshot.get('credit', 0):.2f}"))
            self.snapshots_table.setItem(row, 5, QTableWidgetItem(f"${snapshot.get('total_assets', 0):.2f}"))
