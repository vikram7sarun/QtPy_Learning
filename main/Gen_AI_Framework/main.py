import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt

from main.Gen_AI_Framework.tools.code_review_ad import CodeReviewTool
from main.Gen_AI_Framework.tools.intelligent_script_refactoring_ad import ScriptRefactoringTool
# from tools.code_review.code_review_tool import CodeReviewTool
# from tools.pom_generator.pom_generator_tool import POMGeneratorTool
# from tools.script_refactoring.refactoring_tool import ScriptRefactoringTool

from main.Gen_AI_Framework.utils.decorators import error_handler
from ui.styles import Styles
from utils.logger import Logger
from utils.config import Config


class GenAIDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.logger = Logger().get_logger()
        self.config = Config()
        self.tools = {}
        self.init_ui()
        self.setup_tools()
        self.load_default_tool()

    def init_ui(self):
        self.setWindowTitle("Gen AI Dashboard")
        self.setMinimumSize(1400, 800)
        self.setStyleSheet(Styles.MAIN_STYLE)
        # Rest of your UI initialization code...

    def setup_tools(self):
        """Initialize all tools"""
        self.tools = {
            'code_review': CodeReviewTool,
            # 'pom_generator': POMGeneratorTool,
            'script_refactoring': ScriptRefactoringTool
        }

    def load_default_tool(self):
        """Load the default tool based on configuration"""
        default_tool = self.config.get('default_tool', 'code_review')
        if default_tool in self.tools:
            self.switch_tool(default_tool)

    @error_handler
    def switch_tool(self, tool_name):
        """Switch to the selected tool"""
        if tool_name in self.tools:
            tool_class = self.tools[tool_name]
            tool_instance = tool_class()
            self.stacked_widget.addWidget(tool_instance)
            self.stacked_widget.setCurrentWidget(tool_instance)
            self.logger.info(f"Switched to {tool_name} tool")


def main():
    try:
        app = QApplication(sys.argv)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps)
        app.setAttribute(Qt.AA_EnableHighDpiScaling)

        logger = Logger().get_logger()
        logger.info("Starting Gen AI Dashboard")

        dashboard = GenAIDashboard()
        dashboard.show()

        return_code = app.exec_()
        logger.info("Shutting down Gen AI Dashboard")
        sys.exit(return_code)

    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()