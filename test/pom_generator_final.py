from PyQt5 import QtWidgets, QtGui, QtCore
from selenium import webdriver
from selenium.webdriver.common.by import By
from playwright.sync_api import sync_playwright
import sys
import os
import warnings

from torch import layout

warnings.filterwarnings("ignore", category=DeprecationWarning)


class SelectorTabWidget(QtWidgets.QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_tabs()

    def init_tabs(self):
        # Create container for "All Selectors" tab
        all_container = QtWidgets.QWidget()
        all_layout = QtWidgets.QVBoxLayout(all_container)

        # Text area for All Selectors
        self.all_selectors_text = QtWidgets.QTextEdit()
        self.all_selectors_text.setReadOnly(True)
        self.all_selectors_text.setFont(QtGui.QFont("Courier New", 10))
        self.all_selectors_text.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        all_layout.addWidget(self.all_selectors_text)

        # Add the All Selectors container as first tab
        self.addTab(all_container, "All Selectors")

        # Create container for "Selectors Alternative" tab
        alt_container = QtWidgets.QWidget()
        alt_layout = QtWidgets.QVBoxLayout(alt_container)

        # Search Section
        search_layout = QtWidgets.QHBoxLayout()
        self.search_box = QtWidgets.QLineEdit()
        self.search_box.setPlaceholderText("Search selectors...")
        self.search_box.setClearButtonEnabled(True)
        # Connect text changed signal for real-time search
        self.search_box.textChanged.connect(self.auto_scroll_to_match)
        # Connect returnPressed signal for Enter key
        self.search_box.returnPressed.connect(self.perform_search)
        search_layout.addWidget(self.search_box)

        self.search_button = QtWidgets.QPushButton("Search")
        self.search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)

        # Text area for Alternative Selectors
        self.alt_selectors_text = QtWidgets.QTextEdit()
        self.alt_selectors_text.setReadOnly(True)
        self.alt_selectors_text.setFont(QtGui.QFont("Courier New", 10))
        self.alt_selectors_text.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        alt_layout.addWidget(self.alt_selectors_text)

        # Add the Alternative Selectors container as second tab
        self.addTab(alt_container, "Selectors Alternative")

        # Connect tab change signal
        self.currentChanged.connect(self.on_tab_changed)

    def auto_scroll_to_match(self, search_text):
        """Auto-scroll to first match as user types"""
        try:
            if not search_text.strip():
                # Clear highlighting if search text is empty
                self.clear_highlighting()
                return

            # Store cursor position
            cursor = self.selectors_text.textCursor()

            # Start from the beginning
            cursor.movePosition(QtGui.QTextCursor.Start)
            self.selectors_text.setTextCursor(cursor)

            # Find first match
            found = self.selectors_text.find(search_text)

            if found:
                # Get the cursor with the found text
                cursor = self.selectors_text.textCursor()

                # Highlight the found text
                cursor.movePosition(QtGui.QTextCursor.StartOfLine)
                cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)

                # Create format for highlighting
                format = QtGui.QTextCharFormat()
                format.setBackground(QtGui.QColor("yellow"))
                cursor.mergeCharFormat(format)

                # Ensure the found text is visible
                self.selectors_text.setTextCursor(cursor)
                self.selectors_text.ensureCursorVisible()

                # Update status
                self.update_status(f"Found match for: {search_text}")
            else:
                self.clear_highlighting()
                self.update_status("No matches found")

        except Exception as e:
            print(f"Error in auto_scroll_to_match: {e}")
            self.update_status("Search failed")
    def search_text(self, text):
        """Search and highlight text in the selectors text area"""
        try:
            # Store current cursor position
            cursor = self.selectors_text.textCursor()
            initial_position = cursor.position()

            # Clear previous highlighting
            self.selectors_text.blockSignals(True)  # Block signals temporarily
            cursor.select(QtGui.QTextCursor.Document)
            format = QtGui.QTextCharFormat()
            format.setBackground(QtGui.QColor("white"))
            cursor.mergeCharFormat(format)

            if not text.strip():
                cursor.setPosition(initial_position)
                self.selectors_text.setTextCursor(cursor)
                self.selectors_text.blockSignals(False)  # Restore signals
                return

            # Reset cursor to start
            cursor.movePosition(QtGui.QTextCursor.Start)
            self.selectors_text.setTextCursor(cursor)

            # Prepare highlight format
            highlight_format = QtGui.QTextCharFormat()
            highlight_format.setBackground(QtGui.QColor("yellow"))

            # Find and highlight all occurrences
            found = False
            current_text = self.selectors_text.toPlainText()

            # Create a new cursor for searching
            search_cursor = QtGui.QTextCursor(self.selectors_text.document())
            search_cursor.movePosition(QtGui.QTextCursor.Start)

            while True:
                # Find next occurrence
                search_cursor = self.selectors_text.document().find(text, search_cursor)
                if search_cursor.isNull():
                    break

                found = True
                search_cursor.mergeCharFormat(highlight_format)

            # Reset cursor position if no matches
            if not found:
                cursor.setPosition(initial_position)
                self.selectors_text.setTextCursor(cursor)
                self.selectors_text.blockSignals(False)  # Restore signals
                QtWidgets.QMessageBox.information(
                    self,
                    "Search Result",
                    "No matches found.",
                    QtWidgets.QMessageBox.Ok
                )
            else:
                self.update_status(f"Found matches for: {text}")

            self.selectors_text.blockSignals(False)  # Restore signals

        except Exception as e:
            print(f"Error in search_text: {e}")
            self.update_status("Search failed")



    def clear_highlighting(self):
        """Clear all search highlighting"""
        try:
            self.selectors_text.setExtraSelections([])
            cursor = self.selectors_text.textCursor()
            cursor.movePosition(QtGui.QTextCursor.Start)
            self.selectors_text.setTextCursor(cursor)
        except Exception as e:
            print(f"Error in clear_highlighting: {e}")

    def on_tab_changed(self, index):
        """Handle tab change events"""
        if index == 0:  # All Selectors tab
            self.alt_search_box.clear()
        else:  # Alternative Selectors tab
            self.all_search_box.clear()
