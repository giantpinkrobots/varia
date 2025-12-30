import os
import subprocess
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio
from stringstorage import gettext as _

from window.preferences import show_preferences
from download.actionrow import on_download_clicked
from download.videos import on_video_clicked

def window_create_sidebar(self, variaapp, variaVersion):
    sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    self.sidebar_content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)

    header_bar = Adw.HeaderBar()
    header_bar.add_css_class('flat')
    sidebar_box.append(header_bar)

    preferences_button = Gtk.Button(tooltip_text=_("Preferences"))
    preferences_button.set_icon_name("applications-system-symbolic")
    preferences_button.connect("clicked", show_preferences, self, variaapp, variaVersion)

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

    mac_preferences_action = Gio.SimpleAction.new("preferences", None)
    mac_preferences_action.connect("activate", menubar_preferences_clicked, self, variaapp, variaVersion)
    variaapp.add_action(mac_preferences_action)

    quit_action = Gio.SimpleAction.new("quit_varia", None)
    quit_action.connect("activate", quit_varia, self)
    variaapp.add_action(quit_action)

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
    hamburger_menu_model.append_item(hamburger_menu_item_background)

    hamburger_menu_item_cancel_all = Gio.MenuItem.new(_("Cancel All"), "app.cancel_all_downloads")
    hamburger_menu_model.append_item(hamburger_menu_item_cancel_all)

    hamburger_menu_item_open_downloads_folder = Gio.MenuItem.new(_("Open Download Folder"), "app.downloads_folder")
    hamburger_menu_model.append_item(hamburger_menu_item_open_downloads_folder)

    completion_submenu_model = Gio.Menu()

    completion_submenu_item_exit = Gio.MenuItem.new(_("Exit on Completion"), "app.exit_on_completion")
    completion_submenu_model.append_item(completion_submenu_item_exit)

    if (os.uname().sysname == 'Darwin'):
        completion_submenu_item_shutdown = Gio.MenuItem.new(_("Sleep on Completion"), "app.shutdown_on_completion")
    else:
        completion_submenu_item_shutdown = Gio.MenuItem.new(_("Shutdown on Completion"), "app.shutdown_on_completion")
    completion_submenu_model.append_item(completion_submenu_item_shutdown)

    if (os.uname().sysname == 'Darwin'):
        mac_submenu_model = Gio.Menu()
        mac_submenu_model.append_item(hamburger_menu_item_background)
        mac_submenu_model.append_item(hamburger_menu_item_cancel_all)
        mac_submenu_model.append_item(hamburger_menu_item_open_downloads_folder)
        hamburger_menu_model.append_submenu(_("Other"), mac_submenu_model)

    hamburger_menu_model.append_submenu(_("Completion Options"), completion_submenu_model)

    hamburger_menu_item_about = Gio.MenuItem.new(_("About Varia"), "app.about")
    hamburger_menu_model.append_item(hamburger_menu_item_about)

    hamburger_menu_item_quit = Gio.MenuItem.new(_("Quit"), "app.quit_varia")
    hamburger_menu_model.append_item(hamburger_menu_item_quit)

    hamburger_button.set_menu_model(hamburger_menu_model)

    if (os.uname().sysname == 'Darwin'):
        variaapp.set_menubar(hamburger_menu_model)

    else:
        header_bar.pack_start(preferences_button)
        header_bar.pack_end(hamburger_button)

    box_add_download = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    box_add_download.set_margin_start(8)
    box_add_download.set_margin_end(8)
    box_add_download.set_margin_top(8)
    box_add_download.set_margin_bottom(8)

    download_entry = Gtk.Entry()
    download_entry.set_placeholder_text(_("URL"))

    self.download_button_icon = Gtk.Image.new_from_icon_name("folder-download-symbolic")
    self.download_button_text = Gtk.Label(label=_("Download"))
    download_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    download_button_box.append(self.download_button_icon)
    download_button_box.append(self.download_button_text)

    self.download_button = Gtk.Button()
    self.download_button.set_child(download_button_box)
    self.download_button.add_css_class("suggested-action")
    self.download_button.set_sensitive(False)
    self.download_button.connect("clicked", on_download_clicked, self, download_entry, None, None, "regular", None, False, self.appconf["download_directory"], 0)

    self.video_button_icon = Gtk.Image.new_from_icon_name("camera-video-symbolic")
    self.video_button_text = Gtk.Label(label=_("Video / Audio"))
    video_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    video_button_box.append(self.video_button_icon)
    video_button_box.append(self.video_button_text)

    self.video_button = Gtk.Button()
    self.video_button.set_child(video_button_box)
    self.video_button.add_css_class("suggested-action")
    self.video_button.set_sensitive(False)
    self.video_button.connect("clicked", on_video_clicked, self, download_entry)

    download_entry.connect('changed', on_download_entry_changed, self.download_button, self.video_button)

    self.add_torrent_button = Gtk.Button()
    self.add_torrent_button.connect("clicked", on_add_torrent_clicked, self)

    if (self.appconf['torrent_enabled'] == '1'):
        self.torrent_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.torrent_button_box.append(Gtk.Image.new_from_icon_name("document-open-symbolic"))
        self.torrent_button_box.append(Gtk.Label(label=_("Torrent")))
        self.add_torrent_button.add_css_class("suggested-action")
        self.add_torrent_button.set_sensitive(True)

    else:
        self.torrent_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.torrent_button_box.append(Gtk.Label(label=_("Torrenting Disabled")))
        self.add_torrent_button.set_sensitive(False)

    self.add_torrent_button.set_child(self.torrent_button_box)

    box_add_download.append(download_entry)
    box_add_download.append(self.download_button)
    box_add_download.append(self.video_button)
    box_add_download.append(Gtk.Separator(margin_top=8, margin_bottom=8))
    box_add_download.append(self.add_torrent_button)

    frame_add_download = Gtk.Frame()
    frame_add_download.set_margin_bottom(8)
    frame_add_download.set_child(box_add_download)

    self.filter_button_show_all = Gtk.ToggleButton(tooltip_text=_("Filter downloads by {filter option}").replace("{filter option}", _("All")))
    self.filter_button_show_all.add_css_class('flat')
    filter_button_show_all_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    filter_button_show_all_box.set_margin_top(8)
    filter_button_show_all_box.set_margin_bottom(8)
    filter_button_show_all_box.append(Gtk.Image.new_from_icon_name("radio-symbolic"))
    filter_button_show_all_label = Gtk.Label(label=_("All"))
    filter_button_show_all_label.add_css_class('body')
    filter_button_show_all_box.append(filter_button_show_all_label)
    self.filter_button_show_all.set_child(filter_button_show_all_box)
    self.filter_button_show_all.set_active(True)
    self.filter_button_show_all.connect("clicked", self.filter_download_list, "show_all")

    self.filter_button_show_downloading = Gtk.ToggleButton(tooltip_text=_("Filter downloads by {filter option}").replace("{filter option}", _("In Progress")))
    self.filter_button_show_downloading.add_css_class('flat')
    filter_button_show_downloading_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    filter_button_show_downloading_box.set_margin_top(8)
    filter_button_show_downloading_box.set_margin_bottom(8)
    filter_button_show_downloading_box.append(Gtk.Image.new_from_icon_name("content-loading-symbolic"))
    filter_button_show_downloading_label = Gtk.Label(label=_("In Progress"))
    filter_button_show_downloading_label.add_css_class('body')
    filter_button_show_downloading_box.append(filter_button_show_downloading_label)
    self.filter_button_show_downloading.set_child(filter_button_show_downloading_box)
    self.filter_button_show_downloading.connect("clicked", self.filter_download_list, "show_downloading")

    self.filter_button_show_completed = Gtk.ToggleButton(tooltip_text=_("Filter downloads by {filter option}").replace("{filter option}", _("Completed")))
    self.filter_button_show_completed.add_css_class('flat')
    filter_button_show_completed_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    filter_button_show_completed_box.set_margin_top(8)
    filter_button_show_completed_box.set_margin_bottom(8)
    filter_button_show_completed_box.append(Gtk.Image.new_from_icon_name("object-select-symbolic"))
    filter_button_show_completed_label = Gtk.Label(label=_("Completed"))
    filter_button_show_completed_label.add_css_class('body')
    filter_button_show_completed_box.append(filter_button_show_completed_label)
    self.filter_button_show_completed.set_child(filter_button_show_completed_box)
    self.filter_button_show_completed.connect("clicked", self.filter_download_list, "show_completed")

    self.filter_button_show_seeding = Gtk.ToggleButton(tooltip_text=_("Filter downloads by {filter option}").replace("{filter option}", _("Seeding")))
    self.filter_button_show_seeding.add_css_class('flat')
    filter_button_show_seeding_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    filter_button_show_seeding_box.set_margin_top(8)
    filter_button_show_seeding_box.set_margin_bottom(8)
    filter_button_show_seeding_box.append(Gtk.Image.new_from_icon_name("go-up-symbolic"))
    filter_button_show_seeding_label = Gtk.Label(label=_("Seeding"))
    filter_button_show_seeding_label.add_css_class('body')
    filter_button_show_seeding_box.append(filter_button_show_seeding_label)
    self.filter_button_show_seeding.set_child(filter_button_show_seeding_box)
    self.filter_button_show_seeding.connect("clicked", self.filter_download_list, "show_seeding")

    self.filter_button_show_failed = Gtk.ToggleButton(tooltip_text=_("Filter downloads by {filter option}").replace("{filter option}", _("Failed")))
    self.filter_button_show_failed.add_css_class('flat')
    filter_button_show_failed_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    filter_button_show_failed_box.set_margin_top(8)
    filter_button_show_failed_box.set_margin_bottom(8)
    filter_button_show_failed_box.append(Gtk.Image.new_from_icon_name("process-stop-symbolic"))
    filter_button_show_failed_label = Gtk.Label(label=_("Failed"))
    filter_button_show_failed_label.add_css_class('body')
    filter_button_show_failed_box.append(filter_button_show_failed_label)
    self.filter_button_show_failed.set_child(filter_button_show_failed_box)
    self.filter_button_show_failed.connect("clicked", self.filter_download_list, "show_failed")

    sidebar_filter_buttons_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    sidebar_filter_buttons_box.append(self.filter_button_show_all)
    sidebar_filter_buttons_box.append(self.filter_button_show_downloading)
    sidebar_filter_buttons_box.append(self.filter_button_show_completed)
    sidebar_filter_buttons_box.append(self.filter_button_show_seeding)
    sidebar_filter_buttons_box.append(self.filter_button_show_failed)

    self.sidebar_content_box.append(frame_add_download)
    self.sidebar_content_box.append(sidebar_filter_buttons_box)
    self.sidebar_content_box.append(Gtk.Box(vexpand=True))
    sidebar_box.append(self.sidebar_content_box)

    self.sidebar_shutdown_mode_label = Gtk.Label()
    self.sidebar_shutdown_mode_label.add_css_class('dim-label')

    self.sidebar_remote_mode_label = Gtk.Label(label=_("Remote Mode"))
    self.sidebar_remote_mode_label.add_css_class('dim-label')
    if (self.appconf['remote'] == '1'):
        self.sidebar_content_box.append(self.sidebar_remote_mode_label)
    
    self.sidebar_speed_limited_label = Gtk.Label(label=_("Speed Limited"))
    self.sidebar_speed_limited_label.add_css_class('dim-label')

    self.sidebar_scheduler_label = Gtk.Label(label=_("Scheduler enabled"))
    self.sidebar_scheduler_label.add_css_class('dim-label')

    self.sidebar_exit_on_completion_label = Gtk.Label()
    self.sidebar_exit_on_completion_label.add_css_class('dim-label')

    self.sidebar_content_box.set_margin_start(4)
    self.sidebar_content_box.set_margin_end(4)
    self.sidebar_content_box.set_margin_bottom(4)

    self.overlay_split_view.set_sidebar(sidebar_box)

