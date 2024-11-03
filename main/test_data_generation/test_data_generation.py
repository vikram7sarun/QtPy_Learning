import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QComboBox, QSpinBox, QPushButton, QTableWidget, QTableWidgetItem, \
    QFileDialog, QApplication
from faker import Faker
import pandas as pd

class TestDataGeneratorApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.faker = Faker()

    def initUI(self):
        # Set up the layout
        layout = QVBoxLayout()

        # Title
        title_label = QLabel("Synthetic Test Data Generator")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title_label)

        # Data type selection
        self.data_type_label = QLabel("Select Data Type:")
        self.data_type_combo = QComboBox()
        self.data_type_combo.addItems(["Name", "Email", "Phone Number", "Address", "Date", "Transaction ID"])
        layout.addWidget(self.data_type_label)
        layout.addWidget(self.data_type_combo)

        # Number of records
        self.records_label = QLabel("Number of Records:")
        self.records_spinbox = QSpinBox()
        self.records_spinbox.setRange(1, 1000)
        self.records_spinbox.setValue(10)
        layout.addWidget(self.records_label)
        layout.addWidget(self.records_spinbox)

        # Generate button
        self.generate_button = QPushButton("Generate Data")
        self.generate_button.clicked.connect(self.generate_data)
        layout.addWidget(self.generate_button)

        # Table for displaying generated data
        self.table_widget = QTableWidget()
        layout.addWidget(self.table_widget)

        # Save button
        self.save_button = QPushButton("Save Data to CSV")
        self.save_button.clicked.connect(self.save_data)
        layout.addWidget(self.save_button)

        # Set layout
        self.setLayout(layout)
        self.setWindowTitle("Test Data Generator")
        self.resize(400, 400)

    def generate_data(self):
        # Get user inputs
        data_type = self.data_type_combo.currentText()
        num_records = self.records_spinbox.value()

        # Generate data based on selected type
        data = []
        for _ in range(num_records):
            if data_type == "Name":
                data.append(self.faker.name())
            elif data_type == "Email":
                data.append(self.faker.email())
            elif data_type == "Phone Number":
                data.append(self.faker.phone_number())
            elif data_type == "Address":
                data.append(self.faker.address())
            elif data_type == "Date":
                data.append(self.faker.date())
            elif data_type == "Transaction ID":
                data.append(self.faker.uuid4())

        # Display data in the table
        self.table_widget.setRowCount(num_records)
        self.table_widget.setColumnCount(1)
        self.table_widget.setHorizontalHeaderLabels([data_type])
        for row, item in enumerate(data):
            self.table_widget.setItem(row, 0, QTableWidgetItem(item))

        # Save data in a DataFrame for exporting
        self.data_df = pd.DataFrame(data, columns=[data_type])

    def save_data(self):
        # Open file dialog to save file
        if hasattr(self, 'data_df'):
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Data", "", "CSV Files (*.csv);;All Files (*)", options=options)
            if file_path:
                self.data_df.to_csv(file_path, index=False)
                QtWidgets.QMessageBox.information(self, "Success", f"Data saved to {file_path}")

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = TestDataGeneratorApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = TestDataGeneratorApp()
    window.show()
    sys.exit(app.exec_())
