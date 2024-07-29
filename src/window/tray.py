from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
import os
from gettext import gettext as _

class SystemTray:
    def __init__(self, window):
        self.qapp = QApplication([])
        self.qapp.setQuitOnLastWindowClosed(False)

        self.window = window
        self.shown = False

        trayicon = QIcon(os.path.dirname(os.path.realpath(__file__)) + "/../icon.ico")

        tray = QSystemTrayIcon(icon=trayicon, parent=self.qapp, toolTip="Varia")
        tray.setVisible(True)

        menu = QMenu()
        self.quit_action = QAction(_("Quit Varia"))
        self.quit_action.triggered.connect(lambda: self.window.trayExit())
        menu.addAction(self.quit_action)

        tray.activated.connect(lambda: self._toggle_window())
        tray.setContextMenu(menu)

    def run(self):
        if not self.window.appconf["default_mode"] == "background":
            self.shown = True
            self.window.show()
        self.qapp.exec()

    def set_state(self, state):
        self.shown = state

    def exit(self):
        self.qapp.quit()

    def _toggle_window(self):
        if not self.shown:
            self.window.show()
            self.shown = True
        else:
            self.window.hide()
            self.shown = False

