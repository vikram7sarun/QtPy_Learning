import logging
import time
import utilities.custom_logger as cl
from base.selenium_driver import Selenium_Driver

class TestPage(Selenium_Driver):

    log = cl.customLogger(logging.DEBUG)

    """Page Object for Test"""

    def __init__(self, driver):
        super().__init__(driver)
        self.driver = driver

    # Locators
    __element = "//*[@data-target='#bs-example-navbar-collapse-1' and @data-toggle='collapse']"
    __btn_btn_primary = "//*[contains(@class, 'btn btn-primary')]"
    __home = "//*//*[text()='Home']"
    __email = "email"
    __password = "password"

    # Functions
    def element(self):
            self.element(self.__element, locatorType='xpath')

    def btn_btn_primary(self):
            self.element(self.__btn_btn_primary, locatorType='xpath')

    def home(self):
            self.element(self.__home, locatorType='xpath')

    def email(self):
            self.element(self.__email, locatorType='id')

    def password(self):
            self.element(self.__password, locatorType='id')

