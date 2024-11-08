
import sys
from PyQt5.QtCore import QTimer, QTime, Qt
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QFont

class DigitalClock(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Digital Clock')
        self.setGeometry(100, 100, 250, 100)
        self.time_label = QLabel(self)
        self.time_label.setFont(QFont('Arial', 40))
        self.time_label.setAlignment(Qt.AlignCenter)
        layout = QVBoxLayout()
        layout.addWidget(self.time_label)
        self.setLayout(layout)
        timer = QTimer(self)
        timer.timeout.connect(self.update_time)
        timer.start(1000)
        self.update_time()

    def update_time(self):
        current_time = QTime.currentTime()
        time_text = current_time.toString('hh:mm:ss AP')
        self.time_label.setText(time_text)
if (__name__ == '__main__'):
    app = QApplication(sys.argv)
    clock = DigitalClock()
    clock.show()
    sys.exit(app.exec_())
