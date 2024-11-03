import sqlite3
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

def get_locator_from_db(element_name):
    conn = sqlite3.connect("locators.db")
    cursor = conn.cursor()
    cursor.execute("SELECT locator_type, locator_value FROM locators WHERE element_name = ?", (element_name,))
    result = cursor.fetchone()
    conn.close()
    return result

def update_locator_in_db(element_name, locator_type, locator_value):
    conn = sqlite3.connect("locators.db")
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO locators (element_name, locator_type, locator_value, last_healed) VALUES (?, ?, ?, datetime('now'))",
                   (element_name, locator_type, locator_value))
    conn.commit()
    conn.close()

def heal_locator(driver: WebDriver, element_name, primary_locator_type, primary_locator_value):
    try:
        if primary_locator_type == "id":
            return driver.find_element(By.ID, primary_locator_value)
        elif primary_locator_type == "css":
            return driver.find_element(By.CSS_SELECTOR, primary_locator_value)
        # Add other primary locators as needed
    except:
        # Check if a healed locator exists in the database
        healed_locator = get_locator_from_db(element_name)
        if healed_locator:
            locator_type, locator_value = healed_locator
            try:
                if locator_type == "id":
                    return driver.find_element(By.ID, locator_value)
                elif locator_type == "css":
                    return driver.find_element(By.CSS_SELECTOR, locator_value)
                # Add other locator types as needed
            except:
                print(f"Healing failed for {element_name}")
        return None
