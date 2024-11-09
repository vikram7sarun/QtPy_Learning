import ast
import datetime
import sys
import subprocess
import tempfile
import os
from typing import List, Dict, Optional, Tuple
import astunparse
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QFileDialog, QListWidget, QMessageBox,
    QProgressBar, QSpinBox, QComboBox, QGroupBox, QGridLayout,
    QSplitter, QTreeWidget, QTreeWidgetItem, QCheckBox, QInputDialog,
    QDialog, QLineEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
import autopep8
import black
import isort
import rope.base.project
import rope.refactor.extract
import rope.refactor.rename
import rope.refactor.usefunction
from rope.base.project import Project
from rope.refactor.rename import Rename
from rope.refactor.extract import ExtractMethod
from rope.base import worder


class CodeRefactorer:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.project = Project('.')
        self.resource = self.project.get_resource(file_path)

    def extract_method(self, start_offset: int, end_offset: int, new_name: str) -> str:
        try:
            extractor = ExtractMethod(self.project, self.resource, start_offset, end_offset)
            changes = extractor.get_changes(new_name)
            changes.do()
            return self.get_file_content()
        finally:
            self.project.close()

    def rename_symbol(self, offset: int, new_name: str) -> str:
        try:
            renamer = Rename(self.project, self.resource, offset)
            changes = renamer.get_changes(new_name)
            changes.do()
            return self.get_file_content()
        finally:
            self.project.close()

    def convert_to_context_manager(self, class_name: str) -> str:
        with open(self.file_path, 'r') as file:
            tree = ast.parse(file.read())

        transformer = ContextManagerTransformer(class_name)
        new_tree = transformer.visit(tree)
        return astunparse.unparse(new_tree)

    def simplify_complex_function(self, function_name: str) -> str:
        with open(self.file_path, 'r') as file:
            tree = ast.parse(file.read())

        transformer = ComplexFunctionSimplifier(function_name)
        new_tree = transformer.visit(tree)
        return astunparse.unparse(new_tree)

    def get_file_content(self) -> str:
        with open(self.file_path, 'r') as file:
            return file.read()


class ContextManagerTransformer(ast.NodeTransformer):
    def __init__(self, class_name: str):
        self.class_name = class_name

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        if node.name == self.class_name:
            # Add __enter__ and __exit__ methods if they don't exist
            has_enter = any(m.name == '__enter__' for m in node.body if isinstance(m, ast.FunctionDef))
            has_exit = any(m.name == '__exit__' for m in node.body if isinstance(m, ast.FunctionDef))

            if not has_enter:
                enter_method = ast.FunctionDef(
                    name='__enter__',
                    args=ast.arguments(
                        posonlyargs=[],
                        args=[ast.arg(arg='self', annotation=None)],
                        kwonlyargs=[],
                        kw_defaults=[],
                        defaults=[],
                        vararg=None,
                        kwarg=None
                    ),
                    body=[ast.Return(value=ast.Name(id='self', ctx=ast.Load()))],
                    decorator_list=[],
                    returns=None
                )
                node.body.append(enter_method)

            if not has_exit:
                exit_method = ast.FunctionDef(
                    name='__exit__',
                    args=ast.arguments(
                        posonlyargs=[],
                        args=[
                            ast.arg(arg='self', annotation=None),
                            ast.arg(arg='exc_type', annotation=None),
                            ast.arg(arg='exc_val', annotation=None),
                            ast.arg(arg='exc_tb', annotation=None)
                        ],
                        kwonlyargs=[],
                        kw_defaults=[],
                        defaults=[],
                        vararg=None,
                        kwarg=None
                    ),
                    body=[ast.Return(value=ast.Constant(value=None))],
                    decorator_list=[],
                    returns=None
                )
                node.body.append(exit_method)

        return node


