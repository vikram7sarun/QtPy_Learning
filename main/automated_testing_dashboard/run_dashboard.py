# run_dashboard.py
import sys
from PyQt5.QtWidgets import QApplication
from automated_testing_dashboard import TestDashboard

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dashboard = TestDashboard()
    dashboard.show()  # Display the dashboard
    sys.exit(app.exec_())
