from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
import requests


class InsightsModule:
    def __init__(self, parent_widget, api_client):
        self.parent = parent_widget
        self.api = api_client
        self.setup_ui()

    def load_spending_alerts(self):
        """Load spending alerts and suggestions"""
        # Method content here...

    def load_insights_from_aws(self):
        """Load real insights from AWS"""
        try:
            response = requests.get(
                f"{self.api.aws_api_url}/insights?user_id=user1", timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.update_with_real_data(data)
            else:
                print(f"Failed to load insights: {response.text}")

        except Exception as e:
            print(f"Error loading insights: {e}")

    def update_with_real_data(self, data):
        """Update UI with enhanced insight data from AWS"""
        # Update health score
        score = data.get("health_score", 0)
        self.health_score.setText(f"Score: {score}/100")

        # Update description with natural language summary
        summary = data.get("summary", "")
        if summary:
            self.health_description.setText(summary)
        else:
            # Fallback to old description logic
            if score >= 80:
                description = "Excellent! You're managing your finances very well."
            elif score >= 60:
                description = "Good job! Keep up the good work."
            else:
                description = "There's room for improvement. Review your spending."
            self.health_description.setText(description)
        
        # Color based on score
        if score >= 80:
            color = "#4CAF50"
        elif score >= 60:
            color = "#FFC107"
        else:
            color = "#F44336"
        self.health_score.setStyleSheet(f"color: {color};")

        # Update alerts with new data
        self.alerts_list.clear()
        for alert in data.get("alerts", []):
            self.alerts_list.addItem(alert.get("message", ""))
        
        # If no alerts, show a friendly message
        if not data.get("alerts"):
            self.alerts_list.addItem("✅ Everything looks good!")

        # Update suggestions with actionable recommendations
        self.suggestions_list.clear()
        
        # Add suggestions from backend (with $ amounts and priorities)
        suggestions = data.get("suggestions", [])
        if suggestions:
            for suggestion in suggestions:
                priority = suggestion.get("priority", "medium")
                emoji = "🔴" if priority == "high" else "🟡"
                self.suggestions_list.addItem(f"{emoji} {suggestion.get('message', '')}")
        
        # Add trends information
        trends = data.get("trends", {})
        if trends:
            spending_change = trends.get("spending_change_percent", 0)
            if abs(spending_change) > 5:
                direction = "increased" if spending_change > 0 else "decreased"
                emoji = "📈" if spending_change > 0 else "📉"
                self.suggestions_list.addItem(
                    f"{emoji} Spending {direction} {abs(spending_change):.0f}% vs last month"
                )
        
        # Add forecast information
        forecast = data.get("forecast", {})
        if forecast:
            projected = forecast.get("projected_monthly_spending", 0)
            days_remaining = forecast.get("days_remaining", 0)
            if projected > 0 and days_remaining > 0:
                self.suggestions_list.addItem(
                    f"📊 Projected monthly spending: ${projected:.0f} ({days_remaining} days left)"
                )
        
        # If no suggestions, show encouragement
        if not suggestions and not trends and not forecast:
            self.suggestions_list.addItem("💡 Keep tracking your expenses for personalized insights!")
            self.suggestions_list.addItem("📈 Add more transactions to see trends and forecasts")

    def setup_ui(self):
        layout = QVBoxLayout()
        self.parent.setLayout(layout)

        # Title
        title = QLabel("💰 Smart Insights")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; padding: 10px;")
        layout.addWidget(title)

        # Financial health score
        health_frame = QGroupBox("🏆 Financial Health Score")
        health_frame.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """
        )
        health_layout = QVBoxLayout()
        health_frame.setLayout(health_layout)

        self.health_score = QLabel("Score: 85/100")
        self.health_score.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.health_score.setStyleSheet("color: #4CAF50;")
        health_layout.addWidget(self.health_score)

        self.health_description = QLabel(
            "Great job! You're managing your finances well."
        )
        self.health_description.setStyleSheet("color: #666;")
        health_layout.addWidget(self.health_description)

        layout.addWidget(health_frame)

        # Spending alerts
        alerts_frame = QGroupBox("⚠️ Spending Alerts")
        alerts_frame.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #FF9800;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """
        )
        alerts_layout = QVBoxLayout()
        alerts_frame.setLayout(alerts_layout)

        self.alerts_list = QListWidget()
        self.alerts_list.setStyleSheet(
            """
            QListWidget {
                background-color: #666;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
        """
        )
        alerts_layout.addWidget(self.alerts_list)

        # Load alerts

        layout.addWidget(alerts_frame)

        # Savings suggestions
        suggestions_frame = QGroupBox("💡 Savings Suggestions")
        suggestions_frame.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #2196F3;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """
        )
        suggestions_layout = QVBoxLayout()
        suggestions_frame.setLayout(suggestions_layout)

        self.suggestions_list = QListWidget()
        self.suggestions_list.setStyleSheet(
            """
            QListWidget {
                background-color: #666;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
        """
        )
        suggestions_layout.addWidget(self.suggestions_list)

        # Load suggestions

        layout.addWidget(suggestions_frame)

        # ===== NEW: Period Summary Section =====
        layout.addSpacing(20)

        period_title = QLabel("📊 Monthly Savings Verification")
        period_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        period_title.setStyleSheet("color: white; padding: 10px;")
        layout.addWidget(period_title)

        # Period selector
        period_panel = QFrame()
        period_panel.setStyleSheet(
            """
            QFrame {
                background-color: #2d3748;
                border: 2px solid #4a5568;
                border-radius: 8px;
                padding: 15px;
            }
        """
        )
        period_layout = QHBoxLayout()
        period_panel.setLayout(period_layout)

        start_label = QLabel("Start Date:")
        start_label.setStyleSheet("color: white; font-weight: bold;")
        period_layout.addWidget(start_label)

        self.period_start = QDateEdit()
        self.period_start.setCalendarPopup(True)
        # Default to first day of current month
        from datetime import datetime

        today = datetime.now()
        self.period_start.setDate(datetime(today.year, today.month, 1).date())
        self.period_start.setDisplayFormat("yyyy-MM-dd")
        self.period_start.setStyleSheet(
            """
            QDateEdit {
                background-color: #4a5568;
                color: white;
                padding: 8px;
                border: 1px solid #718096;
                border-radius: 4px;
                min-width: 120px;
            }
        """
        )
        period_layout.addWidget(self.period_start)

        end_label = QLabel("End Date:")
        end_label.setStyleSheet("color: white; font-weight: bold;")
        period_layout.addWidget(end_label)

        self.period_end = QDateEdit()
        self.period_end.setCalendarPopup(True)
        self.period_end.setDate(today.date())
        self.period_end.setDisplayFormat("yyyy-MM-dd")
        self.period_end.setStyleSheet(
            """
            QDateEdit {
                background-color: #4a5568;
                color: white;
                padding: 8px;
                border: 1px solid #718096;
                border-radius: 4px;
                min-width: 120px;
            }
        """
        )
        period_layout.addWidget(self.period_end)

        period_layout.addStretch()

        calculate_btn = QPushButton("Calculate")
        calculate_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #3b82f6;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """
        )
        calculate_btn.clicked.connect(self.calculate_period_summary)
        period_layout.addWidget(calculate_btn)

        layout.addWidget(period_panel)

        # Summary display
        self.summary_frame = QFrame()
        self.summary_frame.setStyleSheet(
            """
            QFrame {
                background-color: #1a202c;
                border: 2px solid #4a5568;
                border-radius: 8px;
                padding: 20px;
            }
        """
        )
        summary_layout = QVBoxLayout()
        self.summary_frame.setLayout(summary_layout)

        self.summary_label = QLabel("Select a date range and click Calculate")
        self.summary_label.setStyleSheet("color: #a0aec0; font-size: 14px;")
        self.summary_label.setWordWrap(True)
        summary_layout.addWidget(self.summary_label)

        layout.addWidget(self.summary_frame)

        # Add refresh button
        refresh_btn = QPushButton("🔄 Refresh Insights")
        refresh_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """
        )
        refresh_btn.clicked.connect(self.load_insights_from_aws)
        layout.addWidget(refresh_btn)

        # Load data after UI is created
        self.load_insights_from_aws()

    def load_spending_alerts(self):
        """Load spending alerts and suggestions"""
        self.alerts_list.clear()
        self.alerts_list.addItem("🍽️ You spent 50% more on dining this month")
        self.alerts_list.addItem("📈 Your savings rate increased by 15% this month")
        self.alerts_list.addItem("🎯 You're 75% towards your vacation goal!")
        self.alerts_list.addItem("⚠️ Credit card balance increased by $200")

    def load_savings_suggestions(self):
        """Load savings suggestions"""
        self.suggestions_list.clear()
        self.suggestions_list.addItem("💡 You could save $200 by reducing dining out")
        self.suggestions_list.addItem(
            "💰 Consider setting up automatic savings transfers"
        )
        self.suggestions_list.addItem(
            "📊 Review your subscription services - save $50/month"
        )
        self.suggestions_list.addItem("🎯 You're on track to meet your savings goal!")

    def update_health_score(self, score, description):
        """Update the financial health score"""
        self.health_score.setText(f"Score: {score}/100")
        self.health_description.setText(description)

    def calculate_period_summary(self):
        """Calculate and display period summary"""
        if not self.api:
            self.summary_label.setText("⚠️ API client not configured")
            return

        start_date = self.period_start.date().toString("yyyy-MM-dd")
        end_date = self.period_end.date().toString("yyyy-MM-dd")

        try:
            response = requests.get(
                f"{self.api.aws_api_url}/summary/period",
                params={
                    "user_id": "user1",
                    "start_date": start_date,
                    "end_date": end_date,
                },
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                self.display_period_summary(data)
            else:
                self.summary_label.setText(f"❌ Failed to calculate: {response.text}")

        except Exception as e:
            self.summary_label.setText(f"❌ Error: {str(e)}")

    def display_period_summary(self, data):
        """Display the period summary with verification"""
        # Clear existing layout
        layout = self.summary_frame.layout()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Build summary text
        period = data.get("period", {})
        balance_based = data.get("balance_based")
        transaction_based = data.get("transaction_based", {})
        verification = data.get("verification", {})

        summary_html = f"""
        <div style="color: white; font-size: 14px; line-height: 1.8;">
            <h3 style="color: #60a5fa; margin-bottom: 15px;">
                📅 Period: {period.get('start_date')} to {period.get('end_date')}
            </h3>
        """

        # Balance-based section
        if balance_based:
            summary_html += f"""
            <div style="background-color: #2d3748; padding: 15px; border-radius: 8px; margin: 10px 0;">
                <h4 style="color: #34d399; margin-bottom: 10px;">💰 Balance-Based (Real Money)</h4>
                <p><b>Starting Balance:</b> ${balance_based.get('starting_balance', 0):,.2f}</p>
                <p><b>Ending Balance:</b> ${balance_based.get('ending_balance', 0):,.2f}</p>
                <p style="font-size: 16px; font-weight: bold; color: #34d399;">
                    <b>Real Savings:</b> ${balance_based.get('savings', 0):,.2f}
                </p>
            </div>
            """
        else:
            summary_html += """
            <div style="background-color: #2d3748; padding: 15px; border-radius: 8px; margin: 10px 0;">
                <p style="color: #fbbf24;">⚠️ No balance snapshots found for this period</p>
                <p style="color: #9ca3af; font-size: 12px;">
                    Save snapshots in the Accounts tab to enable balance verification
                </p>
            </div>
            """

        # Transaction-based section
        summary_html += f"""
        <div style="background-color: #2d3748; padding: 15px; border-radius: 8px; margin: 10px 0;">
            <h4 style="color: #60a5fa; margin-bottom: 10px;">📊 Transaction-Based (Breakdown)</h4>
            <p><b>Income:</b> ${transaction_based.get('income', 0):,.2f}</p>
            <p><b>Spending:</b> ${transaction_based.get('spending', 0):,.2f}</p>
            <p style="font-size: 16px; font-weight: bold; color: #60a5fa;">
                <b>Net Savings:</b> ${transaction_based.get('net_savings', 0):,.2f}
            </p>
            <p><b>Savings Rate:</b> {transaction_based.get('savings_rate', 0):.1f}%</p>
            <p style="color: #9ca3af; font-size: 12px;">
                ({data.get('transaction_count', 0)} transactions, transfers excluded)
            </p>
        </div>
        """

        # Verification section
        status = verification.get("status", "unknown")
        message = verification.get("message", "")
        discrepancy = verification.get("discrepancy")

        if status == "verified":
            status_color = "#10b981"
            status_icon = "✅"
        elif status == "minor_difference":
            status_color = "#fbbf24"
            status_icon = "⚠️"
        elif status == "needs_review":
            status_color = "#ef4444"
            status_icon = "🚨"
        else:
            status_color = "#6b7280"
            status_icon = "ℹ️"

        summary_html += f"""
        <div style="background-color: {status_color}22; border: 2px solid {status_color}; 
                    padding: 15px; border-radius: 8px; margin: 15px 0;">
            <h4 style="color: {status_color}; margin-bottom: 10px;">
                {status_icon} Verification Status
            </h4>
            <p style="color: white; font-size: 14px; font-weight: bold;">{message}</p>
        """

        if discrepancy is not None:
            summary_html += f"""
            <p style="color: #9ca3af; font-size: 12px; margin-top: 10px;">
                Discrepancy: ${abs(discrepancy):,.2f}
            </p>
            """

        summary_html += """
        </div>
        </div>
        """

        # Display in label
        summary_label = QLabel(summary_html)
        summary_label.setWordWrap(True)
        summary_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(summary_label)
