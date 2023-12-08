variaVersion = "v2023.12.8"

import gi
import sys
from gettext import gettext as _
import time
import json
import os
import time
import aria2p
import subprocess
import threading
from pathlib import Path
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio
import requests
from urllib.parse import unquote, urlparse
import textwrap

class MainWindow(Gtk.Window):
    def __init__(self, myapp, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "FLATPAK_ID" in os.environ:
            self.appdir = os.path.join('/var', 'data')
        else:
            self.appdir = os.path.join(os.path.expanduser('~'), '.varia')
            if not os.path.exists(self.appdir):
                os.makedirs(self.appdir)

        self.appconf = {'download_speed_limit_enabled': '0', 'download_speed_limit': '0', 'auth': '0', 'auth_username': '', 'auth_password': '', 'download_directory': GLib.get_user_special_dir(GLib.USER_DIRECTORY_DOWNLOAD)}

        if os.path.exists(os.path.join(self.appdir, 'varia.conf')):
            with open(os.path.join(self.appdir, 'varia.conf'), 'r') as f:
                self.appconf.update(json.load(f))
        else:
            with open(os.path.join(self.appdir, 'varia.conf'), 'w') as f:
                json.dump(self.appconf, f)

        self.api = aria2p.API(
            aria2p.Client(
                host="http://localhost",
                port=6801
            )
        )

        self.set_default_size(800, 600)
        self.set_size_request(650, 450)
        self.set_titlebar(Gtk.Box())

        self.total_download_speed = ""
        self.terminating = False

        self.set_title("Varia")
        Gtk.Settings.get_default().set_property("gtk-icon-theme-name", "Adwaita")

        self.overlay_split_view = Adw.OverlaySplitView.new()
        self.set_child(child=self.overlay_split_view)

        self.downloads = []
        self.pause_buttons = []
        self.all_paused = False

        # Sidebar
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sidebar_content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        header_bar = Adw.HeaderBar()
        header_bar.get_style_context().add_class('flat')
        sidebar_box.append(header_bar)

        preferences_button = Gtk.Button(tooltip_text=_("Preferences"))
        preferences_button.set_icon_name("emblem-system-symbolic")
        preferences_button.connect("clicked", self.show_preferences)

        hamburger_button = Gtk.MenuButton(tooltip_text=_("Other"))
        hamburger_button.set_icon_name("open-menu-symbolic")
        hamburger_menu_model = Gio.Menu()

        about_action = Gio.SimpleAction.new("downloads_folder", None)
        about_action.connect("activate", self.open_downloads_folder)
        myapp.add_action(about_action)

        downloads_folder_action = Gio.SimpleAction.new("about", None)
        downloads_folder_action.connect("activate", self.show_about)
        myapp.add_action(downloads_folder_action)

        hamburger_menu_item_open_downloads_folder = Gio.MenuItem.new(_("Open Download Folder"), "app.downloads_folder")
        hamburger_menu_model.append_item(hamburger_menu_item_open_downloads_folder)

        hamburger_menu_item_about = Gio.MenuItem.new(_("About Varia"), "app.about")
        hamburger_menu_model.append_item(hamburger_menu_item_about)

        hamburger_button.set_menu_model(hamburger_menu_model)

        header_bar.pack_start(preferences_button)
        header_bar.pack_end(hamburger_button)

        download_entry = Gtk.Entry()
        download_entry.set_placeholder_text(_("URL"))
        download_entry.set_placeholder_text("URL")

        download_button = Gtk.Button(label=_("Download"))
        download_button.get_style_context().add_class("pill")
        download_button.get_style_context().add_class("suggested-action")
        download_button.connect("clicked", self.on_download_clicked, download_entry)

        sidebar_expanding_box = Gtk.Box()
        Gtk.Widget.set_vexpand(sidebar_expanding_box, True)

        self.sidebar_speed_limited_label = Gtk.Label()

        sidebar_content_box.set_margin_start(6)
        sidebar_content_box.set_margin_end(6)
        sidebar_content_box.set_margin_top(6)
        sidebar_content_box.set_margin_bottom(6)

        sidebar_content_box.append(download_entry)
        sidebar_content_box.append(download_button)
        sidebar_content_box.append(sidebar_expanding_box)
        sidebar_content_box.append(self.sidebar_speed_limited_label)
        sidebar_box.append(sidebar_content_box)

        self.overlay_split_view.set_sidebar(sidebar_box)

        # Content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        self.total_download_speed_label = Gtk.Label(label=self.total_download_speed)

        header_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)

        header_pause_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        header_pause_label = Gtk.Label(label =_("Pause All"))
        header_pause_image = Gtk.Image.new()
        header_pause_image.set_from_icon_name("media-playback-pause-symbolic")
        header_pause_box.append(header_pause_image)
        header_pause_box.append(header_pause_label)
        header_pause_button = Gtk.Button()
        header_pause_button.set_child(header_pause_box)
        header_pause_button.connect("clicked", lambda button: self.pause_all(header_pause_label, header_pause_image))

        header_button_box.append(header_pause_button)

        header_stop_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        header_stop_label = Gtk.Label(label = _("Cancel All"))
        header_stop_image = Gtk.Image.new()
        header_stop_image.set_from_icon_name("process-stop-symbolic")
        header_stop_box.append(header_stop_image)
        header_stop_box.append(header_stop_label)
        header_stop_button = Gtk.Button()
        header_stop_button.set_child(header_stop_box)
        header_stop_button.connect("clicked", lambda button: self.stop_all())

        header_button_box.append(header_stop_button)

        header_expanding_box = Gtk.Box()
        Gtk.Widget.set_hexpand(header_expanding_box, True)
        header_expanding_box_1 = Gtk.Box()
        Gtk.Widget.set_hexpand(header_expanding_box_1, True)

        header_box.append(header_expanding_box)
        header_box.append(self.total_download_speed_label)
        header_box.append(header_expanding_box_1)
        header_box.append(header_button_box)

        header_bar = Adw.HeaderBar()
        header_bar.get_style_context().add_class('flat')
        header_bar.set_title_widget(header_box)
        content_box.append(header_bar)

        self.download_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.download_list.set_margin_start(10)
        self.download_list.set_margin_end(10)
        self.download_list.set_margin_bottom(10)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_child(self.download_list)
        scrolled_window.set_hexpand(True)
        scrolled_window.set_vexpand(True)

        content_box.append(scrolled_window)

        self.overlay_split_view.set_content(content_box)

        self.total_download_speed_calculator_thread = threading.Thread(target=self.total_download_speed_get, args=(self.downloads, self.total_download_speed_label))
        self.total_download_speed_calculator_thread.start()

        self.check_download_status_thread = threading.Thread(target=self.check_download_status)
        self.check_download_status_thread.start()

        # Check if the download path still exists:
        if not (os.path.exists(self.appconf["download_directory"])):
            self.appconf["download_directory"] = GLib.get_user_special_dir(GLib.USER_DIRECTORY_DOWNLOAD)
            self.save_appconf()

        # Set download speed limit from appconf:
        if ((self.appconf["download_speed_limit_enabled"] == "1") and (self.appconf["download_speed_limit"][:-1] != "0")):
            self.set_speed_limit(self.appconf["download_speed_limit"])

        # Set download directory from appconf:
        self.set_aria2c_download_directory()

        for filename in os.listdir(self.appconf["download_directory"]):
            if filename.endswith('.varia.json'):
                with open(os.path.join(self.appconf["download_directory"], filename), 'r') as f:
                    state = json.load(f)
                objectlist = self.create_actionrow(state['url'])
                download_thread = DownloadThread.load_state(self.api, self.appconf["download_directory"], filename, objectlist[0], objectlist[1], self.appconf["auth"], self.appconf["auth_username"], self.appconf["auth_password"])
                self.downloads.append(download_thread)
                download_thread.start()

    def check_download_status(self):
        while (self.terminating == False):
            i = 0
            for download_thread in self.downloads:
                if (download_thread.download):
                    if (download_thread.download.is_complete == 1):
                        download_thread.speed_label.set_text(_("Download complete."))
                        self.pause_buttons[i].hide()
                    elif (download_thread.download.status == "error") or (download_thread.download.status == "removed"):
                        if (download_thread.download.error_code == "24"):
                            download_thread.speed_label.set_text(_("Authorization failed."))
                        else:
                            download_thread.speed_label.set_text(_("An error occurred:") + " " + str(download_thread.download.error_code))
                        download_thread.stop(False)
                        download_thread.download.remove(force=True)
                        self.pause_buttons[i].hide()
                i += 1
            time.sleep(1)

    def total_download_speed_get(self, downloads, total_download_speed_label):
        while (self.terminating == False):
            total_download_speed = 0
            download_speed_mb = False
            download_speed_kb = False
            for download_thread in downloads:
                try:
                    download_thread.download.update()
                except:
                    continue
                try:
                    speed_label_text_first_digit = download_thread.speed_label.get_text()[0]
                except:
                    speed_label_text_first_digit = "0"
                if (speed_label_text_first_digit.isdigit()):
                    download_speed = (float(download_thread.speed_label.get_text().split(" ")[4]))
                    if (download_thread.speed_label.get_text().split(" ")[5] == _("MB/s")):
                        download_speed_mb = True
                    elif (download_thread.speed_label.get_text().split(" ")[5] == _("KB/s")):
                        download_speed_kb = True
                    total_download_speed = total_download_speed + download_speed
            if (total_download_speed == 0):
                total_download_speed_label.set_text(_("0 B/s"))
            elif (download_speed_mb == True):
                total_download_speed_label.set_text(str(round(total_download_speed, 2)) + _(" MB/s"))
            elif (download_speed_kb == True):
                total_download_speed_label.set_text(str(round(total_download_speed, 2)) + _(" KB/s"))
            else:
                total_download_speed_label.set_text(str(round(total_download_speed, 2)) + _(" B/s"))
            time.sleep(1)

    def create_actionrow(self, url):
        filename = url.split("/")[-1].split("?")[0]

        download_item = Adw.Bin()
        style_context = download_item.get_style_context()
        style_context.add_class('card')

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box_1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box_1.set_margin_bottom(10)

        box_2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box_2.set_margin_start(10)
        box_2.set_margin_end(10)
        box_2.set_margin_top(10)
        box_2.set_margin_bottom(10)

        download_item.set_child(box_2)

        filename_label = Gtk.Label(label=filename)
        filename_label.set_halign(Gtk.Align.START)
        box.append(filename_label)

        progress_bar = Gtk.ProgressBar()

        speed_label = Gtk.Label()
        speed_label.set_halign(Gtk.Align.START)
        box.append(speed_label)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        self.pause_buttons.append(Gtk.Button.new_from_icon_name("media-playback-pause-symbolic"))
        self.pause_buttons[len(self.pause_buttons)-1].connect("clicked", self.on_pause_clicked, self.pause_buttons[len(self.pause_buttons)-1], download_item)
        button_box.append(self.pause_buttons[len(self.pause_buttons)-1])

        stop_button = Gtk.Button.new_from_icon_name("process-stop-symbolic")
        stop_button.connect("clicked", self.on_stop_clicked, download_item)
        button_box.append(stop_button)

        box_1.append(box)

        box_1_expanding_box = Gtk.Box()
        Gtk.Widget.set_hexpand(box_1_expanding_box, True)
        box_1.append(box_1_expanding_box)

        box_1.append(button_box)
        box_2.append(box_1)
        box_2.append(progress_bar)

        self.download_list.append(download_item)
        download_item.index = len(self.downloads)-1

        return [progress_bar, speed_label, self.pause_buttons[len(self.pause_buttons)-1], stop_button]

    def on_download_clicked(self, button, entry):
        url = entry.get_text()
        entry.set_text("")
        if url:
            objectlist = self.create_actionrow(url)
            download_thread = DownloadThread(self.api, url, objectlist[0], objectlist[1], self.appconf["download_directory"], self.appconf["auth"], self.appconf["auth_username"], self.appconf["auth_password"])
            self.downloads.append(download_thread)
            download_thread.start()

    def on_pause_clicked(self, button, pause_button, download_item):
        self.all_paused = False
        download_thread = self.downloads[download_item.index+1]
        if download_thread.download.is_paused:
            download_thread.resume()
            image = Gtk.Image.new()
            image.set_from_icon_name("media-playback-pause-symbolic")
            pause_button.set_child(image)
        else:
            download_thread.pause()
            image = Gtk.Image.new()
            image.set_from_icon_name("media-playback-start-symbolic")
            pause_button.set_child(image)
        download_thread.save_state()

    def on_stop_clicked(self, button, download_item):
        index = download_item.index
        download_thread = self.downloads[index+1]
        try:
            download_thread.stop(True)
        except:
            pass
        self.download_list.remove(download_item)
        if (download_item in self.downloads):
            self.downloads.remove(download_item)

    def pause_all(self, header_pause_label, header_pause_image):
        i = 0
        pause_button_images = []
        if (self.all_paused == False):
            for download_thread in self.downloads:
                download_thread.pause()
                download_thread.save_state()

                pause_button_images.append(Gtk.Image.new())
                pause_button_images[i].set_from_icon_name("media-playback-start-symbolic")
                self.pause_buttons[i].set_child(pause_button_images[i])

                i += 1
            if (header_pause_label != "no"):
                header_pause_image.set_from_icon_name("media-playback-start-symbolic")
                header_pause_label.set_text(_("Resume All"))
            self.all_paused = True
        else:
            for download_thread in self.downloads:
                download_thread.resume()

                pause_button_images.append(Gtk.Image.new())
                pause_button_images[i].set_from_icon_name("media-playback-pause-symbolic")
                self.pause_buttons[i].set_child(pause_button_images[i])

                i += 1
            if (header_pause_label != "no"):
                header_pause_image.set_from_icon_name("media-playback-pause-symbolic")
                header_pause_label.set_text(_("Pause All"))
            self.all_paused = False

    def stop_all(self):
        while (self.downloads != []):
            child = self.download_list.get_first_child()
            while child is not None:
                next_child = child.get_next_sibling()
                self.download_list.remove(child)
                child = next_child
            for download_thread in self.downloads:
                download_thread.stop(True)
                self.downloads.remove(download_thread)

    def set_speed_limit(self, download_limit):
        self.sidebar_speed_limited_label.set_text("")
        if ((download_limit[:-1] != "0") and (self.appconf["download_speed_limit_enabled"] == "1")):
            speed_limited_text = textwrap.wrap(_("Speed limited"), width=40, break_long_words=False)
            speed_limited_text = "\n".join(speed_limited_text)
            self.sidebar_speed_limited_label.set_markup("<span color='red'>" + speed_limited_text + "</span>")
        else:
            download_limit = "0"

        json_request = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "aria2.changeGlobalOption",
            "params": [
                {"max-overall-download-limit": download_limit}
            ]
        }

        response = requests.post('http://localhost:6801/jsonrpc', headers={'Content-Type': 'application/json'}, data=json.dumps(json_request))

    def set_aria2c_download_directory(self):
        json_request = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "aria2.changeGlobalOption",
            "params": [
                {"dir": self.appconf["download_directory"]}
            ]
        }

        response = requests.post('http://localhost:6801/jsonrpc', headers={'Content-Type': 'application/json'}, data=json.dumps(json_request))

    def save_appconf(self):
        with open(os.path.join(self.appdir, 'varia.conf'), 'w') as f:
            json.dump(self.appconf, f)
        print("Config saved")

    def open_downloads_folder(self, app, myapp):
        subprocess.Popen(["xdg-open", self.appconf["download_directory"]])

    def show_about(self, app, myapp):
        dialog = Adw.AboutWindow(transient_for=self)
        dialog.set_application_name("Varia")
        dialog.set_version(variaVersion)
        dialog.set_developer_name("Giant Pink Robots!")
        dialog.set_license_type(Gtk.License(Gtk.License.MPL_2_0))
        dialog.set_comments(_("aria2 based download manager utilizing GTK4 and Libadwaita."))
        dialog.set_website("https://github.com/giantpinkrobots/varia")
        dialog.set_issue_url("https://github.com/giantpinkrobots/varia/issues")
        dialog.set_copyright(_("2023 Giant Pink Robots!\n\nThis application relies on the following pieces of software:\n\n- aria2: GPL v2 License (aria2 itself relies on OpenSSL: OpenSSL License)\n- aria2p: ISC License\n\nThe licenses of all of these pieces of software can be found in the dependencies_information directory in this application's app directory."))
        dialog.set_developers(["Giant Pink Robots! (@giantpinkrobots) https://github.com/giantpinkrobots"])
        dialog.set_application_icon("io.github.giantpinkrobots.varia")
        dialog.set_translator_credits(_("translator-credits"))
        dialog.show()

    def show_preferences(self, app):
        preferences = Adw.PreferencesWindow()

        page = Adw.PreferencesPage(title=_("Preferences"))
        preferences.add(page)
        group_1 = Adw.PreferencesGroup()
        page.add(group_1)

        download_directory_actionrow = Adw.ActionRow()
        download_directory_actionrow.set_title(_("Download Directory"))
        download_directory_actionrow.set_subtitle(self.appconf["download_directory"])

        download_directory_change_button = Gtk.Button(label=_("Change"))
        download_directory_change_button.get_style_context().add_class("suggested-action")
        download_directory_change_button.set_halign(Gtk.Align.START)
        download_directory_change_button.set_valign(Gtk.Align.CENTER)
        download_directory_change_button.connect("clicked", lambda clicked: self.on_download_directory_change(preferences, download_directory_actionrow))

        download_directory_actionrow.add_suffix(download_directory_change_button)

        speed_limit_expanded_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)

        speed_limit_unit_names = Gtk.ListStore(int, str)
        speed_limit_unit_names.append([1, _("KB/s")])
        speed_limit_unit_names.append([2, _("MB/s")])
        speed_limit_unit_names.append([3, _("GB/s")])
        speed_limit_unit_names_dropdown = Gtk.ComboBox.new_with_model(speed_limit_unit_names)
        speed_limit_unit_names_dropdown.set_active(0)
        speed_limit_unit_names_dropdown_renderer_text = Gtk.CellRendererText()
        speed_limit_unit_names_dropdown.pack_start(speed_limit_unit_names_dropdown_renderer_text, True)
        speed_limit_unit_names_dropdown.add_attribute(speed_limit_unit_names_dropdown_renderer_text, "text", 1)

        speed_limit_entry = Gtk.Entry()
        speed_limit_entry.set_placeholder_text(_("Speed"))

        speed_limit_expander_box = Adw.ExpanderRow()
        speed_limit_expander_box.set_title(_("Speed Limit"))

        speed_limit_expander_switch = Gtk.Switch()
        speed_limit_expander_switch.set_halign(Gtk.Align.START)
        speed_limit_expander_switch.set_valign(Gtk.Align.CENTER)
        speed_limit_expander_switch.connect("state-set", self.on_switch_speed_limit)

        if (self.appconf["download_speed_limit_enabled"] == "1"):
            speed_limit_expander_switch.set_active("active")

        speed_limit_expander_box.add_action(speed_limit_expander_switch)

        speed_limit_apply_button = Gtk.Button(tooltip_text=_("Set Speed Limit"))
        speed_limit_apply_button.set_icon_name("emblem-ok-symbolic")
        speed_limit_apply_button.get_style_context().add_class("suggested-action")
        speed_limit_apply_button.connect('clicked', lambda clicked: self.on_speed_limit_changed(speed_limit_entry, speed_limit_unit_names_dropdown))

        preferences_hexpanding_box_left = Gtk.Box()
        Gtk.Widget.set_hexpand(preferences_hexpanding_box_left, True)
        preferences_hexpanding_box_right = Gtk.Box()
        Gtk.Widget.set_hexpand(preferences_hexpanding_box_right, True)

        speed_limit_expanded_box.append(preferences_hexpanding_box_left)
        speed_limit_expanded_box.append(speed_limit_entry)
        speed_limit_expanded_box.append(speed_limit_unit_names_dropdown)
        speed_limit_expanded_box.append(speed_limit_apply_button)
        speed_limit_expanded_box.append(preferences_hexpanding_box_right)

        speed_limit_expanded_box.set_margin_top(10)
        speed_limit_expanded_box.set_margin_bottom(10)

        speed_limit_expander_box.add_row(speed_limit_expanded_box)

        auth_expander = Adw.ExpanderRow()
        auth_expander.set_title(_("Authentication"))

        auth_expander_switch = Gtk.Switch()
        auth_expander_switch.set_halign(Gtk.Align.START)
        auth_expander_switch.set_valign(Gtk.Align.CENTER)
        auth_expander_switch.connect("state-set", self.on_switch_auth)

        if (self.appconf["auth"] == "1"):
            auth_expander_switch.set_active("active")

        auth_expander.add_action(auth_expander_switch)

        username_entry = Gtk.Entry()
        username_entry.set_placeholder_text(_("Username"))
        password_entry = Gtk.Entry()
        password_entry.set_placeholder_text(_("Password"))
        password_entry.set_visibility(False)
        auth_apply_button = Gtk.Button(tooltip_text=_("Set Speed Limit"))
        auth_apply_button.set_icon_name("emblem-ok-symbolic")
        auth_apply_button.get_style_context().add_class("suggested-action")
        auth_apply_button.connect('clicked', lambda entry: self.set_auth_credentials(username_entry, password_entry))

        auth_expander_expanded_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        auth_expander_expanded_box.append(username_entry)
        auth_expander_expanded_box.append(password_entry)
        auth_expander_expanded_box.append(auth_apply_button)
        auth_expander_expanded_box.set_margin_top(10)
        auth_expander_expanded_box.set_margin_bottom(10)
        auth_expander_expanded_box.set_margin_start(10)
        auth_expander_expanded_box.set_margin_end(10)

        auth_expander.add_row(auth_expander_expanded_box)

        group_1.add(download_directory_actionrow)
        group_1.add(speed_limit_expander_box)
        group_1.add(auth_expander)

        match self.appconf["download_speed_limit"][-1]:
            case "K":
                speed_limit_unit_names_dropdown.set_active(0)
            case "M":
                speed_limit_unit_names_dropdown.set_active(1)
            case "G":
                speed_limit_unit_names_dropdown.set_active(2)
        if (self.appconf["download_speed_limit"][:-1] != "0"):
            speed_limit_entry.set_text(self.appconf["download_speed_limit"][:-1])

        preferences.present()

    def on_download_directory_change(self, prefswindow, actionrow):
        Gtk.FileDialog().select_folder(None, None, self.on_download_directory_selected, prefswindow, actionrow)

    def on_download_directory_selected(self, dialog, result, prefswindow, actionrow):
        try:
            folder = dialog.select_folder_finish(result)
            self.appconf["download_directory"] = folder.get_path()
            self.save_appconf()
            self.set_aria2c_download_directory()
            actionrow.set_subtitle(self.appconf["download_directory"])
        except:
            error_dialog = Adw.MessageDialog()
            error_dialog.set_body(_("Failed to open folder."))
            error_dialog.add_response("ok",  _("OK"))
            error_dialog.set_default_response("ok")
            error_dialog.set_close_response("ok")
            error_dialog.set_transient_for(prefswindow)
            error_dialog.connect("response", self.on_dialog_dismiss)
            error_dialog.show()

    def on_dialog_dismiss(self, dialog, response_id):
        dialog.destroy()

    def on_switch_speed_limit(self, switch, state):
        if state:
            self.appconf["download_speed_limit_enabled"] = "1"
        else:
            self.appconf["download_speed_limit_enabled"] = "0"
        self.set_speed_limit(self.appconf["download_speed_limit"])
        self.save_appconf()

    def on_speed_limit_changed(self, speed, speed_type):
        speed = speed.get_text()
        if (speed == ""):
            speed = "0"
        speed_type = speed_type.get_active()
        match speed_type:
            case 0:
                download_limit = speed + "K"
            case 1:
                download_limit = speed + "M"
            case 2:
                download_limit = speed + "G"

        self.set_speed_limit(download_limit)
        self.appconf['download_speed_limit'] = download_limit
        self.save_appconf()

    def on_switch_auth(self, switch, state):
        if state:
            self.appconf["auth"] = "1"
        else:
            self.appconf["auth"] = "0"
        self.save_appconf()

    def set_auth_credentials(self, username_entry, password_entry):
        self.appconf["auth_username"] = username_entry.get_text()
        self.appconf["auth_password"] = password_entry.get_text()
        self.save_appconf()

    def exitProgram(self, app):
        self.terminating = True
        self.all_paused = False
        self.pause_all("no","no")
        self.api.client.shutdown()
        self.destroy()

