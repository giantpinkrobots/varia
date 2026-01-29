import os
def show_notification(title, message, variaapp):
    if os.name == 'nt':
        from winsdk_toast import Notifier, Toast
        from os.path import abspath
        path_pic = abspath('./icon.ico')

        notifier = Notifier(title)
        toast = Toast()
        toast.add_text(message)
        toast.add_image(path_pic, placement='appLogoOverride')
        notifier.show(toast)
    
    elif os.uname().sysname == 'Darwin':
        import subprocess

        title = f"Varia - {title}"

        subprocess.run([
            "osascript",
            "-e", "on run argv",
            "-e", "display notification (item 2 of argv) with title (item 1 of argv)",
            "-e", "end run",
            title,
            message
        ])
    
    else:
        import gi
        gi.require_version('Gtk', '4.0')
        from gi.repository import Gio

        notification = Gio.Notification.new(title)
        notification.set_body(message)
        notification.set_title(title)
        variaapp.send_notification(None, notification)
