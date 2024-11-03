import sys
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QFileDialog, QComboBox
)
from PyQt5.QtCore import Qt


class CodeReviewTool(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Code Review and Quality Assurance Tool')
        self.setGeometry(200, 200, 800, 600)

        # Layout
        layout = QVBoxLayout()

        # File selection
        file_layout = QHBoxLayout()
        self.file_label = QLabel("Select Python file for review:")
        file_layout.addWidget(self.file_label)

        self.select_file_button = QPushButton("Choose File")
        self.select_file_button.clicked.connect(self.open_file_dialog)
        file_layout.addWidget(self.select_file_button)

        layout.addLayout(file_layout)

        # Analysis options
        self.analysis_type = QComboBox()
        self.analysis_type.addItems(["Pylint", "Flake8", "Radon (Complexity)", "Bandit (Security)"])
        layout.addWidget(self.analysis_type)

        # Run analysis button
        self.run_button = QPushButton("Run Analysis")
        self.run_button.clicked.connect(self.run_analysis)
        layout.addWidget(self.run_button)

        # Result display
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        layout.addWidget(self.result_display)

        # Set layout
        self.setLayout(layout)

    def open_file_dialog(self):
        options = QFileDialog.Options()
        file, _ = QFileDialog.getOpenFileName(self, "Select Python file", "", "Python Files (*.py);;All Files (*)",
                                              options=options)
        if file:
            self.file_path = file
            self.file_label.setText(f"File Selected: {file}")

    def run_analysis(self):
        if not hasattr(self, 'file_path'):
            self.result_display.setText("Please select a file first.")
            return

        selected_analysis = self.analysis_type.currentText()
        if selected_analysis == "Pylint":
            result = self.run_pylint(self.file_path)
        elif selected_analysis == "Flake8":
            result = self.run_flake8(self.file_path)
        elif selected_analysis == "Radon (Complexity)":
            result = self.run_radon(self.file_path)
        elif selected_analysis == "Bandit (Security)":
            result = self.run_bandit(self.file_path)

        self.result_display.setText(result)

    def run_pylint(self, file_path):
        try:
            result = subprocess.run(["pylint", file_path], capture_output=True, text=True)
            return result.stdout
        except Exception as e:
            return f"Error running pylint: {e}"

    def run_flake8(self, file_path):
        try:
            result = subprocess.run(["flake8", file_path], capture_output=True, text=True)
            return result.stdout
        except Exception as e:
            return f"Error running flake8: {e}"

    def run_radon(self, file_path):
        try:
            result = subprocess.run(["radon", "cc", "-s", file_path], capture_output=True, text=True)
            return result.stdout
        except Exception as e:
            return f"Error running radon: {e}"

    def run_bandit(self, file_path):
        try:
            result = subprocess.run(["bandit", "-r", file_path], capture_output=True, text=True)
            return result.stdout
        except Exception as e:
            return f"Error running bandit: {e}"


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CodeReviewTool()
    window.show()
    sys.exit(app.exec_())
