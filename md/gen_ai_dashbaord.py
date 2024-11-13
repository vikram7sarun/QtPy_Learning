import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QStackedWidget, QLabel, QSplitter,
                             QToolButton, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# Import the tools from provided files
from pom_generator_final import EnhancedPOMGenerator
from intelligent_script_refactoring_ad import ScriptRefactoringTool
from code_review_ad import CodeReviewTool


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

        # Only include the three tools
        self.tabs = [
            ("POM Generator", "🔧"),
            ("Script Refactoring", "🔄"),
            ("Code Review", "📝")
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
        self.setWindowTitle("Gen AI Dashboard")
        self.setMinimumSize(1400, 800)
        self.init_ui()
        self.tools = []  # Keep track of tool instances

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background: #e0e0e0;
                width: 2px;
            }
        """)

        # Left panel setup
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

        # Dashboard title
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

        # Initialize stacked widget and tab bar
        self.stacked_widget = QStackedWidget()
        self.tab_bar = VerticalTabBar(self.stacked_widget)
        left_layout.addWidget(self.tab_bar)

        # Right panel setup
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        try:
            # Initialize and add tools
            self.pom_generator = EnhancedPOMGenerator()
            self.refactoring_tool = ScriptRefactoringTool()
            self.code_review = CodeReviewTool()

            # Keep track of tools for cleanup
            self.tools.extend([
                self.pom_generator,
                self.refactoring_tool,
                self.code_review
            ])

            self.stacked_widget.addWidget(self.pom_generator)
            self.stacked_widget.addWidget(self.refactoring_tool)
            self.stacked_widget.addWidget(self.code_review)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to initialize tools: {str(e)}")

        right_layout.addWidget(self.stacked_widget)

        # Add panels to splitter
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

    def closeEvent(self, event):
        """Handle application close event"""
        try:
            # Clean up POM Generator's Chrome driver
            if hasattr(self.pom_generator, 'driver'):
                self.pom_generator.driver.quit()

            # Clean up any other resources
            for tool in self.tools:
                if hasattr(tool, 'cleanup'):
                    tool.cleanup()

            event.accept()
        except Exception as e:
            print(f"Error during cleanup: {e}")
            event.accept()


def main():
    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        font = QFont('Segoe UI', 10)
        app.setFont(font)

        # Create and show the dashboard
        dashboard = GenAIDashboard()
        dashboard.show()

        # Start the event loop
        return_code = app.exec_()

        # Cleanup and exit
        sys.exit(return_code)

    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()