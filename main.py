import sys
import threading
from PySide6.QtWidgets import QApplication
from ui.mainwindow import MainWindow

import bot
client = bot.Client()

app = QApplication(sys.argv)
window = MainWindow(client)
client.window = window
thread = threading.Thread(target=client.run, args=(window,), name="Asyncio Thread", daemon=True)
thread.start()

window.show()
app.exec()
