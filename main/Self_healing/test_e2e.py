# test_e2e.py
import pytest
from selenium.webdriver.common.by import By


class TestEcommerce:
    def test_product_search(self, self_healing_driver):
        driver = self_healing_driver

        # Navigate to homepage
        driver.get("https://example.com")

        # Search for a product
        search_box = driver.find_element(By.ID, "search")
        search_box.send_keys("laptop")

        search_button = driver.find_element(By.CSS_SELECTOR, ".search-btn")
        search_button.click()

        # Verify search results
        results = driver.find_elements(By.CSS_SELECTOR, ".product-card")
        assert len(results) > 0

    def test_shopping_cart(self, self_healing_driver):
        driver = self_healing_driver

        # Add item to cart
        add_to_cart_btn = driver.find_element(By.CSS_SELECTOR, ".add-to-cart")
        add_to_cart_btn.click()

        # Verify cart update
        cart_count = driver.find_element(By.CSS_SELECTOR, ".cart-count")
        assert cart_count.text == "1"

    def test_checkout_process(self, self_healing_driver):
        driver = self_healing_driver

        # Navigate to cart
        cart_icon = driver.find_element(By.ID, "cart-icon")
        cart_icon.click()

        # Proceed to checkout
        checkout_btn = driver.find_element(By.CSS_SELECTOR, ".checkout-btn")
        checkout_btn.click()

        # Fill shipping details
        driver.find_element(By.NAME, "firstName").send_keys("John")
        driver.find_element(By.NAME, "lastName").send_keys("Doe")
        driver.find_element(By.NAME, "address").send_keys("123 Test St")

        # Complete order
        place_order_btn = driver.find_element(By.ID, "place-order")
        place_order_btn.click()

        # Verify order confirmation
        confirmation = driver.find_element(By.CSS_SELECTOR, ".order-confirmation")
        assert "Thank you for your order" in confirmation.text