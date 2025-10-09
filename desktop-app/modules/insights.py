from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class InsightsModule:
    def __init__(self, parent_widget):
        self.parent = parent_widget
        self.setup_ui()

    def load_spending_alerts(self):
        """Load spending alerts and suggestions"""
        # Method content here...

    def load_savings_suggestions(self):
        """Load savings suggestions"""
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
        self.load_spending_alerts()
        self.load_savings_suggestions()

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
