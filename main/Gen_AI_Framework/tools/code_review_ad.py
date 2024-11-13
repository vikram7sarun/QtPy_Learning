import sys
import subprocess
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QFileDialog, QComboBox, QProgressBar,
    QTreeWidget, QTreeWidgetItem, QGroupBox, QCheckBox, QSpinBox,
    QTabWidget, QMessageBox, QSplitter, QGridLayout
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QSyntaxHighlighter, QTextCharFormat


class CodeAnalyzerWorker(QThread):
    progress = pyqtSignal(int)
    result = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, file_path: str, analysis_types: List[str], options: Dict):
        super().__init__()
        self.file_path = file_path
        self.analysis_types = analysis_types
        self.options = options

    def run(self):
        try:
            results = {}
            total_steps = len(self.analysis_types)
            current_step = 0

            for analysis_type in self.analysis_types:
                if analysis_type == "Pylint":
                    results['pylint'] = self.run_pylint()
                elif analysis_type == "Flake8":
                    results['flake8'] = self.run_flake8()
                elif analysis_type == "Radon":
                    results['radon'] = self.run_radon()
                elif analysis_type == "Bandit":
                    results['bandit'] = self.run_bandit()
                elif analysis_type == "Mypy":
                    results['mypy'] = self.run_mypy()
                elif analysis_type == "Vulture":
                    results['vulture'] = self.run_vulture()

                current_step += 1
                self.progress.emit(int((current_step / total_steps) * 100))

            self.result.emit(results)

        except Exception as e:
            self.error.emit(str(e))

    def run_pylint(self) -> Dict:
        cmd = ["pylint", "--output-format=json", self.file_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        try:
            return {'data': json.loads(result.stdout), 'raw': result.stdout}
        except json.JSONDecodeError:
            return {'data': None, 'raw': result.stdout}

    def run_flake8(self) -> Dict:
        cmd = ["flake8", "--format=json", self.file_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        try:
            return {'data': json.loads(result.stdout), 'raw': result.stdout}
        except json.JSONDecodeError:
            return {'data': None, 'raw': result.stdout}

    def run_radon(self) -> Dict:
        cc_result = subprocess.run(["radon", "cc", "-j", self.file_path], capture_output=True, text=True)
        mi_result = subprocess.run(["radon", "mi", "-j", self.file_path], capture_output=True, text=True)

        try:
            return {
                'complexity': json.loads(cc_result.stdout),
                'maintainability': json.loads(mi_result.stdout),
                'raw': f"Complexity:\n{cc_result.stdout}\nMaintainability:\n{mi_result.stdout}"
            }
        except json.JSONDecodeError:
            return {'data': None, 'raw': f"{cc_result.stdout}\n{mi_result.stdout}"}

    def run_bandit(self) -> Dict:
        cmd = ["bandit", "-f", "json", "-r", self.file_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        try:
            return {'data': json.loads(result.stdout), 'raw': result.stdout}
        except json.JSONDecodeError:
            return {'data': None, 'raw': result.stdout}

    def run_mypy(self) -> Dict:
        cmd = ["mypy", "--json", self.file_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        try:
            return {'data': json.loads(result.stdout), 'raw': result.stdout}
        except json.JSONDecodeError:
            return {'data': None, 'raw': result.stdout}

    def run_vulture(self) -> Dict:
        cmd = ["vulture", self.file_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {'data': None, 'raw': result.stdout}


class PythonSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#CC7832"))
        keywords = [
            'and', 'assert', 'break', 'class', 'continue', 'def',
            'del', 'elif', 'else', 'except', 'False', 'finally',
            'for', 'from', 'global', 'if', 'import', 'in',
            'is', 'lambda', 'None', 'not', 'or', 'pass',
            'raise', 'return', 'True', 'try', 'while', 'with',
            'yield'
        ]
        self.add_keywords(keywords, keyword_format)

        # String literals
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#6A8759"))
        self.highlighting_rules.append((
            r'"[^"\\]*(\\.[^"\\]*)*"',
            string_format
        ))
        self.highlighting_rules.append((
            r"'[^'\\]*(\\.[^'\\]*)*'",
            string_format
        ))

        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#808080"))
        self.highlighting_rules.append((
            r'#[^\n]*',
            comment_format
        ))

    def add_keywords(self, keywords, format):
        for word in keywords:
            pattern = rf'\b{word}\b'
            self.highlighting_rules.append((pattern, format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = re.compile(pattern)
            for match in expression.finditer(text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, format)


class CodeReviewTool(QWidget):
    def __init__(self):
        super().__init__()
        self.analyzer_thread = None
        self.analysis_history = []
        self.current_results = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Code Review and Quality Assurance Tool')
        self.setGeometry(100, 100, 1200, 800)

        # Main layout
        main_layout = QVBoxLayout()

        # Top controls
        controls_layout = QHBoxLayout()

        # File selection group
        file_group = QGroupBox("File Selection")
        file_layout = QHBoxLayout()

        self.file_label = QLabel("No file selected")
        self.select_file_button = QPushButton("Choose File")
        self.select_file_button.clicked.connect(self.open_file_dialog)
        self.select_file_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.select_file_button)
        file_group.setLayout(file_layout)
        controls_layout.addWidget(file_group)

        # Analysis options group
        options_group = QGroupBox("Analysis Options")
        options_layout = QGridLayout()

        # Checkboxes for different analyzers
        self.analyzer_checks = {
            "Pylint": QCheckBox("Pylint"),
            "Flake8": QCheckBox("Flake8"),
            "Radon": QCheckBox("Radon (Complexity)"),
            "Bandit": QCheckBox("Bandit (Security)")
        }

        row = 0
        col = 0
        for check in self.analyzer_checks.values():
            check.setChecked(True)
            options_layout.addWidget(check, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1

        options_group.setLayout(options_layout)
        controls_layout.addWidget(options_group)

        main_layout.addLayout(controls_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        main_layout.addWidget(self.progress_bar)

        # Create tab widget for results
        self.tabs = QTabWidget()

        # Results tree
        self.result_tree = QTreeWidget()
        self.result_tree.setHeaderLabels(["Tool", "Message"])
        self.tabs.addTab(self.result_tree, "Results")

        # Code preview
        self.code_preview = QTextEdit()
        self.code_preview.setReadOnly(True)
        self.code_preview.setFont(QFont("Consolas", 10))
        self.tabs.addTab(self.code_preview, "Code Preview")

        main_layout.addWidget(self.tabs)

        # Bottom controls
        bottom_layout = QHBoxLayout()

        self.run_button = QPushButton("Run Analysis")
        self.run_button.clicked.connect(self.run_analysis)
        self.run_button.setStyleSheet("""
            QPushButton {
                background-color: #008CBA;
                color: white;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #007399;
            }
        """)

        self.save_button = QPushButton("Save Results")
        self.save_button.clicked.connect(self.save_results)
        self.save_button.setEnabled(False)

        bottom_layout.addWidget(self.run_button)
        bottom_layout.addWidget(self.save_button)
        main_layout.addLayout(bottom_layout)

        self.setLayout(main_layout)

    def open_file_dialog(self):
        options = QFileDialog.Options()
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Select Python file",
            "",
            "Python Files (*.py);;All Files (*)",
            options=options
        )

        if file:
            self.file_path = file
            self.file_label.setText(f"Selected: {os.path.basename(file)}")
            self.load_file_preview()

    def load_file_preview(self):
        try:
            with open(self.file_path, 'r') as file:
                content = file.read()
                self.code_preview.setText(content)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load file: {str(e)}")

    def run_analysis(self):
        if not hasattr(self, 'file_path'):
            QMessageBox.warning(self, "File Error", "Please select a Python file first.")
            return

        # Get selected analyzers
        selected_analyzers = [
            name for name, check in self.analyzer_checks.items()
            if check.isChecked()
        ]

        if not selected_analyzers:
            QMessageBox.warning(self, "Selection Error", "Please select at least one analyzer.")
            return

        # Clear previous results
        self.result_tree.clear()
        self.progress_bar.setValue(0)
        self.save_button.setEnabled(False)

        # Start analysis in background thread
        self.analyzer_thread = CodeAnalyzerWorker(
            self.file_path,
            selected_analyzers,
            {}
        )
        self.analyzer_thread.progress.connect(self.update_progress)
        self.analyzer_thread.result.connect(self.handle_results)
        self.analyzer_thread.error.connect(self.handle_error)
        self.analyzer_thread.start()
        self.run_button.setEnabled(False)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def handle_results(self, results):
        self.run_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.current_results = results

        for tool, result in results.items():
            tool_item = QTreeWidgetItem([tool])
            self.result_tree.addTopLevelItem(tool_item)

            # Add result details
            result_text = result.get('raw', 'No output')
            for line in result_text.split('\n'):
                if line.strip():
                    QTreeWidgetItem(tool_item, ['', line.strip()])

        self.result_tree.expandAll()
        QMessageBox.information(self, "Complete", "Analysis completed successfully!")

    def handle_error(self, error_msg):
        self.run_button.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Analysis failed: {error_msg}")

    def save_results(self):
        if not self.current_results:
            QMessageBox.warning(self, "Warning", "No results to save.")
            return

        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Save Analysis Results",
                "code_review_report.txt",
                "Text Files (*.txt)"
            )

            if filename:
                with open(filename, 'w') as f:
                    f.write(f"Code Review Report\n")
                    f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"File analyzed: {self.file_path}\n\n")

                    for tool, result in self.current_results.items():
                        f.write(f"\n=== {tool} Analysis ===\n")
                        f.write(result.get('raw', 'No output'))
                        f.write("\n")

                QMessageBox.information(
                    self,
                    "Success",
                    f"Results saved to {filename}"
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save results: {str(e)}"
            )

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = CodeReviewTool()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()