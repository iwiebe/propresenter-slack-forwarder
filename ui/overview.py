from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QStatusBar, QStyle, QCommandLinkButton
from PySide6.QtCore import Qt
import threading
import time


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .widget import WidgetMenu
    from .mainwindow import MainWindow

class Status(QWidget):
    def __init__(self, main: MainWindow) -> None:
        super().__init__()
        self.main = main

        self._status_bar = QStatusBar()
        main.setStatusBar(self._status_bar)

        pixmapi = QStyle.StandardPixmap.SP_MessageBoxCritical
        icon = self.style().standardIcon(pixmapi)

        self.slack_status = QLabel("Slack: Disconnected")
        self._status_bar.addPermanentWidget(self.slack_status)

        self.propresenter_status = QLabel("ProPres: Disconnected")
        self._status_bar.addPermanentWidget(self.propresenter_status)


class Overview(QWidget):
    def __init__(self, main: MainWindow, widget: WidgetMenu) -> None:
        super().__init__()
        self.main = main
        self.widget: WidgetMenu = widget

        self._layout = QHBoxLayout()
        self.setLayout(self._layout)

        # left side
        left = QVBoxLayout()
        self.active = QLabel("Active Number: N/A")
        self.active.setAlignment(Qt.AlignmentFlag.AlignLeading)
        left.addWidget(self.active)

        self.queue = QLabel("Numbers Queued:")
        self.queue.setAlignment(Qt.AlignmentFlag.AlignLeading)
        left.addWidget(self.queue)

        self._layout.addLayout(left)

        # right side
        right = QVBoxLayout()
        self.status = Status(main)
        right.addWidget(self.status)

        self._layout.addLayout(right)

        self.poll_thread = threading.Thread(target=self.poll_in_thread, name="Status Poll Thread", daemon=True)
        self.poll_thread.start()

    def poll_in_thread(self):
        time.sleep(2) # give the slack client a bit to set up

        while True:
            # first manage statuses

            try:
                slack = self.main.client.handler.client
                connected = (not slack.closed
                    and not slack.stale
                    and slack.current_session is not None
                    and not slack.current_session.closed)
            except:
                connected = False
                        
            if connected:
                self.status.slack_status.setText("Slack: Connected")
                self.widget.slack_status.setText("Slack: Connected")
            else:
                self.status.slack_status.setText("Slack: Disconnected")
                self.widget.slack_status.setText("Slack: Disconnected")

            propres = self.main.client
            connected = (propres.prop_ws is not None and not propres.prop_ws.closed and propres.prop_authenticated)

            if connected:
                self.status.propresenter_status.setText("ProPres: Connected")
                self.widget.propres_status.setText("Propresenter: Connected")
            else:
                self.status.propresenter_status.setText("ProPres: Disconnected")
                self.widget.propres_status.setText("Propresenter: Disconnected")

            # then manage active numbers
            txt = ""
            if self.main.client.last_number:
                txt = f"Last Number: {self.main.client.last_number}\n"
            
            if self.main.client.current_formatted is not None:
                if len(self.main.client._current_nonce) > 1: # type: ignore
                    s = "s"
                else:
                    s = ""
                
                current_line = f"Active Number{s}: {self.main.client.current_formatted}"
                txt += current_line
                self.widget.queue.setText(current_line)
            
            else:
                self.widget.queue.setText("Active Number: N/A")
                txt += "Active Number: N/A"
            
            self.active.setText(txt.strip())
            
            # then queued numbers:
            try:
                queue: list[tuple[tuple[str, str], ...]] = list(self.main.client.number_queue._queue) # type: ignore
            except AttributeError:
                queue = []
            
            if self.main.client.current_batch:
                queue.append(tuple(self.main.client.current_batch))

            numbers = [self.main.client.process_number_batch(batch)[0] for batch in queue]
            formatted = "\n".join(numbers)
            self.queue.setText(f"Numbers Queued:\n{formatted}")
            
            time.sleep(1)
