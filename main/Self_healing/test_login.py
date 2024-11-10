# test_login.py
def test_login_functionality(self_healing_driver):
    driver = self_healing_driver

    # Navigate to login page
    driver.get("https://example.com/login")

    # Find elements with self-healing capability
    username_field = driver.find_element("id", "username")
    password_field = driver.find_element("id", "password")
    login_button = driver.find_element("css selector", ".login-btn")

    # Perform login
    username_field.send_keys("testuser")
    password_field.send_keys("testpass")
    login_button.click()

    # Assert successful login
    welcome_message = driver.find_element("css selector", ".welcome-msg")
    assert welcome_message.text == "Welcome, Test User"