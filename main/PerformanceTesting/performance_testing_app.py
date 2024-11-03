import sys
import requests
import time
import psutil
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import random


class SimulationThread(QtCore.QThread):
    update_signal = QtCore.pyqtSignal(int, float, int, float,
                                      float)  # User index, response time, status code, CPU, memory
    finished_signal = QtCore.pyqtSignal(list, list, list)  # Send response times, CPU, memory usage after completion

    def __init__(self, api_endpoint, num_users):
        super().__init__()
        self.api_endpoint = api_endpoint
        self.num_users = num_users
        self.simulation_running = True

    def run(self):
        response_times = []
        cpu_usages = []
        memory_usages = []

        for i in range(self.num_users):
            if not self.simulation_running:
                break

            # Measure CPU and memory before request
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory_usage = psutil.virtual_memory().percent
            cpu_usages.append(cpu_usage)
            memory_usages.append(memory_usage)

            start_time = time.time()
            try:
                response = requests.get(self.api_endpoint)
                response_time = time.time() - start_time
                status_code = response.status_code
                response_times.append(response_time)  # Collect response time
            except requests.RequestException:
                response_time = None
                status_code = 0  # Represents a failed request

            # Emit the data for real-time display
            self.update_signal.emit(i + 1, response_time, status_code, cpu_usage, memory_usage)
            time.sleep(0.05)  # Small delay between requests

        self.finished_signal.emit(response_times, cpu_usages, memory_usages)

    def stop(self):
        self.simulation_running = False


class PerformanceTestingApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.simulation_thread = None

    def initUI(self):
        layout = QVBoxLayout()

        # Title
        title_label = QLabel("Performance Testing Simulator")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title_label)

        # Input for API endpoint
        self.api_label = QLabel("API Endpoint:")
        self.api_input = QLineEdit()
        layout.addWidget(self.api_label)
        layout.addWidget(self.api_input)

        # Input for number of users
        self.users_label = QLabel("Number of Virtual Users:")
        self.users_input = QLineEdit()
        layout.addWidget(self.users_label)
        layout.addWidget(self.users_input)

        # Start simulation button
        self.start_button = QPushButton("Start Simulation")
        self.start_button.clicked.connect(self.start_simulation)
        layout.addWidget(self.start_button)

        # Stop simulation button
        self.stop_button = QPushButton("Stop Simulation")
        self.stop_button.clicked.connect(self.stop_simulation)
        layout.addWidget(self.stop_button)

        # Text area for displaying metrics
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        layout.addWidget(self.output_display)

        # Resource usage summary
        self.resource_summary_label = QLabel("Resource Usage Summary:")
        layout.addWidget(self.resource_summary_label)
        self.resource_summary_display = QTextEdit()
        self.resource_summary_display.setReadOnly(True)
        layout.addWidget(self.resource_summary_display)

        # Matplotlib figure for plotting
        self.figure, self.ax = plt.subplots(2, 1, figsize=(5, 8))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Set layout
        self.setLayout(layout)
        self.setWindowTitle("Performance Testing Simulator")
        self.resize(600, 800)

    def start_simulation(self):
        # Get the API endpoint and number of users from input
        api_endpoint = self.api_input.text()
        try:
            num_users = int(self.users_input.text())
        except ValueError:
            self.output_display.append("Error: Please enter a valid number of users.")
            return

        if not api_endpoint:
            self.output_display.append("Error: Please enter a valid API endpoint.")
            return

        # Create and start the simulation thread
        self.simulation_thread = SimulationThread(api_endpoint, num_users)
        self.simulation_thread.update_signal.connect(self.update_metrics)
        self.simulation_thread.finished_signal.connect(self.simulation_finished)
        self.simulation_thread.start()

        self.output_display.append("Starting load simulation...")

    def stop_simulation(self):
        if self.simulation_thread is not None:
            self.simulation_thread.stop()
            self.output_display.append("Simulation stopped.")

    def update_metrics(self, user_index, response_time, status_code, cpu_usage, memory_usage):
        # Display CPU and memory usage warnings if thresholds are exceeded
        if cpu_usage > 80:
            self.output_display.append(f"Warning: High CPU usage detected ({cpu_usage}%)")
        if memory_usage > 75:
            self.output_display.append(f"Warning: High memory usage detected ({memory_usage}%)")

        # Log response time, CPU, and memory usage
        if response_time is not None:
            self.output_display.append(
                f"User {user_index} - Response time: {response_time:.4f} sec, Status: {status_code}, "
                f"CPU: {cpu_usage}%, Memory: {memory_usage}%"
            )
        else:
            self.output_display.append(f"User {user_index} - Request failed")

        # Update plots for response time, CPU, and memory usage
        self.ax[0].plot(user_index, response_time, 'bo') if response_time else None
        self.ax[1].plot(user_index, cpu_usage, 'ro', label="CPU Usage" if user_index == 1 else "")
        self.ax[1].plot(user_index, memory_usage, 'go', label="Memory Usage" if user_index == 1 else "")
        self.ax[0].set_title("Response Time")
        self.ax[0].set_xlabel("User Count")
        self.ax[0].set_ylabel("Response Time (seconds)")
        self.ax[1].set_title("CPU and Memory Usage")
        self.ax[1].set_xlabel("User Count")
        self.ax[1].set_ylabel("Usage (%)")
        self.ax[1].legend(loc="upper right")
        self.canvas.draw()

    def simulation_finished(self, response_times, cpu_usages, memory_usages):
        self.output_display.append("Simulation complete.\n")

        # Calculate average CPU and memory usage
        if cpu_usages and memory_usages:
            avg_cpu = sum(cpu_usages) / len(cpu_usages)
            avg_memory = sum(memory_usages) / len(memory_usages)
            summary_text = (
                f"Average CPU Usage: {avg_cpu:.2f}%\n"
                f"Average Memory Usage: {avg_memory:.2f}%\n"
                f"Max CPU Usage: {max(cpu_usages):.2f}%\n"
                f"Max Memory Usage: {max(memory_usages):.2f}%"
            )
        else:
            summary_text = "No data for CPU or memory usage."

        # Display resource usage summary
        self.resource_summary_display.setPlainText(summary_text)


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = PerformanceTestingApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
