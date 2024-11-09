import html
import sys
import json
import yaml
import random
import string
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTextEdit, QPushButton, QLabel,
                             QFileDialog, QMessageBox, QTreeWidget,
                             QTreeWidgetItem, QSplitter, QMenu)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QCursor
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

class TestCaseGenerator:
    @staticmethod
    def generate_string(min_length=1, max_length=10):
        length = random.randint(min_length, max_length)
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    @staticmethod
    def generate_number(minimum=0, maximum=100):
        if isinstance(minimum, float) or isinstance(maximum, float):
            return round(random.uniform(minimum, maximum), 2)
        return random.randint(minimum, maximum)

    @staticmethod
    def generate_boolean():
        return random.choice([True, False])

    @staticmethod
    def generate_date():
        return datetime.now().isoformat()

    @staticmethod
    def generate_value_for_type(schema):
        if not isinstance(schema, dict):
            return None

        schema_type = schema.get('type', 'string')

        if schema_type == 'string':
            if schema.get('format') == 'date-time':
                return TestCaseGenerator.generate_date()
            min_length = schema.get('minLength', 1)
            max_length = schema.get('maxLength', 10)
            return TestCaseGenerator.generate_string(min_length, max_length)

        elif schema_type == 'number' or schema_type == 'integer':
            minimum = schema.get('minimum', 0)
            maximum = schema.get('maximum', 100)
            return TestCaseGenerator.generate_number(minimum, maximum)

        elif schema_type == 'boolean':
            return TestCaseGenerator.generate_boolean()

        elif schema_type == 'array':
            items = []
            min_items = schema.get('minItems', 1)
            max_items = schema.get('maxItems', 3)
            num_items = random.randint(min_items, max_items)
            for _ in range(num_items):
                items.append(TestCaseGenerator.generate_value_for_type(schema.get('items', {})))
            return items

        elif schema_type == 'object':
            obj = {}
            for prop, prop_schema in schema.get('properties', {}).items():
                if 'required' not in schema or prop in schema.get('required', []):
                    obj[prop] = TestCaseGenerator.generate_value_for_type(prop_schema)
            return obj

        return None

    @staticmethod
    def get_test_explanation(test_case):
        """Generate human-readable explanation for a test case"""
        explanation = f"Test Case: {test_case['title']}\n\n"
        explanation += f"Description: {test_case['description']}\n"
        explanation += f"HTTP Method: {test_case['method']}\n"
        explanation += f"Endpoint: {test_case['path']}\n\n"

        # Explain request details
        explanation += "Request Details:\n"
        explanation += "- Headers:\n"
        for header, value in test_case['request'].get('headers', {}).items():
            explanation += f"  * {header}: {value}\n"

        if 'path_params' in test_case['request']:
            explanation += "- Path Parameters:\n"
            for param, value in test_case['request']['path_params'].items():
                explanation += f"  * {param}: {value}\n"

        if 'query_params' in test_case['request']:
            explanation += "- Query Parameters:\n"
            for param, value in test_case['request']['query_params'].items():
                explanation += f"  * {param}: {value}\n"

        if 'body' in test_case['request']:
            explanation += "- Request Body:\n"
            explanation += f"  {json.dumps(test_case['request']['body'], indent=2)}\n"

        explanation += f"\nExpected Response Status: {test_case['expected_status']}\n"

        # Add validation rules if present
        if 'validation_rules' in test_case:
            explanation += "\nValidation Rules:\n"
            for rule in test_case['validation_rules']:
                explanation += f"- {rule}\n"

        return explanation


class APITestGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("API Test Case Generator")
        self.setGeometry(100, 100, 1400, 800)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)  # Reduced margins

        # Header with minimal height
        header = QLabel("API Test Case Generator")
        header.setFont(QFont('Arial', 12, QFont.Bold))
        header.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        header.setFixedHeight(30)  # Fixed small height for header
        main_layout.addWidget(header)

        # Create horizontal splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Left Panel (Input)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins

        # Compact button layout
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(5, 0, 5, 5)  # Minimal margins

        load_btn = QPushButton("Load Swagger File")
        load_btn.clicked.connect(self.load_swagger_file)
        load_btn.setFixedHeight(30)  # Fixed height for buttons
        button_layout.addWidget(load_btn)

        validate_btn = QPushButton("Validate")
        validate_btn.clicked.connect(self.validate_input)
        validate_btn.setFixedHeight(30)
        button_layout.addWidget(validate_btn)

        generate_btn = QPushButton("Generate Test Cases")
        generate_btn.clicked.connect(self.generate_test_cases)
        generate_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        generate_btn.setFixedHeight(30)
        button_layout.addWidget(generate_btn)

        left_layout.addLayout(button_layout)

        # Swagger input
        self.swagger_input = QTextEdit()
        self.swagger_input.setPlaceholderText("Paste your Swagger/OpenAPI specification here...")
        self.swagger_input.setStyleSheet("font-family: monospace;")
        left_layout.addWidget(self.swagger_input)

        splitter.addWidget(left_panel)

        # Right Panel (Output)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins

        # Save button in compact layout
        # Save and BDD buttons layout
        save_layout = QHBoxLayout()
        save_layout.setContentsMargins(5, 0, 5, 5)

        save_btn = QPushButton("Save Test Cases")
        save_btn.clicked.connect(self.save_test_cases)
        save_btn.setFixedHeight(30)
        save_layout.addWidget(save_btn)

        bdd_btn = QPushButton("BDD Test Case Generator")
        bdd_btn.clicked.connect(self.generate_bdd_test_cases)
        bdd_btn.setFixedHeight(30)
        bdd_btn.setStyleSheet("background-color: #2196F3; color: white;")
        save_layout.addWidget(bdd_btn)

        export_bdd_btn = QPushButton("Export BDD Tests")
        export_bdd_btn.clicked.connect(self.save_bdd_test_cases)
        export_bdd_btn.setFixedHeight(30)
        export_bdd_btn.setStyleSheet("background-color: #FF9800; color: white;")
        save_layout.addWidget(export_bdd_btn)

        save_layout.addStretch()

        right_layout.addLayout(save_layout)

        # Test cases and details in vertical splitter
        vertical_splitter = QSplitter(Qt.Vertical)

        # Test Cases Tree
        self.test_tree = QTreeWidget()
        self.test_tree.setHeaderLabels(["Test Cases"])
        self.test_tree.itemClicked.connect(self.show_test_details)
        vertical_splitter.addWidget(self.test_tree)

        # Test Details
        self.test_details = QTextEdit()
        self.test_details.setReadOnly(True)
        self.test_details.setStyleSheet("font-family: monospace;")
        self.test_details.setPlaceholderText("Test case details will appear here...")
        vertical_splitter.addWidget(self.test_details)

        # Set initial sizes for vertical splitter (40% tree, 60% details)
        vertical_splitter.setSizes([400, 600])

        right_layout.addWidget(vertical_splitter)
        splitter.addWidget(right_panel)

        # Set initial sizes for horizontal splitter (40% input, 60% output)
        splitter.setSizes([560, 840])

        # Status bar
        self.statusBar().showMessage("Ready")

    def load_swagger_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open Swagger File",
            "",
            "YAML files (*.yaml *.yml);;JSON files (*.json);;All Files (*)"
        )
        if file_name:
            try:
                with open(file_name, 'r') as file:
                    if file_name.endswith(('.yaml', '.yml')):
                        content = yaml.safe_load(file)
                        self.swagger_input.setPlainText(yaml.dump(content, default_flow_style=False))
                    else:
                        content = json.load(file)
                        self.swagger_input.setPlainText(json.dumps(content, indent=2))
                self.statusBar().showMessage(f"Loaded: {file_name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading file: {str(e)}")

    def validate_input(self):
        try:
            swagger_text = self.swagger_input.toPlainText()
            if swagger_text:
                try:
                    yaml.safe_load(swagger_text)
                except:
                    json.loads(swagger_text)
                self.statusBar().showMessage("Validation successful")
                QMessageBox.information(self, "Success", "API specification is valid!")
            else:
                raise ValueError("Please provide API specification")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Invalid input: {str(e)}")

    def generate_test_cases(self):
        try:
            swagger_text = self.swagger_input.toPlainText()
            if not swagger_text:
                QMessageBox.warning(self, "Warning", "Please provide API specification")
                return

            # Parse specification
            try:
                spec = yaml.safe_load(swagger_text)
            except:
                spec = json.loads(swagger_text)

            test_cases = []

            # Generate test cases for each path and method
            for path, path_item in spec.get('paths', {}).items():
                for method, operation in path_item.items():
                    if method.lower() not in ['get', 'post', 'put', 'delete', 'patch']:
                        continue

                    # Generate basic positive test
                    test_case = self.generate_positive_test(path, method, operation)
                    test_cases.append(test_case)

                    # Generate negative tests
                    test_cases.extend(self.generate_negative_tests(path, method, operation))

                    # Generate edge cases
                    test_cases.extend(self.generate_edge_cases(path, method, operation))

            # Update tree view
            self.update_test_tree(test_cases)
            self.statusBar().showMessage(f"Generated {len(test_cases)} test cases")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error generating test cases: {str(e)}")

    def generate_positive_test(self, path, method, operation):
        """Generate a positive test case"""
        return {
            'title': f"{method.upper()} {path} - Positive Test",
            'description': operation.get('summary', ''),
            'method': method.upper(),
            'path': path,
            'request': {
                'headers': {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            },
            'expected_status': list(operation.get('responses', {'200': None}).keys())[0]
        }

    def generate_negative_tests(self, path, method, operation):
        """Generate negative test cases"""
        negative_tests = []

        # Invalid auth test
        negative_tests.append({
            'title': f"{method.upper()} {path} - Invalid Authentication",
            'description': "Test with invalid authentication token",
            'method': method.upper(),
            'path': path,
            'request': {
                'headers': {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Authorization': 'Invalid-Token'
                }
            },
            'expected_status': '401'
        })

        # Missing required fields test
        if 'requestBody' in operation:
            negative_tests.append({
                'title': f"{method.upper()} {path} - Missing Required Fields",
                'description': "Test with missing required fields in request body",
                'method': method.upper(),
                'path': path,
                'request': {
                    'headers': {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    'body': {}
                },
                'expected_status': '400'
            })

        return negative_tests

    def generate_edge_cases(self, path, method, operation):
        """Generate edge case test cases"""
        edge_cases = []

        # Large payload test
        if method.lower() in ['post', 'put', 'patch']:
            edge_cases.append({
                'title': f"{method.upper()} {path} - Large Payload",
                'description': "Test with large request payload",
                'method': method.upper(),
                'path': path,
                'request': {
                    'headers': {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    'body': {
                        'data': 'x' * 1000  # Large string
                    }
                },
                'expected_status': '413'
            })

        # Rate limiting test
        edge_cases.append({
            'title': f"{method.upper()} {path} - Rate Limiting",
            'description': "Test rate limiting behavior",
            'method': method.upper(),
            'path': path,
            'request': {
                'headers': {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            },
            'expected_status': '429'
        })

        return edge_cases

    def update_test_tree(self, test_cases):
        """Update the tree view with generated test cases"""
        self.test_tree.clear()

        # Group by endpoint
        endpoints = {}
        for test in test_cases:
            endpoint = f"{test['method']} {test['path']}"
            if endpoint not in endpoints:
                endpoints[endpoint] = []
            endpoints[endpoint].append(test)

        # Add to tree
        for endpoint, tests in endpoints.items():
            endpoint_item = QTreeWidgetItem([endpoint])
            self.test_tree.addTopLevelItem(endpoint_item)

            for test in tests:
                test_item = QTreeWidgetItem([test['title']])
                test_item.setData(0, Qt.UserRole, test)
                endpoint_item.addChild(test_item)

        self.test_tree.expandAll()

    def show_test_explanation(self, item):
        test_case = item.data(0, Qt.UserRole)
        if test_case:
            # Show explanation
            explanation = TestCaseGenerator.get_test_explanation(test_case)
            self.explanation_text.setPlainText(explanation)

            # Show preview in JSON format
            self.preview_text.setPlainText(json.dumps(test_case, indent=2))

    def show_test_details(self, item):
        """Show details of selected test case"""
        test_case = item.data(0, Qt.UserRole)
        if test_case:
            formatted_details = json.dumps(test_case, indent=2)
            self.test_details.setPlainText(formatted_details)

    def save_test_cases(self):
        """Save generated test cases to file"""
        if self.test_tree.topLevelItemCount() == 0:
            QMessageBox.warning(self, "Warning", "No test cases to save!")
            return

        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Test Cases",
            "",
            "JSON files (*.json);;All Files (*)"
        )
        if file_name:
            try:
                test_cases = []
                for i in range(self.test_tree.topLevelItemCount()):
                    endpoint_item = self.test_tree.topLevelItem(i)
                    for j in range(endpoint_item.childCount()):
                        case_item = endpoint_item.child(j)
                        test_case = case_item.data(0, Qt.UserRole)
                        if test_case:
                            test_cases.append(test_case)

                with open(file_name, 'w') as file:
                    json.dump({'test_cases': test_cases}, file, indent=2)

                self.statusBar().showMessage(f"Saved test cases to: {file_name}")
                QMessageBox.information(self, "Success", "Test cases saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving file: {str(e)}")

    def generate_bdd_test_cases(self):
        """Generate BDD format test cases from existing test cases"""
        if self.test_tree.topLevelItemCount() == 0:
            QMessageBox.warning(self, "Warning", "No test cases available to convert to BDD format!")
            return

        bdd_output = "Feature: API Testing Scenarios\n\n"

        # Collect all test cases from tree
        for i in range(self.test_tree.topLevelItemCount()):
            endpoint_item = self.test_tree.topLevelItem(i)
            bdd_output += f"  # Tests for {endpoint_item.text(0)}\n"

            for j in range(endpoint_item.childCount()):
                case_item = endpoint_item.child(j)
                test_case = case_item.data(0, Qt.UserRole)
                if test_case:
                    # Generate BDD scenario
                    bdd_output += self.create_bdd_scenario(test_case)
                    bdd_output += "\n"

        # Display BDD test cases in the details area
        self.test_details.setPlainText(bdd_output)
        self.statusBar().showMessage("BDD test cases generated successfully")

    def create_bdd_scenario(self, test_case):
        """Convert a test case to BDD format"""
        scenario = f"  Scenario: {test_case['title']}\n"
        scenario += f"    # {test_case['description']}\n\n"

        # Given - Setup
        scenario += "    Given the API endpoint is available\n"

        # Add headers
        headers = test_case['request'].get('headers', {})
        for header, value in headers.items():
            scenario += f"    And the request header {header} is set to '{value}'\n"

        # Add path parameters
        path_params = test_case['request'].get('path_params', {})
        for param, value in path_params.items():
            scenario += f"    And the path parameter {param} is set to '{value}'\n"

        # Add query parameters
        query_params = test_case['request'].get('query_params', {})
        for param, value in query_params.items():
            scenario += f"    And the query parameter {param} is set to '{value}'\n"

        # Add request body
        body = test_case['request'].get('body', {})
        if body:
            scenario += f"    And the request body is:\n"
            scenario += f"      \"\"\"\n"
            scenario += f"      {json.dumps(body, indent=6)}\n"
            scenario += f"      \"\"\"\n"

        # When - Action
        scenario += f"    When a {test_case['method']} request is sent to '{test_case['path']}'\n"

        # Then - Assertion
        scenario += f"    Then the response status code should be {test_case['expected_status']}\n"

        # Add validation rules if present
        if 'validation_rules' in test_case:
            for rule in test_case['validation_rules']:
                scenario += f"    And {rule}\n"

        return scenario

    def generate_auth_tests(self, path, method, operation):
        # Implementation for authentication test cases
        test_cases = []
        # ... (implement auth test case generation)
        return test_cases

    def save_bdd_test_cases(self):
        """Save BDD test cases to different formats"""
        if not self.test_details.toPlainText():
            QMessageBox.warning(self, "Warning", "No BDD test cases to save!")
            return

        # Create menu for export options
        export_menu = QMenu(self)

        # Add export options
        feature_file = export_menu.addAction("Export as Feature File (.feature)")
        jenkins_file = export_menu.addAction("Export as Jenkins File (Jenkinsfile)")
        html_report = export_menu.addAction("Export as HTML Report")

        # Show menu and get selected action
        action = export_menu.exec_(QCursor.pos())

        if action == feature_file:
            self.save_as_feature_file()
        elif action == jenkins_file:
            self.save_as_jenkins_file()
        elif action == html_report:
            self.save_as_html_report()

    def save_as_feature_file(self):
        """Save BDD tests as Cucumber feature file"""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Feature File",
            "",
            "Feature files (*.feature);;All Files (*)"
        )
        if file_name:
            try:
                with open(file_name, 'w') as file:
                    file.write(self.test_details.toPlainText())
                QMessageBox.information(self, "Success", "Feature file saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving feature file: {str(e)}")

    def save_as_jenkins_file(self):
        """Save BDD tests as Jenkinsfile with pipeline configuration"""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Jenkinsfile",
            "Jenkinsfile",
            "All Files (*)"
        )
        if file_name:
            try:
                jenkins_content = """pipeline {
        agent any

        stages {
            stage('Checkout') {
                steps {
                    checkout scm
                }
            }

            stage('Install Dependencies') {
                steps {
                    sh 'pip install -r requirements.txt'
                }
            }

            stage('Run BDD Tests') {
                steps {
                    sh 'behave features/'
                }
            }
        }

        post {
            always {
                cucumber '**/cucumber-reports/*.json'
            }
        }
    }

    // BDD Test Scenarios
    """.format(self.test_details.toPlainText())

                with open(file_name, 'w') as file:
                    file.write(jenkins_content)
                QMessageBox.information(self, "Success", "Jenkinsfile saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving Jenkinsfile: {str(e)}")

    def save_as_html_report(self):
        """Save BDD tests as HTML report"""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save HTML Report",
            "",
            "HTML files (*.html);;All Files (*)"
        )
        if file_name:
            try:
                bdd_content = self.test_details.toPlainText()
                html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>BDD Test Cases Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                background-color: white;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .feature {{
                margin-bottom: 20px;
            }}
            .scenario {{
                margin: 10px 0;
                padding: 10px;
                background-color: #f8f9fa;
                border-left: 4px solid #4CAF50;
            }}
            .step {{
                margin: 5px 0;
                padding: 5px 0;
            }}
            .given {{
                color: #2196F3;
            }}
            .when {{
                color: #FF9800;
            }}
            .then {{
                color: #4CAF50;
            }}
            pre {{
                background-color: #f8f9fa;
                padding: 10px;
                border-radius: 4px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>BDD Test Cases Report</h1>
            <div class="feature">
                <pre>{html.escape(bdd_content)}</pre>
            </div>
        </div>
    </body>
    </html>
    """
                with open(file_name, 'w') as file:
                    file.write(html_content)
                QMessageBox.information(self, "Success", "HTML report saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving HTML report: {str(e)}")
    
def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Optional: Set application-wide stylesheet for consistent look
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f5f5f5;
        }
        QTreeWidget {
            border: 1px solid #cccccc;
        }
        QTextEdit {
            border: 1px solid #cccccc;
        }
        QPushButton {
            padding: 5px 10px;
            border: 1px solid #cccccc;
            border-radius: 2px;
        }
        QPushButton:hover {
            background-color: #e0e0e0;
        }
    """)

    window = APITestGenerator()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()