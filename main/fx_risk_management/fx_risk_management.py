from qtpy.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFormLayout, QMessageBox
from fx_calculator import calculate_position_size


class FXRiskManagement(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FX Risk Management Tool")
        self.setGeometry(100, 100, 400, 300)

        # Layout setup
        layout = QVBoxLayout()
        form_layout = QFormLayout()

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

        # Result Display
        self.result_label = QLabel("Position Size: -")

        # Add widgets to layout
        layout.addLayout(form_layout)
        layout.addWidget(self.calculate_button)
        layout.addWidget(self.result_label)
        self.setLayout(layout)

    def calculate_position_size(self):
        try:
            # Retrieve inputs
            account_balance = float(self.account_balance_input.text())
            risk_percent = float(self.risk_percent_input.text())
            stop_loss_pips = float(self.stop_loss_pips_input.text())
            pip_value = float(self.pip_value_input.text())

            # Calculate position size
            position_size = calculate_position_size(account_balance, risk_percent, stop_loss_pips, pip_value)

            # Update the result
            self.result_label.setText(f"Position Size: {position_size:.2f} units")
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter valid numeric values.")


if __name__ == "__main__":
    app = QApplication([])
    window = FXRiskManagement()
    window.show()
    app.exec_()