def on_download_entry_changed(entry, download_button, video_button):
    if entry.get_text() != "":
        download_button.set_sensitive(True)
        video_button.set_sensitive(True)
    else:
        download_button.set_sensitive(False)
        video_button.set_sensitive(False)

def on_add_torrent_clicked(self, variaapp):
    file_filter = Gtk.FileFilter()
    file_filter.add_pattern("*.torrent")
    dialog = Gtk.FileDialog(default_filter=file_filter)
    dialog.open(variaapp, None, on_add_torrent, variaapp)

def on_add_torrent(file_dialog, result, self):
    try:
        file = file_dialog.open_finish(result).get_path()
    except:
        return
    if file.endswith(".torrent"):
        self.api.add_torrent(file)

def menubar_preferences_clicked(app, variaapp1, self, variaapp, variaVersion):
    show_preferences(None, self, variaapp, variaVersion)

def background_mode(app, variaapp1, self, variaapp):
    self.exitProgram(app=app, variaapp=variaapp, background=True)

def show_about(app, variaapp, self, variaVersion):
    if self.overlay_split_view.get_show_sidebar() and \
        self.overlay_split_view.get_collapsed():

        self.overlay_split_view.set_show_sidebar(False)

    dialog = Adw.AboutDialog()
    dialog.set_application_name("Varia")
    dialog.set_version(variaVersion)
    dialog.set_developer_name("Giant Pink Robots!")
    dialog.set_license_type(Gtk.License(Gtk.License.MPL_2_0))
    #dialog.set_comments(_("aria2 based download manager utilizing GTK4 and Libadwaita.")) # Disabling details page
    dialog.set_website("https://giantpinkrobots.github.io/varia")
    dialog.set_issue_url("https://github.com/giantpinkrobots/varia/issues")
    dialog.set_copyright("2023 Giant Pink Robots!\n\n" + _("This application relies on the following pieces of software:") +
        "\n\n- aria2\n- yt-dlp\n- FFmpeg\n- Deno\n- 7zip\n- GTK4\n- Libadwaita\n- Meson\n- OpenSSL\n- Libayatana-AppIndicator\n- Python-appdirs\n- Python-aria2p\n- Python-certifi\n- Python-charset-normalizer\n- Python-gettext\n- Python-idna\n- Python-loguru\n- Python-requests\n- Python-setuptools\n- Python-urllib3\n- Python-websocket-client\n- Python-pystray\n- Python-dbus-next\n- Python-emoji-country-flag\n- PyInstaller\n\n" +
        _("The licenses of all of these pieces of software can be found in the dependencies_information directory in this application's app directory."))
    dialog.set_developers(["Giant Pink Robots! (@giantpinkrobots) https://github.com/giantpinkrobots"])
    dialog.set_application_icon("io.github.giantpinkrobots.varia")
    dialog.set_translator_credits(_("translator-credits"))
    dialog.set_artists(["Jakub Steiner"])
    dialog.set_release_notes_version(variaVersion)
    dialog.set_release_notes('''
        <ul><li>Minor bugfix and translations update.</li></ul>''')
    
    if (os.uname().sysname == 'Linux'):
        dialog.add_other_app("io.github.giantpinkrobots.flatsweep",
                            "Flatsweep",
                            "Flatpak leftover cleaner")
        dialog.add_other_app("io.github.giantpinkrobots.bootqt",
                            "Bootqt",
                            "Create bootable drives")

    if os.name == 'nt':
        dialog.set_content_width(self.get_default_size()[0])
        dialog.set_content_height(self.get_default_size()[1])
    dialog.present(self)

