import sys
import time
from datetime import datetime, timedelta
import requests
from typing import List, Dict
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
                             QLabel, QMessageBox, QProgressBar, QFrame, QScrollArea,
                             QSpacerItem, QSizePolicy, QComboBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QTextCursor, QColor, QPalette


class ChatMessage:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
        self.timestamp = datetime.now()


class HuggingFaceThread(QThread):
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    MODELS = {
        "BlenderBot": "facebook/blenderbot-400M-distill",
        "DialoGPT": "microsoft/DialoGPT-medium",
        "BLOOM": "bigscience/bloom-560m",
        "OPT": "facebook/opt-350m"
    }

    def __init__(self, api_key: str, messages: List[ChatMessage], model_name: str = "BlenderBot"):
        super().__init__()
        self.api_key = api_key
        self.messages = messages
        self.model = self.MODELS.get(model_name, self.MODELS["BlenderBot"])
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def run(self):
        try:
            conversation = " ".join([msg.content for msg in self.messages[-3:]])
            API_URL = f"https://api-inference.huggingface.co/models/{self.model}"

            response = requests.post(
                API_URL,
                headers=self.headers,
                json={"inputs": conversation}
            )

            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    if isinstance(result[0], dict):
                        generated_text = result[0].get('generated_text', '')
                    else:
                        generated_text = str(result[0])
                else:
                    generated_text = str(result)

                generated_text = generated_text.strip()
                if not generated_text:
                    generated_text = "I apologize, but I'm not sure how to respond to that."

                self.response_received.emit(generated_text)
            else:
                error_msg = f"API Error: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f"\nDetails: {error_detail}"
                except:
                    pass
                self.error_occurred.emit(error_msg)

        except Exception as e:
            self.error_occurred.emit(f"Error: {str(e)}")


