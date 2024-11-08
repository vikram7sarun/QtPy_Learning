import sys
import os
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QTextCharFormat, QColor

# Playwright initialization
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

os.environ['PLAYWRIGHT_BROWSERS_PATH'] = os.path.join(application_path, 'playwright', 'browser')
os.environ['PLAYWRIGHT_DRIVER_PATH'] = os.path.join(application_path, 'playwright', 'driver',
                                                  'playwright.cmd' if os.name == 'nt' else 'playwright.sh')

# Rest of your imports
from playwright.sync_api import sync_playwright
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QLabel, QLineEdit, QPushButton,
                            QTextEdit, QFileDialog, QMessageBox, QStatusBar,
                            QTabWidget, QComboBox, QProgressBar, QMenu, QMenuBar,
                            QDialog, QGridLayout, QCheckBox)

#---
#---

class POMGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon('app_icon.ico'))
        self.move_count = 0
        self.previous_text = ""
        self.init_ui()
        self.set_styles()

    def init_ui(self):
        self.setWindowTitle('NessQ POM Generator')
        self.setGeometry(100, 100, 800, 600)

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Priority Section
        priority_label = QLabel(
            'Enter Selector Priorities:\nEg: ID, Name, ClassName, LinkText, PartialLinkText, TagName')
        layout.addWidget(priority_label)

        priority_layout = QHBoxLayout()
        self.priority_entry = QLineEdit()
        self.priority_entry.setText("ID, Name, ClassName, LinkText, PartialLinkText, TagName")
        self.fetch_button = QPushButton('Fetch Selectors')
        self.fetch_button.clicked.connect(self.fetch_selectors)

        priority_layout.addWidget(self.priority_entry)
        priority_layout.addWidget(self.fetch_button)
        layout.addLayout(priority_layout)

        # Output Text Area
        self.output_text = QTextEdit()
        layout.addWidget(self.output_text)

        # Middle Section
        middle_layout = QHBoxLayout()
        self.move_button = QPushButton('Move Selected Lines')
        self.move_button.clicked.connect(self.move_selected_lines)

        self.class_name_entry = QLineEdit()
        self.class_name_entry.setPlaceholderText("Enter Class Name")

        self.generate_button = QPushButton('Generate POM')
        self.generate_button.clicked.connect(self.generate_pom)

        middle_layout.addWidget(self.move_button)
        middle_layout.addWidget(self.class_name_entry)
        middle_layout.addWidget(self.generate_button)
        layout.addLayout(middle_layout)

        # Moved Text Area
        self.moved_text = QTextEdit()
        self.moved_text.textChanged.connect(self.on_text_area_modified)
        layout.addWidget(self.moved_text)

        # Bottom Section
        bottom_layout = QHBoxLayout()
        self.save_button = QPushButton('Save to File')
        self.save_button.clicked.connect(self.save_to_file)

        self.clear_button = QPushButton('Clear POM')
        self.clear_button.clicked.connect(self.clear_generated_pom)

        bottom_layout.addWidget(self.save_button)
        bottom_layout.addWidget(self.clear_button)
        layout.addLayout(bottom_layout)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('Ready')

    def set_styles(self):
        # Set color scheme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QPushButton {
                background-color: #dbe9f4;
                border: 1px solid #999;
                padding: 5px;
                min-width: 80px;
            }
            QLineEdit {
                background-color: #f0f8ff;
                border: 1px solid #999;
                padding: 5px;
            }
            QTextEdit {
                background-color: #e8eff5;
                border: 1px solid #999;
            }
            QLabel {
                color: #333333;
            }
        """)

    def update_status(self, message):
        self.status_bar.showMessage(message)

    def show_error_popup(self, message):
        QMessageBox.critical(self, 'Error', message)

    def get_priorities(self):
        return [p.strip() for p in self.priority_entry.text().split(',')]

    def fetch_selectors(self):
        try:
            priorities = self.get_priorities()
            if not priorities:
                self.show_error_popup("Please specify at least one priority.")
                return

            self.update_status("Fetching selectors...")
            all_selectors = self.fetch_selectors_from_page(priorities)

            filtered_selectors = {priority: selectors for priority, selectors
                                  in all_selectors.items() if priority in priorities}

            self.display_selectors(filtered_selectors)
            self.update_status("Selectors fetched successfully.")

        except Exception as e:
            self.show_error_popup(f"Error fetching selectors: {str(e)}")
            self.update_status("Fetch failed.")

    def fetch_selectors_from_page(self, priorities):
        selectors_by_priority = {
            "ID": set(),
            "Name": set(),
            "ClassName": set(),
            "LinkText": set(),
            "PartialLinkText": set(),
            "TagName": set(),
        }

        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp("http://localhost:9214")
            page = browser.contexts[0].pages[0]
            page.wait_for_load_state("load")

            elements = page.query_selector_all("*")
            for element in elements:
                selector = self.get_priority_selector(element)
                if selector:
                    if "id=" in selector:
                        selectors_by_priority["ID"].add(selector)
                    elif "name=" in selector:
                        selectors_by_priority["Name"].add(selector)
                    elif "contains(@class," in selector:
                        selectors_by_priority["ClassName"].add(selector)
                    elif "text()=" in selector:
                        selectors_by_priority["LinkText"].add(selector)
                    elif "contains(text()," in selector:
                        selectors_by_priority["PartialLinkText"].add(selector)
                    elif selector.startswith("//"):
                        selectors_by_priority["TagName"].add(selector)

            browser.close()
        return selectors_by_priority

    def get_priority_selector(self, element):
        try:
            element_id = element.evaluate("element => element.id")
            if element_id:
                return f"//*[@id='{element_id}']"

            name_attr = element.evaluate("element => element.getAttribute('name')")
            if name_attr:
                return f"//*[@name='{name_attr}']"

            class_attr = element.evaluate("element => element.className")
            if class_attr:
                class_name = " and ".join([f"contains(@class, '{cls}')"
                                           for cls in class_attr.split()])
                return f"//*[{class_name}]"

            inner_text = element.evaluate("element => element.innerText").strip() if element.evaluate(
                "element => element.innerText") else ""
            if inner_text and len(inner_text) <= 10:
                return f"//*[text()='{inner_text}']"

            if inner_text and len(inner_text) > 10:
                return f"//*[contains(text(), '{inner_text[:10]}')]"

            tag_name = element.evaluate("element => element.tagName.toLowerCase()")
            if tag_name:
                return f"//{tag_name}"

        except Exception as e:
            print(f"Error generating selector for element: {e}")

        return None

    def display_selectors(self, selectors):
        self.output_text.clear()
        for priority, sel_list in selectors.items():
            self.output_text.append(f"\n{priority} Selectors:\n")
            for selector in sel_list:
                self.output_text.append(f"{selector}\n")

    def move_selected_lines(self):
        cursor = self.output_text.textCursor()
        if not cursor.hasSelection():
            QMessageBox.information(self, "No Selection", "Please select text to move.")
            return

        selected_text = cursor.selectedText()

        # Check if moved_text contains POM structure
        moved_text_content = self.moved_text.toPlainText()
        if "# Locators" in moved_text_content and "# Functions" in moved_text_content:
            QMessageBox.information(self, "Move Selector", "Clear POM before moving new selector.")
            return

        # Check for duplicates
        existing_text = self.moved_text.toPlainText().strip().splitlines()
        if selected_text.strip() in existing_text:
            QMessageBox.information(self, "Duplicate Selector",
                                    "Duplicate selector! This selector is already added.")
            return

        # Add the text and highlight it in the source
        self.moved_text.append(selected_text + "\n")

        # Highlight the selected text in output_text
        format = QTextCharFormat()
        format.setBackground(QColor("#d4edda"))
        cursor.mergeCharFormat(format)

        # Update move count
        self.move_count += len(selected_text.strip().splitlines())
        self.update_status(f"Moved Selector: {self.move_count}")

    def generate_pom(self):
        if "# Locators" in self.moved_text.toPlainText() and "# Functions" in self.moved_text.toPlainText():
            self.moved_text.clear()
            QMessageBox.information(self, "Generate POM", "Move the Selectors to generate the POM again.")
            return

        class_name = self.class_name_entry.text()
        if not class_name or class_name == "Enter Class Name":
            class_name = "Test"

        selectors = self.moved_text.toPlainText().strip().splitlines()
        pom_code = self.generate_pom_code(class_name, selectors)
        self.moved_text.clear()
        self.moved_text.setText(pom_code)
        self.update_status("POM generated successfully.")

    def generate_pom_code(self, class_name, selectors):
        elements = []
        for selector in selectors:
            name = self.extract_name(selector)
            elements.append({
                'name': name,
                'type': 'xpath',
                'locator': selector
            })

        pom_code = f"""import logging
