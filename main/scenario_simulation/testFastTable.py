import sys
from PyQt5.QtWidgets import QApplication, QTableView
from PyQt5.QtCore import QAbstractTableModel, Qt
import pandas as pd

class DataTableModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self.data = data

    def rowCount(self, parent=None):
        return self.data.shape[0]

    def columnCount(self, parent=None):
        return self.data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return str(self.data.iloc[index.row(), index.column()])
        return None

def main():
    app = QApplication(sys.argv)
    data = pd.DataFrame([[i, i**2] for i in range(10000)], columns=['Number', 'Square'])
    model = DataTableModel(data)

    table_view = QTableView()
    table_view.setModel(model)
    table_view.resize(800, 600)
    table_view.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
