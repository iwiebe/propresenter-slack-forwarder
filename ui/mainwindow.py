import asyncio
import threading
from PySide6.QtWidgets import QMainWindow, QMessageBox
from PySide6.QtCore import Signal, SignalInstance

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
        v = QMessageBox(QMessageBox.Icon.Critical, "Error!", text, QMessageBox.StandardButton.Ok, self)
        v.exec()
    
    def confirm_creation_dialog(self, event: asyncio.Future):
        dialog = QMessageBox(QMessageBox.Icon.Warning, "ProPresenter - Warning", "A VK message was not found. Create one?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        threading.Thread(target=lambda: event.set_result(dialog.exec() == QMessageBox.StandardButton.Yes), name="dialog").start() # non blocking for the asyncio thread
