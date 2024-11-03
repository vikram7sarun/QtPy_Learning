import sys
import sqlite3
from datetime import datetime
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem, QTabWidget,
    QToolBox, QHBoxLayout, QRadioButton, QSizePolicy
)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


# Database setup functions
def init_db():
    conn = sqlite3.connect("locators.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS locators (
                        element_name TEXT PRIMARY KEY,
                        locator_type TEXT,
                        locator_value TEXT,
                        last_healed TEXT)''')
    conn.commit()
    conn.close()


# Update database and refresh the UI function
def update_locator_in_db(element_name, locator_type, locator_value, ui_reference):
    conn = sqlite3.connect("locators.db")
    cursor = conn.cursor()
    cursor.execute(
        "REPLACE INTO locators (element_name, locator_type, locator_value, last_healed) VALUES (?, ?, ?, datetime('now'))",
        (element_name, locator_type, locator_value)
    )
    conn.commit()
    conn.close()
    print(
        f"Database updated with: element_name={element_name}, locator_type={locator_type}, locator_value={locator_value}")

    # Refresh the locator table in the UI after updating the database
    ui_reference.load_locators()


def get_locator_from_db(element_name):
    conn = sqlite3.connect("locators.db")
    cursor = conn.cursor()
    cursor.execute("SELECT locator_type, locator_value FROM locators WHERE element_name = ?", (element_name,))
    result = cursor.fetchone()
    conn.close()
    return result


# Main healing logic function following specified conditions
def heal_locator(driver, element_name, primary_locator_type, primary_locator_value, ui_reference):
    element = None  # Track if an element is successfully found
    found_in_db = False  # Track if found element is from the database

    # Attempt primary locator
    try:
        if primary_locator_type == "id":
            element = driver.find_element(By.ID, primary_locator_value)
        elif primary_locator_type == "css":
            element = driver.find_element(By.CSS_SELECTOR, primary_locator_value)
        elif primary_locator_type == "xpath":
            element = driver.find_element(By.XPATH, primary_locator_value)
        elif primary_locator_type == "name":
            element = driver.find_element(By.NAME, primary_locator_value)

        # If element is found with primary locator, add to database if it’s not already there
        if element:
            print(f"Primary selector for {element_name} is valid. Adding to database.")
            update_locator_in_db(element_name, primary_locator_type, primary_locator_value, ui_reference)
            return element

    except NoSuchElementException:
        print(f"Primary locator failed for {element_name}. Checking database for healed locator...")

    # Check for a healed locator in the database if primary locator fails
    healed_locator = get_locator_from_db(element_name)
    if healed_locator:
        locator_type, locator_value = healed_locator
        try:
            # Attempt to locate using the healed locator
            if locator_type == "id":
                element = driver.find_element(By.ID, locator_value)
            elif locator_type == "css":
                element = driver.find_element(By.CSS_SELECTOR, locator_value)
            elif locator_type == "xpath":
                element = driver.find_element(By.XPATH, locator_value)
            elif locator_type == "name":
                element = driver.find_element(By.NAME, locator_value)
            found_in_db = True  # Set flag if healed locator found and used

            # If healed locator is found, log success and return element
            if element:
                print(f"Found {element_name} using healed locator from database.")
                return element

        except NoSuchElementException:
            # If the healed locator also fails, print a message
            print(
                f"Healed locator not valid for {element_name}: type={locator_type}, value={locator_value}. Attempting dynamic healing...")

    # Perform dynamic healing if both primary and healed locators fail
    if element is None:
        element = dynamic_healing(driver, element_name, ui_reference)

    # Return element only if found and log the appropriate message
    if element:
        if found_in_db:
            print(f"Found {element_name} using healed locator from database.")
        else:
            print(f"Found {element_name} using dynamically healed locator, added to database.")
    else:
        print(
            f"Failed to find {element_name}. The given selector is not valid: type={primary_locator_type}, value={primary_locator_value}. The selector is not in healed data.")
    return element if found_in_db else None


# Dynamic healing logic with additional validation before database update
def dynamic_healing(driver, element_name, ui_reference):
    try:
        print(f"Attempting dynamic healing for {element_name}...")

        # Example: Try locating by class name or partial text (replace with actual identifiers)
        possible_elements = driver.find_elements(By.CLASS_NAME,
                                                 "expected-class-name")  # Replace with realistic class name
        for element in possible_elements:
            if "expected text" in element.text:  # Additional check for unique identification
                print(f"Dynamically found {element_name} by class name.")
                update_locator_in_db(element_name, "class_name", "expected-class-name", ui_reference)
                return element

        # Optionally try locating by partial link text if applicable
        element = driver.find_element(By.PARTIAL_LINK_TEXT, "Expected Text")
        if element:
            print(f"Dynamically found {element_name} by partial link text.")
            update_locator_in_db(element_name, "partial_link_text", "Expected Text", ui_reference)
            return element

    except NoSuchElementException:
        print(f"The given selector is not valid for {element_name}. The selector is not found in healed data.")
        return None


# PyQt5 UI with test execution and locator display
class HealeniumUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_locators()  # Load table at startup

    def initUI(self):
        self.setWindowTitle("Healenium-like Locator Healing UI")
        self.setGeometry(100, 100, 1100, 900)

        # Main Layout
        main_layout = QVBoxLayout()

        # Upper part: Run Test Button
        self.run_test_button = QPushButton("Run Test")
        self.run_test_button.clicked.connect(self.run_test)
        main_layout.addWidget(self.run_test_button)

        # Lower part: Tabs for Reports and Selectors
        self.tabs = QTabWidget()

        # Reports Tab with Accordion-style Healed Dates using QToolBox
        self.healing_tab = QWidget()
        self.healing_tab_layout = QVBoxLayout()

        # QToolBox for displaying healed dates as accordion-style tabs in Reports tab
        self.date_toolbox = QToolBox()
        self.healing_tab_layout.addWidget(self.date_toolbox)

        # Set layout for Reports tab
        self.healing_tab.setLayout(self.healing_tab_layout)
        self.tabs.addTab(self.healing_tab, "Reports")  # Add Reports as the first tab

        # Selectors Tab with Last Healed Date
        self.database_tab = QWidget()
        self.database_tab_layout = QVBoxLayout()
        self.locator_table = QTableWidget(0, 4)  # Updated to 4 columns
        self.locator_table.setHorizontalHeaderLabels(
            ["Element Name", "Locator Type", "Locator Value", "Last Healed Date"])
        self.database_tab_layout.addWidget(self.locator_table)
        self.database_tab.setLayout(self.database_tab_layout)
        self.tabs.addTab(self.database_tab, "Selectors")  # Add Selectors as the second tab

        # Add Tabs to the main layout
        main_layout.addWidget(self.tabs)

        # Test Execution Log label and text area below the tabs
        main_layout.addWidget(QLabel("Test Execution Log:"))
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFixedHeight(150)
        main_layout.addWidget(self.log_display)

        # Set main layout
        self.setLayout(main_layout)

        # Load healed dates into the Reports tab
        self.load_healed_dates()

    def load_healed_dates(self):
        """Loads the healed dates and times into the Reports tab as accordion-style tabs in QToolBox."""
        # Remove all existing items from QToolBox
        while self.date_toolbox.count() > 0:
            self.date_toolbox.removeItem(0)

        # Retrieve healed dates and locator values from the database
        conn = sqlite3.connect("locators.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT element_name, locator_type, locator_value, last_healed FROM locators WHERE last_healed IS NOT NULL ORDER BY last_healed DESC")

        # Add each healed date as a new section in QToolBox
        for element_name, locator_type, locator_value, last_healed in cursor.fetchall():
            healed_datetime = datetime.strptime(last_healed, "%Y-%m-%d %H:%M:%S")
            formatted_date = healed_datetime.strftime("%d %b %Y %H:%M:%S")

            # Create a custom layout for each tab content
            tab_content_layout = QHBoxLayout()

            # Vertical layout for locators (Failed and Healed) - displayed close together
            locator_layout = QVBoxLayout()
            locator_layout.setSpacing(2)  # Reduce spacing between Failed and Healed Locator labels

            # Failed Locator label
            failed_locator_label = QLabel(f"Failed Locator: {locator_type} - {locator_value}")
            locator_layout.addWidget(failed_locator_label)

            # Healed Locator label - here showing the same locator, but you may replace with actual healed locator
            healed_locator_label = QLabel(f"Healed Locator: {locator_type} - {locator_value}")
            locator_layout.addWidget(healed_locator_label)

            # Add the vertical locator layout to the horizontal layout
            tab_content_layout.addLayout(locator_layout)

            # Placeholder for Screenshot - QLabel with fixed size and centered alignment
            screenshot_label = QLabel("Screenshot")
            screenshot_label.setFixedSize(120, 120)  # Set a fixed size for the screenshot placeholder
            screenshot_label.setStyleSheet("border: 1px solid black;")
            screenshot_label.setAlignment(Qt.AlignCenter)  # Center the text within the QLabel
            tab_content_layout.addWidget(screenshot_label)

            # Success healing radio button - properly aligned to the center of its space
            success_healing_radio = QRadioButton("Success Healing")
            success_healing_radio.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            tab_content_layout.addWidget(success_healing_radio, alignment=Qt.AlignCenter)

            # Set the tab content layout in a QWidget and add it to the QToolBox
            tab_content_widget = QWidget()
            tab_content_widget.setLayout(tab_content_layout)
            self.date_toolbox.addItem(tab_content_widget, formatted_date)

        conn.close()
    def run_test(self):
        # Initialize browser
        driver = webdriver.Chrome()
        driver.get("https://acme-test.uipath.com/login")
        self.log_display.append("Opened acme test")

        # Define a primary locator
        element_name = "ForgetYourPassword"
        primary_locator_type = "xpath"
        primary_locator_value = "//*[contains(text(), 'Forgot Your Password?')]"

        # Attempt to heal locator and find element
        element = heal_locator(driver, element_name, primary_locator_type, primary_locator_value, self)

        if element:
            self.log_display.append(f"Found {element_name} using healed locator.")
        else:
            self.log_display.append(f"Failed to find {element_name}. The selector is not valid.")

        driver.quit()

    def load_locators(self):
        """Loads the locator database table into the UI, refreshing existing data."""
        self.locator_table.setRowCount(0)
        conn = sqlite3.connect("locators.db")
        cursor = conn.cursor()
        cursor.execute("SELECT element_name, locator_type, locator_value, last_healed FROM locators")
        for row_index, row_data in enumerate(cursor.fetchall()):
            self.locator_table.insertRow(row_index)
            for col_index, col_data in enumerate(row_data):
                self.locator_table.setItem(row_index, col_index, QTableWidgetItem(str(col_data)))
        conn.close()


# Initialize database and run the PyQt5 app
init_db()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HealeniumUI()
    window.show()
    sys.exit(app.exec_())
