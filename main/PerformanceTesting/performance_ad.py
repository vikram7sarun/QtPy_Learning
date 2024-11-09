import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QTextEdit,
                             QProgressBar, QTabWidget, QGroupBox, QCheckBox,
                             QSpinBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPalette, QColor
import psutil
import time
import json
from datetime import datetime


class PerformanceWorker(QThread):
    progress = pyqtSignal(int)
    result = pyqtSignal(dict)
    log = pyqtSignal(str)

    def __init__(self, test_config):
        super().__init__()
        self.test_config = test_config
        self.running = True

    def run(self):
        results = {}
        total_steps = len([x for x in self.test_config.values() if x])
        current_step = 0

        try:
            if self.test_config.get('memory', False):
                self.log.emit("Starting memory test...")
                results['memory'] = self.measure_memory()
                current_step += 1
                self.progress.emit(int(current_step * 100 / total_steps))

            if self.test_config.get('cpu', False):
                self.log.emit("Starting CPU test...")
                results['cpu'] = self.measure_cpu()
                current_step += 1
                self.progress.emit(int(current_step * 100 / total_steps))

            if self.test_config.get('response', False):
                self.log.emit("Starting response time test...")
                results['response'] = self.measure_response()
                current_step += 1
                self.progress.emit(int(current_step * 100 / total_steps))

            self.result.emit(results)

        except Exception as e:
            self.log.emit(f"Error during test: {str(e)}")

    def measure_memory(self):
        process = psutil.Process()
        return {
            'current': process.memory_info().rss / 1024 / 1024,  # MB
            'percent': process.memory_percent()
        }

    def measure_cpu(self):
        return {
            'percent': psutil.cpu_percent(interval=1),
            'cores': psutil.cpu_count()
        }

    def measure_response(self):
        start_time = time.time()
        QApplication.processEvents()
        return {
            'response_time': (time.time() - start_time) * 1000  # ms
        }


class PerformanceTestUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Performance Test Tool')
        self.setMinimumSize(800, 600)

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)

        # Left panel (controls)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Test configuration group
        config_group = QGroupBox("Test Configuration")
        config_layout = QVBoxLayout()

        # Add checkboxes
        self.memory_check = QCheckBox("Memory Usage")
        self.cpu_check = QCheckBox("CPU Usage")
        self.response_check = QCheckBox("Response Time")

        config_layout.addWidget(self.memory_check)
        config_layout.addWidget(self.cpu_check)
        config_layout.addWidget(self.response_check)

        # Add duration spinner
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Duration (s):"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 3600)
        self.duration_spin.setValue(60)
        duration_layout.addWidget(self.duration_spin)
        config_layout.addLayout(duration_layout)

        config_group.setLayout(config_layout)
        left_layout.addWidget(config_group)

        # Add control buttons
        self.start_button = QPushButton("Start Tests")
        self.start_button.clicked.connect(self.start_tests)
        left_layout.addWidget(self.start_button)

        self.progress_bar = QProgressBar()
        left_layout.addWidget(self.progress_bar)

        left_layout.addStretch()

        # Right panel (results)
        right_panel = QTabWidget()

        # Results tab
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        right_panel.addTab(self.results_text, "Results")

        # Log tab
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        right_panel.addTab(self.log_text, "Log")

        # Add panels to main layout
        layout.addWidget(left_panel)
        layout.addWidget(right_panel, stretch=1)

        self.show()

    def start_tests(self):
        if not any([self.memory_check.isChecked(),
                    self.cpu_check.isChecked(),
                    self.response_check.isChecked()]):
            self.log_message("Please select at least one test to run.")
            return

        self.progress_bar.setValue(0)
        self.results_text.clear()

        config = {
            'memory': self.memory_check.isChecked(),
            'cpu': self.cpu_check.isChecked(),
            'response': self.response_check.isChecked(),
            'duration': self.duration_spin.value()
        }

        self.worker = PerformanceWorker(config)
        self.worker.progress.connect(self.update_progress)
        self.worker.result.connect(self.show_results)
        self.worker.log.connect(self.log_message)
        self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def show_results(self, results):
        text = "Performance Test Results\n"
        text += "=" * 50 + "\n\n"

        for test_name, values in results.items():
            text += f"{test_name.upper()} TEST RESULTS:\n"
            text += "-" * 20 + "\n"
            for metric, value in values.items():
                if isinstance(value, float):
                    text += f"{metric}: {value:.2f}\n"
                else:
                    text += f"{metric}: {value}\n"
            text += "\n"

        self.results_text.setText(text)
        self.log_message("Tests completed successfully.")

    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")


def apply_dark_theme(app):
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)


def main():
    try:
        app = QApplication(sys.argv)
        apply_dark_theme(app)
        window = PerformanceTestUI()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error starting application: {str(e)}")


if __name__ == "__main__":
    main()