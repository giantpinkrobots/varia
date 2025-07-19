import gi
import os
from stringstorage import gettext as _
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
import threading

def window_create_content(self):
    self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    header_box = Gtk.Box()

    self.total_download_speed_label = Gtk.Label(label=self.total_download_speed)
    self.total_download_speed_label.add_css_class("heading")

    header_show_sidebar_button = Gtk.Button()
    header_show_sidebar_button.add_css_class('flat')
    header_show_sidebar_button.set_icon_name("sidebar-show-symbolic")
    header_show_sidebar_button.connect("clicked", toggle_sidebar_overlay, self)
    header_show_sidebar_button.set_halign(Gtk.Align.START)

    self.header_show_sidebar_button_revealer = Gtk.Revealer()
    self.header_show_sidebar_button_revealer.set_transition_type(Gtk.RevealerTransitionType.CROSSFADE)
    self.header_show_sidebar_button_revealer.set_child(header_show_sidebar_button)

    self.header_pause_content = Adw.ButtonContent()
    self.header_pause_content.set_icon_name("media-playback-pause-symbolic")
    self.header_pause_content.set_label(_("Pause All"))
    self.header_pause_button = Gtk.Button()
    self.header_pause_button.add_css_class('flat')
    self.header_pause_button.set_sensitive(False)
    self.header_pause_button.set_child(self.header_pause_content)
    self.header_pause_button.connect("clicked", lambda button: self.pause_all())
    
    header_expanding_box_1 = Gtk.Box()
    header_expanding_box_1.set_hexpand(True)
    header_expanding_box_2 = Gtk.Box()
    header_expanding_box_2.set_hexpand(True)
    
    header_box.append(header_expanding_box_1)
    header_box.append(self.total_download_speed_label)
    header_box.append(header_expanding_box_2)
    header_box.append(self.header_pause_button)
    
    if (os.name == 'nt'): # Don't use Adw.HeaderBar on Windows
        header_box.prepend(self.header_show_sidebar_button_revealer)
        self.content_box.append(header_box)

    else:
        header_bar = Adw.HeaderBar()
        header_bar.add_css_class('flat')
        header_bar.pack_start(self.header_show_sidebar_button_revealer)
        header_bar.set_title_widget(header_box)
        self.content_box.append(header_bar)

    status_page_begin_button_box = Gtk.Box(spacing=12)
    status_page_begin_button_box.append(Gtk.Image.new_from_icon_name("sidebar-show-symbolic"))
    status_page_begin_button_box.append(Gtk.Label(label=_("Show Menu")))

    status_page_begin_button = Gtk.Button(child=status_page_begin_button_box)
    status_page_begin_button.set_halign(Gtk.Align.CENTER)
    status_page_begin_button.add_css_class("pill")
    status_page_begin_button.add_css_class("suggested-action")
    status_page_begin_button.connect("clicked", toggle_sidebar_overlay, self)

    self.status_page_begin_button_revealer = Gtk.Revealer()
    self.status_page_begin_button_revealer.set_transition_type(Gtk.RevealerTransitionType.CROSSFADE)
    self.status_page_begin_button_revealer.set_child(status_page_begin_button)
    
    self.status_page_widget = Adw.StatusPage(icon_name="io.github.giantpinkrobots.varia-symbolic")
    self.status_page_widget.set_hexpand(True)
    self.status_page_widget.set_vexpand(True)
    self.status_page_widget.set_child(self.status_page_begin_button_revealer)
    
    self.download_list_box = Gtk.Box()
    self.download_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    self.download_list.set_margin_start(6)
    self.download_list.set_margin_end(6)
    self.download_list.set_margin_bottom(6)
    self.download_list.set_margin_top(1)
    self.download_list_box.set_hexpand(True)
    self.download_list_box.set_vexpand(True)

    scrolled_window = Gtk.ScrolledWindow()
    scrolled_window.set_child(self.download_list)

    self.content_root_overlay = Gtk.Overlay()
    self.content_root_overlay.set_child(self.download_list_box)
    self.content_root_overlay.add_overlay(self.status_page_widget)

    self.download_list_box.append(scrolled_window)
    self.content_box.append(self.content_root_overlay)
    self.overlay_split_view.set_content(self.content_box)

    self.total_download_speed_calculator_thread = threading.Thread(target=self.total_download_speed_get, args=(self.downloads, self.total_download_speed_label), daemon=True)
    self.total_download_speed_calculator_thread.start()

def toggle_sidebar_overlay(button, self):
    if self.overlay_split_view.get_show_sidebar() == False:
        self.overlay_split_view.set_collapsed(True)
        self.overlay_split_view.set_show_sidebar(True)
    else:
        self.overlay_split_view.set_show_sidebar(False)