class ModelSelector(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QComboBox {
                border: 1px solid #E5E5E5;
                border-radius: 6px;
                padding: 5px 10px;
                background: white;
                min-width: 150px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #E5E5E5;
                selection-background-color: #6B4BCC;
                selection-color: white;
            }
        """)
        self.addItems(HuggingFaceThread.MODELS.keys())


class ChatbotUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api_key = "YOUR_HUGGING_FACE_API_KEY"  # Replace with your API key
        self.messages: List[ChatMessage] = []
        self.current_group = None
        self.last_message_role = None
        self.init_ui()

    def init_ui(self):
        """Initialize the UI components."""
        self.setWindowTitle('AI Assistant')
        self.setMinimumSize(900, 700)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Chat container
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setSpacing(0)
        chat_layout.setContentsMargins(0, 0, 0, 0)

        # Messages area
        self.messages_area = QScrollArea()
        self.messages_area.setWidgetResizable(True)
        self.messages_area.setFrameStyle(QFrame.NoFrame)
        self.messages_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.messages_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #FFFFFF;
            }
            QScrollBar:vertical {
                width: 8px;
                background: #F1F1F1;
            }
            QScrollBar::handle:vertical {
                background: #C1C1C1;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # Messages container
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setSpacing(0)
        self.messages_layout.addStretch()

        self.messages_area.setWidget(self.messages_container)
        chat_layout.addWidget(self.messages_area)

        # Input area
        input_container = QWidget()
        input_container.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-top: 1px solid #E5E5E5;
            }
        """)
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(20, 20, 20, 20)

        # Model selector
        model_layout = QHBoxLayout()
        model_label = QLabel("Model:")
        model_label.setStyleSheet("color: #666666; margin-right: 5px;")
        self.model_selector = ModelSelector()
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_selector)
        model_layout.addStretch()
        input_layout.addLayout(model_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #F0F0F0;
                height: 2px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #6B4BCC;
            }
        """)
        input_layout.addWidget(self.progress_bar)

        # Input field and buttons
        input_row = QHBoxLayout()

        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("Message (Enter to send, Shift+Enter for new line)")
        self.input_field.setMaximumHeight(100)
        self.input_field.setStyleSheet("""
            QTextEdit {
                border: 1px solid #E5E5E5;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                background-color: #FFFFFF;
            }
            QTextEdit:focus {
                border: 1px solid #6B4BCC;
            }
        """)
        input_row.addWidget(self.input_field)

        # Buttons
        button_container = QHBoxLayout()
        button_container.setSpacing(8)

        send_button = QPushButton('Send')
        send_button.clicked.connect(self.send_message)
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #6B4BCC;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5A3FB8;
            }
            QPushButton:pressed {
                background-color: #4A2FA4;
            }
        """)
        button_container.addWidget(send_button)

        clear_button = QPushButton('Clear')
        clear_button.clicked.connect(self.clear_chat)
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #F0F0F0;
                color: #1A1A1A;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #E5E5E5;
            }
            QPushButton:pressed {
                background-color: #D9D9D9;
            }
        """)
        button_container.addWidget(clear_button)

        input_row.addLayout(button_container)
        input_layout.addLayout(input_row)

        # Add to main layout
        main_layout.addWidget(chat_container, stretch=1)
        main_layout.addWidget(input_container)

        # Connect input field signals
        self.input_field.installEventFilter(self)

        # Initialize chat with welcome message
        self.add_message("assistant", "Hello! I'm your AI assistant. How can I help you today?")

    def add_message(self, role: str, content: str):
        """Add a message to the chat."""
        message = ChatMessage(role, content)
        self.messages.append(message)

        # Add message to UI
        message_widget = QFrame()
        message_layout = QVBoxLayout(message_widget)

        text_label = QLabel(content)
        text_label.setWordWrap(True)
        text_label.setStyleSheet(f"""
            QLabel {{
                background-color: {'#F0F0F0' if role == 'user' else '#FFFFFF'};
                padding: 10px;
                border-radius: 8px;
                font-size: 14px;
            }}
        """)

        message_layout.addWidget(text_label)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, message_widget)

        # Scroll to bottom
        QTimer.singleShot(100, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        """Scroll to the bottom of the messages area."""
        scrollbar = self.messages_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def send_message(self):
        """Send user message and get AI response."""
        message = self.input_field.toPlainText().strip()
        if not message:
            return

        # Clear input field
        self.input_field.clear()

        # Add user message to chat
        self.add_message("user", message)

        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        # Get selected model
        selected_model = self.model_selector.currentText()

        # Create and start Hugging Face thread
        self.ai_thread = HuggingFaceThread(self.api_key, self.messages, selected_model)
        self.ai_thread.response_received.connect(self.handle_ai_response)
        self.ai_thread.error_occurred.connect(self.handle_error)
        self.ai_thread.finished.connect(lambda: self.progress_bar.setVisible(False))
        self.ai_thread.start()

    def handle_ai_response(self, response: str):
        """Handle the AI response."""
        self.add_message("assistant", response)

    def handle_error(self, error_message: str):
        """Handle any errors that occur."""
        if "Authorization" in error_message:
            error_display = "API Key error. Please check your Hugging Face API key."
        elif "API Error: 404" in error_message:
            error_display = "Model not found. Please try a different model."
        elif "API Error: 503" in error_message:
            error_display = "Service temporarily unavailable. Please try again later."
        else:
            error_display = f"An error occurred: {error_message}"

        QMessageBox.critical(self, "Error", error_display)
        self.progress_bar.setVisible(False)

    def clear_chat(self):
        """Clear the chat history."""
        self.messages.clear()

        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.add_message("assistant", "Chat history cleared. How can I help you?")

    def eventFilter(self, obj, event):
        if obj == self.input_field and event.type() == event.KeyPress:
            if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier:
                self.send_message()
                return True
        return super().eventFilter(obj, event)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setFont(QFont('Segoe UI', 10))

    chatbot = ChatbotUI()
    chatbot.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()