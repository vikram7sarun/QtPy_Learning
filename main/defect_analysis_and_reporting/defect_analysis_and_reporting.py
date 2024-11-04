import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox, QFormLayout, QFileDialog
import random


class DefectAnalysisApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Title label
        title_label = QLabel("Defect Analysis and Reporting")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title_label)

        # Input fields for defect details
        self.description_input = QLineEdit()
        form_layout.addRow("Defect Description:", self.description_input)

        self.component_input = QLineEdit()
        form_layout.addRow("Affected Component:", self.component_input)

        self.error_type_input = QComboBox()
        self.error_type_input.addItems(["Syntax Error", "Runtime Error", "Logic Error", "UI Bug", "Performance Issue"])
        form_layout.addRow("Error Type:", self.error_type_input)

        self.severity_input = QComboBox()
        self.severity_input.addItems(["Low", "Medium", "High", "Critical"])
        form_layout.addRow("Severity:", self.severity_input)

        # Generate Report button
        self.generate_button = QPushButton("Generate Report")
        self.generate_button.clicked.connect(self.generate_report)
        layout.addWidget(self.generate_button)

        # Display area for generated report
        self.report_display = QTextEdit()
        self.report_display.setReadOnly(True)
        layout.addWidget(QLabel("Defect Report:"))
        layout.addWidget(self.report_display)
        self.report_display.setStyleSheet("border: 1px solid lightgray;")

        # Save Report button
        self.save_button = QPushButton("Save Report")
        self.save_button.clicked.connect(self.save_report)
        layout.addWidget(self.save_button)

        # Set layout
        layout.addLayout(form_layout)
        self.setLayout(layout)
        self.setWindowTitle("Defect Analysis and Reporting")
        self.resize(500, 600)

    def generate_report(self):
        # Collect inputs
        description = self.description_input.text()
        component = self.component_input.text()
        error_type = self.error_type_input.currentText()
        severity = self.severity_input.currentText()

        # Simulate AI-generated insights (these could be enhanced with an actual AI model)
        root_cause = self.get_root_cause(error_type)
        impact = self.get_impact(severity)
        suggested_fix = self.get_suggested_fix(error_type)

        # Generate report text
        report_text = (
            f"Defect Description: {description}\n"
            f"Affected Component: {component}\n"
            f"Error Type: {error_type}\n"
            f"Severity: {severity}\n\n"
            f"Root Cause Analysis:\n{root_cause}\n\n"
            f"Impact Analysis:\n{impact}\n\n"
            f"Suggested Fix:\n{suggested_fix}\n"
        )

        # Display report in the text area
        self.report_display.setPlainText(report_text)

    def get_root_cause(self, error_type):
        root_causes = {
            "Syntax Error": "This is likely due to a missing symbol or misused syntax in the code.",
            "Runtime Error": "The defect may result from unhandled exceptions or incorrect function calls during execution.",
            "Logic Error": "The logic applied does not achieve the intended result; review the algorithm.",
            "UI Bug": "This defect may be due to incorrect styling, layout issues, or platform-specific discrepancies.",
            "Performance Issue": "This may stem from inefficient code or memory leaks. Consider profiling the code."
        }
        return root_causes.get(error_type, "Unknown cause")

    def get_impact(self, severity):
        impact_analysis = {
            "Low": "Minimal impact, does not affect core functionality.",
            "Medium": "Moderate impact, might affect secondary features.",
            "High": "High impact, affects core functionalities and user experience.",
            "Critical": "Severe impact, application may crash or have significant downtime."
        }
        return impact_analysis.get(severity, "Unknown impact level")

    def get_suggested_fix(self, error_type):
        suggested_fixes = {
            "Syntax Error": "Review the syntax in the code editor. Ensure all symbols are correctly placed.",
            "Runtime Error": "Debug the function calls and check for unhandled exceptions.",
            "Logic Error": "Test the logic and correct the algorithm to achieve the intended functionality.",
            "UI Bug": "Verify UI elements and styling. Test on different devices for compatibility.",
            "Performance Issue": "Optimize the code, avoid memory leaks, and consider lazy loading."
        }
        return suggested_fixes.get(error_type, "No fix available")

    def save_report(self):
        # Open a file dialog to save the report
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Report", "", "Text Files (*.txt);;All Files (*)",
                                                   options=options)

        if file_path:
            with open(file_path, "w") as file:
                file.write(self.report_display.toPlainText())
            QtWidgets.QMessageBox.information(self, "Success", f"Report saved to {file_path}")


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = DefectAnalysisApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
