import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QFileDialog, QComboBox, QMessageBox
)
from PyQt5.QtCore import Qt
import re


class POMGenerator(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("AI-Based Page Object Model Generator")
        self.setGeometry(100, 100, 800, 600)

        # Layout
        layout = QVBoxLayout()

        # Load Sample POM File
        layout.addWidget(QLabel("Sample POM File:"))
        self.load_button = QPushButton("Load Sample POM")
        self.load_button.clicked.connect(self.load_sample_pom)
        layout.addWidget(self.load_button)

        # Target Programming Language
        layout.addWidget(QLabel("Select Target Language:"))
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Java", "Python", "JavaScript", "C#", "DotNet"])
        layout.addWidget(self.language_combo)

        # Class Name Input
        layout.addWidget(QLabel("Enter Class Name:"))
        self.class_name_input = QLineEdit()
        layout.addWidget(self.class_name_input)

        # Element Declarations
        layout.addWidget(QLabel("Page Elements (ID/Name/XPath):"))
        self.elements_input = QTextEdit()
        layout.addWidget(self.elements_input)

        # Generate Button
        self.generate_button = QPushButton("Generate POM")
        self.generate_button.clicked.connect(self.generate_pom)
        layout.addWidget(self.generate_button)

        # Output Display
        layout.addWidget(QLabel("Generated POM:"))
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(False)
        layout.addWidget(self.output_display)

        # Save Button
        self.save_button = QPushButton("Save POM File")
        self.save_button.clicked.connect(self.save_pom)
        layout.addWidget(self.save_button)

        # Set layout
        self.setLayout(layout)

    def load_sample_pom(self):
        options = QFileDialog.Options()
        file, _ = QFileDialog.getOpenFileName(self, "Select Sample POM File", "", "All Files (*)", options=options)
        if file:
            with open(file, "r") as f:
                self.sample_pom_content = f.read()
                QMessageBox.information(self, "POM Loaded", "Sample POM file loaded successfully.")

    def generate_pom(self):
        language = self.language_combo.currentText()
        class_name = self.class_name_input.text()
        elements_text = self.elements_input.toPlainText()

        if not class_name or not elements_text:
            QMessageBox.warning(self, "Input Error", "Please provide a class name and page elements.")
            return

        # Parse elements
        elements = []
        for line in elements_text.splitlines():
            match = re.match(r"(\w+): (.*)", line)
            if match:
                element_type, locator = match.groups()
                elements.append((element_type, locator))

        # Generate POM based on language
        pom = self.generate_pom_code(language, class_name, elements)
        self.output_display.setText(pom)

    def generate_pom_code(self, language, class_name, elements):
        # Load appropriate template
        if language == "Java":
            template = """public class {ClassName} {{
    WebDriver driver;

    public {ClassName}(WebDriver driver) {{
        this.driver = driver;
    }}

    {ElementDeclarations}

    {MethodDefinitions}
}}"""
            element_template = "    By {name} = By.{type}(\"{locator}\");"
            method_template = """
    public void {name}() {{
        driver.findElement({name}).click();
    }}
"""

        elif language == "Python":
            template = """class {ClassName}:
    def __init__(self, driver):
        self.driver = driver

    {ElementDeclarations}

    {MethodDefinitions}
"""
            element_template = "    self.{name} = self.driver.find_element(By.{type}, \"{locator}\")"
            method_template = """
    def {name}(self):
        self.{name}.click()
"""

        elif language == "JavaScript":
            template = """class {ClassName} {{
    constructor(driver) {{
        this.driver = driver;
    }}

    {ElementDeclarations}

    {MethodDefinitions}
}}"""
            element_template = "    this.{name} = driver.findElement(By.{type}, '{locator}');"
            method_template = """
    {name}() {{
        this.{name}.click();
    }}
"""

        # Build element and method declarations
        element_declarations = "\n".join(
            element_template.format(name=element[0], type=element[1].upper(), locator=element[2])
            for element in elements
        )
        method_definitions = "\n".join(
            method_template.format(name=element[0])
            for element in elements
        )

        return template.format(ClassName=class_name, ElementDeclarations=element_declarations,
                               MethodDefinitions=method_definitions)

    def save_pom(self):
        pom_content = self.output_display.toPlainText()
        if not pom_content:
            QMessageBox.warning(self, "Save Error", "No POM content to save.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save POM File", "", "All Files (*)")
        if file_path:
            with open(file_path, "w") as f:
                f.write(pom_content)
            QMessageBox.information(self, "Save Successful", "POM file saved successfully.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = POMGenerator()
    window.show()
    sys.exit(app.exec_())
