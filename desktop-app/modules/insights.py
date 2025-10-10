from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
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
        """Update UI with real insight data from AWS"""
        # Update health score
        score = data.get("health_score", 0)
        self.health_score.setText(f"Score: {score}/100")

        # Update description based on score
        if score >= 80:
            description = "Excellent! You're managing your finances very well."
            color = "#4CAF50"
        elif score >= 60:
            description = "Good job! Keep up the good work."
            color = "#FFC107"
        else:
            description = "There's room for improvement. Review your spending."
            color = "#F44336"

        self.health_score.setStyleSheet(f"color: {color};")
        self.health_description.setText(description)

        # Update alerts
        self.alerts_list.clear()
        for alert in data.get("alerts", []):
            self.alerts_list.addItem(alert.get("message", ""))

        # Update suggestions based on category breakdown
        self.suggestions_list.clear()
        category_breakdown = data.get("category_breakdown", {})

        if category_breakdown:
            top_category = max(category_breakdown.items(), key=lambda x: x[1])
            self.suggestions_list.addItem(
                f"💡 Your top spending category is {top_category[0]} at ${top_category[1]:.2f}"
            )

        savings_rate = data.get("savings_rate", 0)
        if savings_rate < 20:
            self.suggestions_list.addItem(
                f"💰 Try to save at least 20% of your income (currently {savings_rate:.0f}%)"
            )
        else:
            self.suggestions_list.addItem(
                f"🎯 Great savings rate of {savings_rate:.0f}%!"
            )
            # Method content here...

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
