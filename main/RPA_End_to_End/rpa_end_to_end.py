
import sys
import pyautogui
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QListWidget, QMessageBox, QComboBox, QTextEdit

class RPAIntegrationTool(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()
        self.tasks = []

    def initUI(self):
        self.setWindowTitle('RPA Integration for End-to-End Process Testing')
        self.setGeometry(200, 200, 600, 500)
        layout = QVBoxLayout()
        self.task_type = QComboBox()
        self.task_type.addItems(['Click', 'Type Text', 'Wait', 'Open Application'])
        layout.addWidget(QLabel('Select Task Type:'))
        layout.addWidget(self.task_type)
        self.task_param_label = QLabel("Task Parameter (e.g., 'x, y' for Click, 'text' for Type Text):")
        self.task_param_input = QLineEdit()
        layout.addWidget(self.task_param_label)
        layout.addWidget(self.task_param_input)
        self.add_task_button = QPushButton('Add Task')
        self.add_task_button.clicked.connect(self.add_task)
        layout.addWidget(self.add_task_button)
        self.task_list = QListWidget()
        layout.addWidget(QLabel('Task Sequence:'))
        layout.addWidget(self.task_list)
        self.execute_button = QPushButton('Execute Workflow')
        self.execute_button.clicked.connect(self.execute_workflow)
        layout.addWidget(self.execute_button)
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        layout.addWidget(QLabel('Execution Log:'))
        layout.addWidget(self.result_display)
        self.setLayout(layout)

    def add_task(self):
        task_type = self.task_type.currentText()
        task_param = self.task_param_input.text()
        if ((not task_param) and (task_type != 'Wait')):
            QMessageBox.warning(self, 'Input Error', 'Please provide task parameters.')
            return
        task = {'type': task_type, 'param': task_param}
        self.tasks.append(task)
        self.task_list.addItem(f'{task_type} - {task_param}')
        self.task_param_input.clear()

    def execute_workflow(self):
        if (not self.tasks):
            QMessageBox.warning(self, 'Workflow Error', 'No tasks added to execute.')
            return
        self.result_display.clear()
        for (i, task) in enumerate(self.tasks):
            task_type = task['type']
            task_param = task['param']
            try:
                if (task_type == 'Click'):
                    (x, y) = map(int, task_param.split(','))
                    pyautogui.click(x, y)
                    self.result_display.append(f'Task {(i + 1)}: Clicked at ({x}, {y})')
                elif (task_type == 'Type Text'):
                    pyautogui.write(task_param)
                    self.result_display.append(f"Task {(i + 1)}: Typed text '{task_param}'")
                elif (task_type == 'Wait'):
                    delay = int(task_param)
                    pyautogui.sleep(delay)
                    self.result_display.append(f'Task {(i + 1)}: Waited for {delay} seconds')
                elif (task_type == 'Open Application'):
                    import os
                    os.system(task_param)
                    self.result_display.append(f"Task {(i + 1)}: Opened application '{task_param}'")
            except Exception as e:
                self.result_display.append(f'Task {(i + 1)}: Failed with error - {str(e)}')
                QMessageBox.warning(self, 'Execution Error', f'Task {(i + 1)} failed: {str(e)}')
        QMessageBox.information(self, 'Workflow Completed', 'All tasks executed successfully.')
if (__name__ == '__main__'):
    app = QApplication(sys.argv)
    window = RPAIntegrationTool()
    window.show()
    sys.exit(app.exec_())
