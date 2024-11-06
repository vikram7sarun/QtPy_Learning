import sys
import random
import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QGridLayout, QLabel, QWidget, QFrame
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QDrag, QPixmap, QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class DraggableRectangle(QFrame):
    def __init__(self, label_text="", parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setStyleSheet("background-color: #e0e0e0; border: 1px solid #777;")

        # Layout and label for the widget
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)  # No margins inside the widget
        self.label = QLabel(label_text, self)
        self.label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            drag.setMimeData(mime_data)

            # Create a visual representation for the dragging widget
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())

            drag.exec_(Qt.MoveAction)

    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        source_widget = event.source()
        if source_widget and source_widget != self:
            # Swap text between this widget and the source widget
            source_text = source_widget.label.text()
            self_text = self.label.text()
            source_widget.label.setText(self_text)
            self.label.setText(source_text)

            # Swap layouts if they contain additional content (e.g., charts)
            source_layout = source_widget.layout.takeAt(1)
            self_layout = self.layout.takeAt(1)
            if source_layout:
                self.layout.addWidget(source_layout.widget())
            if self_layout:
                source_widget.layout.addWidget(self_layout.widget())

            event.acceptProposedAction()


class TestDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Responsive Drag-and-Drop Dashboard")
        self.setGeometry(100, 100, 800, 600)

        # Main widget and layout
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.grid_layout = QGridLayout(self.main_widget)
        self.grid_layout.setSpacing(0)  # No spacing between widgets
        self.grid_layout.setContentsMargins(0, 0, 0, 0)  # No margins around the layout

        # Create 6 draggable rectangles in a fixed grid layout
        self.widgets = [DraggableRectangle(f"Widget {i + 1}", self) for i in range(6)]

        # First widget: Display total test cases and pie chart
        self.init_pie_chart_widget(self.widgets[0])

        # Second widget: Display trend line chart
        self.init_trend_line_chart_widget(self.widgets[1])

        # Third widget: Display bar chart for Broken, Skipped, and Unknown tests
        self.init_bar_chart_widget(self.widgets[2])

        # Fourth widget: Display donut chart for Automated, In Progress, Blocked, and Pending from Dev
        self.init_donut_chart_widget(self.widgets[3])

        # Fifth widget: Display suite details
        self.init_suite_details_widget(self.widgets[4])

        # Arrange widgets in a 2x3 grid
        positions = [(i // 3, i % 3) for i in range(6)]
        for pos, widget in zip(positions, self.widgets):
            self.grid_layout.addWidget(widget, *pos)

        # Set each row and column to stretch to fill the available space
        for i in range(2):  # 2 rows
            self.grid_layout.setRowStretch(i, 1)
        for j in range(3):  # 3 columns
            self.grid_layout.setColumnStretch(j, 1)

    def init_pie_chart_widget(self, widget):
        widget.label.setText("Total Tests: 100")

        # Pie chart setup for the first widget
        figure = Figure()
        canvas = FigureCanvas(figure)
        widget.layout.addWidget(canvas)

        # Sample data for pass/fail
        pass_count = 70
        fail_count = 30
        sizes = [pass_count, fail_count]
        labels = ['Passed', 'Failed']
        colors = ['#4CAF50', '#F44336']

        # Plot the pie chart
        ax = figure.add_subplot(111)
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
        ax.axis('equal')  # Equal aspect ratio for circular pie chart

        canvas.draw()

    def init_trend_line_chart_widget(self, widget):
        widget.label.setText("Daily Pass/Fail Trend")

        # Line chart setup for trend in the second widget
        figure = Figure()
        canvas = FigureCanvas(figure)
        widget.layout.addWidget(canvas)

        # Sample data: Generate dates and pass/fail rates
        dates = [datetime.date.today() - datetime.timedelta(days=i) for i in range(10)]
        dates.reverse()  # Sort dates in ascending order
        pass_rates = [random.randint(70, 100) for _ in range(10)]
        fail_rates = [100 - rate for rate in pass_rates]

        # Plotting pass and fail rates
        ax = figure.add_subplot(111)
        ax.plot(dates, pass_rates, marker='o', color='green', label='Pass Rate (%)')
        ax.plot(dates, fail_rates, marker='o', color='red', label='Fail Rate (%)')

        # Chart styling
        ax.set_xlabel("Date")
        ax.set_ylabel("Rate (%)")
        ax.set_title("Execution Pass/Fail Rate")
        ax.legend()
        ax.grid(True)

        # Rotate date labels for readability
        figure.autofmt_xdate()

        canvas.draw()

    def init_bar_chart_widget(self, widget):
        widget.label.setText("Test Status Breakdown")

        # Bar chart setup for third widget
        figure = Figure()
        canvas = FigureCanvas(figure)
        widget.layout.addWidget(canvas)

        # Sample data for Broken, Skipped, and Unknown test counts
        categories = ["Broken", "Skipped", "Unknown"]
        values = [random.randint(5, 20), random.randint(10, 25), random.randint(1, 10)]
        colors = ['#FF6347', '#FFD700', '#778899']  # Colors for each category

        # Plotting bar chart
        ax = figure.add_subplot(111)
        ax.bar(categories, values, color=colors)

        # Chart styling
        ax.set_ylabel("Test Count")
        ax.set_title("Broken, Skipped, and Unknown Tests")
        ax.grid(axis='y', linestyle='--', alpha=0.7)

        canvas.draw()

    def init_donut_chart_widget(self, widget):
        widget.label.setText("Execution Status")

        # Donut chart setup for the fourth widget
        figure = Figure()
        canvas = FigureCanvas(figure)
        widget.layout.addWidget(canvas)

        # Sample data for Automated, In Progress, Blocked, and Pending from Dev
        labels = ["Automated", "In Progress", "Blocked", "Pending from Dev"]
        sizes = [random.randint(20, 50), random.randint(10, 30), random.randint(5, 15), random.randint(5, 10)]
        colors = ['#1E90FF', '#32CD32', '#FF6347', '#FFD700']  # Colors for each category

        # Plotting donut chart
        ax = figure.add_subplot(111)
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors,
                                          wedgeprops=dict(width=0.3))

        # Center circle for donut effect
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle

        canvas.draw()

    def init_suite_details_widget(self, widget):
        widget.label.setText("Suite Details")

        # Suite details data with color coding (only suite names and colors)
        suites = [
            ("Payment Suite", "#FFC107"),  # Yellow
            ("Cart Suite", "#03A9F4"),  # Light Blue
            ("User Suite", "#8BC34A"),  # Light Green
            ("Product Suite", "#FF5722"),  # Deep Orange
            ("Checkout Suite", "#9C27B0")  # Purple
        ]

        # Display each suite as a styled label with color coding and no description
        for suite_name, color in suites:
            suite_label = QLabel()

            # HTML content for suite title with inline styling
            suite_label.setText(
                f"""
                <div style="padding: 6px 10px; color: white; background-color: {color}; border-radius: 5px;">
                    <b>{suite_name}</b>
                </div>
                """
            )

            # Set additional stylesheet for closer spacing and border radius
            suite_label.setStyleSheet("""
                QLabel {
                    margin-top: 4px;
                    margin-bottom: 4px;
                    border: none;
                }
            """)

            suite_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            widget.layout.addWidget(suite_label)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dashboard = TestDashboard()
    dashboard.show()
    sys.exit(app.exec_())
