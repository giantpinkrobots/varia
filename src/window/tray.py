from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu

from gettext import gettext as _


class SystemTray:
    def __init__(self, window):
        self.app = QApplication([])
        self.app.setQuitOnLastWindowClosed(False)

        self.window = window
        self.shown = False

        icon = QIcon.fromTheme("io.github.giantpinkrobots.varia")

        tray = QSystemTrayIcon(icon=icon, parent=self.app)
        tray.setVisible(True)
        tray.setToolTip(_("Varia"))

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
        self.app.exec()

    def set_state(self, state):
        self.shown = state

    def exit(self):
        self.app.quit()

    def _toggle_window(self):
        if not self.shown:
            self.window.show()
            self.shown = True
        else:
            self.window.hide()
            self.shown = False
