from PySide6.QtWidgets import QMainWindow

from .overview import Overview
from bot import Client

class MainWindow(QMainWindow):
    def __init__(self, client: Client) -> None:
        super().__init__()
        self.client = client

        self.setWindowTitle("Village Kids Pager")
        self.resize(300,200)
        
        self.currentPage = Overview(self)
        self.setCentralWidget(self.currentPage)
