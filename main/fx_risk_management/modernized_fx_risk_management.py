from PyQt5.QtCore import Qt
from qtpy.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFormLayout, QMessageBox
from fx_calculator import calculate_position_size


class FXRiskManagement(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FX Risk Management Tool")
        self.setGeometry(100, 100, 400, 300)

        # Layout setup with adjusted margins and spacing
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        form_layout = QFormLayout()
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(8)

        # Account Balance
        self.account_balance_input = QLineEdit()
        form_layout.addRow("Account Balance ($):", self.account_balance_input)

        # Risk Percentage
        self.risk_percent_input = QLineEdit()
        form_layout.addRow("Risk Percentage (%):", self.risk_percent_input)

        # Stop Loss in Pips
        self.stop_loss_pips_input = QLineEdit()
        form_layout.addRow("Stop Loss (Pips):", self.stop_loss_pips_input)

        # Pip Value
        self.pip_value_input = QLineEdit()
        form_layout.addRow("Pip Value ($):", self.pip_value_input)

        # Calculate Button
        self.calculate_button = QPushButton("Calculate Position Size")
        self.calculate_button.clicked.connect(self.calculate_position_size)

        # Adding form layout and button to main layout
        layout.addLayout(form_layout)
        layout.addWidget(self.calculate_button, alignment=Qt.AlignCenter)

        # Set main layout
        self.setLayout(layout)
        self.setStyleSheet("""
                    QWidget {
                        background-color: #f4f4f4;
                        font-family: Arial, sans-serif;
                    }
                    QLabel {
                        color: #333333;
                    }
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border-radius: 5px;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)

    def calculate_position_size(self):
        try:
            account_balance = float(self.account_balance_input.text())
            risk_percent = float(self.risk_percent_input.text())
            stop_loss_pips = float(self.stop_loss_pips_input.text())
            pip_value = float(self.pip_value_input.text())

            position_size = calculate_position_size(account_balance, risk_percent, stop_loss_pips, pip_value)

            QMessageBox.information(self, "Position Size", f"Your position size is: {position_size:.2f} units")
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter valid numeric values.")


if __name__ == "__main__":
    app = QApplication([])
    window = FXRiskManagement()
    window.show()
    app.exec_()