class ComplexFunctionSimplifier(ast.NodeTransformer):
    def __init__(self, function_name: str):
        self.function_name = function_name
        self.extracted_functions = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        if node.name == self.function_name:
            # Simplify complex if statements
            self.simplify_conditionals(node)

            # Extract complex loops into separate functions
            self.extract_complex_loops(node)

            # Break down long function into smaller ones
            if len(node.body) > 15:
                return self.break_down_function(node)

        return node

    def simplify_conditionals(self, node: ast.FunctionDef) -> None:
        for i, stmt in enumerate(node.body):
            if isinstance(stmt, ast.If) and len(stmt.body) + len(stmt.orelse) > 10:
                # Create a new function for complex conditional logic
                new_func_name = f"{node.name}_condition_{i}"
                new_func = ast.FunctionDef(
                    name=new_func_name,
                    args=ast.arguments(
                        posonlyargs=[],
                        args=[],
                        kwonlyargs=[],
                        kw_defaults=[],
                        defaults=[],
                        vararg=None,
                        kwarg=None
                    ),
                    body=stmt.body,
                    decorator_list=[]
                )
                self.extracted_functions.append(new_func)

                # Replace complex conditional with function call
                node.body[i] = ast.If(
                    test=stmt.test,
                    body=[ast.Expr(value=ast.Call(
                        func=ast.Name(id=new_func_name, ctx=ast.Load()),
                        args=[],
                        keywords=[]
                    ))],
                    orelse=stmt.orelse
                )

    def extract_complex_loops(self, node: ast.FunctionDef) -> None:
        for i, stmt in enumerate(node.body):
            if isinstance(stmt, (ast.For, ast.While)) and len(stmt.body) > 10:
                # Create a new function for complex loop logic
                new_func_name = f"{node.name}_loop_{i}"
                new_func = ast.FunctionDef(
                    name=new_func_name,
                    args=ast.arguments(
                        posonlyargs=[],
                        args=[],
                        kwonlyargs=[],
                        kw_defaults=[],
                        defaults=[],
                        vararg=None,
                        kwarg=None
                    ),
                    body=stmt.body,
                    decorator_list=[]
                )
                self.extracted_functions.append(new_func)

                # Replace complex loop with function call inside the loop
                if isinstance(stmt, ast.For):
                    node.body[i] = ast.For(
                        target=stmt.target,
                        iter=stmt.iter,
                        body=[ast.Expr(value=ast.Call(
                            func=ast.Name(id=new_func_name, ctx=ast.Load()),
                            args=[],
                            keywords=[]
                        ))],
                        orelse=[]
                    )
                else:  # While loop
                    node.body[i] = ast.While(
                        test=stmt.test,
                        body=[ast.Expr(value=ast.Call(
                            func=ast.Name(id=new_func_name, ctx=ast.Load()),
                            args=[],
                            keywords=[]
                        ))],
                        orelse=[]
                    )

    def break_down_function(self, node: ast.FunctionDef) -> ast.FunctionDef:
        # Split function body into chunks
        chunk_size = 10
        chunks = [node.body[i:i + chunk_size] for i in range(0, len(node.body), chunk_size)]

        # Create helper functions for each chunk
        for i, chunk in enumerate(chunks[:-1]):
            helper_name = f"{node.name}_part_{i}"
            helper_func = ast.FunctionDef(
                name=helper_name,
                args=ast.arguments(
                    posonlyargs=[],
                    args=[],
                    kwonlyargs=[],
                    kw_defaults=[],
                    defaults=[],
                    vararg=None,
                    kwarg=None
                ),
                body=chunk,
                decorator_list=[]
            )
            self.extracted_functions.append(helper_func)

        # Update the original function to call the helpers
        new_body = []
        for i in range(len(chunks) - 1):
            new_body.append(
                ast.Expr(value=ast.Call(
                    func=ast.Name(id=f"{node.name}_part_{i}", ctx=ast.Load()),
                    args=[],
                    keywords=[]
                ))
            )
        new_body.extend(chunks[-1])  # Add the last chunk directly

        node.body = new_body
        return node


