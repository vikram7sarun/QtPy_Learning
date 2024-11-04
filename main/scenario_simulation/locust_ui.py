import sys
import subprocess
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QLineEdit, QSpinBox, QPushButton, QTextEdit, QFormLayout


class LocustWorker(QtCore.QThread):
    output_signal = QtCore.pyqtSignal(str)
    finished_signal = QtCore.pyqtSignal()

    def __init__(self, url, users, spawn_rate):
        super().__init__()
        self.url = url
        self.users = users
        self.spawn_rate = spawn_rate
        self.process = None

    def run(self):
        # Set up Locust command
        locust_command = [
            "locust",
            "-f", "locustfile.py",
            "--headless",
            "-u", str(self.users),
            "-r", str(self.spawn_rate),
            "--host", self.url,
            "--only-summary",
            "--run-time", "1m"  # Run for 1 minute; adjust as needed
        ]

        # Start Locust subprocess
        self.process = subprocess.Popen(
            locust_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            universal_newlines=True
        )

        # Capture and emit output line by line
        for line in self.process.stdout:
            self.output_signal.emit(line.strip())

        # Wait for process to complete
        self.process.wait()
        self.finished_signal.emit()

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process = None


class LocustSimulationApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.locust_worker = None

    def initUI(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Title label
        title_label = QLabel("Scenario Simulation with Locust")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title_label)

        # Target URL
        self.url_label = QLabel("Target URL:")
        self.url_input = QLineEdit("http://localhost:8080")
        form_layout.addRow("Target URL:", self.url_input)

        # Number of Users
        self.users_input = QSpinBox()
        self.users_input.setRange(1, 1000)
        self.users_input.setValue(50)
        form_layout.addRow("Number of Users:", self.users_input)

        # Spawn Rate
        self.spawn_rate_input = QSpinBox()
        self.spawn_rate_input.setRange(1, 100)
        self.spawn_rate_input.setValue(5)
        form_layout.addRow("Spawn Rate (users/sec):", self.spawn_rate_input)

        # Run and Stop buttons
        self.run_button = QPushButton("Run Simulation")
        self.run_button.clicked.connect(self.run_simulation)
        layout.addWidget(self.run_button)

        self.stop_button = QPushButton("Stop Simulation")
        self.stop_button.clicked.connect(self.stop_simulation)
        layout.addWidget(self.stop_button)

        # Output Display for metrics
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        layout.addWidget(QLabel("Simulation Output:"))
        layout.addWidget(self.output_display)

        # Set layout
        layout.addLayout(form_layout)
        self.setLayout(layout)
        self.setWindowTitle("Scenario Simulation with Locust")
        self.resize(500, 600)

    def run_simulation(self):
        # Retrieve user inputs
        url = self.url_input.text()
        users = self.users_input.value()
        spawn_rate = self.spawn_rate_input.value()

        # Clear previous output
        self.output_display.clear()
        self.output_display.append("Starting Locust simulation...\n")

        # Start LocustWorker thread
        self.locust_worker = LocustWorker(url, users, spawn_rate)
        self.locust_worker.output_signal.connect(self.update_output)
        self.locust_worker.finished_signal.connect(self.simulation_finished)
        self.locust_worker.start()

    def stop_simulation(self):
        # Stop LocustWorker thread if running
        if self.locust_worker and self.locust_worker.isRunning():
            self.locust_worker.stop()
            self.output_display.append("\nSimulation stopped.")
            self.locust_worker = None

    def update_output(self, line):
        # Update output display with new line from Locust
        self.output_display.append(line)
        self.output_display.verticalScrollBar().setValue(self.output_display.verticalScrollBar().maximum())

    def simulation_finished(self):
        # Called when the Locust simulation finishes
        self.output_display.append("\nSimulation complete.")
        self.locust_worker = None


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = LocustSimulationApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
