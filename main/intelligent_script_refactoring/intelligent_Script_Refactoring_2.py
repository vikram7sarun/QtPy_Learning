import ast
import sys
import subprocess
import tempfile
import os
from typing import List, Dict
import astunparse
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QFileDialog, QListWidget, QMessageBox,
    QProgressBar, QSpinBox, QComboBox, QGroupBox, QGridLayout,
    QSplitter, QTreeWidget, QTreeWidgetItem, QCheckBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
import autopep8
import black
import isort
from rope.base.project import Project
from rope.refactor.rename import Rename
from rope.refactor.extract import ExtractMethod


class CodeAnalyzerWorker(QThread):
    finished = pyqtSignal(dict)
    progress = pyqtSignal(int)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        results = {}

        # Run various analysis tools
        try:
            # Pylint analysis
            result = subprocess.run(["pylint", self.file_path], capture_output=True, text=True)
            results['pylint'] = result.stdout
            self.progress.emit(33)

            # Run additional static analysis
            with open(self.file_path, 'r') as file:
                tree = ast.parse(file.read())

            # Analyze code complexity
            results['complexity'] = self.analyze_complexity(tree)
            self.progress.emit(66)

            # Find code smells
            results['code_smells'] = self.detect_code_smells(tree)
            self.progress.emit(100)

        except Exception as e:
            results['error'] = str(e)

        self.finished.emit(results)

    def analyze_complexity(self, tree) -> Dict:
        complexity_info = {
            'functions': [],
            'classes': [],
            'imports': []
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self.calculate_cyclomatic_complexity(node)
                complexity_info['functions'].append({
                    'name': node.name,
                    'complexity': complexity,
                    'lines': node.lineno
                })
            elif isinstance(node, ast.ClassDef):
                complexity_info['classes'].append({
                    'name': node.name,
                    'methods': len([n for n in node.body if isinstance(n, ast.FunctionDef)])
                })
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                complexity_info['imports'].append(str(node.names[0].name))

        return complexity_info

    def calculate_cyclomatic_complexity(self, node) -> int:
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.And, ast.Or)):
                complexity += 1
        return complexity

    def detect_code_smells(self, tree) -> List[Dict]:
        smells = []

        for node in ast.walk(tree):
            # Long method detection
            if isinstance(node, ast.FunctionDef):
                if len(node.body) > 15:
                    smells.append({
                        'type': 'long_method',
                        'name': node.name,
                        'line': node.lineno
                    })

            # Large class detection
            elif isinstance(node, ast.ClassDef):
                method_count = len([n for n in node.body if isinstance(n, ast.FunctionDef)])
                if method_count > 10:
                    smells.append({
                        'type': 'large_class',
                        'name': node.name,
                        'line': node.lineno
                    })

        return smells