def open_downloads_folder(self, app, variaapp, appconf):
    if (os.uname().sysname == 'Linux'):
        subprocess.Popen(["xdg-open", appconf["download_directory"]])
    elif (os.uname().sysname == 'Darwin'):
        subprocess.call(('open', appconf["download_directory"]))
    else:
        os.startfile(appconf["download_directory"])

def shutdown_on_completion(self, app, variaapp):
    if (variaapp.shutdown_mode == False):
        variaapp.shutdown_mode = True
        variaapp.exit_mode = False
        try:
            variaapp.sidebar_content_box.remove(variaapp.sidebar_exit_on_completion_label)
        except:
            pass
        variaapp.sidebar_exit_on_completion_label.set_text(_("Shutdown on Completion"))
        variaapp.sidebar_content_box.append(variaapp.sidebar_exit_on_completion_label)
    else:
        variaapp.shutdown_mode = False
        try:
            variaapp.sidebar_content_box.remove(variaapp.sidebar_exit_on_completion_label)
        except:
            pass

def exit_on_completion(self, app, variaapp):
    if (variaapp.exit_mode == False):
        variaapp.exit_mode = True
        variaapp.shutdown_mode = False
        try:
            variaapp.sidebar_content_box.remove(variaapp.sidebar_exit_on_completion_label)
        except:
            pass
        variaapp.sidebar_exit_on_completion_label.set_text(_("Exit on Completion"))
        variaapp.sidebar_content_box.append(variaapp.sidebar_exit_on_completion_label)
    else:
        variaapp.exit_mode = False
        try:
            variaapp.sidebar_content_box.remove(variaapp.sidebar_exit_on_completion_label)
        except:
            pass

def quit_varia(app, self, variaapp):
    variaapp.exitProgram(app=app, variaapp=variaapp, background=False)
