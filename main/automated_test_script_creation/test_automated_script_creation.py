# test_automated_script_creation.py
import pytest
from PyQt5.QtWidgets import QApplication
from automated_test_script_creation import TestScriptGeneratorApp


@pytest.fixture(scope="module")
def app():
    """Fixture for creating the QApplication instance."""
    return QApplication([])


def test_ui_elements(qtbot, app):
    """Test the main elements in the Test Script Generator UI."""
    main_window = TestScriptGeneratorApp()
    qtbot.addWidget(main_window)

    # Verify that the main elements are present
    assert main_window.requirements_text.toPlainText() == ""
    assert main_window.script_display.toPlainText() == ""
    assert main_window.windowTitle() == "Automated Test Script Generator"


def test_generate_script_button(qtbot, app):
    """Test clicking the 'Generate Test Script' button."""
    main_window = TestScriptGeneratorApp()
    qtbot.addWidget(main_window)

    # Enter text in the requirements field
    main_window.requirements_text.setPlainText("Verify login functionality")

    # Click generate button
    qtbot.mouseClick(main_window.generate_button, qtbot.LeftButton)

    # Verify that script display is populated (requires actual API key to function)
    assert main_window.script_display.toPlainText() != ""

