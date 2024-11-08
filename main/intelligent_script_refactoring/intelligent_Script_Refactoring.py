
import ast
import sys
import subprocess
import astunparse
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QFileDialog, QListWidget, QMessageBox

class ScriptRefactoringTool(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Intelligent Script Refactoring Tool')
        self.setGeometry(200, 200, 800, 600)
        layout = QVBoxLayout()
        file_layout = QHBoxLayout()
        self.file_label = QLabel('Select Python file for refactoring:')
        file_layout.addWidget(self.file_label)
        self.select_file_button = QPushButton('Choose File')
        self.select_file_button.clicked.connect(self.open_file_dialog)
        file_layout.addWidget(self.select_file_button)
        layout.addLayout(file_layout)
        self.analyze_button = QPushButton('Analyze Code')
        self.analyze_button.clicked.connect(self.analyze_code)
        layout.addWidget(self.analyze_button)
        self.suggestions_list = QListWidget()
        layout.addWidget(self.suggestions_list)
        self.refactor_button = QPushButton('Apply Selected Refactoring')
        self.refactor_button.clicked.connect(self.apply_refactoring)
        layout.addWidget(self.refactor_button)
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        layout.addWidget(self.result_display)
        self.setLayout(layout)

    def open_file_dialog(self):
        options = QFileDialog.Options()
        (file, _) = QFileDialog.getOpenFileName(self, 'Select Python file', '', 'Python Files (*.py);;All Files (*)', options=options)
        if file:
            self.file_path = file
            self.file_label.setText(f'File Selected: {file}')
            self.result_display.setText(f'File selected: {file}')
            self.suggestions_list.clear()
            print(f'File selected: {self.file_path}')

    def analyze_code(self):
        if (not hasattr(self, 'file_path')):
            QMessageBox.warning(self, 'File Error', 'Please select a Python file first.')
            return
        result = subprocess.run(['pylint', self.file_path], capture_output=True, text=True)
        print('Pylint output:', result.stdout)
        pylint_output = result.stdout
        self.result_display.setText(pylint_output)
        if ('unused-import' in pylint_output):
            self.suggestions_list.addItem('Remove unused imports.')
        if ('too-many-locals' in pylint_output):
            self.suggestions_list.addItem('Refactor function with too many local variables.')
        if ('too-many-branches' in pylint_output):
            self.suggestions_list.addItem('Simplify function with too many branches.')

    def apply_refactoring(self):
        selected_suggestion = self.suggestions_list.currentItem()
        if (not selected_suggestion):
            QMessageBox.warning(self, 'Selection Error', 'Please select a refactoring suggestion to apply.')
            return
        suggestion = selected_suggestion.text()
        print(f'Applying refactoring suggestion: {suggestion}')
        with open(self.file_path, 'r') as f:
            source_code = f.read()
        if (suggestion == 'Remove unused imports.'):
            refactored_code = self.remove_unused_imports(source_code)
            self.result_display.setText(('Applied refactoring: Remove unused imports.\n' + refactored_code))
        elif (suggestion == 'Refactor function with too many local variables.'):
            refactored_code = self.simplify_function(source_code)
            self.result_display.setText(('Applied refactoring: Simplify function.\n' + refactored_code))
        with open(self.file_path, 'w') as f:
            f.write(refactored_code)
        QMessageBox.information(self, 'Refactoring Applied', f'{suggestion} applied successfully.')

    def remove_unused_imports(self, source_code):
        '\n        Remove unused imports from the Python code.\n        '
        tree = ast.parse(source_code)
        used_names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        new_body = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                if (not any(((alias.name in used_names) for alias in node.names))):
                    continue
            elif isinstance(node, ast.ImportFrom):
                if (not any(((alias.name in used_names) for alias in node.names))):
                    continue
            new_body.append(node)
        tree.body = new_body
        return astunparse.unparse(tree)

    def simplify_function(self, source_code):
        '\n        Simplify functions by limiting the number of local variables.\n        '

        class FunctionRefactorer(ast.NodeTransformer):

            def visit_FunctionDef(self, node):
                local_vars = {n.id for n in node.body if isinstance(n, ast.Assign)}
                if (len(local_vars) > 5):
                    node.body = [n for n in node.body if (not isinstance(n, ast.Assign))]
                return node
        tree = ast.parse(source_code)
        refactored_tree = FunctionRefactorer().visit(tree)
        return astunparse.unparse(refactored_tree)
if (__name__ == '__main__'):
    app = QApplication(sys.argv)
    window = ScriptRefactoringTool()
    window.show()
    sys.exit(app.exec_())
