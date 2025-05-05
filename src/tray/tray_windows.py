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
        MenuItem(show_text, tray_action_show),
        MenuItem(quit_text, tray_action_quit)
    )

    icon = Icon(
        'Varia',
        icon=image,
        title='Varia',
        menu=menu
    )

    icon.title = "Varia"

    icon.run()

address = ('localhost', 6802)
conn = Client(address, authkey=b'varia-tray-process')

create_tray_icon_pystray()
