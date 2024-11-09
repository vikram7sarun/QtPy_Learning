import sys
import subprocess
import os
import socket
import platform
import psutil
import requests
import json
from datetime import datetime
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (QVBoxLayout, QLabel, QTextEdit, QPushButton,
                             QCheckBox, QFileDialog, QProgressBar, QGroupBox,
                             QGridLayout, QMessageBox)
from PyQt5.QtCore import QThread, pyqtSignal
from importlib.metadata import version


class HealthCheckWorker(QThread):
    progress = pyqtSignal(str, str)  # message, status (success/warning/error)
    finished = pyqtSignal()

    def __init__(self, checks_to_run):
        super().__init__()
        self.checks_to_run = checks_to_run

    def run(self):
        for check in self.checks_to_run:
            check()
        self.finished.emit()


class HealthCheckApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.worker = None
        self.check_results = []

    def initUI(self):
        main_layout = QVBoxLayout()

        # Title label with styling
        title_label = QLabel("Environment Health Check Dashboard")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Create groups of checks
        checks_group = QGroupBox("Available Checks")
        checks_layout = QGridLayout()

        self.software_check = QCheckBox("Required Software")
        self.configuration_check = QCheckBox("Environment Configurations")
        self.network_check = QCheckBox("Network Connectivity")
        self.os_hardware_check = QCheckBox("OS and Hardware")
        self.dependency_check = QCheckBox("Python Dependencies")
        self.port_check = QCheckBox("Common Ports")
        self.disk_performance_check = QCheckBox("Disk Performance")

        # Add checkboxes to grid layout
        checks_layout.addWidget(self.software_check, 0, 0)
        checks_layout.addWidget(self.configuration_check, 0, 1)
        checks_layout.addWidget(self.network_check, 1, 0)
        checks_layout.addWidget(self.os_hardware_check, 1, 1)
        checks_layout.addWidget(self.dependency_check, 2, 0)
        checks_layout.addWidget(self.port_check, 2, 1)
        checks_layout.addWidget(self.disk_performance_check, 3, 0)

        checks_group.setLayout(checks_layout)
        main_layout.addWidget(checks_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        main_layout.addWidget(self.progress_bar)

        # Buttons layout
        button_layout = QGridLayout()

        self.run_button = QPushButton("Run Checks")
        self.run_button.clicked.connect(self.run_checks)
        self.run_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)

        self.save_button = QPushButton("Save Report")
        self.save_button.clicked.connect(self.save_report)
        self.save_button.setEnabled(False)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #008CBA;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #007099;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)

        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self.select_all_checks)
        self.select_all_button.setStyleSheet("""
            QPushButton {
                background-color: #555555;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #333333;
            }
        """)

        button_layout.addWidget(self.select_all_button, 0, 0)
        button_layout.addWidget(self.run_button, 0, 1)
        button_layout.addWidget(self.save_button, 0, 2)

        main_layout.addLayout(button_layout)

        # Results display
        results_label = QLabel("Check Results:")
        results_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        main_layout.addWidget(results_label)

        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        self.result_display.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        main_layout.addWidget(self.result_display)

        # Set main window properties
        self.setLayout(main_layout)
        self.setWindowTitle("Environment Health Check Dashboard")
        self.resize(600, 700)
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #cccccc;
                border-radius: 4px;
                margin-top: 0.5em;
                padding-top: 0.5em;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QCheckBox {
                spacing: 5px;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
            }
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)

    def select_all_checks(self):
        checkboxes = [
            self.software_check, self.configuration_check, self.network_check,
            self.os_hardware_check, self.dependency_check, self.port_check,
            self.disk_performance_check
        ]
        for checkbox in checkboxes:
            checkbox.setChecked(True)

    def run_checks(self):
        self.check_results = []
        self.result_display.clear()
        self.progress_bar.setValue(0)
        self.save_button.setEnabled(False)
        self.run_button.setEnabled(False)

        checks_to_run = []
        if self.software_check.isChecked():
            checks_to_run.append(self.check_software)
        if self.configuration_check.isChecked():
            checks_to_run.append(self.check_configuration)
        if self.network_check.isChecked():
            checks_to_run.append(self.check_network)
        if self.os_hardware_check.isChecked():
            checks_to_run.append(self.check_os_hardware)
        if self.dependency_check.isChecked():
            checks_to_run.append(self.check_dependencies)
        if self.port_check.isChecked():
            checks_to_run.append(self.check_common_ports)
        if self.disk_performance_check.isChecked():
            checks_to_run.append(self.check_disk_performance)

        if not checks_to_run:
            QMessageBox.warning(self, "Warning", "Please select at least one check to run.")
            self.run_button.setEnabled(True)
            return

        self.worker = HealthCheckWorker(checks_to_run)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_checks_completed)
        self.worker.start()

    def update_progress(self, message, status):
        color = {
            "success": "green",
            "warning": "orange",
            "error": "red"
        }.get(status, "black")

        self.result_display.append(f'<span style="color: {color}">{message}</span>')
        self.check_results.append({"message": message, "status": status})

        # Update progress bar
        total_checks = sum(1 for checkbox in [
            self.software_check, self.configuration_check, self.network_check,
            self.os_hardware_check, self.dependency_check, self.port_check,
            self.disk_performance_check
        ] if checkbox.isChecked())

        progress = (len(self.check_results) / total_checks) * 100
        self.progress_bar.setValue(int(progress))

    def on_checks_completed(self):
        self.run_button.setEnabled(True)
        self.save_button.setEnabled(True)
        QMessageBox.information(self, "Complete", "All health checks completed!")

    def check_software(self):
        required_software = {
            "python": "python --version",
            "git": "git --version",
            "pip": "pip --version",
            "node": "node --version"  # Added Node.js check
        }

        for software, command in required_software.items():
            version = self.get_software_version(command)
            if version:
                self.worker.progress.emit(
                    f"✔ {software.capitalize()} is installed. Version: {version}",
                    "success"
                )
            else:
                self.worker.progress.emit(
                    f"✘ {software.capitalize()} is NOT installed.",
                    "error"
                )

    def check_dependencies(self):
        required_packages = ['requests', 'psutil', 'PyQt5']

        for package in required_packages:
            try:
                # Using importlib.metadata instead of pkg_resources
                pkg_version = version(package)
                self.worker.progress.emit(
                    f"✔ {package} is installed (version {pkg_version})",
                    "success"
                )
            except Exception:
                self.worker.progress.emit(
                    f"✘ {package} is NOT installed",
                    "error"
                )

    def check_common_ports(self):
        common_ports = {
            80: "HTTP",
            443: "HTTPS",
            3306: "MySQL",
            5432: "PostgreSQL",
            27017: "MongoDB"
        }

        for port, service in common_ports.items():
            if self.is_port_in_use(port):
                self.worker.progress.emit(
                    f"✔ Port {port} ({service}) is in use",
                    "warning"
                )
            else:
                self.worker.progress.emit(
                    f"✔ Port {port} ({service}) is available",
                    "success"
                )

    def check_disk_performance(self):
        try:
            # Simple write/read test
            test_file = 'disk_speed_test.tmp'

            # Write test
            start_time = datetime.now()
            with open(test_file, 'wb') as f:
                f.write(os.urandom(1024 * 1024 * 10))  # Write 10MB
            write_time = (datetime.now() - start_time).total_seconds()

            # Read test
            start_time = datetime.now()
            with open(test_file, 'rb') as f:
                f.read()
            read_time = (datetime.now() - start_time).total_seconds()

            # Clean up
            os.remove(test_file)

            write_speed = 10 / write_time  # MB/s
            read_speed = 10 / read_time  # MB/s

            self.worker.progress.emit(
                f"Disk Write Speed: {write_speed:.2f} MB/s",
                "success" if write_speed > 50 else "warning"
            )
            self.worker.progress.emit(
                f"Disk Read Speed: {read_speed:.2f} MB/s",
                "success" if read_speed > 100 else "warning"
            )
        except Exception as e:
            self.worker.progress.emit(
                f"Failed to test disk performance: {str(e)}",
                "error"
            )

    def get_software_version(self, command):
        try:
            output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
            return output.strip()
        except subprocess.CalledProcessError:
            return None

    def check_configuration(self):
        # Check environment variables
        important_vars = ['PATH', 'PYTHONPATH', 'JAVA_HOME', 'NODE_PATH']

        for var in important_vars:
            value = os.getenv(var)
            if value:
                self.worker.progress.emit(
                    f"✔ {var} is set: {value[:50]}{'...' if len(value) > 50 else ''}",
                    "success"
                )
            else:
                self.worker.progress.emit(
                    f"ℹ {var} is not set",
                    "warning"
                )

        # Check Python virtual environment
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            self.worker.progress.emit("✔ Running in a virtual environment", "success")
        else:
            self.worker.progress.emit("ℹ Not running in a virtual environment", "warning")

        # Check system-wide Python packages location
        site_packages = next((p for p in sys.path if 'site-packages' in p), None)
        if site_packages:
            self.worker.progress.emit(f"✔ Site packages location: {site_packages}", "success")
        else:
            self.worker.progress.emit("✘ Could not determine site-packages location", "error")

    def check_network(self):
        # Check internet connectivity
        try:
            response = requests.get('https://8.8.8.8', timeout=5)
            self.worker.progress.emit(
                "✔ Internet connectivity check passed",
                "success"
            )
        except requests.RequestException:
            self.worker.progress.emit(
                "✘ Internet connectivity check failed",
                "error"
            )

        # Check DNS resolution
        try:
            socket.gethostbyname('www.google.com')
            self.worker.progress.emit(
                "✔ DNS resolution check passed",
                "success"
            )
        except socket.gaierror:
            self.worker.progress.emit(
                "✘ DNS resolution check failed",
                "error"
            )

        # Check local network interface
        try:
            interfaces = psutil.net_if_addrs()
            for interface, addrs in interfaces.items():
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        self.worker.progress.emit(
                            f"✔ Network interface {interface}: {addr.address}",
                            "success"
                        )
        except Exception as e:
            self.worker.progress.emit(
                f"✘ Failed to check network interfaces: {str(e)}",
                "error"
            )

    def check_os_hardware(self):
        # OS Information
        os_info = platform.platform()
        self.worker.progress.emit(f"Operating System: {os_info}", "success")

        # CPU Information
        cpu_count = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq().current if psutil.cpu_freq() else "Unknown"
        cpu_percent = psutil.cpu_percent(interval=1)

        self.worker.progress.emit(f"CPU Cores: {cpu_count}", "success")
        self.worker.progress.emit(f"CPU Frequency: {cpu_freq:.2f} MHz", "success")
        self.worker.progress.emit(
            f"CPU Usage: {cpu_percent}%",
            "success" if cpu_percent < 80 else "warning"
        )

        # Memory Information
        memory = psutil.virtual_memory()
        total_gb = memory.total / (1024 ** 3)
        available_gb = memory.available / (1024 ** 3)
        used_percent = memory.percent

        self.worker.progress.emit(
            f"Total Memory: {total_gb:.2f} GB",
            "success"
        )
        self.worker.progress.emit(
            f"Available Memory: {available_gb:.2f} GB ({100 - used_percent:.1f}% free)",
            "success" if used_percent < 80 else "warning"
        )

        # Disk Information
        for partition in psutil.disk_partitions():
            try:
                disk = psutil.disk_usage(partition.mountpoint)
                total_gb = disk.total / (1024 ** 3)
                free_gb = disk.free / (1024 ** 3)
                used_percent = disk.percent

                self.worker.progress.emit(
                    f"Partition {partition.mountpoint}:",
                    "success"
                )
                self.worker.progress.emit(
                    f"  - Total Space: {total_gb:.2f} GB",
                    "success"
                )
                self.worker.progress.emit(
                    f"  - Free Space: {free_gb:.2f} GB ({100-used_percent:.1f}% free)",
                    "success" if used_percent < 80 else "warning"
                )
            except Exception as e:
                self.worker.progress.emit(
                    f"Failed to check partition {partition.mountpoint}: {str(e)}",
                    "error"
                )
                # Temperature sensors (if available)
                try:
                    temperatures = psutil.sensors_temperatures()
                    if temperatures:
                        for name, entries in temperatures.items():
                            for entry in entries:
                                self.worker.progress.emit(
                                    f"Temperature {name}: {entry.current}°C",
                                    "success" if entry.current < 80 else "warning"
                                )
                except Exception:
                    self.worker.progress.emit(
                        "Temperature sensors not available",
                        "warning"
                    )

    @staticmethod
    def is_port_in_use(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return False
            except socket.error:
                return True

    def save_report(self):
        options = QFileDialog.Options()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_filename = f"health_check_report_{timestamp}"

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save Report",
            default_filename,
            "JSON Files (*.json);;HTML Files (*.html);;Text Files (*.txt);;All Files (*)",
            options=options
        )

        if not file_path:
            return

        try:
            report_data = {
                "timestamp": datetime.now().isoformat(),
                "system_info": {
                    "os": platform.platform(),
                    "python_version": sys.version,
                    "cpu_count": psutil.cpu_count(),
                    "total_memory": f"{psutil.virtual_memory().total / (1024 ** 3):.2f} GB"
                },
                "results": self.check_results
            }

            # Handle different file formats
            if file_path.endswith('.json'):
                with open(file_path, 'w') as f:
                    json.dump(report_data, f, indent=4)

            elif file_path.endswith('.html'):
                html_content = self.generate_html_report(report_data)
                with open(file_path, 'w') as f:
                    f.write(html_content)

            else:  # Default to text format
                with open(file_path, 'w') as f:
                    f.write(f"Environment Health Check Report\n")
                    f.write(f"Generated: {report_data['timestamp']}\n\n")
                    f.write("System Information:\n")
                    for key, value in report_data['system_info'].items():
                        f.write(f"{key}: {value}\n")
                    f.write("\nCheck Results:\n")
                    for result in report_data['results']:
                        f.write(f"{result['status'].upper()}: {result['message']}\n")

            QMessageBox.information(
                self,
                "Success",
                f"Report saved successfully to:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save report:\n{str(e)}"
            )

    def generate_html_report(self, report_data):
        """Generate a formatted HTML report."""
        status_colors = {
            "success": "#4CAF50",
            "warning": "#FF9800",
            "error": "#F44336"
        }

        html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Environment Health Check Report</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 40px;
                        background-color: #f5f5f5;
                    }}
                    .container {{
                        background-color: white;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 30px;
                    }}
                    .section {{
                        margin-bottom: 20px;
                    }}
                    .result-item {{
                        padding: 10px;
                        margin: 5px 0;
                        border-radius: 4px;
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                    }}
                    th, td {{
                        padding: 8px;
                        text-align: left;
                        border-bottom: 1px solid #ddd;
                    }}
                    th {{
                        background-color: #f8f9fa;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Environment Health Check Report</h1>
                        <p>Generated: {report_data['timestamp']}</p>
                    </div>

                    <div class="section">
                        <h2>System Information</h2>
                        <table>
                            <tr>
                                <th>Property</th>
                                <th>Value</th>
                            </tr>
            """

        for key, value in report_data['system_info'].items():
            html += f"""
                            <tr>
                                <td>{key.replace('_', ' ').title()}</td>
                                <td>{value}</td>
                            </tr>
                """

        html += """
                        </table>
                    </div>

                    <div class="section">
                        <h2>Check Results</h2>
            """

        for result in report_data['results']:
            color = status_colors.get(result['status'], '#000000')
            html += f"""
                        <div class="result-item" style="background-color: {color}20; border-left: 4px solid {color}">
                            {result['message']}
                        </div>
                """

        html += """
                    </div>
                </div>
            </body>
            </html>
            """

        return html


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for a modern look
    window = HealthCheckApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()