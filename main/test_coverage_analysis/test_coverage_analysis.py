import sys
import os
import ast

import pytest
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QTextEdit, QLabel,
                             QFileDialog, QTreeWidget, QTreeWidgetItem, QGroupBox,
                             QProgressBar, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
import coverage
import radon.complexity as radon
from typing import Dict, List
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO


class TestCoverageAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Coverage Analyzer")
        self.setGeometry(100, 100, 1400, 800)
        self.setup_ui()

        # Initialize analysis results
        self.coverage_data = None
        self.code_analysis = None
        self.test_analysis = None

    def setup_ui(self):
        """Setup the main user interface"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()

        # Create top section with file selection
        top_layout = QHBoxLayout()

        # Source code section
        source_group = QGroupBox("Source Code")
        source_layout = QVBoxLayout()
        self.source_path_label = QLabel("No source directory selected")
        select_source_btn = QPushButton("Select Source Directory")
        select_source_btn.clicked.connect(self.select_source_directory)
        source_layout.addWidget(self.source_path_label)
        source_layout.addWidget(select_source_btn)
        source_group.setLayout(source_layout)

        # Test code section
        test_group = QGroupBox("Test Code")
        test_layout = QVBoxLayout()
        self.test_path_label = QLabel("No test directory selected")
        select_test_btn = QPushButton("Select Test Directory")
        select_test_btn.clicked.connect(self.select_test_directory)
        test_layout.addWidget(self.test_path_label)
        test_layout.addWidget(select_test_btn)
        test_group.setLayout(test_layout)

        # Analysis options
        analysis_group = QGroupBox("Analysis Options")
        analysis_layout = QVBoxLayout()
        analyze_btn = QPushButton("Analyze Coverage")
        analyze_btn.clicked.connect(self.analyze_coverage)
        export_btn = QPushButton("Export Report")
        export_btn.clicked.connect(self.export_report)
        analysis_layout.addWidget(analyze_btn)
        analysis_layout.addWidget(export_btn)
        analysis_group.setLayout(analysis_layout)

        top_layout.addWidget(source_group)
        top_layout.addWidget(test_group)
        top_layout.addWidget(analysis_group)

        # Create progress bar
        self.progress_bar = QProgressBar()

        # Create results section
        results_layout = QHBoxLayout()

        # Coverage tree
        coverage_group = QGroupBox("Coverage Analysis")
        coverage_layout = QVBoxLayout()
        self.coverage_tree = QTreeWidget()
        self.coverage_tree.setHeaderLabels(["File/Function", "Coverage %", "Missing Lines"])
        coverage_layout.addWidget(self.coverage_tree)
        coverage_group.setLayout(coverage_layout)

        # Metrics section
        metrics_group = QGroupBox("Code Metrics")
        metrics_layout = QVBoxLayout()
        self.metrics_text = QTextEdit()
        self.metrics_text.setReadOnly(True)
        metrics_layout.addWidget(self.metrics_text)
        metrics_group.setLayout(metrics_layout)

        results_layout.addWidget(coverage_group)
        results_layout.addWidget(metrics_group)

        # Add suggestions section
        suggestions_group = QGroupBox("Test Suggestions")
        suggestions_layout = QVBoxLayout()
        self.suggestions_text = QTextEdit()
        self.suggestions_text.setReadOnly(True)
        suggestions_layout.addWidget(self.suggestions_text)
        suggestions_group.setLayout(suggestions_layout)

        # Add all components to main layout
        layout.addLayout(top_layout)
        layout.addWidget(self.progress_bar)
        layout.addLayout(results_layout)
        layout.addWidget(suggestions_group)

        main_widget.setLayout(layout)

    def select_source_directory(self):
        """Select source code directory"""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Source Code Directory")
        if dir_path:
            self.source_path_label.setText(dir_path)

    def select_test_directory(self):
        """Select test code directory"""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Test Directory")
        if dir_path:
            self.test_path_label.setText(dir_path)

    def analyze_coverage(self):
        """Perform coverage analysis"""
        source_path = self.source_path_label.text()
        test_path = self.test_path_label.text()

        if source_path == "No source directory selected" or test_path == "No test directory selected":
            QMessageBox.warning(self, "Error", "Please select both source and test directories")
            return

        try:
            self.progress_bar.setValue(0)

            # Validate directories
            if not os.path.exists(source_path) or not os.path.exists(test_path):
                raise Exception("Invalid directory path")

            # Check for Python files
            if not any(f.endswith('.py') for f in os.listdir(source_path)):
                raise Exception("No Python files found in source directory")

            if not any(f.endswith('.py') for f in os.listdir(test_path)):
                raise Exception("No Python test files found in test directory")

            # Run coverage analysis
            self.progress_bar.setValue(20)
            self.coverage_data = self.run_coverage_analysis(source_path, test_path)

            # Analyze code complexity
            self.progress_bar.setValue(40)
            self.code_analysis = self.analyze_code_complexity(source_path)

            # Analyze test code
            self.progress_bar.setValue(60)
            self.test_analysis = self.analyze_test_code(test_path)

            # Update UI with results
            self.progress_bar.setValue(80)
            self.update_coverage_tree()
            self.update_metrics()
            self.generate_suggestions()

            self.progress_bar.setValue(100)
            QMessageBox.information(self, "Success", "Analysis completed successfully!")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Analysis failed: {str(e)}")
            self.progress_bar.setValue(0)

    def run_coverage_analysis(self, source_path: str, test_path: str) -> Dict:
        """Run coverage analysis on the code"""
        try:
            # Initialize coverage with source and test directories
            cov = coverage.Coverage(source=[source_path], omit=[test_path + "/*"])

            # Start collecting coverage data
            cov.start()

            # Run tests using pytest
            pytest.main([test_path])

            # Stop coverage collection
            cov.stop()

            # Save coverage data
            cov.save()

            # Create analysis results dictionary
            results = {}

            # Analyze each file
            for filename in cov.get_data().measured_files():
                analysis = cov.analysis(filename)
                missing_lines = list(analysis[3])  # Get missing lines

                # Calculate coverage percentage
                total_lines = len(analysis[1])  # executed + missing lines
                executed_lines = total_lines - len(missing_lines)
                coverage_percentage = (executed_lines / total_lines * 100) if total_lines > 0 else 0

                results[filename] = {
                    'coverage': coverage_percentage,
                    'missing_lines': missing_lines,
                    'executed_lines': list(analysis[1]),
                    'excluded_lines': list(analysis[2])
                }

            return results

        except Exception as e:
            raise Exception(f"Coverage analysis failed: {str(e)}")

    def analyze_code_complexity(self, source_path: str) -> Dict:
        """Analyze code complexity with proper error handling"""
        results = {}
        try:
            for root, _, files in os.walk(source_path):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                code = f.read()

                            # Initialize with default values
                            results[file_path] = {
                                'complexity': [],
                                'loc': 0,
                                'functions': []
                            }

                            # Update with actual values if available
                            if code.strip():  # Check if file is not empty
                                results[file_path].update({
                                    'complexity': radon.cc_visit(code),
                                    'loc': len(code.splitlines()),
                                    'functions': self.extract_functions(code)
                                })

                        except Exception as e:
                            print(f"Error analyzing {file_path}: {str(e)}")
                            results[file_path] = {
                                'complexity': [],
                                'loc': 0,
                                'functions': [],
                                'error': str(e)
                            }

            return results

        except Exception as e:
            raise Exception(f"Code complexity analysis failed: {str(e)}")

    def analyze_test_code(self, test_path: str) -> Dict:
        """Analyze test code with proper error handling"""
        results = {}
        try:
            for root, _, files in os.walk(test_path):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                code = f.read()

                            # Initialize with default values
                            results[file_path] = {
                                'test_count': 0,
                                'loc': 0,
                                'assertions': 0
                            }

                            # Update with actual values if available
                            if code.strip():  # Check if file is not empty
                                results[file_path].update({
                                    'test_count': self.count_tests(code),
                                    'loc': len(code.splitlines()),
                                    'assertions': self.count_assertions(code)
                                })

                        except Exception as e:
                            print(f"Error analyzing {file_path}: {str(e)}")
                            results[file_path] = {
                                'test_count': 0,
                                'loc': 0,
                                'assertions': 0,
                                'error': str(e)
                            }

            return results

        except Exception as e:
            raise Exception(f"Test code analysis failed: {str(e)}")

    def extract_functions(self, code: str) -> List[str]:
        """Extract function names from code"""
        try:
            tree = ast.parse(code)
            return [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        except:
            return []

    def count_tests(self, code: str) -> int:
        """Count number of test functions"""
        try:
            tree = ast.parse(code)
            return len([node for node in ast.walk(tree)
                        if isinstance(node, ast.FunctionDef)
                        and node.name.startswith('test_')])
        except:
            return 0

    def count_assertions(self, code: str) -> int:
        """Count number of assertions in test code"""
        try:
            tree = ast.parse(code)
            return len([node for node in ast.walk(tree)
                        if isinstance(node, ast.Assert) or
                        (isinstance(node, ast.Call) and
                         hasattr(node.func, 'attr') and
                         node.func.attr.startswith('assert_'))])
        except:
            return 0

    def update_coverage_tree(self):
        """Update the coverage tree with analysis results"""
        try:
            self.coverage_tree.clear()

            if not self.coverage_data:
                return

            for file_path, file_data in self.coverage_data.items():
                # Create file item
                file_item = QTreeWidgetItem(self.coverage_tree)
                file_name = os.path.basename(file_path)
                coverage_pct = file_data['coverage']

                # Set file item data
                file_item.setText(0, file_name)
                file_item.setText(1, f"{coverage_pct:.1f}%")
                file_item.setText(2, str(file_data['missing_lines']))

                # Color coding based on coverage
                if coverage_pct < 60:
                    file_item.setForeground(1, QColor('red'))
                elif coverage_pct < 80:
                    file_item.setForeground(1, QColor('orange'))
                else:
                    file_item.setForeground(1, QColor('green'))

                # Add function-level details if available
                if file_path in self.code_analysis:
                    for func_data in self.code_analysis[file_path]['complexity']:
                        func_item = QTreeWidgetItem(file_item)
                        func_item.setText(0, f"  {func_data.name}")

                        # Add complexity indicator
                        complexity = func_data.complexity
                        func_item.setText(1, f"Complexity: {complexity}")

                        # Color code based on complexity
                        if complexity > 10:
                            func_item.setForeground(1, QColor('red'))
                        elif complexity > 5:
                            func_item.setForeground(1, QColor('orange'))
                        else:
                            func_item.setForeground(1, QColor('green'))

            # Expand all items
            self.coverage_tree.expandAll()

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to update coverage tree: {str(e)}")

    def update_metrics(self):
        """Update metrics display with proper error handling"""
        try:
            metrics = []

            if not all([self.coverage_data, self.code_analysis, self.test_analysis]):
                self.metrics_text.setText("No analysis data available")
                return

            # Calculate overall metrics with safe division
            total_source_loc = sum(data['loc'] for data in self.code_analysis.values())
            total_test_loc = sum(data['loc'] for data in self.test_analysis.values())
            total_tests = sum(data['test_count'] for data in self.test_analysis.values())
            total_assertions = sum(data['assertions'] for data in self.test_analysis.values())

            # Overall coverage with safe division
            if self.coverage_data:
                total_coverage = sum(data['coverage'] for data in self.coverage_data.values()) / len(self.coverage_data)
            else:
                total_coverage = 0

            metrics.extend([
                "=== Overall Coverage Metrics ===",
                f"Overall Coverage: {total_coverage:.1f}%",
                f"Total Files Analyzed: {len(self.coverage_data)}",
                "",
                "=== Code Metrics ===",
                f"Total Source LOC: {total_source_loc}",
                f"Total Test LOC: {total_test_loc}"
            ])

            # Safe division for code to test ratio
            if total_source_loc > 0:
                metrics.append(f"Code to Test Ratio: 1:{total_test_loc / total_source_loc:.2f}")
            else:
                metrics.append("Code to Test Ratio: N/A (no source code)")

            metrics.extend([
                f"Total Test Cases: {total_tests}",
                f"Total Assertions: {total_assertions}"
            ])

            # Safe division for tests per LOC
            if total_source_loc > 0:
                metrics.append(f"Tests per Source LOC: {total_tests / total_source_loc:.3f}")
            else:
                metrics.append("Tests per Source LOC: N/A (no source code)")

            metrics.append("\n=== Complexity Metrics ===")

            # Add complexity metrics
            high_complexity_count = 0
            for file_path, data in self.code_analysis.items():
                file_name = os.path.basename(file_path)
                complexities = [cc.complexity for cc in data['complexity']]

                if complexities:
                    avg_complexity = sum(complexities) / len(complexities)
                    max_complexity = max(complexities)
                    high_complexity_count += sum(1 for c in complexities if c > 5)

                    metrics.extend([
                        f"\n{file_name}:",
                        f"  Average Complexity: {avg_complexity:.2f}",
                        f"  Maximum Complexity: {max_complexity}",
                        f"  Functions: {len(data['functions'])}"
                    ])
                else:
                    metrics.extend([
                        f"\n{file_name}:",
                        "  No complexity data available"
                    ])

            metrics.extend([
                "",
                "=== Risk Analysis ===",
                f"High Complexity Functions: {high_complexity_count}",
                f"Files Below 80% Coverage: {sum(1 for d in self.coverage_data.values() if d['coverage'] < 80)}"
            ])

            # Safe division for average assertions per test
            if total_tests > 0:
                metrics.append(f"Average Assertions per Test: {total_assertions / total_tests:.2f}")
            else:
                metrics.append("Average Assertions per Test: N/A (no tests)")

            self.metrics_text.setText("\n".join(metrics))

        except Exception as e:
            self.metrics_text.setText(f"Error updating metrics: {str(e)}")

    def generate_suggestions(self):
        """Generate test improvement suggestions with proper error handling"""
        try:
            suggestions = []

            if not all([self.coverage_data, self.code_analysis, self.test_analysis]):
                self.suggestions_text.setText("No analysis data available for generating suggestions")
                return

            # Analyze coverage gaps
            for file_path, file_data in self.coverage_data.items():
                if file_data['coverage'] < 80:
                    file_name = os.path.basename(file_path)
                    suggestions.append(f"Low coverage in {file_name} ({file_data['coverage']:.1f}%):")
                    suggestions.append(f"- Missing lines: {file_data['missing_lines']}")
                    suggestions.append("- Consider adding tests for these lines\n")

            # Analyze complexity vs test coverage
            for file_path, data in self.code_analysis.items():
                file_name = os.path.basename(file_path)
                complex_functions = [cc for cc in data['complexity'] if cc.complexity > 5]
                if complex_functions:
                    suggestions.append(f"Complex functions in {file_name}:")
                    for func in complex_functions:
                        suggestions.append(f"- {func.name} (complexity: {func.complexity})")
                    suggestions.append("- Consider breaking down complex functions")
                    suggestions.append("- Add more test cases for complex functions\n")

            # Analyze test patterns
            for test_file, data in self.test_analysis.items():
                file_name = os.path.basename(test_file)
                if data['test_count'] > 0:  # Avoid division by zero
                    assertions_per_test = data['assertions'] / data['test_count']
                    if assertions_per_test < 2:
                        suggestions.append(f"Low assertion count in {file_name}:")
                        suggestions.append(f"- Current: {assertions_per_test:.1f} assertions per test")
                        suggestions.append("- Recommended: At least 2 assertions per test")
                        suggestions.append("- Consider adding more assertions to verify different aspects\n")
                else:
                    suggestions.append(f"No tests found in {file_name}")
                    suggestions.append("- Consider adding test cases\n")

            # General suggestions based on metrics
            if not suggestions:
                suggestions.append("General suggestions:")
                suggestions.append("- Continue maintaining good test coverage")
                suggestions.append("- Regularly review and update tests")
                suggestions.append("- Consider adding integration tests")
                suggestions.append("- Document test cases and scenarios")

            self.suggestions_text.setText("\n".join(suggestions))

        except Exception as e:
            self.suggestions_text.setText(f"Error generating suggestions: {str(e)}")

    def export_report(self):
        """Export analysis report"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Report",
                "coverage_report.html",
                "HTML files (*.html);;All Files (*.*)"
            )

            if file_path:
                # Generate HTML report
                report = self.generate_html_report()

                with open(file_path, 'w') as f:
                    f.write(report)

                QMessageBox.information(self, "Success", "Report exported successfully!")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to export report: {str(e)}")

    def generate_html_report(self) -> str:
        """Generate HTML report with analysis results"""
        return f"""
        <html>
        <head>
            <title>Test Coverage Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2 {{ color: #333; }}
                .metrics {{ margin: 20px 0; }}
                .suggestions {{ background-color: #f0f0f0; padding: 10px; }}
            </style>
        </head>
        <body>
            <h1>Test Coverage Analysis Report</h1>

            <h2>Metrics</h2>
            <div class="metrics">
                {self.metrics_text.toPlainText().replace('\n', '<br>')}
            </div>

            <h2>Suggestions</h2>
            <div class="suggestions">
                {self.suggestions_text.toPlainText().replace('\n', '<br>')}
            </div>
        </body>
        </html>
        """


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TestCoverageAnalyzer()
    window.show()
    sys.exit(app.exec_())