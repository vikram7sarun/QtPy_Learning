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
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


class POMGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon('app_icon.ico'))
        self.move_count = 0
        self.previous_text = ""
        self.template = None
        self.init_ui()
        self.set_styles()

    def init_ui(self):
        self.setWindowTitle('NessQ POM Generator')
        self.setGeometry(100, 100, 650, 800)

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

        # Move Button
        self.move_button = QPushButton('Move Selected Lines')
        self.move_button.clicked.connect(self.move_selected_lines)
        middle_layout.addWidget(self.move_button)

        # Class Name Entry with reduced width
        class_name_layout = QHBoxLayout()
        self.class_name_entry = QLineEdit()
        self.class_name_entry.setPlaceholderText("Enter Class Name")
        self.class_name_entry.setFixedWidth(150)  # Set fixed width
        middle_layout.addWidget(self.class_name_entry)

        # Language Dropdown
        self.language_combo = QComboBox()
        self.language_combo.addItems(['Python', 'Java', 'C#'])
        self.language_combo.setCurrentText('Python')
        self.language_combo.setFixedWidth(100)  # Set fixed width
        middle_layout.addWidget(self.language_combo)

        # Generate button
        self.generate_button = QPushButton('Generate POM')
        self.generate_button.clicked.connect(self.generate_pom)
        middle_layout.addWidget(self.generate_button)

        # Add spacing between elements
        middle_layout.setSpacing(10)
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
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                padding: 5px;
                min-width: 80px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border: 1px solid #b3b3b3;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
                border: 2px solid #999999;
                padding: 6px 4px 4px 6px;
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                border: 1px solid #dddddd;
                color: #999999;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                padding: 5px;
                border-radius: 3px;
            }
            QLineEdit:focus {
                border: 2px solid #999999;
                background-color: #ffffff;
            }
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 3px;
            }
            QTextEdit:focus {
                border: 2px solid #999999;
                background-color: #ffffff;
            }
            QLabel {
                color: #333333;
                font-weight: normal;
            }
            QComboBox {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                padding: 4px;
                border-radius: 3px;
            }
            QComboBox:hover {
                background-color: #e0e0e0;
                border: 1px solid #b3b3b3;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
                margin-right: 5px;
            }
            QStatusBar {
                background-color: #f5f5f5;
                color: #333333;
                border-top: 1px solid #dddddd;
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
            # Check if output text area has content
            if self.output_text.toPlainText().strip():
                reply = QMessageBox.question(self, 'Clear Content',
                                             'Text area contains content. Do you want to clear it and fetch new selectors?',
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

                if reply == QMessageBox.Yes:
                    self.output_text.clear()
                else:
                    return

            priorities = self.get_priorities()
            if not priorities:
                self.show_error_popup("Please specify at least one priority.")
                return

            self.update_status("Fetching selectors...")
            all_selectors = self.fetch_selectors_from_page(priorities)

            filtered_selectors = {priority: selectors for priority, selectors
                                  in all_selectors.items() if priority in priorities}

            self.display_selectors(filtered_selectors)

            # Ensure focus is on the output text area
            self.output_text.setFocus()

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
        # Clear the output text
        self.output_text.clear()

        # Build the text content
        text_content = ""
        for priority, sel_list in selectors.items():
            text_content += f"\n{priority} Selectors:\n\n"
            for selector in sel_list:
                text_content += f"{selector}\n"

        # Set the text content
        self.output_text.setText(text_content)

        # Move cursor to the start
        cursor = self.output_text.textCursor()
        cursor.movePosition(cursor.Start)
        self.output_text.setTextCursor(cursor)

        # Ensure scrollbar is at the top
        self.output_text.verticalScrollBar().setValue(0)

    def move_selected_lines(self):
        cursor = self.output_text.textCursor()
        if not cursor.hasSelection():
            QMessageBox.information(self, "No Selection", "Please select text to move.")
            return

        selected_text = cursor.selectedText()

        # Check if moved_text contains POM structure
        moved_text_content = self.moved_text.toPlainText()
        if "# Locators" in moved_text_content or "# Functions" in moved_text_content:
            reply = QMessageBox.question(
                self,
                'Clear Content',
                'Text area contains a POM structure. Do you want to clear it to move new selectors?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.moved_text.clear()
                self.move_count = 0
            else:
                return

        # Check for duplicates
        existing_text = self.moved_text.toPlainText().strip().splitlines()
        if selected_text.strip() in existing_text:
            QMessageBox.information(
                self,
                "Duplicate Selector",
                "This selector has already been added."
            )
            return

        # Validate if the selected text is a valid XPath selector
        if not selected_text.strip().startswith("//"):
            QMessageBox.warning(
                self,
                "Invalid Selection",
                "Please select a valid XPath selector starting with '//'."
            )
            return

        # Add the text and highlight it in the source
        self.moved_text.append(selected_text + "\n")

        # Highlight the selected text in output_text
        format = QTextCharFormat()
        format.setBackground(QColor("#d4edda"))
        cursor.mergeCharFormat(format)

        # Update move count
        self.move_count += 1
        self.update_status(f"Moved Selector: {self.move_count}")

    def generate_pom(self):
        try:
            # Get content from moved_text (text area 2)
            moved_text_content = self.moved_text.toPlainText().strip()

            # Check if content exists
            if not moved_text_content:
                self.show_error_popup("No content to generate POM. Please select and move selectors first.")
                return

            # Check if the content contains POM structure
            if "# Locators" in moved_text_content or "# Functions" in moved_text_content:
                reply = QMessageBox.question(
                    self,
                    'Clear Content',
                    'Text area contains a POM structure. Do you want to clear it and create a new POM?',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    self.moved_text.clear()
                    self.update_status("Please select and move selectors to generate a new POM.")
                return

            # If we reach here, we have valid selectors to process
            class_name = self.class_name_entry.text()
            if not class_name or class_name == "Enter Class Name":
                class_name = "Test"

            # Get selectors from moved text
            selectors = moved_text_content.splitlines()

            # Validate selectors
            valid_selectors = [s for s in selectors if s.strip() and s.startswith("//")]
            if not valid_selectors:
                self.show_error_popup("No valid selectors found.Clear POM and Please select and move valid selectors.")
                return

            # Generate POM code based on selected language
            pom_code = self.generate_pom_code(class_name, valid_selectors)
            if pom_code:  # Only update if generation was successful
                self.moved_text.clear()
                self.moved_text.setText(pom_code)
                self.update_status(f"POM generated successfully in {self.language_combo.currentText()}")

        except Exception as e:
            self.show_error_popup(f"Error generating POM: {str(e)}")
            self.update_status("POM generation failed.")

    def clear_generated_pom(self):
        if self.moved_text.toPlainText().strip():
            reply = QMessageBox.question(
                self,
                'Clear Content',
                'Are you sure you want to clear the current content?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                removed_text = self.moved_text.toPlainText().strip()
                if removed_text:
                    self.move_count = 0
                    self.moved_text.clear()
                    self.update_status("Content cleared. Ready for new selectors.")
        else:
            self.update_status("Nothing to clear.")

    def generate_pom_code(self, class_name, selectors):
        selected_language = self.language_combo.currentText()

        if selected_language == 'Python':
            return self.generate_python_pom(class_name, selectors)
        elif selected_language == 'Java':
            return self.generate_java_pom(class_name, selectors)
        elif selected_language == 'C#':
            return self.generate_csharp_pom(class_name, selectors)

        return self.generate_python_pom(class_name, selectors)

    def generate_python_pom(self, class_name, selectors):
            # Existing Python POM generation code...
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

    def generate_java_pom(self, class_name, selectors):
        elements = []
        for selector in selectors:
            name = self.extract_name(selector)
            elements.append({
                'name': name,
                'type': 'xpath',
                'locator': selector
            })

        pom_code = f"""import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.openqa.selenium.support.ui.ExpectedConditions;

public class {class_name.capitalize()}Page {{
private WebDriver driver;
private WebDriverWait wait;

    // Locators
    """
        for element in elements:
            locator_name = f"__{element['name']}"
            pom_code += f"    private final String {locator_name} = \"{element['locator']}\";\n"

            pom_code += f"""
        public {class_name.capitalize()}Page(WebDriver driver) {{
            this.driver = driver;
            this.wait = new WebDriverWait(driver, 10);
        }}

        // Functions
    """
        for element in elements:
            function_name = element['name']
            pom_code += f"""
        public WebElement {function_name}() {{
            return wait.until(ExpectedConditions.presenceOfElementLocated(By.xpath({function_name})));
        }}
    """
            pom_code += "}\n"
            return pom_code

    def generate_csharp_pom(self, class_name, selectors):
        elements = []
        for selector in selectors:
            name = self.extract_name(selector)
            elements.append({
                'name': name,
                'type': 'xpath',
                'locator': selector
            })

        pom_code = f"""using OpenQA.Selenium;
using OpenQA.Selenium.Support.UI;
using System;

namespace Pages
{{
    public class {class_name.capitalize()}Page
    {{
        private IWebDriver _driver;
        private WebDriverWait _wait;

        // Locators
"""
        for element in elements:
            locator_name = f"__{element['name']}"
            pom_code += f"        private readonly string {locator_name} = \"{element['locator']}\";\n"

        pom_code += f"""
    public {class_name.capitalize()}Page(IWebDriver driver)
    {{
        _driver = driver;
        _wait = new WebDriverWait(driver, TimeSpan.FromSeconds(10));
    }}

    // Functions
    """
        for element in elements:
            function_name = element['name']
            pom_code += f"""
    public IWebElement {function_name}()
    {{
        return _wait.Until(SeleniumExtras.WaitHelpers.ExpectedConditions.ElementExists(By.XPath({function_name})));
    }}
    """
        pom_code += "    }\n}"
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
        try:
            content = self.moved_text.toPlainText()
            if not content.strip():
                self.show_error_popup("No content available to save.")
                return

            # Adjust file extension based on selected language
            file_filter = "Python Files (*.py)"
            if self.language_combo.currentText() == "Java":
                file_filter = "Java Files (*.java)"
            elif self.language_combo.currentText() == "C#":
                file_filter = "C# Files (*.cs)"

            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save POM", "", file_filter)

            if file_path:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                QMessageBox.information(self, "Saved", f"POM saved as {file_path}")
                self.update_status("POM saved successfully.")

        except Exception as e:
            self.show_error_popup(f"Error saving file: {str(e)}")

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

    def update_status(self, message):
        self.status_bar.showMessage(message)

    def show_error_popup(self, message):
        QMessageBox.critical(self, 'Error', message)


if __name__ == '__main__':
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    app = QApplication(sys.argv)
    pom_generator = POMGenerator()
    pom_generator.show()
    sys.exit(app.exec_())