class DownloadThread(threading.Thread):
    def __init__(self, api, url, progress_bar, speed_label, downloaddir, auth, auth_username, auth_password):
        threading.Thread.__init__(self)
        self.api = api
        self.downloaddir = downloaddir
        self.download = None
        self.url = url
        self.speed_label = speed_label
        self.stop_event = threading.Event()
        self.auth = auth
        self.auth_username = auth_username
        self.auth_password = auth_password
        self.progress_bar = progress_bar

    def is_valid_url(self):
        if not ((self.url[0:7] == "http://") or (self.url[0:8] == "https://")):
            self.url = "http://" + self.url
        result = urlparse(self.url)
        try:
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def run(self):
        if not (self.is_valid_url()):
            try:
                GLib.idle_add(self.show_message(_("This is not a valid URL.")))
                print("Error: Not a valid url.")
            except:
                print("Error: Couldn't display 'not a valid url' error, for some reason.")
                return
        else:
            response = requests.head(self.url)
            if ((response.status_code == 401) and (self.auth == '1')):
                if (self.url[0:7] == "http://"):
                    self.url = self.url[:7] + self.auth_username + ":" + self.auth_password + "@" + self.url[7:]
                elif (self.url[0:8] == "https://"):
                    self.url = self.url[:8] + self.auth_username + ":" + self.auth_password + "@" + self.url[8:]
                else:
                    self.url = self.auth_username + ":" + self.auth_password + "@" + self.url
                print ("Authentication enabled.")
            print(self.url)
            self.download = self.api.add_uris([self.url])
            downloadname = self.download.name
            print("Download added.\n" + self.downloaddir + "\n" + self.url)
            while (True):
                try:
                    self.download.update()
                    GLib.idle_add(self.update_labels_and_things)
                    if (self.download.is_complete):
                        if os.path.exists(os.path.join(self.downloaddir,(self.download.gid + ".varia.json"))):
                            os.remove(os.path.join(self.downloaddir,(self.download.gid + ".varia.json")))
                        break
                    elif (self.download.status == "error"):
                        return
                except:
                    return
                time.sleep(1)

    def show_message(self, message):
        self.speed_label.set_text(message)

    def update_labels_and_things(self):
        self.progress_bar.set_fraction(self.download.progress / 100)
        download_speed_mb = (self.download.download_speed / 1024 / 1024)
        if int(str(download_speed_mb)[0]) == 0:
            download_speed_kb = (self.download.download_speed / 1024)
            if int(str(download_speed_kb)[0]) == 0:
                self.speed_label.set_text(f"{round(self.download.progress)}%  |  {round(self.download.download_speed, 2)} B/s")
            else:
                self.speed_label.set_text(f"{round(self.download.progress)}%  |  {round(self.download.download_speed / 1024, 2)} KB/s")
        else:
            self.speed_label.set_text(f"{round(self.download.progress)}%  |  {round(self.download.download_speed / 1024 / 1024, 2)} MB/s")

    def pause(self):
        if self.download:
            if self.download.is_paused == False:
                try:
                    self.download.pause()
                    print ("Download paused.")
                except:
                    try:
                        self.download.pause([self.download.gid])
                        print ("Download paused.")
                    except:
                        self.stop(False)
                        print ("Something went wrong when pausing. Stopping download without removing files.")

    def resume(self):
        if self.download:
            if self.download.is_paused == True:
                try:
                    self.download.resume()
                    print ("Download resumed.")
                except:
                    self.speed_label.set_text(_("An error occurred:") + " " + self.download.error_message.split("status=")[1])
                    print ("An error occurred when resuming. " + self.download.error_message.split("status=")[1])

    def stop(self, deletefiles):
        if self.download:
            downloadgid = self.download.gid
            downloadname = self.download.name
            self.download.remove(force=True)
            if not self.download.is_complete:
                if (deletefiles == True):
                    if os.path.exists(os.path.join(self.downloaddir,(downloadgid + ".varia.json"))):
                        os.remove(os.path.join(self.downloaddir,(downloadgid + ".varia.json")))
                    if os.path.exists(os.path.join(self.downloaddir, downloadname)):
                        os.remove(os.path.join(self.downloaddir, downloadname))
            print ("Download stopped.")

    def save_state(self):
        if self.download:
            try:
                self.download.update()
            except:
                print ("Couldn't update the status of the download. Skipping state saving.")
                return
            state = {
                'url': self.url,
                'downloaded': self.download.completed_length,
            }
            with open(os.path.join(self.downloaddir, f'{self.download.gid}.varia.json'), 'w') as f:
                json.dump(state, f)
            print ("State saved for download.")

    @classmethod
    def load_state(cls, api, downloaddir, filename, progress_bar, speed_label, auth, auth_username, auth_password):
        with open(os.path.join(downloaddir, filename), 'r') as f:
            state = json.load(f)
            os.remove(os.path.join(downloaddir, filename))
        instance = cls(api, state['url'], progress_bar, speed_label, downloaddir, auth, auth_username, auth_password)
        return instance

class MyApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.win = MainWindow(application=app, myapp=self)
        self.win.present()

def main(version):
    app = MyApp(application_id="io.github.giantpinkrobots.varia")
    try:
        app.run(sys.argv)
    finally:
        app.win.exitProgram(app)

