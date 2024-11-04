import sys
import random
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox, QTableWidget, \
    QTableWidgetItem, QFormLayout


class TestOrchestrationApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.tests = []
        self.environments = ["Env 1", "Env 2", "Env 3"]  # Example environments
        self.test_status = {}  # Track test execution status

    def initUI(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Title label
        title_label = QLabel("Intelligent Test Orchestration")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title_label)

        # Input fields for test details
        self.test_name_input = QLineEdit()
        form_layout.addRow("Test Name:", self.test_name_input)

        self.priority_input = QComboBox()
        self.priority_input.addItems(["High", "Medium", "Low"])
        form_layout.addRow("Priority:", self.priority_input)

        self.dependencies_input = QLineEdit()
        form_layout.addRow("Dependencies (comma-separated):", self.dependencies_input)

        self.resource_input = QComboBox()
        self.resource_input.addItems(["CPU", "Memory", "Storage"])
        form_layout.addRow("Required Resource:", self.resource_input)

        # Button to add test
        self.add_test_button = QPushButton("Add Test")
        self.add_test_button.clicked.connect(self.add_test)
        layout.addWidget(self.add_test_button)

        # Table to display tests and their statuses
        self.test_table = QTableWidget(0, 4)
        self.test_table.setHorizontalHeaderLabels(["Test Name", "Priority", "Dependencies", "Status"])
        layout.addWidget(self.test_table)

        # Start Orchestration button
        self.start_button = QPushButton("Start Orchestration")
        self.start_button.clicked.connect(self.start_orchestration)
        layout.addWidget(self.start_button)

        # Set layout
        layout.addLayout(form_layout)
        self.setLayout(layout)
        self.setWindowTitle("Intelligent Test Orchestration")
        self.resize(600, 500)

    def add_test(self):
        # Collect test details
        test_name = self.test_name_input.text()
        priority = self.priority_input.currentText()
        dependencies = self.dependencies_input.text().split(',')
        resource = self.resource_input.currentText()

        if test_name:
            # Add test details to the list and table
            self.tests.append({
                "name": test_name,
                "priority": priority,
                "dependencies": dependencies,
                "resource": resource,
                "status": "Pending"
            })
            self.update_test_table()
            self.test_status[test_name] = "Pending"
            self.clear_input_fields()

    def clear_input_fields(self):
        # Clear input fields after adding test
        self.test_name_input.clear()
        self.dependencies_input.clear()
        self.priority_input.setCurrentIndex(0)
        self.resource_input.setCurrentIndex(0)

    def update_test_table(self):
        # Update table with the latest test data
        self.test_table.setRowCount(0)  # Clear the table
        for test in self.tests:
            row_position = self.test_table.rowCount()
            self.test_table.insertRow(row_position)
            self.test_table.setItem(row_position, 0, QTableWidgetItem(test["name"]))
            self.test_table.setItem(row_position, 1, QTableWidgetItem(test["priority"]))
            self.test_table.setItem(row_position, 2, QTableWidgetItem(", ".join(test["dependencies"])))
            self.test_table.setItem(row_position, 3, QTableWidgetItem(test["status"]))

    def start_orchestration(self):
        # Schedule and execute tests based on priority and dependencies
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        self.result_display.append("Starting Test Orchestration...\n")

        # Sort tests by priority (High, Medium, Low)
        sorted_tests = sorted(self.tests, key=lambda x: {"High": 1, "Medium": 2, "Low": 3}[x["priority"]])

        for test in sorted_tests:
            # Check if all dependencies are completed
            dependencies_met = all(
                self.test_status.get(dep.strip(), "Completed") == "Completed" for dep in test["dependencies"] if
                dep.strip())
            if dependencies_met:
                self.execute_test(test)
            else:
                test["status"] = "Waiting for dependencies"
                self.result_display.append(f"{test['name']} is waiting for dependencies to complete.\n")
                self.update_test_table()

    def execute_test(self, test):
        # Assign environment and mark as running
        assigned_env = random.choice(self.environments)
        test["status"] = f"Running on {assigned_env}"
        self.update_test_table()
        self.result_display.append(f"Executing {test['name']} on {assigned_env}...\n")

        # Simulate test execution delay
        QtCore.QTimer.singleShot(2000, lambda: self.complete_test(test))

    def complete_test(self, test):
        # Mark test as completed
        test["status"] = "Completed"
        self.test_status[test["name"]] = "Completed"
        self.update_test_table()
        self.result_display.append(f"{test['name']} completed.\n")


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = TestOrchestrationApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