import time
import utilities.custom_logger as cl
from base.selenium_driver import Selenium_Driver

class {class_name.capitalize()}Page(Selenium_Driver):

    log = cl.customLogger(logging.DEBUG)

    \"\"\"Page Object for {class_name}\"\"\"

    def __init__(self, driver):
        super().__init__(driver)
        self.driver = driver

    # Locators
"""
        for element in elements:
            locator_name = f"__{element['name']}"
            pom_code += f"    {locator_name} = \"{element['locator']}\"\n"

        pom_code += "\n    # Functions\n"

        for element in elements:
            function_name = element['name']
            pom_code += f"\n    def {function_name}(self):\n"
            pom_code += f"        self.element(self.__{function_name}, locatorType='xpath')\n"

        return pom_code

    def extract_name(self, selector):
        if "@id='" in selector:
            return selector.split("@id='")[1].split("']")[0]
        elif "@name='" in selector:
            return selector.split("@name='")[1].split("']")[0]
        elif "contains(@class," in selector:
            return "_".join(cls.split("')")[0] for cls in selector.split("contains(@class, '")[1:])
        elif "text()=" in selector:
            return selector.split("text()='")[1].split("']")[0]
        elif "contains(text()," in selector:
            return selector.split("contains(text(), '")[1].split("')")[0]
        else:
            return "custom_selector"

    def save_to_file(self):
        content = self.moved_text.toPlainText()
        if not content.strip():
            self.show_error_popup("No content available to save.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save POM", "", "Python Files (*.py)")

        if file_path:
            with open(file_path, 'w') as file:
                file.write(content)
            QMessageBox.information(self, "Saved", f"POM saved as {file_path}")
            self.update_status("POM saved successfully.")

    def clear_generated_pom(self):
        removed_text = self.moved_text.toPlainText().strip()
        if removed_text:
            removed_line_count = len(removed_text.splitlines())
            self.move_count -= removed_line_count
            if self.move_count < 0:
                self.move_count = 0
            self.update_status(f"Moved Selector: {self.move_count}")
        self.moved_text.clear()

    def on_text_area_modified(self):
        current_text = self.moved_text.toPlainText().strip()

        # Check for removed lines
        removed_lines = set(self.previous_text.splitlines()) - set(current_text.splitlines())
        if removed_lines:
            removed_line_count = len(removed_lines)
            self.move_count -= removed_line_count
            if self.move_count < 0:
                self.move_count = 0
            self.update_status(f"Moved Selector: {self.move_count}")

        self.previous_text = current_text


if __name__ == '__main__':
    app = QApplication(sys.argv)
    pom_generator = POMGenerator()
    pom_generator.show()
    sys.exit(app.exec_())