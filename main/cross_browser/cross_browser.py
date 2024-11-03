import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QCheckBox, QHBoxLayout, QMessageBox, QFileDialog
)


class CrossBrowserTestGenerator(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Cross-Browser and Platform Test Script Generator")
        self.setGeometry(100, 100, 800, 600)

        # Layout
        layout = QVBoxLayout()

        # Test Scenario Input
        layout.addWidget(QLabel("Define Test Scenario (Steps):"))
        self.test_scenario_input = QTextEdit()
        layout.addWidget(self.test_scenario_input)

        # Browser Selection
        layout.addWidget(QLabel("Select Browsers:"))
        self.chrome_check = QCheckBox("Chrome")
        self.firefox_check = QCheckBox("Firefox")
        self.safari_check = QCheckBox("Safari")
        self.edge_check = QCheckBox("Edge")

        browser_layout = QHBoxLayout()
        browser_layout.addWidget(self.chrome_check)
        browser_layout.addWidget(self.firefox_check)
        browser_layout.addWidget(self.safari_check)
        browser_layout.addWidget(self.edge_check)
        layout.addLayout(browser_layout)

        # Platform Selection
        layout.addWidget(QLabel("Select Platforms:"))
        self.windows_check = QCheckBox("Windows")
        self.mac_check = QCheckBox("macOS")
        self.linux_check = QCheckBox("Linux")

        platform_layout = QHBoxLayout()
        platform_layout.addWidget(self.windows_check)
        platform_layout.addWidget(self.mac_check)
        platform_layout.addWidget(self.linux_check)
        layout.addLayout(platform_layout)

        # Generate Script Button
        self.generate_button = QPushButton("Generate Test Scripts")
        self.generate_button.clicked.connect(self.generate_test_scripts)
        layout.addWidget(self.generate_button)

        # Result Display
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(False)
        layout.addWidget(QLabel("Generated Test Scripts:"))
        layout.addWidget(self.result_display)

        # Save Button
        self.save_button = QPushButton("Save Test Scripts")
        self.save_button.clicked.connect(self.save_scripts)
        layout.addWidget(self.save_button)

        # Set layout
        self.setLayout(layout)

    def generate_test_scripts(self):
        # Collect selected browsers and platforms
        selected_browsers = []
        if self.chrome_check.isChecked():
            selected_browsers.append("Chrome")
        if self.firefox_check.isChecked():
            selected_browsers.append("Firefox")
        if self.safari_check.isChecked():
            selected_browsers.append("Safari")
        if self.edge_check.isChecked():
            selected_browsers.append("Edge")

        selected_platforms = []
        if self.windows_check.isChecked():
            selected_platforms.append("Windows")
        if self.mac_check.isChecked():
            selected_platforms.append("macOS")
        if self.linux_check.isChecked():
            selected_platforms.append("Linux")

        if not selected_browsers or not selected_platforms:
            QMessageBox.warning(self, "Selection Error", "Please select at least one browser and one platform.")
            return

        # Generate test scenario
        test_scenario = self.test_scenario_input.toPlainText()
        if not test_scenario:
            QMessageBox.warning(self, "Input Error", "Please define a test scenario.")
            return

        # Generate test scripts for each combination
        generated_scripts = ""
        for browser in selected_browsers:
            for platform in selected_platforms:
                script = self.create_test_script(browser, platform, test_scenario)
                generated_scripts += f"### {browser} on {platform} ###\n{script}\n\n"

        self.result_display.setText(generated_scripts)

    def create_test_script(self, browser, platform, test_scenario):
        """
        Generate a Selenium script for the specified browser and platform.
        """
        # Placeholder for actual Selenium WebDriver initialization code
        driver_setup = ""
        if browser == "Chrome":
            driver_setup = "driver = webdriver.Chrome()"
        elif browser == "Firefox":
            driver_setup = "driver = webdriver.Firefox()"
        elif browser == "Safari":
            driver_setup = "driver = webdriver.Safari()"
        elif browser == "Edge":
            driver_setup = "driver = webdriver.Edge()"

        # Starting test script
        script = f"""from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

# Setup WebDriver for {browser} on {platform}
{driver_setup}

# Test Scenario
try:
"""

        # Convert test scenario steps into Selenium commands
        for line in test_scenario.splitlines():
            if "open" in line.lower():
                url = line.split(" ")[-1]
                script += f"    driver.get('{url}')\n"
            elif "click" in line.lower():
                element = line.split(" ")[-1]
                script += f"    driver.find_element(By.ID, '{element}').click()\n"
            elif "type" in line.lower():
                parts = line.split(" ")
                element = parts[-2]
                text = parts[-1]
                script += f"    driver.find_element(By.ID, '{element}').send_keys('{text}')\n"
            elif "wait" in line.lower():
                seconds = line.split(" ")[-1]
                script += f"    time.sleep({seconds})\n"
            elif "assert" in line.lower():
                text = " ".join(line.split(" ")[1:])
                script += f"    assert '{text}' in driver.page_source\n"

        # Close and quit the driver
        script += """finally:
    driver.quit()
"""

        return script

    def save_scripts(self):
        # Get generated scripts
        generated_scripts = self.result_display.toPlainText()
        if not generated_scripts:
            QMessageBox.warning(self, "Save Error", "No scripts to save.")
            return

        # Save scripts to a file
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Test Scripts", "", "Python Files (*.py)")
        if file_path:
            with open(file_path, "w") as script_file:
                script_file.write(generated_scripts)
            QMessageBox.information(self, "Save Successful", "Test scripts saved successfully.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CrossBrowserTestGenerator()
    window.show()
    sys.exit(app.exec_())
