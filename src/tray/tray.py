from multiprocessing.connection import Client
import os
import sys

def tray_action_show(arg):
    conn.send("show")

def tray_action_quit(arg):
    conn.send("quit")

image_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "tray.png")
show_text = sys.argv[1]
quit_text = sys.argv[2]

def create_tray_icon_pystray():
    from pystray import Icon, MenuItem, Menu
    from PIL import Image

    image = Image.open(image_path)

    menu = Menu(
        MenuItem("Varia", None, enabled=False),
        MenuItem("───", None, enabled=False),
        MenuItem(show_text, tray_action_show),
        MenuItem(quit_text, tray_action_quit)
    )

    icon = Icon(
        'Varia',
        icon=image,
        menu=menu
    )

    icon.title = "Varia"
    
    icon.run()

def create_tray_icon_ayatana():
    import gi
    gi.require_version('AyatanaAppIndicator3', '0.1')
    gi.require_version('Gtk', '3.0')
    from gi.repository import AyatanaAppIndicator3, Gtk

    indicator = AyatanaAppIndicator3.Indicator.new(
        "Varia",
        "io.github.giantpinkrobots.varia",
        AyatanaAppIndicator3.IndicatorCategory.APPLICATION_STATUS
    )

    indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)

    menu = Gtk.Menu()

    title_item = Gtk.MenuItem(label="Varia")
    title_item.set_sensitive(False)
    menu.append(title_item)

    separator = Gtk.SeparatorMenuItem()
    menu.append(separator)

    show_item = Gtk.MenuItem(label=show_text)
    show_item.connect("activate", tray_action_show)
    menu.append(show_item)

    quit_item = Gtk.MenuItem(label=quit_text)
    quit_item.connect("activate", tray_action_quit)
    menu.append(quit_item)

    menu.show_all()
    indicator.set_menu(menu)
    Gtk.main()

address = ('localhost', 6802)
conn = Client(address, authkey=b'varia-tray-process')

# On Linux, pystray doesn't work with the given icon, so we must use AyatanaAppIndicator3 directly:
if os.name == 'nt':
    create_tray_icon_pystray()

else:
    create_tray_icon_ayatana()