class EnhancedPOMGenerator(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.move_count = 0
        self.previous_text = ""
        self.setup_chrome()
        self.init_ui()
        self.set_styles()

    def init_ui(self):
        self.setWindowTitle('Enhanced POM Generator')
        self.setGeometry(100, 100, 750, 850)

        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget)
        layout = QtWidgets.QVBoxLayout(main_widget)

        # Priority Section
        priority_label = QtWidgets.QLabel(
            'Enter Selector Priorities:\nEg: ID, Name, ClassName, LinkText, PartialLinkText, TagName')
        layout.addWidget(priority_label)

        priority_layout = QtWidgets.QHBoxLayout()
        self.priority_entry = QtWidgets.QLineEdit()
        self.priority_entry.setText("ID, Name, ClassName, LinkText, PartialLinkText, TagName")
        self.fetch_button = QtWidgets.QPushButton('Fetch Selectors')
        self.fetch_button.clicked.connect(self.fetch_selectors)

        priority_layout.addWidget(self.priority_entry)
        priority_layout.addWidget(self.fetch_button)
        layout.addLayout(priority_layout)

        # Search Section
        search_layout = QtWidgets.QHBoxLayout()
        self.search_box = QtWidgets.QLineEdit()
        self.search_box.setPlaceholderText("Search selectors...")
        self.search_box.setClearButtonEnabled(True)
        search_layout.addWidget(self.search_box)

        self.search_button = QtWidgets.QPushButton("Search")
        self.search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)

        # Selectors Text Area
        self.selectors_text = QtWidgets.QTextEdit()
        self.selectors_text.setReadOnly(True)
        self.selectors_text.setFont(QtGui.QFont("Courier New", 10))
        self.selectors_text.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        layout.addWidget(self.selectors_text)

        # Middle Section
        middle_layout = QtWidgets.QHBoxLayout()

        # Move Button
        self.move_button = QtWidgets.QPushButton('Move Selected Lines')
        self.move_button.clicked.connect(self.move_selected_lines)
        middle_layout.addWidget(self.move_button)

        # Class Name Entry
        self.class_name_entry = QtWidgets.QLineEdit()
        self.class_name_entry.setPlaceholderText("Enter Class Name")
        self.class_name_entry.setFixedWidth(150)
        middle_layout.addWidget(self.class_name_entry)

        # Language Dropdown
        self.language_combo = QtWidgets.QComboBox()
        self.language_combo.addItems(['Python', 'Java', 'C#'])
        self.language_combo.setFixedWidth(100)
        middle_layout.addWidget(self.language_combo)

        # Generate button
        self.generate_button = QtWidgets.QPushButton('Generate POM')
        self.generate_button.clicked.connect(self.generate_pom)
        middle_layout.addWidget(self.generate_button)

        layout.addLayout(middle_layout)

        # Moved Text Area
        self.moved_text = QtWidgets.QTextEdit()
        self.moved_text.textChanged.connect(self.on_moved_text_changed)
        layout.addWidget(self.moved_text)

        # Bottom Section
        bottom_layout = QtWidgets.QHBoxLayout()
        self.save_button = QtWidgets.QPushButton('Save to File')
        self.save_button.clicked.connect(self.save_to_file)
        self.clear_button = QtWidgets.QPushButton('Clear POM')
        self.clear_button.clicked.connect(self.clear_generated_pom)

        bottom_layout.addWidget(self.save_button)
        bottom_layout.addWidget(self.clear_button)
        layout.addLayout(bottom_layout)

        # Status Bar
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status('Ready')

        # Set object names for specific styling
        self.fetch_button.setObjectName("fetch_button")
        self.move_button.setObjectName("move_button")
        self.generate_button.setObjectName("generate_button")
        self.search_button.setObjectName("search_button")
        self.clear_button.setObjectName("clear_button")
        self.save_button.setObjectName("save_button")

        # Add tooltips
        self.fetch_button.setToolTip("Fetch selectors from the current page")
        self.search_box.setToolTip("Enter text to search in selectors")
        self.search_button.setToolTip("Search for text in selectors")
        self.move_button.setToolTip("Move selected selectors to POM")
        self.class_name_entry.setToolTip("Enter the class name for POM")
        self.language_combo.setToolTip("Select the programming language")
        self.generate_button.setToolTip("Generate Page Object Model")
        self.clear_button.setToolTip("Clear all content")

        # Set uniform sizes for text areas
        self.selectors_text.setMinimumHeight(200)
        self.moved_text.setMinimumHeight(200)

    def perform_search(self):
        """Handle search button click and Enter key press"""
        try:
            search_text = self.search_box.text().strip()
            if not search_text:
                self.clear_highlighting()
                return

            # Store original cursor position
            original_cursor = self.selectors_text.textCursor()

            # Start from the beginning
            cursor = QtGui.QTextCursor(self.selectors_text.document())
            self.selectors_text.setTextCursor(cursor)

            # Find and highlight all matches
            extra_selections = []
            found = False

            while True:
                found_cursor = self.selectors_text.document().find(search_text, cursor)
                if found_cursor.isNull():
                    break

                # Create highlight selection
                selection = QtWidgets.QTextEdit.ExtraSelection()
                selection.format = QtGui.QTextCharFormat()
                selection.format.setBackground(QtGui.QColor("yellow"))
                selection.cursor = found_cursor
                extra_selections.append(selection)

                cursor = found_cursor
                found = True

            # Apply highlights
            self.selectors_text.setExtraSelections(extra_selections)

            if found:
                # Scroll to first match
                first_match = extra_selections[0].cursor
                self.selectors_text.setTextCursor(first_match)
                self.selectors_text.ensureCursorVisible()
                self.update_status(f"Found {len(extra_selections)} matches for: {search_text}")
            else:
                self.selectors_text.setTextCursor(original_cursor)
                QtWidgets.QMessageBox.information(
                    self,
                    "Search Result",
                    "No matches found.",
                    QtWidgets.QMessageBox.Ok
                )
                self.update_status("No matches found")

        except Exception as e:
            print(f"Error in perform_search: {e}")
            self.update_status("Search failed")

    def highlight_text(self, search_text):
        """Highlight matching text in the selectors text area"""
        try:
            # Get current content and cursor
            content = self.selectors_text.toPlainText()
            cursor = self.selectors_text.textCursor()
            initial_position = cursor.position()

            # Clear existing highlighting
            cursor.select(QtGui.QTextCursor.Document)
            normal_format = QtGui.QTextCharFormat()
            normal_format.setBackground(QtGui.QColor("white"))
            cursor.mergeCharFormat(normal_format)

            if not search_text.strip():
                return

            # Create highlight format
            highlight_format = QtGui.QTextCharFormat()
            highlight_format.setBackground(QtGui.QColor("yellow"))

            # Start from the beginning
            cursor.movePosition(QtGui.QTextCursor.Start)
            self.selectors_text.setTextCursor(cursor)

            # Find and highlight all matches
            found = False
            extra_selections = []

            while True:
                cursor = self.selectors_text.document().find(search_text, cursor)
                if cursor.isNull():
                    break

                selection = QtWidgets.QTextEdit.ExtraSelection()
                selection.format = highlight_format
                selection.cursor = cursor
                extra_selections.append(selection)
                found = True

            # Apply highlights
            self.selectors_text.setExtraSelections(extra_selections)

            if not found:
                # Reset cursor and show message
                cursor = self.selectors_text.textCursor()
                cursor.setPosition(initial_position)
                self.selectors_text.setTextCursor(cursor)

                QtWidgets.QMessageBox.information(
                    self,
                    "Search Result",
                    "No matches found.",
                    QtWidgets.QMessageBox.Ok
                )
            else:
                self.update_status(f"Found matches for: {search_text}")

        except Exception as e:
            print(f"Error in highlight_text: {e}")
            self.update_status("Search failed")


    def setup_chrome(self):
        """Setup Chrome WebDriver"""
        try:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9214")
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            self.show_error_popup(
                "Error: Could not connect to Chrome. Ensure Chrome is running with debugging enabled.")

    def fetch_selectors(self):
        """Fetch selectors based on priorities"""
        try:
            if self.selectors_text.toPlainText().strip():
                reply = QtWidgets.QMessageBox.question(
                    self,
                    'Clear Content',
                    'Text area contains content. Do you want to clear it and fetch new selectors?',
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No
                )
                if reply == QtWidgets.QMessageBox.No:
                    return

            # Get and validate priorities
            priorities = [p.strip().lower() for p in self.priority_entry.text().split(',') if p.strip()]
            if not priorities:
                self.show_error_popup("Please specify at least one priority.")
                return

            self.selectors_text.clear()
            self.update_status("Fetching selectors...")

            # Get current URL
            current_url = self.driver.current_url
            self.selectors_text.append(f"\nURL: {current_url}")
            self.selectors_text.append("---------------------")

            # Get all functional elements using multiple selectors
            elements = self._get_all_functional_elements()
            formatted_outputs = self.format_elements_info(elements, priorities)

            if formatted_outputs:
                self.selectors_text.append('\n'.join(formatted_outputs))
                self.update_status("Selectors fetched successfully")
            else:
                self.update_status("No selectors found for the specified priorities")

        except Exception as e:
            self.show_error_popup(f"Error fetching selectors: {str(e)}")
            self.update_status("Fetch failed")

    def format_elements_info(self, elements, priorities):
        """Format element information based on priorities"""
        formatted_outputs = []

        for element in elements:
            try:
                element_info = self._get_element_full_info(element)
                attributes = element_info.get('attributes', {})

                # Check if element matches any priority
                if self._has_priority_attributes(element_info, priorities):
                    formatted_output = []

                    # Add tag name
                    formatted_output.append(f"Tag: {element_info['tag']}")

                    # Add prioritized attributes first
                    for priority in priorities:
                        priority = priority.lower()
                        if priority == 'id' and attributes.get('id'):
                            formatted_output.append(f"id: {attributes['id']}")
                        elif priority == 'name' and attributes.get('name'):
                            formatted_output.append(f"name: {attributes['name']}")
                        elif priority == 'class' and attributes.get('class'):
                            formatted_output.append(f"class: {attributes['class']}")
                        elif priority == 'type' and attributes.get('type'):
                            formatted_output.append(f"type: {attributes['type']}")
                        elif priority in ['text', 'linktext'] and element_info.get('text'):
                            formatted_output.append(f"text: {element_info['text']}")

                    # Add other available attributes
                    for attr, value in attributes.items():
                        if value and attr not in ['id', 'name', 'class', 'type']:
                            formatted_output.append(f"{attr}: {value}")

                    # Generate and add XPaths
                    xpath1, xpath2, xpath3, xpath4 = self._generate_xpaths(element_info, priorities)
                    if xpath1:
                        formatted_output.append(f"xpath1: {xpath1}")
                    if xpath2:
                        formatted_output.append(f"xpath2: {xpath2}")
                    if xpath3:
                        formatted_output.append(f"xpath3: {xpath3}")
                    if xpath4:
                        formatted_output.append(f"xpath4: {xpath4}")

                    formatted_output.append("---------------------")

                    if len(formatted_output) > 2:  # More than just tag and separator
                        formatted_outputs.append('\n'.join(formatted_output))

            except Exception as e:
                print(f"Error processing element: {e}")
                continue

        return formatted_outputs

    def _get_element_full_info(self, element):
        """Get complete information about an element"""
        try:
            # Get all attributes using JavaScript
            attributes = self.driver.execute_script("""
                var items = {};
                for (index = 0; index < arguments[0].attributes.length; ++index) { 
                    items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value 
                }; 
                return items;
            """, element)

            # Basic element information
            tag_name = element.tag_name
            text = element.text.strip() if element.text else None

            # Get additional info for specific elements
            element_type = element.get_attribute('type')
            element_value = element.get_attribute('value')
            element_role = element.get_attribute('role')

            # Combine all information
            info = {
                'tag': tag_name,
                'attributes': {},  # Initialize empty attributes dict
                'text': text if text else None
            }

            # Add standard attributes if they exist
            if element_type:
                info['attributes']['type'] = element_type
            if element_value:
                info['attributes']['value'] = element_value
            if element_role:
                info['attributes']['role'] = element_role

            # Add all other attributes
            for attr, value in attributes.items():
                if value:  # Only add non-empty attributes
                    info['attributes'][attr] = value

            # For select elements, get options
            if tag_name == 'select':
                try:
                    options = element.find_elements(By.TAG_NAME, 'option')
                    option_texts = [opt.text for opt in options if opt.text.strip()]
                    if option_texts:
                        info['options'] = option_texts
                except:
                    pass

            # Get aria attributes
            aria_attrs = {}
            for attr in attributes:
                if attr.startswith('aria-') or attr.startswith('data-'):
                    value = element.get_attribute(attr)
                    if value:
                        aria_attrs[attr] = value
            if aria_attrs:
                info['aria'] = aria_attrs

            return info

        except Exception as e:
            print(f"Error getting element info: {e}")
            return {
                'tag': 'unknown',
                'attributes': {},
                'text': None
            }

    def _format_element_display(self, element_info):
        """Format element information for display"""
        lines = []

        # Add tag
        if 'tag' in element_info:
            lines.append(f"Tag: {element_info['tag']}")

        # Add attributes in a specific order
        priority_attrs = ['id', 'type', 'name', 'class', 'value', 'role']
        attrs = element_info.get('attributes', {})

        # First add priority attributes
        for attr in priority_attrs:
            if attr in attrs:
                lines.append(f"{attr}: {attrs[attr]}")

        # Then add remaining attributes
        for attr, value in attrs.items():
            if attr not in priority_attrs:
                lines.append(f"{attr}: {value}")

        # Add text if present
        if element_info.get('text'):
            lines.append(f"text: {element_info['text']}")

        # Add options for select elements
        if 'options' in element_info:
            lines.append("options:")
            for option in element_info['options']:
                lines.append(f"  - {option}")

        # Add aria attributes
        if 'aria' in element_info:
            for attr, value in element_info['aria'].items():
                lines.append(f"{attr}: {value}")

        return lines

    def _is_visible(self, element):
        """Check if element is visible"""
        try:
            return element.is_displayed() and element.size['height'] > 0 and element.size['width'] > 0
        except:
            return False

    def _is_interactive(self, element):
        """Check if element is interactive"""
        try:
            tag = element.tag_name.lower()
            type_attr = element.get_attribute('type')
            role = element.get_attribute('role')

            # Check if element is inherently interactive
            if tag in ['a', 'button', 'select', 'textarea']:
                return True

            # Check input types
            if tag == 'input' and type_attr not in ['hidden']:
                return True

            # Check ARIA roles
            if role in ['button', 'link', 'textbox', 'combobox', 'checkbox', 'radio']:
                return True

            # Check for click handlers
            if element.get_attribute('onclick') or element.get_attribute('onkeydown'):
                return True

            return False
        except:
            return False

    def _has_priority_attributes(self, element_info, priorities):
        """Check if element has any of the prioritized attributes"""
        attributes = element_info.get('attributes', {})

        for priority in priorities:
            priority = priority.lower()

            # Check for standard attributes
            if (priority == 'id' and 'id' in attributes) or \
                    (priority == 'name' and 'name' in attributes) or \
                    (priority == 'class' and 'class' in attributes) or \
                    (priority == 'type' and 'type' in attributes):
                return True

            # Check for text content
            if priority in ['text', 'linktext', 'partiallinktext'] and element_info.get('text'):
                return True

            # Check for tag name
            if priority == 'tagname' and element_info.get('tag'):
                return True

        return False

    def _get_all_functional_elements(self):
        """Get all functional elements from the page"""
        functional_elements = []

        # Define all functional element selectors
        selectors = [
            "input[type='text']",
            "input[type='password']",
            "input[type='email']",
            "input[type='number']",
            "input[type='tel']",
            "input[type='search']",
            "input[type='url']",
            "input[type='date']",
            "input[type='datetime-local']",
            "input[type='time']",
            "input[type='week']",
            "input[type='month']",
            "input[type='file']",
            "input[type='submit']",
            "input[type='button']",
            "input[type='reset']",
            "input[type='checkbox']",
            "input[type='radio']",
            "select",
            "textarea",
            "button",
            "a[href]",
            "[role='button']",
            "[role='link']",
            "[role='tab']",
            "[role='menuitem']",
            "[role='checkbox']",
            "[role='radio']",
            "[role='switch']",
            "[role='textbox']",
            "[role='searchbox']",
            "[role='combobox']",
            "[role='spinbutton']",
            "[role='slider']",
            "[contenteditable='true']",
            "input:not([type='hidden'])",  # Any input that's not hidden
            "label"  # Include labels as they're often useful for identification
        ]

        # Find elements for each selector
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                functional_elements.extend(elements)
            except Exception as e:
                print(f"Error finding elements for selector {selector}: {e}")

        # Remove duplicates while preserving order
        seen = set()
        unique_elements = []
        for element in functional_elements:
            try:
                element_id = element.id
                if element_id not in seen:
                    seen.add(element_id)
                    unique_elements.append(element)
            except:
                continue

        return unique_elements

    def _generate_xpaths(self, element_info, priorities):
        """Generate XPaths in standard format"""
        try:
            xpaths = []
            attributes = element_info.get('attributes', {})

            # First generate priority-based XPaths
            for priority in priorities:
                priority = priority.lower()
                if priority == 'id' and attributes.get('id'):
                    xpaths.append(f"//*[@id='{attributes['id']}']")
                elif priority == 'name' and attributes.get('name'):
                    xpaths.append(f"//*[@name='{attributes['name']}']")

            # Generate additional XPaths based on available attributes
            attr_combinations = []
            valid_attrs = [(k, v) for k, v in attributes.items() if v and k not in ['class']]

            if len(valid_attrs) >= 2:
                # AND combinations
                for i in range(len(valid_attrs)):
                    for j in range(i + 1, len(valid_attrs)):
                        attr1, val1 = valid_attrs[i]
                        attr2, val2 = valid_attrs[j]
                        if f"//*[@{attr1}='{val1}']" not in xpaths:  # Avoid duplicate base attributes
                            attr_combinations.append(
                                f"//*[@{attr1}='{val1}' and @{attr2}='{val2}']")

            # Add text-based XPath if text is present
            if element_info.get('text'):
                text_xpath = f"//*[text()='{element_info['text']}']"
                if text_xpath not in xpaths:
                    attr_combinations.append(text_xpath)

            # Add class-based XPath if class is present
            if attributes.get('class'):
                class_xpath = f"//*[contains(@class, '{attributes['class']}')]"
                if class_xpath not in xpaths:
                    attr_combinations.append(class_xpath)

            # Combine priority XPaths with attribute combinations
            xpaths.extend(attr_combinations)

            # Return up to 4 unique XPaths, prioritizing simpler ones first
            unique_xpaths = []
            seen = set()
            for xpath in xpaths:
                if xpath not in seen:
                    seen.add(xpath)
                    unique_xpaths.append(xpath)
                if len(unique_xpaths) == 4:
                    break

            # Pad with None if we have fewer than 4 XPaths
            while len(unique_xpaths) < 4:
                unique_xpaths.append(None)

            return tuple(unique_xpaths)

        except Exception as e:
            print(f"Error generating XPaths: {e}")
            return None, None, None, None

    def fetch_playwright_selectors(self, priorities):
        """Original selector fetching method using Playwright"""
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp("http://localhost:9214")
            page = browser.contexts[0].pages[0]

            selectors_by_priority = self.get_playwright_selectors(page)
            filtered_selectors = {priority: selectors for priority, selectors
                                  in selectors_by_priority.items() if priority in priorities}

            self.display_playwright_selectors(filtered_selectors)
            browser.close()

    def get_playwright_selectors(self, page):
        """Get selectors using Playwright"""
        selectors_by_priority = {
            "ID": set(),
            "Name": set(),
            "ClassName": set(),
            "LinkText": set(),
            "PartialLinkText": set(),
            "TagName": set(),
        }

        elements = page.query_selector_all("*")
        for element in elements:
            selector = self.get_priority_selector(element)
            if selector:
                if "@id=" in selector:
                    selectors_by_priority["ID"].add(selector)
                elif "@name=" in selector:
                    selectors_by_priority["Name"].add(selector)
                elif "contains(@class," in selector:
                    selectors_by_priority["ClassName"].add(selector)
                elif "text()=" in selector:
                    selectors_by_priority["LinkText"].add(selector)
                elif "contains(text()," in selector:
                    selectors_by_priority["PartialLinkText"].add(selector)
                elif selector.startswith("//"):
                    selectors_by_priority["TagName"].add(selector)

        return selectors_by_priority

    def get_priority_selector(self, element):
        """Generate priority-based selector for an element"""
        try:
            # Check for ID
            element_id = element.evaluate("element => element.id")
            if element_id:
                return f"//*[@id='{element_id}']"

            # Check for Name
            name_attr = element.evaluate("element => element.getAttribute('name')")
            if name_attr:
                return f"//*[@name='{name_attr}']"

            # Check for Class
            class_attr = element.evaluate("element => element.className")
            if class_attr:
                classes = class_attr.split()
                if classes:
                    class_conditions = " and ".join([f"contains(@class, '{cls}')" for cls in classes])
                    return f"//*[{class_conditions}]"

            # Check for Text
            inner_text = element.evaluate("element => element.innerText").strip() if element.evaluate(
                "element => element.innerText") else ""
            if inner_text:
                if len(inner_text) <= 50:  # Use exact text match for shorter text
                    return f"//*[text()='{inner_text}']"
                else:  # Use contains for longer text
                    return f"//*[contains(text(), '{inner_text[:50]}')]"

            # Fallback to tag name
            tag_name = element.evaluate("element => element.tagName.toLowerCase()")
            if tag_name:
                return f"//{tag_name}"

        except Exception as e:
            print(f"Error generating selector: {e}")
            return None

    def fetch_selenium_selectors(self):
        """Fetch alternative selectors using Selenium"""
        try:
            elements = self._get_functional_elements()
            formatted_outputs = []

            for elem in elements:
                elem_info = self._get_element_info(elem)
                if elem_info:
                    formatted_info = self._format_element_info(elem_info)
                    if formatted_info:
                        formatted_outputs.append(formatted_info)

            self.selector_tabs.alt_selectors_text.setText('\n'.join(formatted_outputs))

        except Exception as e:
            print(f"Error in fetch_selenium_selectors: {e}")

    def _get_functional_elements(self):
        """Get interactive elements from the page"""
        selector = ("button, input, select, textarea, a[href], [onclick], "
                   "[role='button'], [type='submit'], [role='link'], [role='textbox']")
        return self.driver.find_elements(By.CSS_SELECTOR, selector)

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

            info = {k: v for k, v in info.items() if v}

            # Generate XPaths
            xpath1, xpath2 = self._generate_dynamic_xpaths(element, attributes)
            if xpath1: info['xpath1'] = xpath1
            if xpath2: info['xpath2'] = xpath2

            return info

        except Exception as e:
            print(f"Error in _get_element_info: {e}")
            return None

    def _format_element_info(self, info):
        """Format element information for display"""
        if not info:
            return None

        output_lines = ['']
        attr_order = ['Tag', 'id', 'type', 'name', 'class', 'text', 'xpath1', 'xpath2']

        output_lines.extend(f"{attr}: {info[attr]}" for attr in attr_order if attr in info)
        output_lines.append('-------------')

        return '\n'.join(output_lines)

    def _generate_dynamic_xpaths(self, element, attributes):
        """Generate two unique dynamic XPaths"""
        try:
            tag = element.tag_name
            text = element.text.strip()

            xpath_candidates = []

            # ID-based XPath
            if attributes.get('id'):
                xpath_candidates.append(f"//*[@id='{attributes['id']}']")

            # Name-based XPath
            if attributes.get('name'):
                xpath_candidates.append(f"//*[@name='{attributes['name']}']")

            # Class-based XPath
            if attributes.get('class'):
                classes = attributes['class'].split()
                if len(classes) > 1:
                    xpath_candidates.append(
                        f"//*[contains(@class,'{classes[0]}') and contains(@class,'{classes[1]}')]")
                else:
                    xpath_candidates.append(f"//*[contains(@class,'{classes[0]}')]")

            # Text-based XPath
            if text:
                xpath_candidates.append(f"//*[text()='{text}']")

            # Ensure we have at least two unique XPaths
            unique_xpaths = list(dict.fromkeys(xpath_candidates))

            if len(unique_xpaths) < 2:
                unique_xpaths.append(f"//{tag}")

            return unique_xpaths[0], unique_xpaths[1] if len(unique_xpaths) > 1 else f"//{tag}"

        except Exception as e:
            print(f"Error generating XPaths: {str(e)}")
            return "//invalid", "//invalid"

    def display_playwright_selectors(self, selectors):
        """Display selectors in the All Selectors tab"""
        text_content = ""
        for priority, sel_list in selectors.items():
            if sel_list:  # Only show priorities that have selectors
                text_content += f"\n{priority} Selectors:\n\n"
                for selector in sel_list:
                    text_content += f"{selector}\n"

        self.selector_tabs.all_selectors_text.setText(text_content)

    def move_selected_lines(self):
        """Move selected lines to the bottom text area"""
        try:
            cursor = self.selectors_text.textCursor()

            if not cursor.hasSelection():
                QtWidgets.QMessageBox.information(self, "No Selection", "Please select text to move.")
                return

            selected_text = cursor.selectedText()

            # Check for POM structure
            moved_text_content = self.moved_text.toPlainText()
            if "# Locators" in moved_text_content or "# Functions" in moved_text_content:
                reply = QtWidgets.QMessageBox.question(
                    self,
                    'Clear Content',
                    'Text area contains a POM structure. Do you want to clear it to move new selectors?',
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No
                )
                if reply == QtWidgets.QMessageBox.Yes:
                    self.moved_text.clear()
                    self.move_count = 0
                else:
                    return

            # Process selected text
            valid_selectors = []
            found_selectors = False

            for line in selected_text.replace('\u2029', '\n').split('\n'):
                line = line.strip()
                if not line:
                    continue

                # Check if it's a selector line
                if ':' in line:
                    selector_type, value = [part.strip() for part in line.split(':', 1)]
                    selector_type = selector_type.lower()

                    # Skip empty values
                    if not value:
                        continue

                    found_selectors = True
                    if selector_type in ['id', 'name', 'class', 'type', 'text', 'xpath1', 'xpath2']:
                        valid_selectors.append(f"{selector_type}: {value}")

                # Handle direct XPath
                elif line.startswith('//'):
                    found_selectors = True
                    valid_selectors.append(line)

            if not found_selectors:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Invalid Selection",
                    "Please select lines containing selectors in format:\n" +
                    "- id: value\n" +
                    "- name: value\n" +
                    "- class: value\n" +
                    "- type: value\n" +
                    "- text: value\n" +
                    "- xpath1: //xpath\n" +
                    "- xpath2: //xpath\n" +
                    "- Direct xpath starting with '//'")
                return

            if not valid_selectors:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Invalid Selection",
                    "No valid selectors found in selection.")
                return

            # Add valid selectors to moved text area
            if self.moved_text.toPlainText().strip():
                self.moved_text.append('\n')
            self.moved_text.append('\n'.join(valid_selectors))
            self.move_count += len(valid_selectors)

            # Highlight selected text
            format = QtGui.QTextCharFormat()
            format.setBackground(QtGui.QColor("#d4edda"))
            cursor.mergeCharFormat(format)

            self.update_status(f"Moved Selectors: {self.move_count}")

        except Exception as e:
            print(f"Error in move_selected_lines: {e}")
            self.show_error_popup("Error moving selected lines. Please try again.")

    def validate_selection(self, text):
        """Validate that the selected text contains valid XPath selectors"""
        if not text:
            return False

        lines = text.split('\n')
        xpath_lines = [line.strip() for line in lines if line.strip().startswith("//")]
        return len(xpath_lines) > 0

    def on_moved_text_changed(self):
        """Handle changes in the moved text area"""
        current_text = self.moved_text.toPlainText()

        # Update line count if text was removed
        if len(current_text.split('\n')) < len(self.previous_text.split('\n')):
            self.move_count = len([line for line in current_text.split('\n') if line.strip().startswith("//")])
            self.update_status(f"Moved Selectors: {self.move_count}")

        self.previous_text = current_text

    def closeEvent(self, event):
        """Handle application close event"""
        try:
            self.driver.quit()
        except:
            pass
        event.accept()

    def add_to_moved_text(self, text):
        """Add validated text to the moved text area"""
        lines = text.split('\n')
        for line in lines:
            if line.strip().startswith("//"):
                # Check for duplicates
                existing_text = self.moved_text.toPlainText().strip().splitlines()
                if line.strip() not in existing_text:
                    self.moved_text.append(line.strip() + "\n")
                    self.move_count += 1
                    self.update_status(f"Moved Selector: {self.move_count}")
                else:
                    QtWidgets.QMessageBox.information(
                        self,
                        "Duplicate Selector",
                        f"Selector already exists:\n{line.strip()}"
                    )

    def generate_pom(self):
        """Generate Page Object Model code"""
        try:
            moved_text_content = self.moved_text.toPlainText().strip()

            if not moved_text_content:
                self.show_error_popup("No content to generate POM. Please select and move selectors first.")
                return

            if "# Locators" in moved_text_content:
                reply = QtWidgets.QMessageBox.question(
                    self,
                    'Clear Content',
                    'Text area contains a POM structure. Do you want to clear it and create a new POM?',
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No
                )
                if reply == QtWidgets.QMessageBox.Yes:
                    self.moved_text.clear()
                    self.update_status("Please select and move selectors to generate a new POM.")
                return

            # Split the content into lines and process each selector
            selectors = [line.strip() for line in moved_text_content.split('\n') if line.strip()]

            # Validate if we have any selectors
            if not selectors:
                self.show_error_popup("No selectors found. Please add selectors first.")
                return

            valid_selectors = []
            for selector in selectors:
                # Check if the selector has the correct format
                if ':' in selector or selector.startswith('//'):
                    valid_selectors.append(selector)

            if not valid_selectors:
                self.show_error_popup(
                    "No valid selectors found. Selectors should be in format 'type: value' or start with '//'")
                return

            class_name = self.class_name_entry.text() or "Test"
            pom_code = self.generate_pom_code(class_name, valid_selectors)

            if pom_code:
                self.moved_text.clear()
                self.moved_text.setText(pom_code)
                self.update_status(f"POM generated successfully in {self.language_combo.currentText()}")

        except Exception as e:
            self.show_error_popup(f"Error generating POM: {str(e)}")
            self.update_status("POM generation failed.")

    def extract_name_from_xpath(self, xpath):
        """Extract meaningful name from XPath selector"""
        try:
            # Remove leading '//' and split by '[' to get base element
            base = xpath.lstrip('/').split('[')[0]

            # Extract identifier from common XPath patterns
            if "@id='" in xpath:
                return xpath.split("@id='")[1].split("']")[0]
            elif "@name='" in xpath:
                return xpath.split("@name='")[1].split("']")[0]
            elif "@class='" in xpath:
                return self.sanitize_name(xpath.split("@class='")[1].split("']")[0])
            elif "@type='" in xpath:
                return self.sanitize_name(xpath.split("@type='")[1].split("']")[0])
            elif "text()='" in xpath:
                return self.sanitize_name(xpath.split("text()='")[1].split("']")[0])

            return self.sanitize_name(base)

        except Exception:
            return "element"

    def generate_pom_code(self, class_name, selectors):
        """Generate POM code based on selected language"""
        selected_language = self.language_combo.currentText()

        if selected_language == 'Python':
            return self.generate_python_pom(class_name, selectors)
        elif selected_language == 'Java':
            return self.generate_java_pom(class_name, selectors)
        elif selected_language == 'C#':
            return self.generate_csharp_pom(class_name, selectors)

        return self.generate_python_pom(class_name, selectors)  # Default to Python

    def process_selectors(self, selectors):
        """Process selectors for POM generation with specific format"""
        try:
            processed_elements = []

            for selector in selectors:
                selector = selector.strip()
                if not selector:
                    continue

                # Handle xpath1 and xpath2 format
                if ':' in selector:
                    selector_type, value = [part.strip() for part in selector.split(':', 1)]
                    selector_type = selector_type.lower()

                    if selector_type in ['xpath1', 'xpath2']:
                        # Extract meaningful name from XPath
                        if "[text()='" in value:
                            name = value.split("[text()='")[1].split("']")[0]
                        elif "[@" in value:
                            name = value.split("'")[1]
                        else:
                            name = f"element_{len(processed_elements)}"

                        processed_elements.append({
                            'name': self.sanitize_name(name),
                            'locator': value,
                            'locator_type': 'xpath'
                        })
                    else:
                        # Handle other selector types (id, name, class, etc.)
                        element_info = {
                            'name': self.sanitize_name(value),
                            'locator': value,
                            'locator_type': selector_type
                        }
                        if selector_type == 'class':
                            element_info['locator'] = f"//tag[@class='{value}']"
                            element_info['locator_type'] = 'xpath'
                        processed_elements.append(element_info)

            return processed_elements

        except Exception as e:
            print(f"Error processing selectors: {e}")
            return []

    def extract_base_name(self, value):
        """Extract base name from selector value"""
        try:
            # Remove special characters and convert to lowercase
            base_name = ''.join(c if c.isalnum() else '_' for c in value.lower())
            # Remove consecutive underscores
            base_name = '_'.join(filter(None, base_name.split('_')))
            # Remove trailing numbers and underscores
            base_name = base_name.rstrip('0123456789_')
            return base_name
        except Exception:
            return "element"

    def generate_python_pom(self, class_name, selectors):
        processed_elements = self.process_selectors(selectors)
        """Generate Python POM code"""
        elements = []
        for selector in selectors:
            name = self.extract_name(selector)
            elements.append({
                'name': name,
                'type': 'xpath',
                'locator': selector
            })

        pom_code = f"""import logging
import time
import utilities.custom_logger as cl
from base.selenium_driver import Selenium_Driver

class {class_name.capitalize()}Page(Selenium_Driver):

    log = cl.customLogger(logging.DEBUG)

    \"\"\"Page Object for {class_name}\"\"\"

    def __init__(self, driver):
        super().__init__(driver)
        self.driver = driver

    # Locators
    """
        # Add locators
        for element in processed_elements:
            name = element['name']
            locator = element['locator']
            pom_code += f"    __{name} = \"{locator}\"\n"

        pom_code += "\n    # Functions\n"

        # Add functions
        for element in processed_elements:
            name = element['name']
            locator_type = element['locator_type']

            pom_code += f"""    def {name}(self):
                return self.element(self.__{name}, locatorType='{locator_type}')\n\n"""

        return pom_code


    def generate_java_pom(self, class_name, selectors):
        """Generate Java POM code"""
        elements = []
        for selector in selectors:
            name = self.extract_name(selector)
            elements.append({
                'name': name,
                'type': 'xpath',
                'locator': selector
            })

        pom_code = f"""import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.openqa.selenium.support.ui.ExpectedConditions;

public class {class_name.capitalize()}Page {{
    private WebDriver driver;
    private WebDriverWait wait;

    // Locators
    """
        for element in elements:
            locator_name = f"__{element['name']}"
            pom_code += f"    private final String {locator_name} = \"{element['locator']}\";\n"

        pom_code += f"""
    public {class_name.capitalize()}Page(WebDriver driver) {{
        this.driver = driver;
        this.wait = new WebDriverWait(driver, 10);
        }}

        // Functions
        """
        for element in elements:
            function_name = element['name']
            locator_type = element['type']
            pom_code += f"""
    public WebElement get_{function_name}() {{
        wait.until(ExpectedConditions.presenceOfElementLocated(By.{locator_type}(__{function_name})));
    }}
        """
        pom_code += "}\n"
        return pom_code

    def generate_csharp_pom(self, class_name, selectors):
        """Generate C# POM code"""
        elements = []
        for selector in selectors:
            name = self.extract_name(selector)
            elements.append({
                'name': name,
                'type': 'xpath',
                'locator': selector
            })

        pom_code = f"""using OpenQA.Selenium;
using OpenQA.Selenium.Support.UI;
using System;

namespace Pages
{{
    public class {class_name.capitalize()}Page
    {{
        private IWebDriver _driver;
        private WebDriverWait _wait;

        // Locators
    """
        for element in elements:
            locator_name = f"__{element['name']}"
            pom_code += f"        private readonly string {locator_name} = \"{element['locator']}\";\n"

        pom_code += f"""
                public {class_name.capitalize()}Page(IWebDriver driver)
                {{
                    _driver = driver;
                    _wait = new WebDriverWait(driver, TimeSpan.FromSeconds(10));
                }}

                // Functions
        """
        for element in elements:
            function_name = element['name']
            locator_type = element['type']
            pom_code += f"""
                public IWebElement Get_{function_name}()
                {{
                    _wait.Until(SeleniumExtras.WaitHelpers.ExpectedConditions.ElementExists(By.{locator_type}(__{function_name})));
                }}
        """
        pom_code += "    }\n}"
        return pom_code

    def extract_name(self, selector):
        """Extract a suitable name from the selector"""
        try:
            # Handle ID based selectors
            if "@id='" in selector:
                name = selector.split("@id='")[1].split("']")[0]
                return self.sanitize_name(name)

            # Handle name based selectors
            elif "@name='" in selector:
                name = selector.split("@name='")[1].split("']")[0]
                return self.sanitize_name(name)

            # Handle class based selectors
            elif "contains(@class," in selector:
                # Extract class names from the selector
                classes = []
                parts = selector.split("contains(@class, '")
                for part in parts[1:]:  # Skip the first part before first contains
                    class_name = part.split("')")[0]
                    classes.append(class_name)
                return self.sanitize_name("_".join(classes))

            # Handle text based selectors
            elif "text()=" in selector:
                text = selector.split("text()='")[1].split("']")[0]
                return self.sanitize_name(text)

            # Handle contains text based selectors
            elif "contains(text()," in selector:
                text = selector.split("contains(text(), '")[1].split("')")[0]
                return self.sanitize_name(text)

            # Handle basic element selectors
            elif selector.startswith("//"):
                # Extract element type and any attributes
                parts = selector.split("/")
                element_type = parts[-1].split("[")[0]
                if "[" in selector:  # Has conditions
                    conditions = selector.split("[")[1].split("]")[0]
                    return f"{element_type}_{self.sanitize_name(conditions)}"
                return element_type

            return "element"

        except Exception as e:
            print(f"Error extracting name: {e}")
            return "element"

    def parse_selector(self, selector):
        """Parse selector to determine type and value and generate XPaths"""
        try:
            selector = selector.strip()

            # Split the selector if it contains a colon
            if ':' in selector:
                selector_type, value = [part.strip() for part in selector.split(':', 1)]
                selector_type = selector_type.lower()

                if selector_type == 'tag':
                    return None  # Skip Tag selectors

                # Generate corresponding XPaths
                xpath1, xpath2 = self.generate_xpaths(selector_type, value)

                return {
                    'name': self.sanitize_name(value),
                    'type': selector_type,
                    'locator': value,
                    'xpath1': xpath1,
                    'xpath2': xpath2
                }

            # Handle direct XPath selectors
            if selector.startswith('//'):
                return {
                    'name': self.extract_name_from_xpath(selector),
                    'type': 'xpath',
                    'locator': selector,
                    'xpath1': None,
                    'xpath2': None
                }

            return None

        except Exception as e:
            print(f"Error parsing selector: {e}")
            return None

    def generate_xpaths(self, selector_type, value):
        """Generate XPaths based on selector type and value"""
        try:
            xpath1 = None
            xpath2 = None

            if selector_type == 'id':
                xpath1 = f"//tag[@id='{value}']"
                xpath2 = f"//*[@id='{value}']"
            elif selector_type == 'name':
                xpath1 = f"//tag[@name='{value}']"
                xpath2 = f"//*[@name='{value}']"
            elif selector_type == 'class':
                xpath1 = f"//tag[@class='{value}']"
                xpath2 = f"//*[contains(@class, '{value}')]"
            elif selector_type == 'type':
                xpath1 = f"//tag[@type='{value}']"
                xpath2 = f"//*[@type='{value}']"
            elif selector_type == 'text':
                xpath1 = f"//tag[text()='{value}']"
                xpath2 = f"//*[contains(text(), '{value}')]"

            return xpath1, xpath2

        except Exception as e:
            print(f"Error generating XPaths: {e}")
            return None, None

    def extract_name_from_xpath(self, xpath):
        """Extract meaningful name from XPath selector"""
        try:
            if "@id='" in xpath:
                return xpath.split("@id='")[1].split("']")[0]
            elif "@name='" in xpath:
                return xpath.split("@name='")[1].split("']")[0]
            elif "text()=" in xpath:
                return xpath.split("text()='")[1].split("']")[0]
            elif "contains(@class," in xpath:
                classes = []
                parts = xpath.split("contains(@class, '")
                for part in parts[1:]:
                    class_name = part.split("')")[0]
                    classes.append(class_name)
                return "_".join(classes)
            else:
                # Extract the element name from the last part of the XPath
                parts = xpath.split('/')
                last_part = parts[-1].split('[')[0]
                return last_part

        except Exception:
            return "element"

    def sanitize_name(self, name):
        """Sanitize the name for use as a variable name"""
        try:
            # Replace special characters with underscore
            sanitized = ''.join(c if c.isalnum() else '_' for c in name)
            # Remove consecutive underscores
            sanitized = '_'.join(filter(None, sanitized.split('_')))
            # Ensure it starts with a letter or underscore
            if sanitized[0].isdigit():
                sanitized = f"_{sanitized}"
            return sanitized.lower()
        except Exception:
            return "element"

    def set_styles(self):
        self.setStyleSheet("""
               QMainWindow {
                   background-color: #f8f9fa;
               }
               QPushButton {
                   background-color: #6c757d;
                   color: white;
                   border: 1px solid #5a6268;
                   padding: 6px;
                   min-width: 80px;
                   border-radius: 4px;
                   font-weight: 500;
               }
               QPushButton:hover {
                   background-color: #5a6268;
                   border: 1px solid #545b62;
               }
               QPushButton:pressed {
                   background-color: #545b62;
                   border: 2px solid #4e555b;
                   padding: 7px 5px 5px 7px;
               }
               QPushButton#fetch_button, QPushButton#generate_button {
                   background-color: #28a745;
                   border: 1px solid #28a745;
               }
               QPushButton#fetch_button:hover, QPushButton#generate_button:hover {
                   background-color: #218838;
                   border: 1px solid #1e7e34;
               }
               QPushButton#fetch_button:pressed, QPushButton#generate_button:pressed {
                   background-color: #1e7e34;
                   border: 2px solid #1c7430;
               }
               QPushButton#clear_button {
                   background-color: #dc3545;
                   border: 1px solid #dc3545;
               }
               QPushButton#clear_button:hover {
                   background-color: #c82333;
                   border: 1px solid #bd2130;
               }
               QPushButton#clear_button:pressed {
                   background-color: #bd2130;
                   border: 2px solid #b21f2d;
               }
               QPushButton:disabled {
                   background-color: #cccccc;
                   border: 1px solid #bbbbbb;
                   color: #666666;
               }
               QLineEdit {
                   background-color: #ffffff;
                   border: 1px solid #ced4da;
                   padding: 6px;
                   border-radius: 4px;
                   color: #495057;
               }
               QLineEdit:focus {
                   border: 2px solid #80bdff;
                   background-color: #ffffff;
               }
               QTextEdit {
                   background-color: #ffffff;
                   border: 1px solid #ced4da;
                   border-radius: 4px;
                   padding: 4px;
                   color: #495057;
               }
               QTextEdit:focus {
                   border: 2px solid #80bdff;
                   background-color: #ffffff;
               }
               QLabel {
                   color: #495057;
                   font-weight: 500;
                   padding: 4px;
               }
               QComboBox {
                   background-color: #ffffff;
                   border: 1px solid #ced4da;
                   padding: 5px;
                   border-radius: 4px;
                   color: #495057;
                   min-width: 100px;
               }
               QComboBox:hover {
                   border: 1px solid #b8bdc2;
                   background-color: #f8f9fa;
               }
               QComboBox:on {
                   border: 2px solid #80bdff;
               }
               QComboBox::drop-down {
                   border: none;
                   padding-right: 4px;
               }
               QComboBox::down-arrow {
                   width: 12px;
                   height: 12px;
                   margin-right: 5px;
               }
               QStatusBar {
                   background-color: #f8f9fa;
                   color: #495057;
                   border-top: 1px solid #dee2e6;
                   padding: 4px;
               }
               QMessageBox {
                   background-color: #ffffff;
               }
               QMessageBox QPushButton {
                   min-width: 70px;
                   padding: 5px 15px;
               }
           """)

    def update_status(self, message):
        """Update the status bar message"""
        self.status_bar.showMessage(message)

    def show_error_popup(self, message):
        """Show error message in a popup"""
        QtWidgets.QMessageBox.critical(self, 'Error', message)

    def get_priorities(self):
        """Get the list of priorities from the input field"""
        priorities_text = self.priority_entry.text().strip()
        if not priorities_text:
            return []
        return [p.strip() for p in priorities_text.split(',')]

    def save_to_file(self):
        """Save generated POM to file"""
        try:
            content = self.moved_text.toPlainText()
            if not content.strip():
                self.show_error_popup("No content available to save.")
                return

            selected_language = self.language_combo.currentText()
            if selected_language == "Java":
                file_filter = "Java Files (*.java)"
            elif selected_language == "C#":
                file_filter = "C# Files (*.cs)"
            else:
                file_filter = "Python Files (*.py)"

            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "Save POM", "", file_filter)

            if file_path:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                QtWidgets.QMessageBox.information(
                    self, "Success", f"File saved successfully: {file_path}")
                self.update_status(f"File saved: {file_path}")

        except Exception as e:
            self.show_error_popup(f"Error saving file: {str(e)}")
            self.update_status("Failed to save file")

    def clear_generated_pom(self):
        """Clear the generated POM content"""
        if self.moved_text.toPlainText().strip():
            reply = QtWidgets.QMessageBox.question(
                self,
                'Clear Content',
                'Are you sure you want to clear the current content?',
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No
            )

            if reply == QtWidgets.QMessageBox.Yes:
                self.moved_text.clear()
                self.move_count = 0
                self.update_status("Content cleared")



def main():
    """Main application entry point"""
    app = QtWidgets.QApplication(sys.argv)
    app.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
    app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    window = EnhancedPOMGenerator()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
