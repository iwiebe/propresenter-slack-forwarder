import sys
import threading
from PySide6.QtWidgets import QApplication
from ui.mainwindow import MainWindow
from ui.widget import WidgetMenu

import bot
client = bot.Client()

app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

window = MainWindow(client, app)
client.window = window
thread = threading.Thread(target=client.run, args=(window,), name="Asyncio Thread", daemon=True)
thread.start()
app.exec()
