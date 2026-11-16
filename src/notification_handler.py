import os
def show_notification(title, message, variaapp):
    if os.name == 'nt':
        from win11toast import toast
        toast(title, message)
    
    elif os.uname().sysname == 'Darwin':
        from mac_notifications import client

        client.create_notification(
            title=title,
            subtitle=message
        )
    
    else:
        import gi
        gi.require_version('Gtk', '4.0')
        from gi.repository import Gio

        notification = Gio.Notification.new(title)
        notification.set_body(message)
        notification.set_title(title)
        variaapp.send_notification(None, notification)
