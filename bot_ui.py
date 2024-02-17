import sys
import io
import os
import json

class Stream(io.StringIO):
    def write(self, __s: str) -> int:
        label.setText("\n".join((label.text()+__s).splitlines()[:100]))
        return 0

sys.stderr = Stream()

import threading
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget


def run_client():
    import bot
    client = bot.Client()
    client.run()

app = QApplication(sys.argv)
scrollarea = QWidget()
box = QVBoxLayout()
scrollarea.setLayout(box)
label = QLabel("Hello World")
box.addWidget(label)
scrollarea.show()
thread = threading.Thread(target=run_client, name="Client Thread")
thread.daemon = True
thread.start()

app.exec()
