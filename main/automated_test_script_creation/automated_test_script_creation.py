import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QTextEdit, QPushButton, QFileDialog, QApplication
import openai  # Ensure the OpenAI library is installed

# Set your OpenAI API key here (or securely handle it in production)
openai.api_key = "your_openai_api_key"


class TestScriptGeneratorApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Main layout
        layout = QVBoxLayout()

        # Title label
        title_label = QLabel("Automated Test Script Generator")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title_label)

        # Input field for requirements
        self.requirements_label = QLabel("Enter Requirements or User Story:")
        self.requirements_text = QTextEdit()
        layout.addWidget(self.requirements_label)
        layout.addWidget(self.requirements_text)

        # Button to generate script
        self.generate_button = QPushButton("Generate Test Script")
        self.generate_button.clicked.connect(self.generate_script)
        layout.addWidget(self.generate_button)

        # Display area for generated script
        self.script_label = QLabel("Generated Test Script:")
        self.script_display = QTextEdit()
        self.script_display.setReadOnly(True)
        layout.addWidget(self.script_label)
        layout.addWidget(self.script_display)

        # Button to save script
        self.save_button = QPushButton("Save Script to File")
        self.save_button.clicked.connect(self.save_script)
        layout.addWidget(self.save_button)

        # Set the layout
        self.setLayout(layout)
        self.setWindowTitle("Automated Test Script Generator")
        self.resize(500, 600)

    def generate_script(self):
        # Get user input requirements
        requirements = self.requirements_text.toPlainText()

        # Generate the test script with OpenAI API
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",  # Specify model
                prompt=f"Generate a Python test script using pytest for the following requirements:\n{requirements}",
                max_tokens=150,
                n=1,
                stop=None,
                temperature=0.5,
            )

            # Display generated script
            generated_script = response.choices[0].text.strip()
            self.script_display.setPlainText(generated_script)

        except Exception as e:
            self.script_display.setPlainText(f"Error generating script: {e}")

    def save_script(self):
        # Open a file dialog to save the generated script
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Script", "", "Python Files (*.py);;All Files (*)",
                                                   options=options)

        if file_path:
            with open(file_path, "w") as file:
                file.write(self.script_display.toPlainText())
            QtWidgets.QMessageBox.information(self, "Success", f"Script saved to {file_path}")


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = TestScriptGeneratorApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = TestScriptGeneratorApp()
    window.show()
    sys.exit(app.exec_())
