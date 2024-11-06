import pytest
from PyQt5.QtWidgets import QApplication
from automated_testing_dashboard import TestDashboard

@pytest.fixture(scope="module")
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def dashboard_instance(app, qtbot):
    dashboard = TestDashboard()
    qtbot.addWidget(dashboard)  # Allows pytest-qt to control the widget
    return dashboard

def test_initialization(dashboard_instance):
    assert dashboard_instance.passed_tests == 0
    assert dashboard_instance.failed_tests == 0
    assert dashboard_instance.execution_time == 0
