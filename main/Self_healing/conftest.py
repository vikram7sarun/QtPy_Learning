# conftest.py
import pytest
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import requests
import json
import base64
from datetime import datetime

from main.Self_healing.bd_schema import HealingReport


class SelfHealingDriver:
    def __init__(self, driver, db_session):
        self.driver = driver
        self.db_session = db_session
        self.websocket_client = WebSocketClient()

    def find_element(self, by, value):
        try:
            element = self.driver.find_element(by, value)
            return element
        except NoSuchElementException:
            healed_element = self.heal_selector(by, value)
            if healed_element:
                return healed_element
            raise

    def heal_selector(self, by, value):
        # Capture screenshot of the area
        screenshot = self.driver.get_screenshot_as_base64()

        # Get alternative selectors from database
        alternative_selectors = self.get_alternative_selectors(by, value)

        for selector in alternative_selectors:
            try:
                element = self.driver.find_element(selector['type'], selector['value'])
                if element:
                    # Record successful healing
                    self.record_healing(by, value, selector, screenshot)
                    return element
            except NoSuchElementException:
                continue
        return None

    def record_healing(self, original_by, original_value, healed_selector, screenshot):
        report = HealingReport(
            page_name=self.driver.current_url,
            element_name=f"{original_by}={original_value}",
            failed_selector=f"{original_by}={original_value}",
            healed_selector=f"{healed_selector['type']}={healed_selector['value']}",
            healing_score=healed_selector.get('confidence', 0.0),
            screenshot_path=screenshot,
            status='success',
            execution_time=0.0
        )
        self.db_session.add(report)
        self.db_session.commit()

        # Broadcast update via WebSocket
        self.websocket_client.send_update(report)


@pytest.fixture
def self_healing_driver(selenium):
    driver = SelfHealingDriver(selenium)
    yield driver
    driver.quit()