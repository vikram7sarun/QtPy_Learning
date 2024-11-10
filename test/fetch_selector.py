from PyQt5 import QtWidgets, QtGui, QtCore
from selenium import webdriver
from selenium.webdriver.common.by import By
import sys


class WebScraperUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_chrome()

    def init_ui(self):
        """Initialize the UI components"""
        self.setWindowTitle("Web Element Selector Scraper")
        self.setGeometry(100, 100, 1200, 800)

        layout = QtWidgets.QVBoxLayout()

        # Toolbar
        toolbar = QtWidgets.QHBoxLayout()

        self.scrape_button = QtWidgets.QPushButton("Scrape Elements")
        self.scrape_button.clicked.connect(self.scrape_functional_elements)
        toolbar.addWidget(self.scrape_button)

        clear_button = QtWidgets.QPushButton("Clear")
        clear_button.clicked.connect(lambda: self.results_area.clear())
        toolbar.addWidget(clear_button)

        layout.addLayout(toolbar)

        # Results area
        self.results_area = QtWidgets.QTextEdit()
        self.results_area.setReadOnly(True)
        self.results_area.setFont(QtGui.QFont("Courier New", 10))
        self.results_area.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        layout.addWidget(self.results_area)

        self.setLayout(layout)

    def setup_chrome(self):
        try:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9214")
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            self.results_area.append(
                "Error: Could not connect to Chrome. Ensure Chrome is running with debugging enabled.")
            self.scrape_button.setEnabled(False)

    def _get_functional_elements(self):
        """Get interactive elements from the page"""
        selector = ("button, input, select, textarea, a[href], [onclick], "
                    "[role='button'], [type='submit'], [role='link'], [role='textbox']")
        return self.driver.find_elements(By.CSS_SELECTOR, selector)

    def _create_attribute_xpath(self, tag, attributes, text):
        """Create XPath based on element attributes with priority order"""
        # Priority 1: ID based
        if attributes.get('id'):
            return f"//*[@id='{attributes['id']}']"

        # Priority 2: Multiple attributes combination
        attr_combinations = [
            ('name', 'type'),
            ('class', 'type'),
            ('name', 'role'),
            ('class', 'name')
        ]

        for attr1, attr2 in attr_combinations:
            if attributes.get(attr1) and attributes.get(attr2):
                return f"//*[@{attr1}='{attributes[attr1]}' and @{attr2}='{attributes[attr2]}']"

        # Priority 3: Class with contains
        if attributes.get('class'):
            classes = attributes['class'].split()
            if len(classes) > 1:
                return f"//*[contains(@class,'{classes[0]}') and contains(@class,'{classes[1]}')]"
            return f"//*[contains(@class,'{attributes['class']}')]"

        # Priority 4: Single attribute with tag
        for attr in ['name', 'role', 'type', 'placeholder']:
            if attributes.get(attr):
                return f"//{tag}[@{attr}='{attributes[attr]}']"

        return None

    def _create_text_based_xpath(self, tag, attributes, text):
        """Create XPath based on text and accessibility attributes"""
        xpath_patterns = [
            # Priority 1: Text with tag
            (text, lambda t: f"//{tag}[text()='{t}']"),
            # Priority 2: Placeholder with contains
            (attributes.get('placeholder'), lambda p: f"//*[contains(@placeholder,'{p}')]"),
            # Priority 3: Title with contains
            (attributes.get('title'), lambda t: f"//*[contains(@title,'{t}')]"),
            # Priority 4: Aria-label exact match
            (attributes.get('aria-label'), lambda a: f"//*[@aria-label='{a}']"),
            # Priority 5: Data-test-id or other data attributes
            (attributes.get('data-test-id'), lambda d: f"//*[@data-test-id='{d}']"),
            # Priority 6: Value with type
            (attributes.get('value'), lambda v: f"//{tag}[@value='{v}']" if attributes.get('type') else None)
        ]

        for value, pattern in xpath_patterns:
            if value:
                xpath = pattern(value)
                if xpath:
                    return xpath

        return None

    def _generate_dynamic_xpaths(self, element, attributes):
        """Generate two unique dynamic XPaths"""
        try:
            tag = element.tag_name
            text = element.text.strip()

            # Get all possible XPaths
            xpath_candidates = []

            # Add attribute-based XPath
            attr_xpath = self._create_attribute_xpath(tag, attributes, text)
            if attr_xpath:
                xpath_candidates.append(attr_xpath)

            # Add text-based XPath
            text_xpath = self._create_text_based_xpath(tag, attributes, text)
            if text_xpath:
                xpath_candidates.append(text_xpath)

            # Add position-based XPath
            pos_xpath = self._get_position_based_xpath(element, tag, attributes)
            if pos_xpath:
                xpath_candidates.append(pos_xpath)

            # Add more candidates if needed
            if attributes.get('class'):
                class_parts = attributes['class'].split()
                if len(class_parts) > 0:
                    xpath_candidates.append(f"//{tag}[contains(@class,'{class_parts[0]}')]")

            if text:
                xpath_candidates.append(f"//*[contains(text(),'{text}')]")

            # Ensure we have at least two unique XPaths
            unique_xpaths = list(dict.fromkeys(xpath_candidates))  # Remove duplicates

            if len(unique_xpaths) < 2:
                # Add fallback XPath if we don't have enough unique ones
                fallback = f"//{tag}"
                if fallback not in unique_xpaths:
                    unique_xpaths.append(fallback)

            # Return the two best unique XPaths
            return unique_xpaths[0], unique_xpaths[1] if len(unique_xpaths) > 1 else f"//{tag}"

        except Exception as e:
            print(f"Error generating XPaths: {str(e)}")
            return "//invalid", "//invalid"

    def _get_position_based_xpath(self, element, tag, attributes):
        """Generate position-based XPath with parent context"""
        try:
            # Try to get a unique identifier from parent
            parent_attrs = self.driver.execute_script("""
                var parent = arguments[0].parentElement;
                var attrs = {};
                for (var i = 0; i < parent.attributes.length; i++) {
                    attrs[parent.attributes[i].name] = parent.attributes[i].value;
                }
                return attrs;
            """, element)

            parent_tag = self.driver.execute_script("return arguments[0].parentElement.tagName.toLowerCase()", element)

            # Get position among siblings
            position = self.driver.execute_script("""
                let element = arguments[0];
                let tag = element.tagName.toLowerCase();
                let parent = element.parentElement;
                let siblings = Array.from(parent.children).filter(e => e.tagName.toLowerCase() === tag);
                return siblings.indexOf(element) + 1;
            """, element)

            # Create XPath with parent context if available
            if parent_attrs.get('id'):
                return f"//*[@id='{parent_attrs['id']}']/{tag}[{position}]"
            elif parent_attrs.get('class'):
                return f"//*[contains(@class,'{parent_attrs['class']}')]/{tag}[{position}]"
            else:
                return f"//{parent_tag}/{tag} [{position}]"

        except Exception:
            return f"//{tag} [{position}]"

    def _get_element_info(self, element):
        """Get element information and attributes"""
        try:
            attributes = self.driver.execute_script("""
                var items = {};
                for (index = 0; index < arguments[0].attributes.length; ++index) { 
                    items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value 
                }; 
                return items;
            """, element)

            tag = element.tag_name
            text = element.text.strip()

            info = {
                'Tag': tag,
                'id': attributes.get('id', ''),
                'type': attributes.get('type', ''),
                'name': attributes.get('name', ''),
                'class': attributes.get('class', ''),
                'text': text
            }

            # Clean up empty values
            info = {k: v for k, v in info.items() if v}

            # Add CSS selector
            if 'class' in info:
                info['css'] = f"{tag}.{'.'.join(info['class'].split())}"

            # Generate XPaths
            xpath1, xpath2 = self._generate_dynamic_xpaths(element, attributes)
            if xpath1: info['xpath1'] = xpath1
            if xpath2: info['xpath2'] = xpath2

            return info

        except Exception:
            return None

    def _format_element_info(self, info):
        """Format element information for display"""
        if not info:
            return None

        output_lines = ['']
        attr_order = ['Tag', 'id', 'type', 'name', 'class', 'css', 'text', 'xpath1', 'xpath2']

        output_lines.extend(f"{attr}: {info[attr]}" for attr in attr_order if attr in info)
        output_lines.append('-------------')

        return '\n'.join(output_lines)

    def scrape_functional_elements(self):
        """Main scraping function"""
        try:
            self.scrape_button.setEnabled(False)
            self.results_area.clear()

            current_url = self.driver.current_url
            self.results_area.append(f"URL: {current_url}\n")

            elements = self._get_functional_elements()
            formatted_outputs = []

            for elem in elements:
                elem_info = self._get_element_info(elem)
                if elem_info:
                    formatted_info = self._format_element_info(elem_info)
                    if formatted_info:
                        formatted_outputs.append(formatted_info)

            self.results_area.append('\n'.join(formatted_outputs))

        except Exception as e:
            self.results_area.append(f"Error during scraping: {str(e)}")
        finally:
            self.scrape_button.setEnabled(True)

    def closeEvent(self, event):
        try:
            self.driver.quit()
        except:
            pass
        event.accept()


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
    app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    window = WebScraperUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()