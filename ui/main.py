from PySide2.QtWidgets import QMainWindow

from .overview import Overview
from bot import Client

class MainWindow(QMainWindow):
    def __init__(self, client: Client) -> None:
        super().__init__()
        self.client = client

        self.setWindowTitle("Village Kids Pager")
        
        self.currentPage = Overview(self)
        self.setCentralWidget(self.currentPage)
