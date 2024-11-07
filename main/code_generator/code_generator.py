import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QTextEdit, QLabel,
                             QComboBox, QGroupBox, QCheckBox, QFileDialog, QMessageBox,
                             QScrollArea)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QColor


class SyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6"))  # Blue
        keywords = [
            "class", "def", "import", "from", "try", "except", "finally",
            "if", "else", "elif", "for", "while", "return", "yield",
            "public", "private", "protected", "static", "void", "const",
            "function", "var", "let", "const", "async", "await"
        ]
        for word in keywords:
            pattern = f"\\b{word}\\b"
            self.highlighting_rules.append((pattern, keyword_format))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))  # Orange
        self.highlighting_rules.append(("\".*\"", string_format))
        self.highlighting_rules.append(("\'.*\'", string_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))  # Green
        self.highlighting_rules.append(("#[^\n]*", comment_format))
        self.highlighting_rules.append(("//[^\n]*", comment_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = pattern
            index = text.find(expression)
            while index >= 0:
                length = len(expression)
                self.setFormat(index, length, format)
                index = text.find(expression, index + length)


class TestScriptGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced Test Script Generator")
        self.setGeometry(100, 100, 1400, 800)

        # Available languages and frameworks
        self.language_frameworks = {
            "Python": ["Pytest", "Unittest", "Robot Framework", "Behave"],
            "Java": ["TestNG", "JUnit", "Cucumber", "Serenity"],
            "JavaScript": ["Jest", "Mocha", "Cypress", "Playwright"],
            "C#": ["NUnit", "MSTest", "xUnit", "SpecFlow"],
            "Ruby": ["RSpec", "Cucumber", "Watir", "Capybara"],
            "TypeScript": ["Jest", "Mocha", "Protractor", "TestCafe"]
        }

        # Test types
        self.test_types = [
            "UI Test", "API Test", "Unit Test", "Integration Test",
            "Performance Test", "Security Test", "Database Test"
        ]

        self.setup_ui()
        self.setup_connections()

        # Set default selections
        self.set_default_selections()

        # Apply syntax highlighting
        self.highlighter = SyntaxHighlighter(self.output_area.document())

        # Generate initial script
        self.update_template()

    def set_default_selections(self):
        """Set default selections for language, framework and test type"""
        # Set Python as default language
        self.lang_combo.setCurrentText("Python")

        # Set Pytest as default framework
        self.framework_combo.setCurrentText("Pytest")

        # Set UI Test as default test type
        self.test_type_combo.setCurrentText("UI Test")

        # Set all checkboxes to checked by default
        for checkbox in [
            self.setup_teardown, self.assertions, self.logging,
            self.error_handling, self.comments, self.reporting,
            self.parallel_execution, self.data_driven,
            self.retry_mechanism, self.screenshots
        ]:
            checkbox.setChecked(True)

    def create_options_group(self):
        """Create the options group"""
        options_group = QGroupBox("Generation Options")
        layout = QVBoxLayout()

        # Create buttons - removed Generate Script button
        buttons = [
            ("Preview Script", self.preview_script),
            ("Copy to Clipboard", self.copy_to_clipboard),
            ("Save to File", self.save_to_file),
            ("Clear Form", self.clear_form)
        ]

        for button_text, callback in buttons:
            btn = QPushButton(button_text)
            btn.clicked.connect(callback)
            layout.addWidget(btn)

        layout.addStretch()
        options_group.setLayout(layout)
        return options_group

    def create_test_details_group(self):
        """Create the test details group"""
        details_group = QGroupBox("Test Details")
        layout = QVBoxLayout()

        # Class name input
        class_label = QLabel("Test Class Name:")
        self.class_name = QComboBox()
        self.class_name.setEditable(True)
        self.class_name.addItems([
            "LoginTest", "UserRegistrationTest", "PaymentTest",
            "CheckoutTest", "SearchTest", "NavigationTest"
        ])

        # Description input
        description_label = QLabel("Test Description:")
        self.description = QTextEdit()
        self.description.setMaximumHeight(100)
        self.description.setPlaceholderText("Enter test description here...")

        layout.addWidget(class_label)
        layout.addWidget(self.class_name)
        layout.addWidget(description_label)
        layout.addWidget(self.description)

        details_group.setLayout(layout)
        return details_group

    def setup_ui(self):
        """Setup the main user interface"""
        # Create main widget with scroll area
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()

        # Create scroll area for top section
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()

        # Top section
        top_widget = QWidget()
        top_layout = QHBoxLayout()

        # Left side - Test Configuration
        config_group = self.create_config_group()
        top_layout.addWidget(config_group)

        # Middle - Test Features
        features_group = self.create_features_group()
        top_layout.addWidget(features_group)

        # Right side - Generation Options
        options_group = self.create_options_group()
        top_layout.addWidget(options_group)

        top_widget.setLayout(top_layout)
        scroll_layout.addWidget(top_widget)

        # Test Details
        details_group = self.create_test_details_group()
        scroll_layout.addWidget(details_group)

        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)

        # Output section
        main_layout.addWidget(QLabel("Generated Test Script:"))
        self.output_area = QTextEdit()
        self.output_area.setFont(QFont("Courier", 10))
        self.output_area.setMinimumHeight(300)
        main_layout.addWidget(self.output_area)

        main_widget.setLayout(main_layout)

    def create_config_group(self):
        """Create the configuration group"""
        config_group = QGroupBox("Test Configuration")
        layout = QVBoxLayout()

        # Language Selection
        lang_label = QLabel("Programming Language:")
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(self.language_frameworks.keys())

        # Framework Selection
        framework_label = QLabel("Testing Framework:")
        self.framework_combo = QComboBox()

        # Test Type Selection
        test_type_label = QLabel("Test Type:")
        self.test_type_combo = QComboBox()
        self.test_type_combo.addItems(self.test_types)

        layout.addWidget(lang_label)
        layout.addWidget(self.lang_combo)
        layout.addWidget(framework_label)
        layout.addWidget(self.framework_combo)
        layout.addWidget(test_type_label)
        layout.addWidget(self.test_type_combo)
        layout.addStretch()

        config_group.setLayout(layout)
        return config_group

    def create_features_group(self):
        """Create the features group"""
        features_group = QGroupBox("Test Features")
        layout = QVBoxLayout()

        # Create checkboxes
        self.setup_teardown = QCheckBox("Setup/Teardown Methods")
        self.assertions = QCheckBox("Assertions")
        self.logging = QCheckBox("Logging")
        self.error_handling = QCheckBox("Error Handling")
        self.comments = QCheckBox("Comments")
        self.reporting = QCheckBox("Test Reporting")
        self.parallel_execution = QCheckBox("Parallel Execution")
        self.data_driven = QCheckBox("Data-Driven")
        self.retry_mechanism = QCheckBox("Retry Mechanism")
        self.screenshots = QCheckBox("Screenshot Capture")

        checkboxes = [
            self.setup_teardown, self.assertions, self.logging,
            self.error_handling, self.comments, self.reporting,
            self.parallel_execution, self.data_driven,
            self.retry_mechanism, self.screenshots
        ]

        for checkbox in checkboxes:
            layout.addWidget(checkbox)
            checkbox.setChecked(True)  # Default all features to enabled

        layout.addStretch()
        features_group.setLayout(layout)
        return features_group

    def create_options_group(self):
        """Create the options group"""
        options_group = QGroupBox("Generation Options")
        layout = QVBoxLayout()

        # Create buttons
        buttons = [
            ("Generate Script", self.generate_script),
            ("Preview Script", self.preview_script),
            ("Copy to Clipboard", self.copy_to_clipboard),
            ("Save to File", self.save_to_file),
            ("Clear Form", self.clear_form)
        ]

        for button_text, callback in buttons:
            btn = QPushButton(button_text)
            btn.clicked.connect(callback)
            layout.addWidget(btn)

        layout.addStretch()
        options_group.setLayout(layout)
        return options_group

    def create_test_details_group(self):
        """Create the test details group"""
        details_group = QGroupBox("Test Details")
        layout = QVBoxLayout()

        # Class name input
        class_label = QLabel("Test Class Name:")
        self.class_name = QComboBox()
        self.class_name.setEditable(True)
        self.class_name.addItems([
            "LoginTest", "UserRegistrationTest", "PaymentTest",
            "CheckoutTest", "SearchTest", "NavigationTest"
        ])

        # Method name input
        method_label = QLabel("Test Method Name:")
        self.method_name = QComboBox()
        self.method_name.setEditable(True)
        self.method_name.addItems([
            "testValidLogin", "testInvalidLogin",
            "testUserRegistration", "testPaymentProcess",
            "testSearchFunctionality", "testNavigationFlow"
        ])

        # Description input
        description_label = QLabel("Test Description:")
        self.description = QTextEdit()
        self.description.setMaximumHeight(100)
        self.description.setPlaceholderText("Enter test description here...")

        layout.addWidget(class_label)
        layout.addWidget(self.class_name)
        layout.addWidget(method_label)
        layout.addWidget(self.method_name)
        layout.addWidget(description_label)
        layout.addWidget(self.description)

        details_group.setLayout(layout)
        return details_group

    def setup_connections(self):
        """Setup signal connections"""
        self.lang_combo.currentTextChanged.connect(self.update_frameworks)
        self.framework_combo.currentTextChanged.connect(self.update_template)
        self.test_type_combo.currentTextChanged.connect(self.update_template)

        # Connect all checkboxes
        checkboxes = [
            self.setup_teardown, self.assertions, self.logging,
            self.error_handling, self.comments, self.reporting,
            self.parallel_execution, self.data_driven,
            self.retry_mechanism, self.screenshots
        ]
        for checkbox in checkboxes:
            checkbox.stateChanged.connect(self.update_template)

    def update_frameworks(self):
        """Update framework options based on selected language"""
        self.framework_combo.clear()
        language = self.lang_combo.currentText()
        frameworks = self.language_frameworks.get(language, [])
        self.framework_combo.addItems(frameworks)
        self.update_template()

    def update_template(self):
        """Update the template when options change"""
        self.generate_script()

    def generate_script(self):
        """Generate test script based on selected options"""
        try:
            language = self.lang_combo.currentText()
            framework = self.framework_combo.currentText()
            test_type = self.test_type_combo.currentText()
            class_name = self.class_name.currentText()
            # Use a default method name based on the class name
            method_name = f"test_{class_name.lower().replace('test', '')}"

            # Get the appropriate template generator
            template_generators = {
                "Python": self.generate_python_script,
                "Java": self.generate_java_script,
                "JavaScript": self.generate_javascript_script,
                "C#": self.generate_csharp_script,
                "Ruby": self.generate_ruby_script,
                "TypeScript": self.generate_typescript_script
            }

            generator = template_generators.get(language)
            if generator:
                script = generator(framework, test_type, class_name, method_name)
                self.output_area.setText(script)
            else:
                self.output_area.setText(f"Language {language} not yet supported")

        except Exception as e:
            self.output_area.setText(f"Error generating script: {str(e)}")

    def generate_python_script(self, framework, test_type, class_name, method_name):
        """Generate Python test script"""
        if framework == "Pytest":
            return self.generate_pytest_script(test_type, class_name, method_name)
        elif framework == "Unittest":
            return self.generate_unittest_script(test_type, class_name, method_name)
        elif framework == "Robot Framework":
            return self.generate_robot_script(test_type, class_name, method_name)
        elif framework == "Behave":
            return self.generate_behave_script(test_type, class_name, method_name)
        else:
            return f"# Template not yet implemented for Python {framework}"

    def generate_pytest_script(self, test_type, class_name, method_name):
        """Generate Pytest script"""
        imports = []
        body = []
        setup = []

        # Add imports based on test type and features
        imports.extend([
            "import pytest",
            "from datetime import datetime",
        ])

        if test_type == "UI Test":
            imports.extend([
                "from selenium import webdriver",
                "from selenium.webdriver.common.by import By",
                "from selenium.webdriver.support.ui import WebDriverWait",
                "from selenium.webdriver.support import expected_conditions as EC"
            ])
        elif test_type == "API Test":
            imports.extend([
                "import requests",
                "import json"
            ])

        if self.logging.isChecked():
            imports.append("import logging")

        if self.screenshots.isChecked() and test_type == "UI Test":
            imports.append("import os")

        # Add class definition
        body.append(f"\n\nclass Test{class_name}:")

        # Add setup/teardown if selected
        if self.setup_teardown.isChecked():
            if test_type == "UI Test":
                setup.extend([
                    "    @pytest.fixture(autouse=True)",
                    "    def setup_method(self):",
                    "        self.driver = webdriver.Chrome()",
                    "        self.driver.implicitly_wait(10)",
                    "        yield",
                    "        self.driver.quit()",
                    ""
                ])
            elif test_type == "API Test":
                setup.extend([
                    "    @pytest.fixture(autouse=True)",
                    "    def setup_method(self):",
                    "        self.base_url = 'https://api.example.com'",
                    "        self.headers = {'Content-Type': 'application/json'}",
                    "        yield",
                    ""
                ])

        # Add test method
        body.append(f"    def test_{method_name}(self):")

        # Add description as docstring if comments enabled
        if self.comments.isChecked():
            description = self.description.toPlainText() or "Test implementation"
            body.append(f'        """{description}"""')

        # Add logging setup if selected
        if self.logging.isChecked():
            body.append("        logger = logging.getLogger(__name__)")

        # Add error handling if selected
        if self.error_handling.isChecked():
            body.append("        try:")

        # Add test implementation based on type
        if test_type == "UI Test":
            body.extend([
                "            # Navigate to the test page",
                "            self.driver.get('https://example.com')",
                "",
                "            # Wait for elements",
                "            wait = WebDriverWait(self.driver, 10)",
                "            element = wait.until(",
                "                EC.presence_of_element_located((By.ID, 'example-element'))",
                "            )",
                ""
            ])

            if self.screenshots.isChecked():
                body.extend([
                    "            # Capture screenshot",
                    "            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')",
                    "            self.driver.save_screenshot(f'screenshot_{timestamp}.png')",
                    ""
                ])

            if self.assertions.isChecked():
                body.extend([
                    "            # Assertions",
                    "            assert self.driver.title == 'Expected Title'",
                    "            assert element.is_displayed(), 'Element should be visible'",
                    ""
                ])

        elif test_type == "API Test":
            body.extend([
                "            # Make API request",
                "            response = requests.get(",
                "                f'{self.base_url}/endpoint',",
                "                headers=self.headers",
                "            )",
                ""
            ])

            if self.assertions.isChecked():
                body.extend([
                    "            # Assertions",
                    "            assert response.status_code == 200",
                    "            data = response.json()",
                    "            assert data['status'] == 'success'",
                    ""
                ])

        # Add error handling closure if selected
        if self.error_handling.isChecked():
            body.extend([
                "        except Exception as e:",
                "            if self.logging.isChecked():",
                "                logger.error(f'Test failed: {str(e)}')",
                "            raise"
            ])

        # Combine all parts
        return "\n".join(imports + body)

    def generate_java_script(self, framework, test_type, class_name, method_name):
        """Generate Java test script"""
        if framework == "TestNG":
            template = self.get_testng_template(test_type, class_name, method_name)
        elif framework == "JUnit":
            template = self.get_junit_template(test_type, class_name, method_name)
        else:
            template = f"// Template not yet implemented for Java {framework}"
        return template

    def get_testng_template(self, test_type, class_name, method_name):
        imports = [
            "package com.example.tests;",
            "",
            "import org.testng.annotations.*;",
            "import org.testng.Assert;"
        ]

        if test_type == "UI Test":
            imports.extend([
                "import org.openqa.selenium.WebDriver;",
                "import org.openqa.selenium.By;",
                "import org.openqa.selenium.chrome.ChromeDriver;",
                "import org.openqa.selenium.support.ui.WebDriverWait;",
                "import org.openqa.selenium.support.ui.ExpectedConditions;",
                "import java.time.Duration;"
            ])
        elif test_type == "API Test":
            imports.extend([
                "import io.restassured.RestAssured;",
                "import io.restassured.response.Response;",
                "import io.restassured.http.ContentType;"
            ])

        if self.logging.isChecked():
            imports.append("import java.util.logging.Logger;")

        class_def = [
            "",
            f"public class {class_name} {{",
        ]

        if test_type == "UI Test":
            class_def.extend([
                "    private WebDriver driver;",
                "    private WebDriverWait wait;"
            ])

        if self.logging.isChecked():
            class_def.append("    private static final Logger logger = Logger.getLogger(Test.class.getName());")

        # Add more implementation details here...

        return "\n".join(imports + class_def)

    def generate_javascript_script(self, framework, test_type, class_name, method_name):
        """Generate JavaScript test script"""
        if framework == "Jest":
            template = self.get_jest_template(test_type, class_name, method_name)
        elif framework == "Mocha":
            template = self.get_mocha_template(test_type, class_name, method_name)
        else:
            template = f"// Template not yet implemented for JavaScript {framework}"
        return template

    def preview_script(self):
        """Show script preview in new window"""
        preview = QMainWindow(self)
        preview.setWindowTitle("Script Preview")
        preview.setGeometry(200, 200, 800, 600)

        preview_text = QTextEdit()
        preview_text.setFont(QFont("Courier", 10))
        preview_text.setPlainText(self.output_area.toPlainText())
        preview_text.setReadOnly(True)

        preview.setCentralWidget(preview_text)
        preview.show()

    def copy_to_clipboard(self):
        """Copy generated script to clipboard"""
        QApplication.clipboard().setText(self.output_area.toPlainText())
        QMessageBox.information(self, "Success", "Script copied to clipboard!")

    def save_to_file(self):
        """Save generated script to file"""
        try:
            language = self.lang_combo.currentText().lower()
            extensions = {
                "python": ".py",
                "java": ".java",
                "javascript": ".js",
                "c#": ".cs",
                "ruby": ".rb",
                "typescript": ".ts"
            }

            ext = extensions.get(language, ".txt")
            class_name = self.class_name.currentText()

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Test Script",
                f"{class_name}{ext}",
                f"Source Files (*{ext});;All Files (*.*)"
            )

            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.output_area.toPlainText())
                QMessageBox.information(self, "Success", "File saved successfully!")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error saving file: {str(e)}")

    def clear_form(self):
        """Clear all form inputs"""
        self.output_area.clear()
        self.class_name.setCurrentText("")
        self.method_name.setCurrentText("")
        self.description.clear()

        checkboxes = [
            self.setup_teardown, self.assertions, self.logging,
            self.error_handling, self.comments, self.reporting,
            self.parallel_execution, self.data_driven,
            self.retry_mechanism, self.screenshots
        ]
        for checkbox in checkboxes:
            checkbox.setChecked(False)

    def generate_csharp_script(self, framework, test_type, class_name, method_name):
        """Generate C# test script"""
        if framework == "NUnit":
            return self.get_nunit_template(test_type, class_name, method_name)
        elif framework == "MSTest":
            return self.get_mstest_template(test_type, class_name, method_name)
        elif framework == "xUnit":
            return self.get_xunit_template(test_type, class_name, method_name)
        else:
            return f"// Template not yet implemented for C# {framework}"

    def get_nunit_template(self, test_type, class_name, method_name):
        imports = [
            "using NUnit.Framework;",
            "using System;"
        ]

        if test_type == "UI Test":
            imports.extend([
                "using OpenQA.Selenium;",
                "using OpenQA.Selenium.Chrome;",
                "using OpenQA.Selenium.Support.UI;"
            ])
        elif test_type == "API Test":
            imports.extend([
                "using System.Net.Http;",
                "using System.Threading.Tasks;",
                "using Newtonsoft.Json;"
            ])

        if self.logging.isChecked():
            imports.append("using NLog;")

        body = [
            "",
            "namespace TestProject",
            "{",
            "    [TestFixture]",
            f"    public class {class_name}",
            "    {"
        ]

        if self.logging.isChecked():
            body.append("        private static readonly ILogger Logger = LogManager.GetCurrentClassLogger();")

        if test_type == "UI Test":
            body.append("        private IWebDriver driver;")
            body.append("        private WebDriverWait wait;")

        if self.setup_teardown.isChecked():
            body.extend([
                "",
                "        [SetUp]",
                "        public void Setup()",
                "        {",
                "            driver = new ChromeDriver();",
                "            wait = new WebDriverWait(driver, TimeSpan.FromSeconds(10));",
                "        }",
                "",
                "        [TearDown]",
                "        public void Teardown()",
                "        {",
                "            driver?.Quit();",
                "        }"
            ])

        # Add test method
        body.extend([
            "",
            "        [Test]",
            f"        public void {method_name}()",
            "        {"
        ])

        if self.error_handling.isChecked():
            body.append("            try")
            body.append("            {")

        if test_type == "UI Test":
            body.extend([
                "                driver.Navigate().GoToUrl(\"https://example.com\");",
                "",
                "                // Wait for elements",
                "                var element = wait.Until(ExpectedConditions.ElementExists(By.Id(\"example-element\")));"
            ])

            if self.assertions.isChecked():
                body.extend([
                    "",
                    "                // Assertions",
                    "                Assert.That(element.Displayed, Is.True, \"Element should be visible\");",
                    "                Assert.That(driver.Title, Is.EqualTo(\"Expected Title\"));"
                ])

        elif test_type == "API Test":
            body.extend([
                "                using (var client = new HttpClient())",
                "                {",
                "                    var response = await client.GetAsync(\"https://api.example.com\");",
                "                    var content = await response.Content.ReadAsStringAsync();",
                "",
                "                    // Assertions",
                "                    Assert.That(response.IsSuccessStatusCode, Is.True);",
                "                    Assert.That(content, Does.Contain(\"expected content\"));",
                "                }"
            ])

        if self.error_handling.isChecked():
            body.extend([
                "            }",
                "            catch (Exception ex)",
                "            {",
                "                Logger.Error(ex, \"Test failed\");",
                "                throw;",
                "            }"
            ])

        body.extend([
            "        }",
            "    }",
            "}"
        ])

        return "\n".join(imports + body)

    def get_mstest_template(self, test_type, class_name, method_name):
        imports = [
            "using Microsoft.VisualStudio.TestTools.UnitTesting;",
            "using System;"
        ]

        if test_type == "UI Test":
            imports.extend([
                "using OpenQA.Selenium;",
                "using OpenQA.Selenium.Chrome;",
                "using OpenQA.Selenium.Support.UI;"
            ])

        body = [
            "",
            "namespace TestProject",
            "{",
            "    [TestClass]",
            f"    public class {class_name}",
            "    {"
        ]

        # Add similar implementation as NUnit but with MSTest attributes
        # [TestInitialize] instead of [SetUp]
        # [TestCleanup] instead of [TearDown]
        # [TestMethod] instead of [Test]

        body.extend([
            "    }",
            "}"
        ])

        return "\n".join(imports + body)

    def generate_ruby_script(self, framework, test_type, class_name, method_name):
        """Generate Ruby test script"""
        if framework == "RSpec":
            return self.get_rspec_template(test_type, class_name, method_name)
        elif framework == "Cucumber":
            return self.get_cucumber_template(test_type, class_name, method_name)
        else:
            return "# Template not yet implemented for Ruby #{framework}"

    def get_rspec_template(self, test_type, class_name, method_name):
        script = [
            "require 'spec_helper'",
        ]

        if test_type == "UI Test":
            script.extend([
                "require 'selenium-webdriver'",
                "require 'capybara/rspec'"
            ])
        elif test_type == "API Test":
            script.append("require 'rest-client'")

        script.extend([
            "",
            f"RSpec.describe '{class_name}' do",
            f"  describe '#{method_name}' do"
        ])

        if test_type == "UI Test":
            script.extend([
                "    let(:driver) { Selenium::WebDriver.for :chrome }",
                "",
                "    before do",
                "      driver.get('https://example.com')",
                "    end",
                "",
                "    after do",
                "      driver.quit",
                "    end",
                "",
                "    it 'performs the test' do",
                "      expect(driver.title).to eq('Expected Title')",
                "    end"
            ])
        elif test_type == "API Test":
            script.extend([
                "    it 'performs the API test' do",
                "      response = RestClient.get('https://api.example.com')",
                "      expect(response.code).to eq(200)",
                "      expect(JSON.parse(response.body)['status']).to eq('success')",
                "    end"
            ])

        script.extend([
            "  end",
            "end"
        ])

        return "\n".join(script)

    def generate_typescript_script(self, framework, test_type, class_name, method_name):
        """Generate TypeScript test script"""
        if framework == "Jest":
            return self.get_typescript_jest_template(test_type, class_name, method_name)
        elif framework == "Mocha":
            return self.get_typescript_mocha_template(test_type, class_name, method_name)
        else:
            return "// Template not yet implemented for TypeScript #{framework}"

    def get_typescript_jest_template(self, test_type, class_name, method_name):
        imports = ["import { test, expect } from '@jest/globals';"]

        if test_type == "UI Test":
            imports.extend([
                "import { Builder, By, until, WebDriver } from 'selenium-webdriver';",
                "import { Options } from 'selenium-webdriver/chrome';"
            ])
        elif test_type == "API Test":
            imports.append("import axios from 'axios';")

        script = [
            "",
            f"describe('{class_name}', () => {{",
            "    let driver: WebDriver;" if test_type == "UI Test" else ""
        ]

        if test_type == "UI Test":
            script.extend([
                "",
                "    beforeEach(async () => {",
                "        driver = await new Builder()",
                "            .forBrowser('chrome')",
                "            .build();",
                "    });",
                "",
                "    afterEach(async () => {",
                "        await driver?.quit();",
                "    });",
                "",
                f"    test('{method_name}', async () => {{",
                "        await driver.get('https://example.com');",
                "        const element = await driver.findElement(By.id('example'));",
                "        expect(await element.isDisplayed()).toBe(true);",
                "    });"
            ])
        elif test_type == "API Test":
            script.extend([
                "",
                f"    test('{method_name}', async () => {{",
                "        const response = await axios.get('https://api.example.com');",
                "        expect(response.status).toBe(200);",
                "        expect(response.data.status).toBe('success');",
                "    });"
            ])

        script.extend([
            "});",
            ""
        ])

        return "\n".join(imports + script)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TestScriptGenerator()
    window.show()
    sys.exit(app.exec_())