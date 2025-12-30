import signal
import gi
import sys
from multiprocessing.connection import Client

gi.require_version("Gtk", "3.0")
gi.require_version("AyatanaAppIndicator3", "0.1")
from gi.repository import Gtk, AyatanaAppIndicator3

class TrayHelper:
    def __init__(self, show_label, quit_label):
        self.indicator = AyatanaAppIndicator3.Indicator.new(
            "io.github.giantpinkrobots.varia",
            "io.github.giantpinkrobots.varia-symbolic",
            AyatanaAppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)

        self.client = Client(('localhost', 6802), authkey=b'varia-tray-process')

        menu = Gtk.Menu()
        item_show = Gtk.MenuItem(label=show_label)
        item_show.connect("activate", lambda *_: self.send_command("show"))
        item_show.show()
        menu.append(item_show)

        separator = Gtk.SeparatorMenuItem()
        separator.show()
        menu.append(separator)

        item_quit = Gtk.MenuItem(label=quit_label)
        item_quit.connect("activate", lambda *_: self.send_command("quit"))
        item_quit.show()
        menu.append(item_quit)

        self.indicator.set_menu(menu)

    def send_command(self, cmd):
        print('command sent:' + cmd)
        try:
            self.client.send(cmd)
        except:
            pass

def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    helper = TrayHelper(sys.argv[1], sys.argv[2])
    Gtk.main()

if __name__ == "__main__":
    main()
