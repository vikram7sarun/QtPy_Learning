from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException
import time

class SelfHealingLoginTest:
    def __init__(self, driver_path):
        # Initialize WebDriver
        self.driver = webdriver.Chrome()
        self.driver.get("https://acme-test.uipath.com/login")

        # Predefined locators for elements on the login page
        self.locator_mapping = {
            "email_input": [
                (By.ID, "email"),
                (By.NAME, "email"),
                (By.XPATH, "//input[@type='email']"),
                (By.CSS_SELECTOR, "input[type='email']")
            ],
            "password_input": [
                (By.ID, "password"),
                (By.NAME, "password"),
                (By.XPATH, "//input[@type='password']"),
                (By.CSS_SELECTOR, "input[type='password']")
            ],
            "login_button": [
                (By.ID, "loginButton"),
                (By.NAME, "login"),
                (By.XPATH, "//button[text()='Login']"),
                (By.CSS_SELECTOR, "button[type='submit']")
            ]
        }

    def find_element_with_healing(self, element_name):
        """
        Tries to find an element using multiple locators in case of failure (self-healing).
        """
        locators = self.locator_mapping.get(element_name, [])
        for by, value in locators:
            try:
                element = self.driver.find_element(by, value)
                return element
            except NoSuchElementException:
                # If a locator fails, try the next one
                continue
        # Raise exception if no locator succeeds
        raise NoSuchElementException(f"Element '{element_name}' could not be located.")

    def login(self, email, password):
        """
        Performs login using provided email and password.
        Uses self-healing to locate elements.
        """
        try:
            # Find and fill email input field
            email_input = self.find_element_with_healing("email_input")
            email_input.send_keys(email)

            # Find and fill password input field
            password_input = self.find_element_with_healing("password_input")
            password_input.send_keys(password)

            # Find and click the login button
            login_button = self.find_element_with_healing("login_button")
            login_button.click()

            print("Login action completed successfully!")
            time.sleep(3)  # Allow time for the page to load after login
        except NoSuchElementException as e:
            print(f"Error during login: {e}")
        except WebDriverException as e:
            print(f"WebDriver error: {e}")
        finally:
            # Close the WebDriver
            self.driver.quit()

# Usage Example
if __name__ == "__main__":
    # Set your WebDriver path
    driver_path = "path/to/chromedriver"  # Update this path

    # Initialize and run the self-healing login test
    test = SelfHealingLoginTest(driver_path)
    test.login("your_email@example.com", "your_password")
