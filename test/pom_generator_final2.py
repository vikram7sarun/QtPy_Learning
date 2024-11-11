from PyQt5 import QtWidgets, QtGui, QtCore
from selenium import webdriver
from selenium.webdriver.common.by import By
from playwright.sync_api import sync_playwright
import sys
import warnings
import re

warnings.filterwarnings("ignore", category=DeprecationWarning)

class EnhancedPOMGenerator(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("POM Generator")
        self.setup_ui()

    def setup_ui(self):
        self.language_combo = QtWidgets.QComboBox(self)
        self.language_combo.addItems(["Python", "Java", "C#"])
        self.set_styles()

    def set_styles(self):
        self.setStyleSheet(
           "QMainWindow { background-color: #f8f9fa; }"
           "QPushButton { background-color: #6c757d; color: white; border-radius: 4px; }"
           "QLineEdit, QTextEdit { background-color: #ffffff; border: 1px solid #ced4da; }"
           "QLabel { color: #495057; font-weight: 500; }"
           "QComboBox { background-color: #ffffff; border: 1px solid #ced4da; }"
           "QStatusBar { background-color: #f8f9fa; color: #495057; }"
        )

    def process_selectors(self, selectors):
        try:
            processed_elements = []
            for selector in selectors:
                name, value = self.parse_selector(selector)
                processed_elements.append({"name": name, "locator": value, "type": "xpath"})
            return processed_elements
        except Exception as e:
            print(f"Error processing selectors: {e}")
            return []

    def parse_selector(self, selector):
        selector = selector.strip()
        if ':' in selector:
            selector_type, value = [part.strip() for part in selector.split(':', 1)]
            selector_type = selector_type.lower()
            return self.sanitize_name(value), f"//tag[@{selector_type}='{value}']"
        elif selector.startswith('//'):
            return "element", selector
        return None

    def sanitize_name(self, name):
        sanitized = re.sub(r'\W|^(?=\d)', '_', name).lower()
        return sanitized

    def generate_pom(self, class_name, selectors, language):
        processed_elements = self.process_selectors(selectors)
        if language == "Python":
            return self._generate_python_pom(class_name, processed_elements)
        elif language == "Java":
            return self._generate_java_pom(class_name, processed_elements)
        elif language == "C#":
            return self._generate_csharp_pom(class_name, processed_elements)

    def _generate_python_pom(self, class_name, elements):
        pom_code = f"import logging\nclass {class_name.capitalize()}Page:\n\n    def __init__(self, driver):\n        self.driver = driver\n"
        for element in elements:
            pom_code += f"    def {element['name']}(self):\n        return self.driver.find_element_by_xpath('{element['locator']}')\n"
        return pom_code

    def _generate_java_pom(self, class_name, elements):
        pom_code = f"public class {class_name.capitalize()}Page \n    private WebDriver driver;\n"
        for element in elements:
            pom_code += f"    public WebElement get_{element['name']}() {{\n        return driver.findElement(By.xpath('{element['locator']}'));\n    }}\n"
        return pom_code

    def _generate_csharp_pom(self, class_name, elements):
        pom_code = f"public class {class_name.capitalize()}Page \n    private IWebDriver driver;\n"
        for element in elements:
            pom_code += f"    public IWebElement Get_{element['name']}() => driver.FindElement(By.XPath(\"{element['locator']}\"));\n"
        return pom_code

    def update_status(self, message):
        self.statusBar().showMessage(message)

    def clear_generated_pom(self):
        reply = QtWidgets.QMessageBox.question(self, 'Clear Content', 'Are you sure?', QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            self.update_status("Content cleared")

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = EnhancedPOMGenerator()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
