import pytest
from PyQt5.QtWidgets import QApplication
from test_data_generation import TestDataGeneratorApp

@pytest.fixture(scope="module")
def app():
    """Set up and yield QApplication instance."""
    app = QApplication.instance() or QApplication([])
    yield app
    app.quit()  # Ensure cleanup

def test_app_launch(qtbot, app):
    """Verify TestDataGeneratorApp launches and displays UI elements."""
    main_window = TestDataGeneratorApp()
    qtbot.addWidget(main_window)

    main_window.show()  # Show the main window to trigger the UI

    # Check if the title matches
    assert main_window.windowTitle() == "Test Data Generator"

    # Simulate actions and validate outcomes
    main_window.records_spinbox.setValue(5)
    main_window.generate_button.click()
    assert main_window.table_widget.rowCount() == 5
