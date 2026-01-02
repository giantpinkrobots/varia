import os
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import GLib

def on_window_resize(self, widget, param):
    GLib.idle_add(self.apply_window_resize)
    GLib.timeout_add(50, self.apply_window_resize)
    
def apply_window_resize(self):
    if self.root_window_overlay.get_width() < 600:
        self.header_show_sidebar_button_revealer.set_reveal_child(True)
        self.status_page_begin_button_revealer.set_reveal_child(True)
        self.overlay_split_view.set_show_sidebar(False)

        if (os.uname().sysname == 'Darwin'):
            self.mac_header_empty_space.set_visible(True)

    else:
        self.header_show_sidebar_button_revealer.set_reveal_child(False)
        self.status_page_begin_button_revealer.set_reveal_child(False)
        self.overlay_split_view.set_collapsed(False)
        self.overlay_split_view.set_show_sidebar(True)

        if (os.uname().sysname == 'Darwin'):
            self.mac_header_empty_space.set_visible(False)

def save_window_size(self):
    self.appconf['window_size'] = self.get_default_size()
    self.save_appconf()