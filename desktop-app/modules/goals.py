from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
import requests


class GoalsModule:
    def __init__(self, parent_widget, api_client):
        self.parent = parent_widget
        self.api = api_client
        self.setup_ui()
        self.load_goals()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.parent.setLayout(layout)

        # Title
        title = QLabel("🎯 Financial Goals")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; padding: 10px;")
        layout.addWidget(title)

        # Add goal button
        add_goal_btn = QPushButton("➕ Add New Goal")
        add_goal_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """
        )
        add_goal_btn.clicked.connect(self.add_new_goal)
        layout.addWidget(add_goal_btn)

        # Goals list
        self.goals_list = QListWidget()
        self.goals_list.setStyleSheet(
            """
            QListWidget {
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 5px;
                padding: 5px;
                color: white;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #4a5568;
            }
            QListWidget::item:selected {
                background-color: #4a5568;
            }
        """
        )
        layout.addWidget(self.goals_list)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh Goals")
        refresh_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """
        )
        refresh_btn.clicked.connect(self.load_goals)
        layout.addWidget(refresh_btn)

    def load_goals(self):
        """Load goals from AWS"""
        try:
            response = requests.get(
                f"{self.api.aws_api_url}/goals?user_id=user1", timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.display_goals(data.get("goals", []))
            else:
                print(f"Failed to load goals: {response.text}")
                self.goals_list.clear()
                self.goals_list.addItem("⚠️ Failed to load goals from AWS")

        except Exception as e:
            print(f"Error loading goals: {e}")
            self.goals_list.clear()
            self.goals_list.addItem("❌ Error connecting to AWS")

    def display_goals(self, goals):
        """Display goals in the list"""
        self.goals_list.clear()

        if not goals:
            self.goals_list.addItem(
                "📝 No goals yet. Click 'Add New Goal' to create one!"
            )
            return

        for goal in goals:
            progress = goal.get("progress", 0)
            current = goal.get("current_amount", 0)
            target = goal.get("target_amount", 0)

            # Format goal item
            goal_type_emoji = {"savings": "💰", "debt": "💳", "investment": "📈"}.get(
                goal.get("goal_type", "savings"), "🎯"
            )

            item_text = f"{goal_type_emoji} {goal['name']} - ${current:.2f} / ${target:.2f} ({progress:.0f}%)"
            self.goals_list.addItem(item_text)

    def add_new_goal(self):
        """Add a new financial goal"""
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("Add Financial Goal")
        dialog.setModal(True)
        dialog.setStyleSheet("background-color: #2d3748; color: white;")

        layout = QVBoxLayout()
        dialog.setLayout(layout)

        # Goal type
        layout.addWidget(QLabel("Goal Type:"))
        goal_type = QComboBox()
        goal_type.addItems(["Savings Goal", "Debt Payoff", "Investment Goal"])
        goal_type.setStyleSheet(
            """
            QComboBox {
                background-color: #4a5568;
                color: white;
                padding: 5px;
                border: 1px solid #718096;
                border-radius: 4px;
            }
        """
        )
        layout.addWidget(goal_type)

        # Goal name
        layout.addWidget(QLabel("Goal Name:"))
        goal_name = QLineEdit()
        goal_name.setPlaceholderText("e.g., Vacation Fund")
        goal_name.setStyleSheet(
            """
            QLineEdit {
                background-color: #4a5568;
                color: white;
                padding: 5px;
                border: 1px solid #718096;
                border-radius: 4px;
            }
        """
        )
        layout.addWidget(goal_name)

        # Target amount
        layout.addWidget(QLabel("Target Amount:"))
        target_amount = QLineEdit()
        target_amount.setPlaceholderText("5000")
        target_amount.setStyleSheet(
            """
            QLineEdit {
                background-color: #4a5568;
                color: white;
                padding: 5px;
                border: 1px solid #718096;
                border-radius: 4px;
            }
        """
        )
        layout.addWidget(target_amount)

        # Current amount
        layout.addWidget(QLabel("Current Amount:"))
        current_amount = QLineEdit()
        current_amount.setPlaceholderText("0")
        current_amount.setStyleSheet(
            """
            QLineEdit {
                background-color: #4a5568;
                color: white;
                padding: 5px;
                border: 1px solid #718096;
                border-radius: 4px;
            }
        """
        )
        layout.addWidget(current_amount)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Goal")
        save_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
        """
        )
        save_btn.clicked.connect(dialog.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
        """
        )
        cancel_btn.clicked.connect(dialog.reject)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Save goal to AWS
            self.save_goal_to_aws(
                goal_type.currentText(),
                goal_name.text(),
                target_amount.text(),
                current_amount.text(),
            )

    def save_goal_to_aws(self, goal_type, name, target, current):
        """Save goal to AWS API"""
        try:
            # Map display names to API values
            type_map = {
                "Savings Goal": "savings",
                "Debt Payoff": "debt",
                "Investment Goal": "investment",
            }

            payload = {
                "user_id": "user1",
                "goal_type": type_map.get(goal_type, "savings"),
                "name": name,
                "target_amount": float(target or 0),
                "current_amount": float(current or 0),
            }

            response = requests.post(
                f"{self.api.aws_api_url}/goals", json=payload, timeout=10
            )

            if response.status_code == 200:
                QMessageBox.information(
                    self.parent, "Success", f"Goal '{name}' created!"
                )
                self.load_goals()  # Refresh the list
            else:
                QMessageBox.critical(
                    self.parent, "Error", f"Failed to create goal: {response.text}"
                )

        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"Error saving goal: {str(e)}")
