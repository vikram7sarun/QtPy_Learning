from PyQt5.QtWidgets import QWidget
from utils.logger import Logger

class BaseTool(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = Logger().get_logger()
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        raise NotImplementedError("Subclasses must implement setup_ui")

    def connect_signals(self):
        raise NotImplementedError("Subclasses must implement connect_signals")

    def cleanup(self):
        """Cleanup resources before closing"""
        pass