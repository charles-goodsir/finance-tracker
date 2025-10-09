from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class GoalsModule:
    def __init__(self, parent_widget):
        self.parent = parent_widget
        self.setup_ui()

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
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
            }
        """
        )
        layout.addWidget(self.goals_list)

        # Load existing goals
        self.load_goals()

    def add_new_goal(self):
        """Add a new financial goal"""
        dialog = QDialog()
        dialog.setWindowTitle("Add Financial Goal")
        dialog.setModal(True)

        layout = QVBoxLayout()
        dialog.setLayout(layout)

        # Goal type
        layout.addWidget(QLabel("Goal Type:"))
        goal_type = QComboBox()
        goal_type.addItems(["Savings Goal", "Debt Payoff", "Investment Goal"])
        layout.addWidget(goal_type)

        # Goal name
        layout.addWidget(QLabel("Goal Name:"))
        goal_name = QLineEdit()
        goal_name.setPlaceholderText("e.g., Vacation Fund")
        layout.addWidget(goal_name)

        # Target amount
        layout.addWidget(QLabel("Target Amount:"))
        target_amount = QLineEdit()
        target_amount.setPlaceholderText("5000")
        layout.addWidget(target_amount)

        # Current amount
        layout.addWidget(QLabel("Current Amount:"))
        current_amount = QLineEdit()
        current_amount.setPlaceholderText("0")
        layout.addWidget(current_amount)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Goal")
        save_btn.clicked.connect(dialog.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Save goal logic here
            self.load_goals()

    def load_goals(self):
        """Load and display goals"""
        self.goals_list.clear()
        self.goals_list.addItem("🎯 Vacation Fund - $2,500 / $5,000 (50%)")
        self.goals_list.addItem("💳 Credit Card Payoff - $1,200 / $3,000 (40%)")
