import sqlite3
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, InvalidSelectorException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class LocatorManager:
    def __init__(self, db_path="locators.db", driver_path=None):
        # Initialize database and WebDriver
        self.conn = sqlite3.connect(db_path)
        self.ensure_table_schema()
        service = Service(driver_path) if driver_path else None
        self.driver = webdriver.Chrome(service=service)
        self.wait = WebDriverWait(self.driver, 10)

    def ensure_table_schema(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS locators (
                    element_name TEXT PRIMARY KEY,
                    primary_locator TEXT,
                    fallback_locators TEXT
                )
            """)

    def add_locators(self, element_name, primary_locator, fallback_locators):
        """
        Adds or updates primary and fallback locators in the database.
        """
        fallback_locators_json = json.dumps(fallback_locators)
        with self.conn:
            self.conn.execute("""
                INSERT OR REPLACE INTO locators (element_name, primary_locator, fallback_locators)
                VALUES (?, ?, ?)
            """, (element_name, primary_locator, fallback_locators_json))
        print(f"Locator for '{element_name}' added/updated in database.")

    def generate_fallback_locators(self, primary_by, primary_value):
        """
        Generate fallback locators, converting XPath to CSS selectors where possible.
        """
        fallback_locators = []

        if primary_by == "id":
            fallback_locators.append(("name", primary_value))
            fallback_locators.append(("css_selector", f"[id='{primary_value}']"))
            fallback_locators.append(("xpath", f"//*[@id='{primary_value}']"))
        elif primary_by == "name":
            fallback_locators.append(("id", primary_value))
            fallback_locators.append(("css_selector", f"[name='{primary_value}']"))
            fallback_locators.append(("xpath", f"//*[@name='{primary_value}']"))
        elif primary_by == "class_name":
            fallback_locators.append(("css_selector", f".{primary_value}"))
            fallback_locators.append(("xpath", f"//*[@class='{primary_value}']"))
        elif primary_by == "css_selector":
            fallback_locators.append(("xpath", f"//{primary_value}"))
        elif primary_by == "xpath":
            # Handle specific XPath patterns
            if primary_value.startswith("//*[@id="):
                # XPath with ID attribute -> CSS with ID selector
                id_value = primary_value.split("'")[1]  # Extract ID value
                fallback_locators.append(("css_selector", f"[id='{id_value}']"))

            elif primary_value.startswith("//*[contains(@class,"):
                # XPath contains class -> CSS partial match
                class_value = primary_value.split("'")[1]
                fallback_locators.append(("css_selector", f"[class*='{class_value}']"))

            elif primary_value.startswith("//*[contains(@"):
                # General attribute contains match -> CSS attribute partial match
                attr_name = primary_value.split("@")[1].split(",")[0]
                attr_value = primary_value.split("'")[1]
                fallback_locators.append(("css_selector", f"[{attr_name}*='{attr_value}']"))

            elif primary_value.startswith("//") and "[*[contains(text()" not in primary_value:
                # Direct tag and attribute match -> CSS equivalent
                tag, attr = primary_value.replace("//*", "").replace("[@", "[").split("[", 1)
                css_selector = f"{tag}[{attr}"
                fallback_locators.append(("css_selector", css_selector))
                print("css")

            # # Always keep original XPath as a fallback
            # fallback_locators.append(("xpath", primary_value))

        return fallback_locators

    def find_element(self, element_name, primary_locator):
        """
        Attempt to find an element using the primary locator; if it fails, use fallbacks if available.
        """
        primary_by, primary_value = primary_locator.split("=", 1)

        # Check if element is in the database
        cursor = self.conn.execute("SELECT primary_locator, fallback_locators FROM locators WHERE element_name = ?",
                                   (element_name,))
        row = cursor.fetchone()

        # If the element is not in the database, attempt the primary locator and add to database on success
        if not row:
            try:
                # Try locating element with the provided primary locator for the first time
                element = self.wait.until(
                    EC.presence_of_element_located((getattr(By, primary_by.upper()), primary_value)))
                print(f"Element '{element_name}' found using primary locator on first attempt.")

                # Generate fallback locators and add both primary and fallback locators to the database
                fallback_locators = self.generate_fallback_locators(primary_by.lower(), primary_value)
                self.add_locators(element_name, primary_locator, fallback_locators)
                return element
            except TimeoutException:
                print(
                    f"Primary locator for '{element_name}' failed on first attempt, and no fallback locators are available.")
                raise NoSuchElementException(
                    f"Element '{element_name}' could not be located and no stored locators exist in the database.")

        # If element exists in database, attempt primary locator from database
        db_primary_locator = row[0]
        db_primary_by, db_primary_value = db_primary_locator.split("=", 1)

        try:
            element = self.wait.until(
                EC.presence_of_element_located((getattr(By, db_primary_by.upper()), db_primary_value)))
            print(f"Element '{element_name}' found using database primary locator: {db_primary_locator}")
            return element
        except TimeoutException:
            print(f"Database primary locator for '{element_name}' failed. Trying fallback locators...")

        # Attempt fallback locators only if they are stored in the database
        fallback_locators = json.loads(row[1]) if row[1] else []
        if not fallback_locators:
            print(f"No fallback locators available for '{element_name}' in database.")
            raise NoSuchElementException(f"Element '{element_name}' could not be located with any stored locators.")

        for fallback_by, fallback_value in fallback_locators:
            try:
                element = self.wait.until(
                    EC.presence_of_element_located((getattr(By, fallback_by.upper()), fallback_value)))
                print(f"Element '{element_name}' found using fallback locator: ({fallback_by}={fallback_value}).")

                # Update the database: set this fallback as the new primary locator, regenerate fallbacks
                new_fallback_locators = self.generate_fallback_locators(fallback_by, fallback_value)
                self.add_locators(element_name, f"{fallback_by}={fallback_value}", new_fallback_locators)
                return element
            except TimeoutException:
                print(f"Fallback locator ({fallback_by}={fallback_value}) failed.")

        # Raise an exception if all locators fail
        raise NoSuchElementException(f"Element '{element_name}' could not be located with any stored locators.")


# Usage Example
if __name__ == "__main__":
    driver_path = r"C:\Codebase\QtPy_Learning\main\self_healing_test_automation\chromedriver.exe"  # Update with actual ChromeDriver path
    locator_manager = LocatorManager(driver_path=driver_path)

    locator_manager.driver.get("https://acme-test.uipath.com/login")

    element_name = "register_button"
    primary_locator = "xpath=//*[contains(text(), 'Register')]"

    try:
        locator_manager.find_element(element_name, primary_locator)
    except NoSuchElementException as e:
        print(e)

    locator_manager.driver.quit()
