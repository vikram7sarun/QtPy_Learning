import sys
import time
from datetime import datetime, timedelta
from typing import List, Dict
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
                             QLabel, QMessageBox, QProgressBar, QFrame, QScrollArea,
                             QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QTextCursor, QColor, QPalette


class SmoothScrollArea(QScrollArea):
    def __init__(self):
        super().__init__()
        self.animation = QPropertyAnimation(self.verticalScrollBar(), b"value")
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.setDuration(300)  # 300ms for smooth scroll

    def smooth_scroll_to(self, value):
        self.animation.stop()
        self.animation.setStartValue(self.verticalScrollBar().value())
        self.animation.setEndValue(value)
        self.animation.start()


class TimeStampLabel(QLabel):
    def __init__(self, timestamp, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 11px;
                margin: 2px 10px;
            }
        """)
        self.setText(self.format_timestamp(timestamp))

    def format_timestamp(self, timestamp):
        now = datetime.now()
        if timestamp.date() == now.date():
            return timestamp.strftime("Today at %I:%M %p")
        elif timestamp.date() == now.date() - timedelta(days=1):
            return timestamp.strftime("Yesterday at %I:%M %p")
        else:
            return timestamp.strftime("%B %d at %I:%M %p")


class MessageGroup(QWidget):
    def __init__(self, role, parent=None):
        super().__init__(parent)
        self.role = role
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(2)
        self.layout.setContentsMargins(10, 5, 10, 5)

        self.messages: List[MessageWidget] = []

        # Group style
        if role == "user":
            self.setStyleSheet("MessageGroup { background-color: #F7F7F8; }")
        else:
            self.setStyleSheet("MessageGroup { background-color: #FFFFFF; }")

    def add_message(self, message_widget):
        self.messages.append(message_widget)
        self.layout.addWidget(message_widget)


class MessageWidget(QFrame):
    def __init__(self, role: str, content: str, timestamp: datetime, parent=None):
        super().__init__(parent)
        self.role = role
        self.timestamp = timestamp
        self.init_ui(content)

    def init_ui(self, content: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(40, 5, 40, 5)

        # Message header with timestamp
        header_layout = QHBoxLayout()

        # Avatar and name
        avatar_label = QLabel()
        avatar_size = QSize(24, 24)
        avatar_label.setFixedSize(avatar_size)

        if self.role == "user":
            avatar_label.setStyleSheet("""
                QLabel {
                    background-color: #007AFF;
                    border-radius: 12px;
                    color: white;
                    font-weight: bold;
                }
            """)
            avatar_label.setText("U")
            name_label = QLabel("You")
        else:
            avatar_label.setStyleSheet("""
                QLabel {
                    background-color: #6B4BCC;
                    border-radius: 12px;
                    color: white;
                    font-weight: bold;
                }
            """)
            avatar_label.setText("A")
            name_label = QLabel("NessQ Assistant")

        avatar_label.setAlignment(Qt.AlignCenter)

        name_label.setStyleSheet("""
            QLabel {
                color: #1A1A1A;
                font-weight: bold;
                font-size: 13px;
            }
        """)

        # Add timestamp
        timestamp_label = TimeStampLabel(self.timestamp)

        header_layout.addWidget(avatar_label)
        header_layout.addWidget(name_label)
        header_layout.addWidget(timestamp_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Message content
        content_widget = QTextEdit()
        content_widget.setPlainText(content)
        content_widget.setReadOnly(True)
        content_widget.setFrameStyle(QFrame.NoFrame)
        content_widget.setStyleSheet("""
            QTextEdit {
                border: none;
                background-color: transparent;
                color: #1A1A1A;
                font-size: 14px;
                line-height: 1.5;
            }
        """)

        # Auto-adjust height
        content_widget.document().setDocumentMargin(0)
        doc_height = int(content_widget.document().size().height())
        content_widget.setMinimumHeight(doc_height + 10)
        content_widget.setMaximumWidth(700)

        layout.addWidget(content_widget)


class ChatbotUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api_key = ""  # Add your OpenAI API key here
        self.messages: List[ChatMessage] = []
        self.current_group = None
        self.last_message_role = None
        self.init_ui()

    def init_ui(self):
        """Initialize the UI components with enhanced styling."""
        self.setWindowTitle('AI Assistant')
        self.setMinimumSize(900, 700)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Enhanced window style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFFFFF;
            }
        """)

        # Chat container
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setSpacing(0)
        chat_layout.setContentsMargins(0, 0, 0, 0)

        # Create smooth scroll area
        self.scroll_area = SmoothScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameStyle(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #FFFFFF;
            }
            QScrollBar:vertical {
                width: 10px;
                background: #F1F1F1;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #C1C1C1;
                min-height: 30px;
                border-radius: 5px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #A1A1A1;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                border: none;
                background: none;
                height: 0px;
            }
        """)

        # Messages container
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setSpacing(0)
        self.messages_layout.addStretch()

        self.scroll_area.setWidget(self.messages_container)
        chat_layout.addWidget(self.scroll_area)

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

        # Progress bar with improved style
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

        # Buttons with enhanced style
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

        # Add components to main layout
        main_layout.addWidget(chat_container, stretch=1)
        main_layout.addWidget(input_container)

        # Connect input field signals
        self.input_field.installEventFilter(self)

        # Initialize chat
        self.add_message("assistant", "Hello! I'm your AI assistant. How can I help you today?")

    def add_message(self, role: str, content: str):
        """Add a message to the chat display with grouping."""
        timestamp = datetime.now()
        message = ChatMessage(role, content)
        self.messages.append(message)

        # Create message widget
        message_widget = MessageWidget(role, content, timestamp)

        # Handle message grouping
        if role != self.last_message_role:
            # Create new group
            self.current_group = MessageGroup(role)
            self.messages_layout.insertWidget(self.messages_layout.count() - 1, self.current_group)

        # Add message to current group
        self.current_group.add_message(message_widget)
        self.last_message_role = role

        # Ensure UI is updated
        QApplication.processEvents()

        # Smooth scroll to bottom
        QTimer.singleShot(100, lambda: self.scroll_area.smooth_scroll_to(
            self.scroll_area.verticalScrollBar().maximum()
        ))

    def eventFilter(self, obj, event):
        if obj == self.input_field and event.type() == event.KeyPress:
            if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier:
                self.send_message()
                return True
        return super().eventFilter(obj, event)

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

        # Create and start AI thread
        self.ai_thread = AIThread(self.api_key, self.messages)
        self.ai_thread.response_received.connect(self.handle_ai_response)
        self.ai_thread.error_occurred.connect(self.handle_error)
        self.ai_thread.finished.connect(lambda: self.progress_bar.setVisible(False))
        self.ai_thread.start()

    def handle_ai_response(self, response: str):
        """Handle the AI response."""
        self.add_message("assistant", response)

    def handle_error(self, error_message: str):
        """Handle any errors that occur during AI processing."""
        QMessageBox.critical(self, "Error", f"An error occurred: {error_message}")
        self.progress_bar.setVisible(False)

    def clear_chat(self):
        """Clear the chat display and message history."""
        self.messages.clear()
        self.last_message_role = None
        self.current_group = None

        # Remove all message groups
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.add_message("assistant", "Chat history cleared. How can I help you?")


class ChatMessage:
    """Class to store chat message information"""

    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
        self.timestamp = datetime.now()

    def to_dict(self):
        """Convert message to dictionary format for API"""
        return {
            "role": self.role,
            "content": self.content
        }

    def __str__(self):
        """String representation of the message"""
        return f"{self.role}: {self.content}"


class AIThread(QThread):
    """Thread for handling AI responses"""
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, api_key: str, messages: List[ChatMessage]):
        super().__init__()
        self.api_key = api_key
        self.messages = messages

    def run(self):
        try:
            # Simulate AI response for testing (replace with actual API call)
            time.sleep(1)  # Simulate API delay
            response = "This is a simulated AI response. Replace with actual API integration."
            self.response_received.emit(response)
        except Exception as e:
            self.error_occurred.emit(str(e))

def main():
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')
    app.setFont(QFont('Segoe UI', 10))

    chatbot = ChatbotUI()
    chatbot.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()