class ScriptRefactoringTool(QWidget):
    def __init__(self):
        super().__init__()
        self.analyzer_thread = None
        self.refactoring_history = []
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Advanced Script Refactoring Tool')
        self.setGeometry(100, 100, 1200, 800)

        # Main layout
        main_layout = QHBoxLayout()

        # Left panel for controls
        left_panel = QVBoxLayout()

        # File selection group
        file_group = QGroupBox("File Selection")
        file_layout = QVBoxLayout()

        self.file_label = QLabel("No file selected")
        self.select_file_button = QPushButton("Choose File")
        self.select_file_button.clicked.connect(self.open_file_dialog)
        self.select_file_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.select_file_button)
        file_group.setLayout(file_layout)
        left_panel.addWidget(file_group)

        # Analysis options group
        analysis_group = QGroupBox("Analysis Options")
        analysis_layout = QVBoxLayout()

        self.auto_fix_check = QCheckBox("Apply automatic fixes")
        self.style_check = QCheckBox("Check code style (PEP 8)")
        self.complexity_check = QCheckBox("Analyze complexity")

        analysis_layout.addWidget(self.auto_fix_check)
        analysis_layout.addWidget(self.style_check)
        analysis_layout.addWidget(self.complexity_check)

        self.analyze_button = QPushButton("Analyze Code")
        self.analyze_button.clicked.connect(self.analyze_code)
        self.analyze_button.setStyleSheet("""
            QPushButton {
                background-color: #008CBA;
                color: white;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #007399;
            }
        """)

        analysis_layout.addWidget(self.analyze_button)
        analysis_group.setLayout(analysis_layout)
        left_panel.addWidget(analysis_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        left_panel.addWidget(self.progress_bar)

        # Refactoring options
        refactor_group = QGroupBox("Refactoring Options")
        refactor_layout = QVBoxLayout()

        self.refactoring_type = QComboBox()
        self.refactoring_type.addItems([
            "Remove Unused Imports",
            "Extract Method",
            "Rename Symbol",
            "Convert to Context Manager",
            "Simplify Complex Function",
            "Format with Black",
            "Sort Imports"
        ])

        self.refactor_button = QPushButton("Apply Refactoring")
        self.refactor_button.clicked.connect(self.apply_refactoring)
        self.refactor_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)

        refactor_layout.addWidget(self.refactoring_type)
        refactor_layout.addWidget(self.refactor_button)
        refactor_group.setLayout(refactor_layout)
        left_panel.addWidget(refactor_group)

        # Add left panel to main layout
        main_layout.addLayout(left_panel, stretch=1)

        # Right panel for results
        right_panel = QVBoxLayout()

        # Results tree
        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderLabels(["Analysis Results"])
        self.results_tree.setFont(QFont("Consolas", 10))
        right_panel.addWidget(self.results_tree)

        # Code preview
        self.code_preview = QTextEdit()
        self.code_preview.setReadOnly(True)
        self.code_preview.setFont(QFont("Consolas", 10))
        self.code_preview.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 3px;
            }
        """)
        right_panel.addWidget(self.code_preview)

        # Add right panel to main layout
        main_layout.addLayout(right_panel, stretch=2)

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

    def analyze_code(self):
        if not hasattr(self, 'file_path'):
            QMessageBox.warning(self, "File Error", "Please select a Python file first.")
            return

        self.progress_bar.setValue(0)
        self.results_tree.clear()

        # Start analysis in background thread
        self.analyzer_thread = CodeAnalyzerWorker(self.file_path)
        self.analyzer_thread.progress.connect(self.update_progress)
        self.analyzer_thread.finished.connect(self.handle_analysis_results)
        self.analyzer_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def handle_analysis_results(self, results):
        self.results_tree.clear()

        if 'error' in results:
            QMessageBox.warning(self, "Analysis Error", results['error'])
            return

        # Add pylint results
        pylint_item = QTreeWidgetItem(["Pylint Analysis"])
        self.results_tree.addTopLevelItem(pylint_item)
        for line in results['pylint'].split('\n'):
            if line.strip():
                QTreeWidgetItem(pylint_item, [line.strip()])

        # Add complexity results
        complexity_item = QTreeWidgetItem(["Code Complexity"])
        self.results_tree.addTopLevelItem(complexity_item)

        for func in results['complexity']['functions']:
            func_text = f"Function {func['name']}: Complexity {func['complexity']}"
            func_item = QTreeWidgetItem(complexity_item, [func_text])
            if func['complexity'] > 10:
                func_item.setForeground(0, Qt.red)

        # Add code smells
        smells_item = QTreeWidgetItem(["Code Smells"])
        self.results_tree.addTopLevelItem(smells_item)

        for smell in results['code_smells']:
            smell_text = f"{smell['type']} in {smell['name']} at line {smell['line']}"
            QTreeWidgetItem(smells_item, [smell_text])

        self.results_tree.expandAll()

    def apply_refactoring(self):
        if not hasattr(self, 'file_path'):
            QMessageBox.warning(self, "File Error", "Please select a Python file first.")
            return

        refactoring_type = self.refactoring_type.currentText()

        try:
            with open(self.file_path, 'r') as file:
                source_code = file.read()

            if refactoring_type == "Remove Unused Imports":
                refactored_code = self.remove_unused_imports(source_code)
            elif refactoring_type == "Format with Black":
                refactored_code = black.format_str(source_code, mode=black.FileMode())
            elif refactoring_type == "Sort Imports":
                refactored_code = isort.code(source_code)
            else:
                QMessageBox.warning(self, "Not Implemented",
                                    f"Refactoring type '{refactoring_type}' is not yet implemented.")
                return

            # Create backup
            backup_path = f"{self.file_path}.bak"
            with open(backup_path, 'w') as file:
                file.write(source_code)

            # Save refactored code
            with open(self.file_path, 'w') as file:
                file.write(refactored_code)

            # Update preview
            self.code_preview.setText(refactored_code)

            # Add to history
            self.refactoring_history.append({
                'type': refactoring_type,
                'backup': backup_path
            })

            QMessageBox.information(self, "Success",
                                    f"Applied {refactoring_type} successfully.\nBackup saved as {backup_path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply refactoring: {str(e)}")

    def remove_unused_imports(self, source_code):
        tree = ast.parse(source_code)
        transformer = UnusedImportTransformer()
        transformed = transformer.visit(tree)
        return astunparse.unparse(transformed)


class UnusedImportTransformer(ast.NodeTransformer):
    def visit_Module(self, node):
        # First pass: collect all used names
        used_names = set()
        for n in ast.walk(node):
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
                used_names.add(n.id)

        # Second pass: filter imports
        new_body = []
        for n in node.body:
            if isinstance(n, ast.Import):
                names = [name for name in n.names
                         if name.asname in used_names or name.name in used_names]
                if names:
                    n.names = names
                    new_body.append(n)
            elif isinstance(n, ast.ImportFrom):
                names = [name for name in n.names
                         if name.asname in used_names or name.name in used_names]
                if names:
                    n.names = names
                    new_body.append(n)
            else:
                new_body.append(n)

        node.body = new_body
        return node


def main():
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    window = ScriptRefactoringTool()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()