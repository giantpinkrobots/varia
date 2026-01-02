from stringstorage import gettext as _
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import GLib, Gio

def on_drag_enter(self, target, x, y):
    self.root_window_overlay.add_overlay(self.drag_drop_revealer)
    self.drag_drop_revealer.set_reveal_child(True)
    return 0

def on_drag_leave(self, target, timeout_milliseconds):
    GLib.timeout_add(timeout_milliseconds - 250, self.drag_drop_revealer.set_reveal_child, False)
    GLib.timeout_add(timeout_milliseconds, self.root_window_overlay.remove_overlay, self.drag_drop_revealer)
    GLib.timeout_add(timeout_milliseconds, self.drag_drop_status_page.add_css_class, "drag_drop_status_page")
    GLib.timeout_add(timeout_milliseconds, self.drag_drop_status_page.set_icon_name, "document-send-symbolic")

    return 0

def on_file_drop(self, target, value, x, y):
    timeout_milliseconds = 1000

    if isinstance(value, Gio.File) and \
        value.get_path() and \
        value.get_path().lower().endswith(".torrent"):

        try:
            if self.appconf["torrent_download_directory_custom_enabled"] == "1":
                self.api.add_torrent(value.get_path(), options={"dir": self.appconf["torrent_download_directory"]})

            else:
                self.api.add_torrent(value.get_path())

            print(f"Torrent file dragged: {value.get_path()}")
            timeout_milliseconds = 600
            #self.drag_drop_status_page.remove_css_class("drag_drop_status_page")
            #self.drag_drop_status_page.add_css_class("drag_drop_status_page_success")

        except:
            pass

    if timeout_milliseconds == 1000:
        # Error
        pass

    return 0