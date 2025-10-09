import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor
from database import DatabaseManager
from api_client import APIClient
from modules.dashboard import DashboardModule
from modules.transactions import TransactionsModule
from modules.csv_import import CSVImportModule
from modules.accounts import AccountsModule
from modules.goals import GoalsModule
from modules.insights import InsightsModule


class FinanceTrackerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Finance Tracker 2.0 - Fast")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize modules
        self.db = DatabaseManager(
            "https://35kdl5sqm4.execute-api.ap-southeast-2.amazonaws.com/Prod"
        )
        self.api = APIClient(
            "https://35kdl5sqm4.execute-api.ap-southeast-2.amazonaws.com/Prod"
        )

        # Create UI
        self.create_widgets()

        # Setup database in background
        self.db.setup_database()

    def apply_dark_mode(self):
        """Apply dark mode palette to the application"""
        dark_palette = QPalette()

        # Base colors
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(35, 35, 35))

        QApplication.instance().setPalette(dark_palette)

    def create_widgets(self):
        # Central widget with tabs
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # Dashboard tab
        self.dashboard_widget = QWidget()
        self.tab_widget.addTab(self.dashboard_widget, "📊 Dashboard")
        self.dashboard_module = DashboardModule(self.dashboard_widget, self.db)

        # Transactions tab
        self.transactions_widget = QWidget()
        self.tab_widget.addTab(self.transactions_widget, "💳 Transactions")
        self.transactions_module = TransactionsModule(self.transactions_widget, self.db)

        # CSV Import tab
        self.csv_widget = QWidget()
        self.tab_widget.addTab(self.csv_widget, "📁 CSV Import")
        self.csv_import_module = CSVImportModule(self.csv_widget, self.api, self.db)

        # Accounts tab
        self.accounts_widget = QWidget()
        self.tab_widget.addTab(self.accounts_widget, "🏦 Accounts")
        self.accounts_module = AccountsModule(self.accounts_widget)

        # Goals tab
        self.goals_widget = QWidget()
        self.tab_widget.addTab(self.goals_widget, "🎯 Goals")
        self.goals_module = GoalsModule(self.goals_widget)

        # Insights tab
        self.insights_widget = QWidget()
        self.tab_widget.addTab(self.insights_widget, "💰 Insights")
        self.insights_module = InsightsModule(self.insights_widget)

        # Connect modules for data sharing
        self.connect_modules()

    def connect_modules(self):
        """Connect modules so they can share data"""
        # When transactions are loaded, refresh dashboard
        if hasattr(self.transactions_module, "load_transactions"):
            # Connect transaction loading to dashboard refresh
            pass

        # When CSV is imported, refresh other modules
        if hasattr(self.csv_import_module, "on_import_complete"):
            # Connect CSV import completion to other modules
            pass


def main():
    app = QApplication(sys.argv)

    # Set application style for better macOS integration
    app.setStyle("Fusion")

    # Create and show main window
    window = FinanceTrackerGUI()

    # Always apply dark mode
    window.apply_dark_mode()

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
