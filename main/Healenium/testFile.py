from PyQt5 import QtWidgets
import sys

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Accordion-Style Vertical Tabs")

        # Create QToolBox for accordion-style tabs
        self.toolbox = QtWidgets.QToolBox()
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.toolbox)

        # Add sections to the toolbox
        self.add_toolbox_section("Overview", "This is the overview content.")
        self.add_toolbox_section("Details", "Details of the item are here.")
        self.add_toolbox_section("Additional Info", "Additional information goes here.")

    def add_toolbox_section(self, title, content_text):
        # Add a section with given title and content
        content = QtWidgets.QLabel(content_text)
        content.setWordWrap(True)
        self.toolbox.addItem(content, title)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.resize(400, 300)
    window.show()
    sys.exit(app.exec_())
