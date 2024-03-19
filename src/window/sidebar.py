import os
import subprocess
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio
from gettext import gettext as _

from window.preferences import show_preferences
from download.actionrow import on_download_clicked

def window_create_sidebar(self, variaapp, DownloadThread, variaVersion):
    sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    sidebar_content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

    header_bar = Adw.HeaderBar()
    header_bar.get_style_context().add_class('flat')
    sidebar_box.append(header_bar)

    preferences_button = Gtk.Button(tooltip_text=_("Preferences"))
    preferences_button.set_icon_name("emblem-system-symbolic")
    preferences_button.connect("clicked", show_preferences, self, variaapp)

    hamburger_button = Gtk.MenuButton(tooltip_text=_("Other"))
    hamburger_button.set_icon_name("open-menu-symbolic")
    hamburger_menu_model = Gio.Menu()

    background_action = Gio.SimpleAction.new("background_mode", None)
    background_action.connect("activate", background_mode, self, variaapp)
    variaapp.add_action(background_action)

    cancel_all_action = Gio.SimpleAction.new("cancel_all_downloads", None)
    cancel_all_action.connect("activate", self.stop_all)
    variaapp.add_action(cancel_all_action)

    about_action = Gio.SimpleAction.new("downloads_folder", None)
    about_action.connect("activate", open_downloads_folder, self, self.appconf)
    variaapp.add_action(about_action)

    downloads_folder_action = Gio.SimpleAction.new("about", None)
    downloads_folder_action.connect("activate", show_about, self, variaVersion)
    variaapp.add_action(downloads_folder_action)

    shutdown_action = Gio.SimpleAction.new("shutdown_on_completion", None)
    shutdown_action.connect("activate", shutdown_on_completion, self)
    shutdown_action.set_enabled(False)
    variaapp.add_action(shutdown_action)

    hamburger_menu_item_background = Gio.MenuItem.new(_("Background Mode"), "app.background_mode")
    if (os.name != 'nt'):
        hamburger_menu_model.append_item(hamburger_menu_item_background)

    hamburger_menu_item_cancel_all = Gio.MenuItem.new(_("Cancel All"), "app.cancel_all_downloads")
    hamburger_menu_model.append_item(hamburger_menu_item_cancel_all)

    hamburger_menu_item_open_downloads_folder = Gio.MenuItem.new(_("Open Download Folder"), "app.downloads_folder")
    hamburger_menu_model.append_item(hamburger_menu_item_open_downloads_folder)

    hamburger_menu_item_shutdown = Gio.MenuItem.new(_("Shutdown on Completion"), "app.shutdown_on_completion")
    hamburger_menu_model.append_item(hamburger_menu_item_shutdown)

    hamburger_menu_item_about = Gio.MenuItem.new(_("About Varia"), "app.about")
    hamburger_menu_model.append_item(hamburger_menu_item_about)

    hamburger_button.set_menu_model(hamburger_menu_model)

    header_bar.pack_start(preferences_button)
    header_bar.pack_end(hamburger_button)

    download_entry = Gtk.Entry()
    download_entry.set_placeholder_text(_("URL"))

    download_button = Gtk.Button(label=_("Download"))
    download_button.get_style_context().add_class("pill")
    download_button.get_style_context().add_class("suggested-action")
    download_button.connect("clicked", on_download_clicked, self, download_entry, DownloadThread)

    self.filter_button_show_all = Gtk.ToggleButton()
    self.filter_button_show_all.get_style_context().add_class('flat')
    filter_button_show_all_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    filter_button_show_all_box.set_margin_top(8)
    filter_button_show_all_box.set_margin_bottom(8)
    filter_button_show_all_box.append(Gtk.Image.new_from_icon_name("switch-off-symbolic"))
    filter_button_show_all_label = Gtk.Label(label=_("All"))
    filter_button_show_all_label.get_style_context().add_class('body')
    filter_button_show_all_box.append(filter_button_show_all_label)
    self.filter_button_show_all.set_child(filter_button_show_all_box)
    self.filter_button_show_all.set_active(True)
    self.filter_button_show_all.connect("clicked", self.filter_download_list, "show_all")

    self.filter_button_show_downloading = Gtk.ToggleButton()
    self.filter_button_show_downloading.get_style_context().add_class('flat')
    filter_button_show_downloading_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    filter_button_show_downloading_box.set_margin_top(8)
    filter_button_show_downloading_box.set_margin_bottom(8)
    filter_button_show_downloading_box.append(Gtk.Image.new_from_icon_name("content-loading-symbolic"))
    filter_button_show_downloading_label = Gtk.Label(label=_("In Progress"))
    filter_button_show_downloading_label.get_style_context().add_class('body')
    filter_button_show_downloading_box.append(filter_button_show_downloading_label)
    self.filter_button_show_downloading.set_child(filter_button_show_downloading_box)
    self.filter_button_show_downloading.connect("clicked", self.filter_download_list, "show_downloading")

    self.filter_button_show_completed = Gtk.ToggleButton()
    self.filter_button_show_completed.get_style_context().add_class('flat')
    filter_button_show_completed_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    filter_button_show_completed_box.set_margin_top(8)
    filter_button_show_completed_box.set_margin_bottom(8)
    filter_button_show_completed_box.append(Gtk.Image.new_from_icon_name("emblem-ok-symbolic"))
    filter_button_show_completed_label = Gtk.Label(label=_("Completed"))
    filter_button_show_completed_label.get_style_context().add_class('body')
    filter_button_show_completed_box.append(filter_button_show_completed_label)
    self.filter_button_show_completed.set_child(filter_button_show_completed_box)
    self.filter_button_show_completed.connect("clicked", self.filter_download_list, "show_completed")

    sidebar_separator = Gtk.Separator()
    sidebar_separator.set_margin_top(8)
    sidebar_separator.set_margin_bottom(8)

    sidebar_expanding_box = Gtk.Box()
    Gtk.Widget.set_vexpand(sidebar_expanding_box, True)

    self.sidebar_remote_mode_label = Gtk.Label()
    if (self.appconf['remote'] == '1'):
        self.sidebar_remote_mode_label.set_text(_("Remote Mode"))
    self.sidebar_speed_limited_label = Gtk.Label()

    sidebar_content_box.set_margin_start(6)
    sidebar_content_box.set_margin_end(6)
    sidebar_content_box.set_margin_top(6)
    sidebar_content_box.set_margin_bottom(6)

    sidebar_filter_buttons_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    sidebar_filter_buttons_box.append(self.filter_button_show_all)
    sidebar_filter_buttons_box.append(self.filter_button_show_downloading)
    sidebar_filter_buttons_box.append(self.filter_button_show_completed)

    sidebar_content_box.append(download_entry)
    sidebar_content_box.append(download_button)
    sidebar_content_box.append(sidebar_separator)
    sidebar_content_box.append(sidebar_filter_buttons_box)
    sidebar_content_box.append(sidebar_expanding_box)
    sidebar_content_box.append(self.sidebar_remote_mode_label)
    sidebar_content_box.append(self.sidebar_speed_limited_label)
    sidebar_box.append(sidebar_content_box)

    self.overlay_split_view.set_sidebar(sidebar_box)

