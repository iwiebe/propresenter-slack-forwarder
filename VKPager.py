import sys
import threading
from PySide2.QtWidgets import QApplication
from ui.main import MainWindow

import bot
client = bot.Client()

app = QApplication(sys.argv)
main = MainWindow(client)
thread = threading.Thread(target=client.run, name="Asyncio Thread", daemon=True)
thread.start()

main.show()
app.exec_()
