import os
import subprocess
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio
from gettext import gettext as _
import textwrap

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

    self.shutdown_action = Gio.SimpleAction.new("shutdown_on_completion", None)
    self.shutdown_action.connect("activate", shutdown_on_completion, self)
    self.shutdown_action.set_enabled(False)
    variaapp.add_action(self.shutdown_action)

    self.exit_action = Gio.SimpleAction.new("exit_on_completion", None)
    self.exit_action.connect("activate", exit_on_completion, self)
    self.exit_action.set_enabled(False)
    variaapp.add_action(self.exit_action)

    hamburger_menu_item_background = Gio.MenuItem.new(_("Background Mode"), "app.background_mode")
    if (os.name != 'nt'):
        hamburger_menu_model.append_item(hamburger_menu_item_background)

    hamburger_menu_item_cancel_all = Gio.MenuItem.new(_("Cancel All"), "app.cancel_all_downloads")
    hamburger_menu_model.append_item(hamburger_menu_item_cancel_all)

    hamburger_menu_item_open_downloads_folder = Gio.MenuItem.new(_("Open Download Folder"), "app.downloads_folder")
    hamburger_menu_model.append_item(hamburger_menu_item_open_downloads_folder)

    completion_submenu_model = Gio.Menu()

    completion_submenu_item_exit = Gio.MenuItem.new(_("Exit on Completion"), "app.exit_on_completion")
    completion_submenu_model.append_item(completion_submenu_item_exit)

    completion_submenu_item_shutdown = Gio.MenuItem.new(_("Shutdown on Completion"), "app.shutdown_on_completion")
    completion_submenu_model.append_item(completion_submenu_item_shutdown)

    hamburger_menu_model.append_submenu(_("Completion Options"), completion_submenu_model)

    hamburger_menu_item_about = Gio.MenuItem.new(_("About Varia"), "app.about")
    hamburger_menu_model.append_item(hamburger_menu_item_about)

    hamburger_button.set_menu_model(hamburger_menu_model)

    header_bar.pack_start(preferences_button)
    header_bar.pack_end(hamburger_button)

    download_entry = Gtk.Entry()
    download_entry.set_placeholder_text(_("URL"))

    self.download_button = Gtk.Button(label=_("Download"))
    self.download_button.get_style_context().add_class("pill")
    self.download_button.get_style_context().add_class("suggested-action")
    self.download_button.connect("clicked", on_download_clicked, self, download_entry, DownloadThread)

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

    self.filter_button_show_seeding = Gtk.ToggleButton()
    self.filter_button_show_seeding.get_style_context().add_class('flat')
    filter_button_show_seeding_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    filter_button_show_seeding_box.set_margin_top(8)
    filter_button_show_seeding_box.set_margin_bottom(8)
    filter_button_show_seeding_box.append(Gtk.Image.new_from_icon_name("go-up-symbolic"))
    filter_button_show_seeding_label = Gtk.Label(label=_("Seeding"))
    filter_button_show_seeding_label.get_style_context().add_class('body')
    filter_button_show_seeding_box.append(filter_button_show_seeding_label)
    self.filter_button_show_seeding.set_child(filter_button_show_seeding_box)
    self.filter_button_show_seeding.connect("clicked", self.filter_download_list, "show_seeding")

    self.filter_button_show_failed = Gtk.ToggleButton()
    self.filter_button_show_failed.get_style_context().add_class('flat')
    filter_button_show_failed_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    filter_button_show_failed_box.set_margin_top(8)
    filter_button_show_failed_box.set_margin_bottom(8)
    filter_button_show_failed_box.append(Gtk.Image.new_from_icon_name("process-stop-symbolic"))
    filter_button_show_failed_label = Gtk.Label(label=_("Failed"))
    filter_button_show_failed_label.get_style_context().add_class('body')
    filter_button_show_failed_box.append(filter_button_show_failed_label)
    self.filter_button_show_failed.set_child(filter_button_show_failed_box)
    self.filter_button_show_failed.connect("clicked", self.filter_download_list, "show_failed")

    sidebar_separator = Gtk.Separator()
    sidebar_separator.set_margin_top(8)
    sidebar_separator.set_margin_bottom(8)

    sidebar_expanding_box = Gtk.Box()
    Gtk.Widget.set_vexpand(sidebar_expanding_box, True)

    self.sidebar_shutdown_mode_label = Gtk.Label()
    self.sidebar_remote_mode_label = Gtk.Label()
    if (self.appconf['remote'] == '1'):
        self.sidebar_remote_mode_label.set_text(textwrap.fill(_("Remote Mode"), 23))
    self.sidebar_speed_limited_label = Gtk.Label()
    self.sidebar_scheduler_label = Gtk.Label()

    sidebar_content_box.set_margin_start(6)
    sidebar_content_box.set_margin_end(6)
    sidebar_content_box.set_margin_top(6)
    sidebar_content_box.set_margin_bottom(6)

    sidebar_filter_buttons_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    sidebar_filter_buttons_box.append(self.filter_button_show_all)
    sidebar_filter_buttons_box.append(self.filter_button_show_downloading)
    sidebar_filter_buttons_box.append(self.filter_button_show_completed)
    sidebar_filter_buttons_box.append(self.filter_button_show_seeding)
    sidebar_filter_buttons_box.append(self.filter_button_show_failed)

    sidebar_content_box.append(download_entry)
    sidebar_content_box.append(self.download_button)
    sidebar_content_box.append(sidebar_separator)
    sidebar_content_box.append(sidebar_filter_buttons_box)
    sidebar_content_box.append(sidebar_expanding_box)
    sidebar_content_box.append(self.sidebar_shutdown_mode_label)
    sidebar_content_box.append(self.sidebar_remote_mode_label)
    sidebar_content_box.append(self.sidebar_speed_limited_label)
    sidebar_content_box.append(self.sidebar_scheduler_label)
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
    dialog.set_release_notes_version("v2024.5.7")
    dialog.set_release_notes('''
        <ul><li>Download scheduling: Start or stop downloading in given timespans.</li>
        <li>cookies.txt file import support.</li>
        <li>Remote timestamp support.</li>
        <li>Options to filter by seeding and failed downloads in the sidebar.</li>
        <li>Quit on completion option.</li>
        <li>Start in background mode option.</li>
        <li>Spanish language support.</li>
        <li>Persian language support.</li>
        <li>Hindi language support.</li></ul>''')

    dialog.present(self)

def open_downloads_folder(self, app, variaapp, appconf):
    if (os.name == 'nt'):
        os.startfile(appconf["download_directory"])
    else:
        subprocess.Popen(["xdg-open", appconf["download_directory"]])

def shutdown_on_completion(self, app, variaapp):
    if (variaapp.shutdown_mode == False):
        variaapp.shutdown_mode = True
        variaapp.exit_mode = False
        variaapp.sidebar_remote_mode_label.set_text(textwrap.fill(_("Shutdown on Completion"), 23))
    else:
        variaapp.shutdown_mode = False
        variaapp.sidebar_remote_mode_label.set_text("")

def exit_on_completion(self, app, variaapp):
    if (variaapp.exit_mode == False):
        variaapp.exit_mode = True
        variaapp.shutdown_mode = False
        variaapp.sidebar_remote_mode_label.set_text(textwrap.fill(_("Exit on Completion"), 23))
    else:
        variaapp.exit_mode = False
        variaapp.sidebar_remote_mode_label.set_text("")