def background_mode(app, variaapp1, self, variaapp):
    self.exitProgram(app=app, variaapp=variaapp, background=True)

def show_about(app, variaapp, self, variaVersion):
    dialog = Adw.AboutDialog()
    dialog.set_application_name("Varia")
    dialog.set_version(variaVersion)
    dialog.set_developer_name("Giant Pink Robots!")
    dialog.set_license_type(Gtk.License(Gtk.License.MPL_2_0))
    dialog.set_comments(_("aria2 based download manager utilizing GTK4 and Libadwaita."))
    dialog.set_website("https://giantpinkrobots.github.io/varia")
    dialog.set_issue_url("https://github.com/giantpinkrobots/varia/issues")
    dialog.set_copyright("2023 Giant Pink Robots!\n\n" + _("This application relies on the following pieces of software:") +
        "\n\n- aria2\n- GTK4\n- Libadwaita\n- Meson\n- OpenSSL\n- Python-appdirs\n- Python-aria2p\n- Python-certifi\n- Python-charset-normalizer\n- Python-gettext\n- Python-idna\n- Python-loguru\n- Python-requests\n- Python-setuptools\n- Python-urllib3\n- Python-websocket-client\n\n" +
        _("The licenses of all of these pieces of software can be found in the dependencies_information directory in this application's app directory."))
    dialog.set_developers(["Giant Pink Robots! (@giantpinkrobots) https://github.com/giantpinkrobots"])
    dialog.set_application_icon("io.github.giantpinkrobots.varia")
    dialog.set_translator_credits(_("translator-credits"))
    dialog.set_artists(["Jakub Steiner"])
    dialog.set_release_notes_version("v2024.2.29-2")
    dialog.set_release_notes('''<p>v2024.2.29:</p>
        <ul><li>Support for Firefox and Chromium extension.</li>
        <li>Initial torrenting support.</li>
        <li>Remote mode that allows connection to a remote aria2 instance.</li>
        <li>Background mode that allows the window to be hidden while still downloading.</li>
        <li>Bug fixes and adjustments.</li></ul>
        <p>v2024.2.29-1:</p>
        <ul><li>Hotfix: an error that prevented the app from running in the Flathub release.</li>
        <li>German translation updates.</li>
        <li>Dutch translation updates.</li></ul>
        <p>v2024.2.29-2:</p>
        <ul><li>Hotfix: an error in the browser extension integration.</li>
        <li>Tiny UI adjustments.</li>
        <li>Russian translation updates.</li>
        <li>New Norwegian (Bokmål) translation.</li></ul>''')

    dialog.present(self)

def open_downloads_folder(self, app, variaapp, appconf):
    if (os.name == 'nt'):
        os.startfile(appconf["download_directory"])
    else:
        subprocess.Popen(["xdg-open", appconf["download_directory"]])

def shutdown_on_completion(self, app, variaapp):
    print("sus")
