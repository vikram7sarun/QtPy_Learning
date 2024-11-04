import sys
import subprocess
import os
import socket
import platform
import psutil
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QTextEdit, QPushButton, QCheckBox, QFileDialog


class HealthCheckApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Title label
        title_label = QLabel("Environment Health Checks")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title_label)

        # Checkboxes for specific checks
        self.software_check = QCheckBox("Check Required Software (Python, Git)")
        self.configuration_check = QCheckBox("Check Environment Configurations (e.g., PATH)")
        self.network_check = QCheckBox("Check Network Connectivity")
        self.os_hardware_check = QCheckBox("Check Operating System and Hardware")
        self.dependency_check = QCheckBox("Check Python Package Dependencies")

        layout.addWidget(self.software_check)
        layout.addWidget(self.configuration_check)
        layout.addWidget(self.network_check)
        layout.addWidget(self.os_hardware_check)

        # Run Checks button
        self.run_button = QPushButton("Run Checks")
        self.run_button.clicked.connect(self.run_checks)
        layout.addWidget(self.run_button)

        # Display area for results
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        layout.addWidget(QLabel("Check Results:"))
        layout.addWidget(self.result_display)

        # Save Report button
        self.save_button = QPushButton("Save Report")
        self.save_button.clicked.connect(self.save_report)
        layout.addWidget(self.save_button)

        # Set layout
        self.setLayout(layout)
        self.setWindowTitle("Environment Health Checks")
        self.resize(500, 500)

    def run_checks(self):
        # Clear previous results
        self.result_display.clear()

        # Perform each selected check
        if self.software_check.isChecked():
            self.result_display.append("Running Software Check...")
            self.check_software()

        if self.configuration_check.isChecked():
            self.result_display.append("Running Configuration Check...")
            self.check_configuration()

        if self.network_check.isChecked():
            self.result_display.append("Running Network Check...")
            self.check_network()

        if self.os_hardware_check.isChecked():
            self.result_display.append("Running Operating System and Hardware Check...")
            self.check_os_hardware()

    def check_software(self):
        # Check Python version
        python_version = self.get_software_version("python --version")
        if python_version:
            self.result_display.append(f"✔ Python is installed. Version: {python_version}")
        else:
            self.result_display.append("✘ Python is NOT installed.")

        # Check Git version
        git_version = self.get_software_version("git --version")
        if git_version:
            self.result_display.append(f"✔ Git is installed. Version: {git_version}")
        else:
            self.result_display.append("✘ Git is NOT installed.")

    def get_software_version(self, command):
        try:
            # Capture the output of the version command
            output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
            return output.strip()  # Remove any extra whitespace or newline
        except subprocess.CalledProcessError:
            return None

    def check_configuration(self):
        # Example check: Verify PATH environment variable is set
        path_var = os.getenv("PATH")
        if path_var:
            self.result_display.append("✔ PATH environment variable is set.")
        else:
            self.result_display.append("✘ PATH environment variable is NOT set.")

    def check_network(self):
        # Check network connectivity by pinging a known server
        hostname = "8.8.8.8"  # Google DNS server
        port = 53  # DNS service port

        if self.is_host_reachable(hostname, port):
            self.result_display.append("✔ Network connectivity check passed.")
        else:
            self.result_display.append("✘ Network connectivity check failed.")

    def is_host_reachable(self, hostname, port, timeout=5):
        try:
            with socket.create_connection((hostname, port), timeout):
                return True
        except OSError:
            return False

    def check_os_hardware(self):
        # OS Information
        os_info = platform.platform()
        self.result_display.append(f"Operating System: {os_info}")

        # CPU Information
        cpu_count = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq().current if psutil.cpu_freq() else "Unknown"
        self.result_display.append(f"CPU Count: {cpu_count}")
        self.result_display.append(f"CPU Frequency: {cpu_freq} MHz")

        # Memory Information
        memory_info = psutil.virtual_memory()
        self.result_display.append(f"Total Memory: {memory_info.total / (1024 ** 3):.2f} GB")
        self.result_display.append(f"Available Memory: {memory_info.available / (1024 ** 3):.2f} GB")

        # Disk Space Information
        disk_info = psutil.disk_usage('/')
        self.result_display.append(f"Total Disk Space: {disk_info.total / (1024 ** 3):.2f} GB")
        self.result_display.append(f"Free Disk Space: {disk_info.free / (1024 ** 3):.2f} GB")

    def save_report(self):
        # Open a file dialog to save the report
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Report", "", "Text Files (*.txt);;All Files (*)",
                                                   options=options)

        if file_path:
            try:
                # Write the contents of the result display to the selected file
                with open(file_path, "w") as file:
                    file.write(self.result_display.toPlainText())
                # Notify the user of a successful save
                QtWidgets.QMessageBox.information(self, "Success", f"Report saved to {file_path}")
            except Exception as e:
                # Notify the user if there was an error during the save process
                QtWidgets.QMessageBox.warning(self, "Error", f"Failed to save report: {e}")


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = HealthCheckApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
