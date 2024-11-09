import sys
import psutil
import platform
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QStackedWidget, QLabel, QSplitter,
                             QToolButton, QTextEdit, QPushButton, QComboBox,
                             QProgressBar, QGridLayout, QFrame)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor

# Import all the tool classes
from pom_generator import POMGenerator
from api_automation_capabality import APITestGenerator
from intelligent_script_refactoring_ad import ScriptRefactoringTool
from code_review_ad import CodeReviewTool
from chatbot import ChatbotUI
from environment_health_check_ad import HealthCheckApp
from code_generator import TestScriptGenerator


class CodeGenerator(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Template selection
        template_layout = QHBoxLayout()
        template_label = QLabel("Select Template:")
        self.template_combo = QComboBox()
        self.template_combo.addItems([
            "REST API Service",
            "Microservice Template",
            "Database CRUD Operations",
            "Authentication Service",
            "WebSocket Server",
            "GraphQL API",
            "Unit Test Template",
            "Docker Configuration",
            "CI/CD Pipeline"
        ])
        template_layout.addWidget(template_label)
        template_layout.addWidget(self.template_combo)
        layout.addLayout(template_layout)

        # Configuration editor
        config_label = QLabel("Configuration:")
        self.config_editor = QTextEdit()
        self.config_editor.setPlaceholderText("Enter configuration parameters in JSON format...")
        layout.addWidget(config_label)
        layout.addWidget(self.config_editor)

        # Generated code preview
        preview_label = QLabel("Generated Code:")
        self.code_preview = QTextEdit()
        self.code_preview.setReadOnly(True)
        self.code_preview.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Courier New', monospace;
                background-color: #2b2b2b;
                color: #a9b7c6;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        layout.addWidget(preview_label)
        layout.addWidget(self.code_preview)

        # Buttons
        button_layout = QHBoxLayout()
        generate_button = QPushButton("Generate Code")
        generate_button.setStyleSheet("""
            QPushButton {
                background-color: #6B4BCC;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a3fb8;
            }
        """)
        save_button = QPushButton("Save Code")
        button_layout.addWidget(generate_button)
        button_layout.addWidget(save_button)
        layout.addLayout(button_layout)


class EnvironmentHealthCheck(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.start_monitoring()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # System Information
        sys_info_group = QFrame()
        sys_info_group.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #fff;
                margin: 5px;
            }
        """)
        sys_info_layout = QGridLayout(sys_info_group)

        # System details
        self.sys_info_labels = {}
        info_items = [
            "OS", "Python Version", "CPU Cores", "Total Memory",
            "Disk Space", "Network Status"
        ]

        for i, item in enumerate(info_items):
            label = QLabel(f"{item}:")
            value = QLabel("Loading...")
            value.setStyleSheet("font-weight: bold;")
            sys_info_layout.addWidget(label, i, 0)
            sys_info_layout.addWidget(value, i, 1)
            self.sys_info_labels[item] = value

        layout.addWidget(sys_info_group)

        # Resource Monitors
        monitor_group = QFrame()
        monitor_group.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #fff;
                margin: 5px;
            }
        """)
        monitor_layout = QGridLayout(monitor_group)

        # CPU Usage
        monitor_layout.addWidget(QLabel("CPU Usage:"), 0, 0)
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #6B4BCC;
            }
        """)
        monitor_layout.addWidget(self.cpu_progress, 0, 1)

        # Memory Usage
        monitor_layout.addWidget(QLabel("Memory Usage:"), 1, 0)
        self.memory_progress = QProgressBar()
        self.memory_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #6B4BCC;
            }
        """)
        monitor_layout.addWidget(self.memory_progress, 1, 1)

        layout.addWidget(monitor_group)

        # Add status log
        self.status_log = QTextEdit()
        self.status_log.setReadOnly(True)
        self.status_log.setMaximumHeight(150)
        self.status_log.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #f8f9fa;
                margin: 5px;
            }
        """)
        layout.addWidget(self.status_log)

    def start_monitoring(self):
        self.update_system_info()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_metrics)
        self.timer.start(2000)  # Update every 2 seconds

    def update_system_info(self):
        # Update system information
        self.sys_info_labels["OS"].setText(platform.platform())
        self.sys_info_labels["Python Version"].setText(platform.python_version())
        self.sys_info_labels["CPU Cores"].setText(str(psutil.cpu_count()))
        self.sys_info_labels["Total Memory"].setText(
            f"{psutil.virtual_memory().total / (1024 ** 3):.2f} GB"
        )
        self.sys_info_labels["Disk Space"].setText(
            f"{psutil.disk_usage('/').free / (1024 ** 3):.2f} GB free"
        )
        self.sys_info_labels["Network Status"].setText("Connected")

    def update_metrics(self):
        # Update CPU and memory usage
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent

        self.cpu_progress.setValue(int(cpu_percent))
        self.memory_progress.setValue(int(memory_percent))

        # Add log entry if there's high usage
        if cpu_percent > 80 or memory_percent > 80:
            self.status_log.append(
                f"Warning: High resource usage detected - CPU: {cpu_percent}%, Memory: {memory_percent}%"
            )


class VerticalTabBar(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.current_index = 0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 10, 0, 10)

        # Updated tabs list with new items
        self.tabs = [
            ("POM Generator", "🔧"),
            ("API Code Builder", "🔌"),
            ("Code Generator", "💻"),
            ("Intelligent Refactoring", "🔄"),
            ("Code Review", "📝"),
            ("Chat Bot", "💬"),
            ("Environment Health", "🏥")
        ]

        self.buttons = []
        for i, (text, icon) in enumerate(self.tabs):
            button = QToolButton()
            button.setText(f" {icon} {text}")
            button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            button.setCheckable(True)
            button.setFixedHeight(50)
            button.setMinimumWidth(250)
            button.clicked.connect(lambda checked, index=i: self.handle_tab_click(index))

            button.setStyleSheet("""
                QToolButton {
                    border: none;
                    border-radius: 5px;
                    padding: 10px;
                    text-align: left;
                    margin: 2px 10px;
                    font-size: 14px;
                    color: #333333;
                    background-color: transparent;
                }
                QToolButton:hover {
                    background-color: #e0e0e0;
                }
                QToolButton:checked {
                    background-color: #6B4BCC;
                    color: white;
                    font-weight: bold;
                }
            """)

            self.buttons.append(button)
            layout.addWidget(button)

        layout.addStretch()
        self.buttons[0].setChecked(True)

    def handle_tab_click(self, index):
        for i, button in enumerate(self.buttons):
            if i != index:
                button.setChecked(False)
        self.current_index = index
        self.stacked_widget.setCurrentIndex(index)


class GenAIDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NessQ Gen AI Dashboard")
        self.setMinimumSize(1400, 800)
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background: #e0e0e0;
                width: 2px;
            }
        """)

        left_panel = QWidget()
        left_panel.setMaximumWidth(300)
        left_panel.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-right: 1px solid #e0e0e0;
            }
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        title_label = QLabel("Gen AI Dashboard")
        title_label.setStyleSheet("""
            QLabel {
                background-color: #6B4BCC;
                color: white;
                padding: 20px;
                font-size: 18px;
                font-weight: bold;
                border-bottom: 1px solid #5a3fb8;
            }
        """)
        left_layout.addWidget(title_label)

        self.stacked_widget = QStackedWidget()
        self.tab_bar = VerticalTabBar(self.stacked_widget)
        left_layout.addWidget(self.tab_bar)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Initialize all tools including new ones
        self.pom_generator = POMGenerator()
        self.api_generator = APITestGenerator()
        self.code_generator = TestScriptGenerator()
        self.refactoring_tool = ScriptRefactoringTool()
        self.code_review = CodeReviewTool()
        self.chatbot = ChatbotUI()
        self.env_health = EnvironmentHealthCheck()

        # Add all tools to stacked widget
        self.stacked_widget.addWidget(self.pom_generator)
        self.stacked_widget.addWidget(self.api_generator)
        self.stacked_widget.addWidget(self.code_generator)
        self.stacked_widget.addWidget(self.refactoring_tool)
        self.stacked_widget.addWidget(self.code_review)
        self.stacked_widget.addWidget(self.chatbot)
        self.stacked_widget.addWidget(self.env_health)

        right_layout.addWidget(self.stacked_widget)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([280, 1120])
        main_layout.addWidget(splitter)

        self.set_application_style()

    def set_application_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QStackedWidget {
                background-color: white;
            }
            QScrollBar:vertical {
                width: 12px;
                background: #f1f1f1;
            }
            QScrollBar::handle:vertical {
                background: #888;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    font = QFont('Segoe UI', 10)
    app.setFont(font)
    dashboard = GenAIDashboard()
    dashboard.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()