class RefactoringDialog(QDialog):
    def __init__(self, refactoring_type: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Configure {refactoring_type}")
        self.setModal(True)
        self.layout = QVBoxLayout()
        self.refactoring_type = refactoring_type
        self.setup_ui()
        self.setLayout(self.layout)

    def setup_ui(self):
        if self.refactoring_type == "Extract Method":
            self.setup_extract_method_ui()
        elif self.refactoring_type == "Rename Symbol":
            self.setup_rename_symbol_ui()
        elif self.refactoring_type == "Convert to Context Manager":
            self.setup_context_manager_ui()
        elif self.refactoring_type == "Simplify Complex Function":
            self.setup_simplify_function_ui()

    def setup_extract_method_ui(self):
        self.method_name = QLineEdit()
        self.layout.addWidget(QLabel("New Method Name:"))
        self.layout.addWidget(self.method_name)

        self.start_line = QSpinBox()
        self.layout.addWidget(QLabel("Start Line:"))
        self.layout.addWidget(self.start_line)

        self.end_line = QSpinBox()
        self.layout.addWidget(QLabel("End Line:"))
        self.layout.addWidget(self.end_line)

        button = QPushButton("Extract")
        button.clicked.connect(self.accept)
        self.layout.addWidget(button)

    def setup_rename_symbol_ui(self):
        self.old_name = QLineEdit()
        self.layout.addWidget(QLabel("Symbol to Rename:"))
        self.layout.addWidget(self.old_name)

        self.new_name = QLineEdit()
        self.layout.addWidget(QLabel("New Name:"))
        self.layout.addWidget(self.new_name)

        button = QPushButton("Rename")
        button.clicked.connect(self.accept)
        self.layout.addWidget(button)

    def setup_context_manager_ui(self):
        self.class_name = QLineEdit()
        self.layout.addWidget(QLabel("Class Name:"))
        self.layout.addWidget(self.class_name)

        button = QPushButton("Convert")
        button.clicked.connect(self.accept)
        self.layout.addWidget(button)

    def setup_simplify_function_ui(self):
        self.function_name = QLineEdit()
        self.layout.addWidget(QLabel("Function Name:"))
        self.layout.addWidget(self.function_name)

        button = QPushButton("Simplify")
        button.clicked.connect(self.accept)
        self.layout.addWidget(button)


class ScriptRefactoringTool(QWidget):
    def __init__(self):
        super().__init__()
        self.analyzer_thread = None
        self.refactoring_history = []
        self.refactorer = None
        self.initUI()

    # [Previous UI initialization code remains the same]

    def apply_refactoring(self):
        if not hasattr(self, 'file_path'):
            QMessageBox.warning(self, "File Error", "Please select a Python file first.")
            return

        refactoring_type = self.refactoring_type.currentText()

        try:
            # Initialize refactorer if needed
            if not self.refactorer:
                self.refactorer = CodeRefactorer(self.file_path)

            # Create backup before refactoring
            backup_path = f"{self.file_path}.bak"
            with open(self.file_path, 'r') as file:
                original_code = file.read()
            with open(backup_path, 'w') as file:
                file.write(original_code)

            # Get refactoring parameters through dialog
            dialog = RefactoringDialog(refactoring_type, self)
            if dialog.exec_() != QDialog.Accepted:
                return

            # Apply the selected refactoring
            if refactoring_type == "Remove Unused Imports":
                refactored_code = self.remove_unused_imports(original_code)

            elif refactoring_type == "Extract Method":
                start_offset = self.get_offset_for_line(original_code, dialog.start_line.value())
                end_offset = self.get_offset_for_line(original_code, dialog.end_line.value())
                refactored_code = self.refactorer.extract_method(
                    start_offset, end_offset, dialog.method_name.text())

            elif refactoring_type == "Rename Symbol":
                offset = self.find_symbol_offset(original_code, dialog.old_name.text())
                refactored_code = self.refactorer.rename_symbol(
                    offset, dialog.new_name.text())

            elif refactoring_type == "Convert to Context Manager":
                refactored_code = self.refactorer.convert_to_context_manager(
                    dialog.class_name.text())

            elif refactoring_type == "Simplify Complex Function":
                refactored_code = self.refactorer.simplify_complex_function(
                    dialog.function_name.text())

            elif refactoring_type == "Format with Black":
                refactored_code = black.format_str(original_code, mode=black.FileMode())


            elif refactoring_type == "Format with Black":

                refactored_code = black.format_str(original_code, mode=black.FileMode())


            elif refactoring_type == "Sort Imports":

                refactored_code = isort.code(original_code)

                # Save refactored code

            with open(self.file_path, 'w') as file:

                file.write(refactored_code)

                # Update preview

            self.code_preview.setText(refactored_code)

            # Add to history

            self.refactoring_history.append({

                'type': refactoring_type,

                'backup': backup_path,

                'timestamp': datetime.now().isoformat()

            })

            # Update results tree

            self.add_refactoring_result(refactoring_type)

            QMessageBox.information(

                self,

                "Success",

                f"Applied {refactoring_type} successfully.\nBackup saved as {backup_path}"

            )


        except Exception as e:

            # Restore from backup if something went wrong

            if 'backup_path' in locals():
                with open(backup_path, 'r') as file:
                    original_code = file.read()

                with open(self.file_path, 'w') as file:
                    file.write(original_code)

            QMessageBox.critical(self, "Error", f"Failed to apply refactoring: {str(e)}")

    def get_offset_for_line(self, code: str, line_number: int) -> int:
        """Convert line number to character offset."""
        lines = code.split('\n')
        offset = 0
        for i in range(line_number - 1):
            offset += len(lines[i]) + 1  # +1 for newline character
        return offset

    def find_symbol_offset(self, code: str, symbol_name: str) -> int:
        """Find the first occurrence of a symbol in the code."""
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == symbol_name:
                return self.get_offset_for_line(code, node.lineno)
        raise ValueError(f"Symbol {symbol_name} not found in code")

    def add_refactoring_result(self, refactoring_type: str):
        """Add refactoring result to the results tree."""
        result_item = QTreeWidgetItem(["Recent Refactoring"])
        result_item.addChild(QTreeWidgetItem([f"Type: {refactoring_type}"]))
        result_item.addChild(QTreeWidgetItem([f"Time: {datetime.now().strftime('%H:%M:%S')}"]))
        self.results_tree.insertTopLevelItem(0, result_item)
        self.results_tree.expandItem(result_item)

    def remove_unused_imports(self, source_code: str) -> str:
        """Remove unused imports from the code."""
        tree = ast.parse(source_code)

        # First pass: collect all used names
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Load):
                    used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                # Handle attribute access (e.g., module.function)
                names = []
                current = node
                while isinstance(current, ast.Attribute):
                    names.append(current.attr)
                    current = current.value
                if isinstance(current, ast.Name):
                    names.append(current.id)
                    used_names.add(names[-1])  # Add the root name

        # Second pass: remove unused imports
        new_body = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                new_names = []
                for alias in node.names:
                    if alias.asname:
                        if alias.asname in used_names:
                            new_names.append(alias)
                    elif alias.name in used_names:
                        new_names.append(alias)
                if new_names:
                    node.names = new_names
                    new_body.append(node)
            elif isinstance(node, ast.ImportFrom):
                new_names = []
                for alias in node.names:
                    if alias.asname:
                        if alias.asname in used_names:
                            new_names.append(alias)
                    elif alias.name in used_names or alias.name == '*':
                        new_names.append(alias)
                if new_names:
                    node.names = new_names
                    new_body.append(node)
            else:
                new_body.append(node)

        tree.body = new_body
        return astunparse.unparse(tree)

    def create_context_manager_template(self) -> str:
        """Create a template for context manager implementation."""
        return '''
    def __enter__(self):
        """Set up the context manager."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Clean up the context manager."""
        if exc_type is not None:
            # Handle any cleanup needed if an exception occurred
            pass
        # Perform cleanup operations
        return False  # Re-raise any exceptions
        '''

    def show_refactoring_preview(self, original_code: str, refactored_code: str):
        """Show a preview of the refactoring changes."""
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle("Refactoring Preview")
        preview_dialog.setModal(True)
        preview_dialog.resize(800, 600)

        layout = QVBoxLayout()

        # Create a splitter for side-by-side comparison
        splitter = QSplitter(Qt.Horizontal)

        # Original code panel
        original_panel = QTextEdit()
        original_panel.setReadOnly(True)
        original_panel.setText(original_code)
        original_panel.setFont(QFont("Consolas", 10))
        splitter.addWidget(original_panel)

        # Refactored code panel
        refactored_panel = QTextEdit()
        refactored_panel.setReadOnly(True)
        refactored_panel.setText(refactored_code)
        refactored_panel.setFont(QFont("Consolas", 10))
        splitter.addWidget(refactored_panel)

        layout.addWidget(splitter)

        # Buttons
        button_layout = QHBoxLayout()
        apply_button = QPushButton("Apply Changes")
        apply_button.clicked.connect(preview_dialog.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(preview_dialog.reject)

        button_layout.addWidget(apply_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        preview_dialog.setLayout(layout)
        return preview_dialog.exec_() == QDialog.Accepted

    def undo_last_refactoring(self):
        """Undo the last refactoring operation."""
        if not self.refactoring_history:
            QMessageBox.warning(self, "Warning", "No refactoring to undo.")
            return

        last_refactoring = self.refactoring_history.pop()
        try:
            # Restore from backup
            with open(last_refactoring['backup'], 'r') as backup_file:
                backup_code = backup_file.read()

            with open(self.file_path, 'w') as current_file:
                current_file.write(backup_code)

            # Update preview
            self.code_preview.setText(backup_code)

            # Update results tree
            undo_item = QTreeWidgetItem(["Undo Operation"])
            undo_item.addChild(QTreeWidgetItem([f"Reverted: {last_refactoring['type']}"]))
            self.results_tree.insertTopLevelItem(0, undo_item)

            QMessageBox.information(self, "Success", "Successfully undid last refactoring.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to undo refactoring: {str(e)}")

    def save_refactoring_history(self):
        """Save the refactoring history to a file."""
        if not self.refactoring_history:
            QMessageBox.warning(self, "Warning", "No refactoring history to save.")
            return

        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Refactoring History",
                "",
                "JSON Files (*.json)"
            )

            if file_path:
                with open(file_path, 'w') as f:
                    json.dump(self.refactoring_history, f, indent=2)
                QMessageBox.information(self, "Success", "Refactoring history saved successfully.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save history: {str(e)}")
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
    app.setStyle('Fusion')

    # Set up stylesheets for a modern look
    app.setStyleSheet("""
        QWidget {
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        QGroupBox {
            border: 1px solid #cccccc;
            border-radius: 4px;
            margin-top: 0.5em;
            padding-top: 0.5em;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px 0 3px;
        }
        QPushButton {
            padding: 5px 15px;
            border-radius: 4px;
        }
        QTextEdit {
            border: 1px solid #cccccc;
            border-radius: 4px;
        }
    """)

    window = ScriptRefactoringTool()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()