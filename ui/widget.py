from __future__ import annotations

import os
from PySide6.QtWidgets import QMenu, QSystemTrayIcon, QApplication
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .mainwindow import MainWindow


class WidgetMenu:
    def __init__(self, main: MainWindow, app: QApplication) -> None:
        self.main: MainWindow = main
        self.app: QApplication = app
        self.menu = QMenu()
        self.tray = QSystemTrayIcon()

        icon_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "menu-bar-icons")

        icon = QIcon(os.path.join(icon_dir, "icon_32x32_alert_0.png"))
        self.tray.setIcon(icon)
        self.tray.setVisible(True)

        self.propres_status = QAction("Propresenter: Disconnected")
        self.propres_status.setEnabled(False)
        self.menu.addAction(self.propres_status)

        self.slack_status = QAction("Slack: Disconnected")
        self.slack_status.setEnabled(False)
        self.menu.addAction(self.slack_status)

        self.menu.addSeparator()

        self.queue = QAction("Active Number: N/A")
        self.queue.setEnabled(False)
        self.menu.addAction(self.queue)

        self.menu.addSeparator()

        self.open_action = QAction("Open Window")
        self.open_action.triggered.connect(self.show_main_window)
        self.menu.addAction(self.open_action)

        self.quit_action = QAction("Quit")
        self.quit_action.triggered.connect(self.quit)
        self.menu.addAction(self.quit_action)

        self.tray.setContextMenu(self.menu)

    
    # the following functions could be direct callbacks in the QActions instead of defined here, but this is more future-proof

    def show_main_window(self):
        self.main.show()
        self.main.raise_()
    
    def hide_main_window(self):
        self.main.hide()
    
    def quit(self):
        self.app.quit()
