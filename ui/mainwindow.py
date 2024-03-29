from PySide6.QtWidgets import QMainWindow, QDialog, QVBoxLayout, QLabel
from PySide6.QtCore import Signal, Qt, SignalInstance

from .overview import Overview
from bot import Client

class MainWindow(QMainWindow):
    setup_err_signal: SignalInstance = Signal(str, name="err") # type: ignore

    def __init__(self, client: Client) -> None:
        super().__init__()
        self.client = client

        self.setWindowTitle("Village Kids Pager")
        self.resize(300,200)
        
        self.currentPage = Overview(self)
        self.setCentralWidget(self.currentPage)
        self.setup_err_signal.connect(self.setup_err_alert)
    
    def setup_err_alert(self, text: str):
        v = QDialog(None, Qt.WindowType.Dialog)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(text))

        v.setLayout(layout)
        v.show()
        v.exec()
