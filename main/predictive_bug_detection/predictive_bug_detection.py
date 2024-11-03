import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QLineEdit, QPushButton, QFormLayout, QMessageBox
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import numpy as np

class PredictiveBugDetectionApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.model = self.train_model()  # Train model on initialization

    def initUI(self):
        # Main layout
        layout = QVBoxLayout()

        # Title
        title_label = QLabel("Predictive Bug Detection")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title_label)

        # Form layout for input fields
        form_layout = QFormLayout()

        # Input fields for code metrics
        self.lines_of_code_input = QLineEdit()
        self.cyclomatic_complexity_input = QLineEdit()
        self.change_frequency_input = QLineEdit()
        self.defect_count_input = QLineEdit()

        form_layout.addRow("Lines of Code:", self.lines_of_code_input)
        form_layout.addRow("Cyclomatic Complexity:", self.cyclomatic_complexity_input)
        form_layout.addRow("Change Frequency:", self.change_frequency_input)
        form_layout.addRow("Defect Count:", self.defect_count_input)

        layout.addLayout(form_layout)

        # Predict button
        self.predict_button = QPushButton("Predict Bug Likelihood")
        self.predict_button.clicked.connect(self.predict_bug_likelihood)
        layout.addWidget(self.predict_button)

        # Set layout and window title
        self.setLayout(layout)
        self.setWindowTitle("Predictive Bug Detection")
        self.resize(400, 300)

    def train_model(self):
        # Example historical data for training (mock data for demonstration)
        data = {
            "lines_of_code": [120, 250, 180, 90, 300],
            "cyclomatic_complexity": [10, 20, 15, 5, 25],
            "change_frequency": [5, 15, 10, 2, 20],
            "defect_count": [2, 5, 3, 0, 7],
            "has_bug": [1, 1, 1, 0, 1]  # Target variable
        }

        # Convert to DataFrame
        df = pd.DataFrame(data)
        X = df[["lines_of_code", "cyclomatic_complexity", "change_frequency", "defect_count"]]
        y = df["has_bug"]

        # Train a simple RandomForest model
        model = RandomForestClassifier(random_state=42)
        model.fit(X, y)
        return model

    def predict_bug_likelihood(self):
        # Get values from input fields
        try:
            lines_of_code = int(self.lines_of_code_input.text())
            cyclomatic_complexity = int(self.cyclomatic_complexity_input.text())
            change_frequency = int(self.change_frequency_input.text())
            defect_count = int(self.defect_count_input.text())

            # Prepare data for prediction
            input_data = pd.DataFrame([[lines_of_code, cyclomatic_complexity, change_frequency, defect_count]],
                                      columns=["lines_of_code", "cyclomatic_complexity", "change_frequency", "defect_count"])

            # Prediction
            prediction = self.model.predict(input_data)[0]
            probability = self.model.predict_proba(input_data)[0][prediction]

            # Display result
            result_text = ("High likelihood of bugs" if prediction == 1 else "Low likelihood of bugs")
            QMessageBox.information(self, "Prediction Result", f"{result_text}\nProbability: {probability:.2f}")

        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter valid numbers for all fields.")

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = PredictiveBugDetectionApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
