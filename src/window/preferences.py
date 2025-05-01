import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio
from stringstorage import gettext as _
import os
from math import floor

from download.communicate import set_speed_limit, set_aria2c_download_directory, set_aria2c_custom_global_option, set_aria2c_cookies
from window.scheduler import show_scheduler_dialog
from window.updater import windows_updater

def show_preferences(button, self, app, variaVersion):
    if self.overlay_split_view.get_show_sidebar() and \
        self.overlay_split_view.get_collapsed():

        self.overlay_split_view.set_show_sidebar(False)

    preferences = Adw.PreferencesDialog(title=_("Preferences"))
    preferences.set_search_enabled(True)

    page_1 = Adw.PreferencesPage(title=_("Basic Settings"), icon_name="preferences-system-symbolic")
    page_2 = Adw.PreferencesPage(title=_("Torrent Settings"), icon_name="network-wired-symbolic")
    page_3 = Adw.PreferencesPage(title=_("Advanced Settings"), icon_name="application-x-executable-symbolic")
    preferences.add(page_1)
    preferences.add(page_2)
    preferences.add(page_3)
    group_extensions = Adw.PreferencesGroup()
    group_1 = Adw.PreferencesGroup()
    group_tray = Adw.PreferencesGroup()
    group_2 = Adw.PreferencesGroup()
    group_3 = Adw.PreferencesGroup()
    group_4 = Adw.PreferencesGroup()

    page_1.add(group_extensions)
    page_1.add(group_1)
    page_1.add(group_tray)    
    page_2.add(group_4)
    page_2.add(group_3)
    page_3.add(group_2)

    # Updater section for Windows:

    if (os.name == 'nt') and (os.path.exists("./updater-function-enabled")):
        update_actionrow = Adw.SwitchRow()
        update_actionrow.set_title(_("Automatically Check for Updates"))
        update_actionrow.connect("notify::active", on_switch_auto_update_check, self)

        update_button = Gtk.Button(label=_("Check Now"))
        update_button.set_halign(Gtk.Align.START)
        update_button.set_valign(Gtk.Align.CENTER)
        update_button.add_css_class("suggested-action")
        update_button.connect("clicked", lambda clicked: windows_updater(None, self, app, preferences, variaVersion, 1))

        update_actionrow.add_suffix(update_button)

        group_extensions.add(update_actionrow)

        if (self.appconf["check_for_updates_on_startup_enabled"] == '1'):
            update_actionrow.set_active("active")

    # Browser extensions section:

    browser_extension_actionrow = Adw.ActionRow()
    browser_extension_actionrow.set_title(_("Browser Extension"))

    browser_extension_firefox_button = Gtk.Button(label="Firefox")
    browser_extension_firefox_button.set_halign(Gtk.Align.START)
    browser_extension_firefox_button.set_valign(Gtk.Align.CENTER)
    browser_extension_chrome_button = Gtk.Button(label="Chrome, Edge, Opera...")
    browser_extension_chrome_button.set_halign(Gtk.Align.START)
    browser_extension_chrome_button.set_valign(Gtk.Align.CENTER)

    browser_extension_firefox_button.connect("clicked", lambda clicked: on_extension_selected(self, preferences, 'firefox'))
    browser_extension_chrome_button.connect("clicked", lambda clicked: on_extension_selected(self, preferences, 'chrome'))

    browser_extension_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
    browser_extension_buttons_box.append(browser_extension_firefox_button)
    browser_extension_buttons_box.append(browser_extension_chrome_button)

    browser_extension_actionrow.add_suffix(browser_extension_buttons_box)

    group_extensions.add(browser_extension_actionrow)

    # Download directory:

    download_directory_actionrow = Adw.ActionRow()
    download_directory_actionrow.set_title(_("Download Directory"))
    if (self.appconf["remote"] == "0"):
        download_directory_actionrow.set_subtitle(self.appconf["download_directory"])

    download_directory_change_button = Gtk.Button(label=_("Change"))
    download_directory_change_button.add_css_class("suggested-action")
    download_directory_change_button.set_halign(Gtk.Align.START)
    download_directory_change_button.set_valign(Gtk.Align.CENTER)
    download_directory_change_button.connect("clicked", lambda clicked: on_download_directory_change(self, "download_directory", preferences, download_directory_actionrow))

    download_directory_change_remote_label = Gtk.Label(label=_("Remote Mode"))
    download_directory_change_remote_label.set_halign(Gtk.Align.START)
    download_directory_change_remote_label.set_valign(Gtk.Align.CENTER)

    if (self.appconf["remote"] == "0"):
        download_directory_actionrow.add_suffix(download_directory_change_button)
    else:
        download_directory_actionrow.add_suffix(download_directory_change_remote_label)

    # Speed limit:

    speed_limit_unit_names_dropdown = Gtk.DropDown.new_from_strings(["KB/s", "MB/s", "GB/s"])
    speed_limit_unit_names_dropdown.set_selected(0)
    speed_limit_unit_names_dropdown.connect("notify::selected-item", lambda dropdown, param: on_speed_limit_changed(self, speed_limit_entry, speed_limit_unit_names_dropdown, speed_limit_expander_switch))

    speed_limit_expander_box = Adw.ExpanderRow()
    speed_limit_expander_box.set_title(_("Speed Limit"))

    speed_limit_expander_switch = Gtk.Switch()
    speed_limit_expander_switch.set_halign(Gtk.Align.START)
    speed_limit_expander_switch.set_valign(Gtk.Align.CENTER)
    speed_limit_expander_switch.connect("state-set", on_switch_speed_limit, self, preferences)

    speed_limit_entry = Adw.EntryRow()
    speed_limit_entry.set_title(_("Speed"))
    speed_limit_entry.set_input_purpose(Gtk.InputPurpose.NUMBER)
    speed_limit_entry.set_show_apply_button(True)
    speed_limit_entry.connect('changed', speed_limit_text_filter, self)
    speed_limit_entry.connect('apply', lambda clicked: on_speed_limit_changed(self, speed_limit_entry, speed_limit_unit_names_dropdown, speed_limit_expander_switch))

    if (self.appconf["download_speed_limit"][0] != "0"):
        speed_limit_expander_switch.set_sensitive(True)
        speed_limit_entry.set_text(self.appconf["download_speed_limit"][:-1])
        match (self.appconf["download_speed_limit"][-1]):
            case "K":
                speed_limit_unit_names_dropdown.set_selected(0)
            case "M":
                speed_limit_unit_names_dropdown.set_selected(1)
            case "G":
                speed_limit_unit_names_dropdown.set_selected(2)
    else:
        speed_limit_expander_switch.set_sensitive(False)

    if (self.appconf["download_speed_limit_enabled"] == "1"):
        speed_limit_expander_switch.set_active("active")

    speed_limit_expander_box.add_action(speed_limit_expander_switch)

    speed_limit_dropdown_hexpanding_box_left = Gtk.Box()
    Gtk.Widget.set_hexpand(speed_limit_dropdown_hexpanding_box_left, True)
    speed_limit_dropdown_hexpanding_box_right = Gtk.Box()
    Gtk.Widget.set_hexpand(speed_limit_dropdown_hexpanding_box_right, True)

    speed_limit_dropdown_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
    speed_limit_dropdown_box.append(speed_limit_dropdown_hexpanding_box_left)
    speed_limit_dropdown_box.append(speed_limit_unit_names_dropdown)
    speed_limit_dropdown_box.append(speed_limit_dropdown_hexpanding_box_right)

    speed_limit_dropdown_box.set_margin_top(5)
    speed_limit_dropdown_box.set_margin_bottom(5)

    speed_limit_expander_box.add_row(speed_limit_dropdown_box)
    speed_limit_expander_box.add_row(speed_limit_entry)

    # Scheduler:

    scheduler_actionrow = Adw.ActionRow()
    scheduler_actionrow.set_title(_("Scheduler"))

    scheduler_actionrow_edit_button = Gtk.Button(label=_("Change"))
    scheduler_actionrow_edit_button.set_halign(Gtk.Align.START)
    scheduler_actionrow_edit_button.set_valign(Gtk.Align.CENTER)
    scheduler_actionrow_edit_button.add_css_class("suggested-action")

    scheduler_actionrow_edit_button.connect("clicked", lambda clicked: show_scheduler_dialog(self, preferences, app, show_preferences, variaVersion))

    scheduler_actionrow_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    scheduler_actionrow_buttons_box.append(scheduler_actionrow_edit_button)

    scheduler_actionrow.add_suffix(scheduler_actionrow_buttons_box)

    # Simultaneous download amount:

    simultaneous_download_amount_spinrow = Adw.SpinRow(adjustment=Gtk.Adjustment(step_increment=1.0))
    simultaneous_download_amount_spinrow.set_title(_("Simultaneous Download Amount"))
    simultaneous_download_amount_spinrow.set_range(1.0, 20.0)
    simultaneous_download_amount_spinrow.set_value(float(self.appconf["download_simultaneous_amount"]))
    simultaneous_download_amount_spinrow.connect("changed", on_simultaneous_download_amount_changed, self)

    # Start in background:

    start_in_background = Adw.SwitchRow()
    start_in_background.set_title(_("Start in Background Mode"))
    start_in_background.connect("notify::active", on_start_in_background, self)

    if (self.appconf["default_mode"] == "background"):
        start_in_background.set_active("active")

    # Close to tray:

    use_tray_icon = Adw.SwitchRow()
    use_tray_icon.set_title(_("Background Mode on Close"))
    use_tray_icon.set_subtitle(_("Upon closing, Varia will close to tray insted of exiting."))
    use_tray_icon.connect("notify::active", on_use_tray_icon, self)

    if self.appconf["use_tray"] == "true":
        use_tray_icon.set_active("active")
    
    tray_icon_always_visible = Adw.SwitchRow()
    tray_icon_always_visible.set_title(_("Tray Icon Always Visible"))
    tray_icon_always_visible.set_subtitle(_("The tray icon will be visible even when Varia is not in background mode."))
    tray_icon_always_visible.connect("notify::active", on_tray_always_visible, self, app)

    if self.appconf["tray_always_visible"] == "true":
        tray_icon_always_visible.set_active("active")

    # Construct Group 1:

    group_1.add(download_directory_actionrow)
    group_1.add(speed_limit_expander_box)
    group_1.add(scheduler_actionrow)
    group_1.add(simultaneous_download_amount_spinrow)
    
    group_tray.add(use_tray_icon)
    group_tray.add(tray_icon_always_visible)
    group_tray.add(start_in_background)

    # Remote aria2:

    remote_aria2_expander_box = Adw.ExpanderRow()
    remote_aria2_expander_box.set_title(_("Remote Mode"))
    remote_aria2_expander_box.set_subtitle(_("This will disable the video download functionality.") + "\n" + _("The browser extension will not work when Remote Mode is enabled."))

    remote_aria2_expander_switch = Gtk.Switch()
    remote_aria2_expander_switch.set_halign(Gtk.Align.START)
    remote_aria2_expander_switch.set_valign(Gtk.Align.CENTER)

    if ((self.appconf["remote_protocol"] == "") or (self.appconf["remote_ip"] == "") or (self.appconf["remote_port"] == "") or (self.appconf["remote_location"] == "")):
        remote_aria2_expander_switch.set_sensitive(False)
    else:
        remote_aria2_expander_switch.set_sensitive(True)

    if (self.appconf["remote"] == "1"):
        remote_aria2_expander_switch.set_active("active")

    remote_aria2_expander_switch.connect("state-set", on_switch_remote, self, preferences)

    remote_aria2_expander_box.add_action(remote_aria2_expander_switch)

    remote_aria2_ip_protocol_names_dropdown_hexpanding_box_left = Gtk.Box()
    Gtk.Widget.set_hexpand(remote_aria2_ip_protocol_names_dropdown_hexpanding_box_left, True)
    remote_aria2_ip_protocol_names_dropdown_hexpanding_box_right = Gtk.Box()
    Gtk.Widget.set_hexpand(remote_aria2_ip_protocol_names_dropdown_hexpanding_box_right, True)

    remote_aria2_ip_protocol_names_dropdown = Gtk.DropDown.new_from_strings(["https://", "http://"])
    if (self.appconf['remote_protocol'] == 'https://'):
        remote_aria2_ip_protocol_names_dropdown.set_selected(0)
    else:
        remote_aria2_ip_protocol_names_dropdown.set_selected(1)
    remote_aria2_ip_protocol_names_dropdown.connect("notify::selected-item", lambda dropdown, param: set_remote(self, remote_aria2_ip_protocol_names_dropdown, remote_aria2_ip_entry, remote_aria2_port_entry, remote_aria2_rpc_entry, remote_aria2_location_entry, remote_aria2_expander_switch, preferences))

    remote_aria2_ip_protocol_names_dropdown_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
    remote_aria2_ip_protocol_names_dropdown_box.append(remote_aria2_ip_protocol_names_dropdown_hexpanding_box_left)
    remote_aria2_ip_protocol_names_dropdown_box.append(remote_aria2_ip_protocol_names_dropdown)
    remote_aria2_ip_protocol_names_dropdown_box.append(remote_aria2_ip_protocol_names_dropdown_hexpanding_box_right)

    remote_aria2_ip_protocol_names_dropdown_box.set_margin_top(5)
    remote_aria2_ip_protocol_names_dropdown_box.set_margin_bottom(5)

    remote_aria2_ip_entry = Adw.EntryRow()
    remote_aria2_ip_entry.set_title(_("Remote aria2 IP"))
    remote_aria2_ip_entry.set_show_apply_button(True)
    remote_aria2_ip_entry.connect('apply', lambda entry: set_remote(self, remote_aria2_ip_protocol_names_dropdown, remote_aria2_ip_entry, remote_aria2_port_entry, remote_aria2_rpc_entry, remote_aria2_location_entry, remote_aria2_expander_switch, preferences))

    remote_aria2_port_entry = Adw.EntryRow()
    remote_aria2_port_entry.set_title(_("Remote aria2 Port"))
    remote_aria2_port_entry.set_show_apply_button(True)
    remote_aria2_port_entry.connect('apply', lambda entry: set_remote(self, remote_aria2_ip_protocol_names_dropdown, remote_aria2_ip_entry, remote_aria2_port_entry, remote_aria2_rpc_entry, remote_aria2_location_entry, remote_aria2_expander_switch, preferences))

    remote_aria2_rpc_entry = Adw.EntryRow()
    remote_aria2_rpc_entry.set_title(_("Remote aria2 RPC Secret"))
    remote_aria2_rpc_entry.set_show_apply_button(True)
    remote_aria2_rpc_entry.connect('apply', lambda entry: set_remote(self, remote_aria2_ip_protocol_names_dropdown, remote_aria2_ip_entry, remote_aria2_port_entry, remote_aria2_rpc_entry, remote_aria2_location_entry, remote_aria2_expander_switch, preferences))

    remote_aria2_location_entry = Adw.EntryRow()
    remote_aria2_location_entry.set_title(_("Remote Download Location"))
    remote_aria2_location_entry.set_show_apply_button(True)
    remote_aria2_location_entry.connect('apply', lambda entry: set_remote(self, remote_aria2_ip_protocol_names_dropdown, remote_aria2_ip_entry, remote_aria2_port_entry, remote_aria2_rpc_entry, remote_aria2_location_entry, remote_aria2_expander_switch, preferences))

    remote_aria2_ip_entry.set_text(self.appconf["remote_ip"])
    remote_aria2_port_entry.set_text(self.appconf["remote_port"])
    remote_aria2_rpc_entry.set_text(self.appconf["remote_secret"])
    remote_aria2_location_entry.set_text(self.appconf["remote_location"])

    remote_aria2_expander_box.add_row(remote_aria2_ip_protocol_names_dropdown_box)
    remote_aria2_expander_box.add_row(remote_aria2_ip_entry)
    remote_aria2_expander_box.add_row(remote_aria2_port_entry)
    remote_aria2_expander_box.add_row(remote_aria2_rpc_entry)
    remote_aria2_expander_box.add_row(remote_aria2_location_entry)

    # Remote time:

    remote_time = Adw.SwitchRow()
    remote_time.set_title(_("Remote Timestamp"))
    remote_time.connect("notify::active", on_remote_time, self)

    if (self.appconf["remote_time"] == "1"):
        remote_time.set_active("active")

    # Auth:

    auth_expander = Adw.ExpanderRow()
    auth_expander.set_title(_("Authentication"))

    auth_expander_switch = Gtk.Switch()
    auth_expander_switch.set_halign(Gtk.Align.START)
    auth_expander_switch.set_valign(Gtk.Align.CENTER)
    auth_expander_switch.connect("state-set", on_switch_auth, self, preferences)

    username_entry = Adw.EntryRow()
    username_entry.set_title(_("Username"))
    username_entry.set_show_apply_button(True)
    username_entry.connect('apply', lambda entry: set_auth_credentials(self, username_entry, password_entry, auth_expander_switch))

    password_entry = Adw.PasswordEntryRow()
    password_entry.set_title(_("Password"))
    password_entry.set_show_apply_button(True)
    password_entry.connect('apply', lambda entry: set_auth_credentials(self, username_entry, password_entry, auth_expander_switch))

    username_entry.set_text(self.appconf["auth_username"])
    password_entry.set_text(self.appconf["auth_password"])

    if ((self.appconf["auth_username"] != "") and (self.appconf["auth_password"] != "")):
        auth_expander_switch.set_sensitive(True)
    else:
        auth_expander_switch.set_sensitive(False)

    if (self.appconf["auth"] == "1"):
        auth_expander_switch.set_active(True)

    auth_expander.add_action(auth_expander_switch)

    auth_expander.add_row(username_entry)
    auth_expander.add_row(password_entry)

    # Cookies.txt:

    cookies_txt_action = Adw.ActionRow()
    cookies_txt_action.set_title(_("Use cookies.txt"))

    cookies_txt_action_switch = Gtk.Switch()
    cookies_txt_action_switch.set_halign(Gtk.Align.START)
    cookies_txt_action_switch.set_valign(Gtk.Align.CENTER)
    cookies_txt_action_switch.connect("state-set", on_switch_cookies_txt, self)

    cookies_txt_import_button = Gtk.Button(label=_("Import cookies.txt"))
    cookies_txt_import_button.set_halign(Gtk.Align.START)
    cookies_txt_import_button.set_valign(Gtk.Align.CENTER)
    cookies_txt_import_button.add_css_class("suggested-action")

    cookies_txt_remove_button = Gtk.Button(label=_("Remove cookies.txt"))
    cookies_txt_remove_button.set_halign(Gtk.Align.START)
    cookies_txt_remove_button.set_valign(Gtk.Align.CENTER)
    cookies_txt_remove_button.add_css_class("destructive-action")

    cookies_txt_import_button.connect("clicked", lambda clicked: cookies_txt_import(self, True, cookies_txt_import_button, cookies_txt_remove_button, cookies_txt_action_switch))
    cookies_txt_remove_button.connect("clicked", lambda clicked: cookies_txt_import(self, False, cookies_txt_import_button, cookies_txt_remove_button, cookies_txt_action_switch))

    if os.path.exists(os.path.join(self.appdir, 'cookies.txt')):
        cookies_txt_action_switch.set_sensitive(True)
        cookies_txt_import_button.set_visible(False)
        cookies_txt_remove_button.set_visible(True)
    else:
        cookies_txt_action_switch.set_sensitive(False)
        cookies_txt_import_button.set_visible(True)
        cookies_txt_remove_button.set_visible(False)

    if (self.appconf["cookies_txt"] == "1"):
        cookies_txt_action_switch.set_active("active")

    cookies_txt_action.add_suffix(cookies_txt_import_button)
    cookies_txt_action.add_suffix(cookies_txt_remove_button)
    cookies_txt_action.add_suffix(cookies_txt_action_switch)

    # Construct Group 2:

    group_2.add(auth_expander)
    group_2.add(remote_time)
    group_2.add(cookies_txt_action)
    group_2.add(cookies_txt_action)
    group_2.add(remote_aria2_expander_box)

    # Enable or disable torrenting:

    torrent_enabled_switchrow = Adw.SwitchRow()
    torrent_enabled_switchrow.set_title(_("Enable Torrenting"))
    torrent_enabled_switchrow.set_subtitle(_("Disabling torrenting will prevent new torrents from being added. It will not stop current torrent instances."))

    if (self.appconf["torrent_enabled"] == "1"):
        torrent_enabled_switchrow.set_active("active")

    torrent_enabled_switchrow.connect("notify::active", on_switch_torrent, self)

    # Enable or disable seeding:

    seeding_enabled_switchrow = Adw.SwitchRow()
    seeding_enabled_switchrow.set_title(_("Allow Seeding"))

    if (self.appconf["torrent_seeding_enabled"] == "1"):
        seeding_enabled_switchrow.set_active("active")

    seeding_enabled_switchrow.connect("notify::active", on_switch_torrent_seeding, self)

    # Set seeding ratio limit:

    seeding_ratio_limit_switch = Gtk.Switch()
    seeding_ratio_limit_switch.set_halign(Gtk.Align.START)
    seeding_ratio_limit_switch.set_valign(Gtk.Align.CENTER)
    seeding_ratio_limit_switch.connect("state-set", on_switch_torrent_seeding_ratio_limit, self)

    seeding_ratio_limit_spinrow = Adw.SpinRow(adjustment=Gtk.Adjustment(step_increment=0.1))
    seeding_ratio_limit_spinrow.set_digits(1)
    seeding_ratio_limit_spinrow.set_title(_("Seeding Ratio Limit"))
    seeding_ratio_limit_spinrow.set_range(0.1, 100000.0)
    seeding_ratio_limit_spinrow.set_value(float(self.appconf["torrent_seeding_ratio"][1]))
    seeding_ratio_limit_spinrow.connect("changed", on_torrent_seeding_ratio_limit_change, self)
    seeding_ratio_limit_spinrow.add_suffix(seeding_ratio_limit_switch)

    if (self.appconf["torrent_seeding_ratio"][1] == True):
        seeding_ratio_limit_switch.set_active("active")

    # Custom download directory for torrents:

    torrent_download_directory_actionrow = Adw.ActionRow()
    torrent_download_directory_actionrow.set_title(_("Custom Download Directory for Torrents"))
    if (self.appconf["remote"] == "0"):
        torrent_download_directory_actionrow.set_subtitle(self.appconf["torrent_download_directory"])

    torrent_download_directory_switch = Gtk.Switch()
    torrent_download_directory_switch.set_halign(Gtk.Align.START)
    torrent_download_directory_switch.set_valign(Gtk.Align.CENTER)
    torrent_download_directory_switch.connect("state-set", on_switch_custom_torrent_download_directory, self)

    torrent_download_directory_change_button = Gtk.Button(label=_("Change"))
    torrent_download_directory_change_button.add_css_class("suggested-action")
    torrent_download_directory_change_button.set_halign(Gtk.Align.START)
    torrent_download_directory_change_button.set_valign(Gtk.Align.CENTER)
    torrent_download_directory_change_button.connect("clicked", lambda clicked: on_download_directory_change(self, "torrent_download_directory", preferences, torrent_download_directory_actionrow))

    torrent_download_directory_change_remote_label = Gtk.Label(label=_("Remote Mode"))
    torrent_download_directory_change_remote_label.set_halign(Gtk.Align.START)
    torrent_download_directory_change_remote_label.set_valign(Gtk.Align.CENTER)

    if self.appconf["torrent_download_directory_custom_enabled"] == "1":
        torrent_download_directory_switch.set_active("active")

    if (self.appconf["remote"] == "0"):
        torrent_download_directory_actionrow.add_suffix(torrent_download_directory_change_button)
        torrent_download_directory_actionrow.add_suffix(torrent_download_directory_switch)
    else:
        torrent_download_directory_actionrow.add_suffix(torrent_download_directory_change_remote_label)
        torrent_download_directory_actionrow.add_suffix(torrent_download_directory_switch)
        torrent_download_directory_switch.set_sensitive(False)

    # Construct Group 4 and 3:

    group_4.add(torrent_enabled_switchrow)

    self.group_3_options = []
    self.group_3_options.append(seeding_enabled_switchrow)
    self.group_3_options.append(seeding_ratio_limit_spinrow)
    self.group_3_options.append(torrent_download_directory_actionrow)

    for option in self.group_3_options:
        group_3.add(option)

    # Set all group 3 settings insensitive if torrenting is disabled:

    torrent_settings_set_sensitive(self)

    preferences.present(self)

def on_switch_auto_update_check(switch, state, self):
    state = switch.get_active()
    if state:
        self.appconf["check_for_updates_on_startup_enabled"] = '1'
    else:
        self.appconf["check_for_updates_on_startup_enabled"] = '0'
        if hasattr(self, 'update_available_banner'):
            if self.update_available_banner != None:
                self.update_available_banner.set_revealed(False)

    self.save_appconf()

def speed_limit_text_filter(entry, self):
    text = entry.get_text()
    new_text = ""
    for char in text:
        if (char.isdigit()):
            new_text += char
    if (new_text != text):
        GLib.idle_add(entry.set_text, new_text)
        GLib.idle_add(entry.set_position, -1)

def on_extension_selected(self, prefswindow, browser):
    if (browser == 'firefox'):
        link = 'https://addons.mozilla.org/firefox/addon/varia-integrator/'
    else:
        link = 'https://chrome.google.com/webstore/detail/dacakhfljjhgdfdlgjpabkkjhbpcmiff'
    Gio.AppInfo.launch_default_for_uri(link)

def on_download_directory_change(self, directory_to_be_changed, prefswindow, actionrow):
    Gtk.FileDialog().select_folder(None, None, on_download_directory_selected, directory_to_be_changed, self, prefswindow, actionrow)

def on_download_directory_selected(dialog, result, directory_to_be_changed, self, prefswindow, actionrow):
    try:
        folder = dialog.select_folder_finish(result)
        self.appconf[directory_to_be_changed] = folder.get_path()
        self.save_appconf()

        if directory_to_be_changed == "download_directory": # If what's being changed is the regular download directory and not the torrent download directory
            set_aria2c_download_directory(self)

        actionrow.set_subtitle(self.appconf[directory_to_be_changed])

    except GLib.GError as exception:
        if (exception.domain == 'gtk-dialog-error-quark' and exception.code == 2) == False: # If there was an actual issue instead of the user just dismissing the dialog
            error_dialog = Adw.AlertDialog()
            error_dialog.set_body(_("Failed to open directory."))
            error_dialog.add_response("ok",  _("OK"))
            error_dialog.set_default_response("ok")
            error_dialog.set_close_response("ok")
            error_dialog.present(prefswindow)

def on_switch_speed_limit(switch, state, self, preferencesWindow):
    if state:
        self.appconf["download_speed_limit_enabled"] = "1"
    else:
        self.appconf["download_speed_limit_enabled"] = "0"
    set_speed_limit(self, self.appconf["download_speed_limit"])

    self.save_appconf()

def on_speed_limit_changed(self, speed, speed_type, switch):
    speed = speed.get_text()
    if (speed == ""):
        speed = "0"

    speed = str(int(speed))

    speed_type = speed_type.get_selected()
    match speed_type:
        case 0:
            download_limit = speed + "K"
        case 1:
            download_limit = speed + "M"
        case 2:
            download_limit = speed + "G"

    set_speed_limit(self, download_limit)
    self.appconf['download_speed_limit'] = download_limit

    print(self.appconf["download_speed_limit"])

    if ((self.appconf["download_speed_limit"] == "0K") or (self.appconf["download_speed_limit"] == "0M") or (self.appconf["download_speed_limit"] == "0G")):
        switch.set_active(False)
        switch.set_sensitive(False)
    else:
        switch.set_sensitive(True)

    self.save_appconf()

def on_start_in_background(switch, state, self):
    state = switch.get_active()
    if state:
        self.appconf["default_mode"] = "background"
    else:
        self.appconf["default_mode"] = "visible"

    self.save_appconf()

def on_use_tray_icon(switch, state, self):
    state = switch.get_active()
    if state:
        self.appconf["use_tray"] = "true"
    else:
        self.appconf["use_tray"] = "false"

    self.save_appconf()

def on_tray_always_visible(switch, state, self, variaapp):
    state = switch.get_active()
    if state:
        self.appconf["tray_always_visible"] = "true"
        self.start_tray_process(variaapp)
    else:
        self.appconf["tray_always_visible"] = "false"
        self.tray_connection_thread_stop = True
        self.tray_process.kill()
        self.tray_process = None

    self.save_appconf()

def on_remote_time(switch, state, self):
    state = switch.get_active()
    if state:
        self.appconf["remote_time"] = "1"
        set_aria2c_custom_global_option(self, "remote-time", "true")
    else:
        self.appconf["remote_time"] = "0"
        set_aria2c_custom_global_option(self, "remote-time", "false")

    self.save_appconf()

def on_switch_auth(switch, state, self, preferencesWindow):
    if state:
        self.appconf["auth"] = "1"
    else:
        self.appconf["auth"] = "0"

    self.save_appconf()

def set_auth_credentials(self, username_entry, password_entry, switch):
    self.appconf["auth_username"] = username_entry.get_text()
    self.appconf["auth_password"] = password_entry.get_text()

    if ((self.appconf["auth_username"] == "") or (self.appconf["auth_password"] == "")):
        switch.set_active(False)
        switch.set_sensitive(False)
    else:
        switch.set_sensitive(True)

    self.save_appconf()

def on_simultaneous_download_amount_changed(spinrow, self):
    self.appconf["download_simultaneous_amount"] = str(int(spinrow.get_value()))
    print(str(int(spinrow.get_value())))
    self.save_appconf()

    #set_aria2c_download_simultaneous_amount(self)
    set_aria2c_custom_global_option(self, "max-concurrent-downloads", str(self.appconf["download_simultaneous_amount"]))

def set_remote(self, remote_protocol, remote_ip, remote_port, remote_secret, remote_location, switch, preferencesWindow):
    if (remote_protocol.get_selected() == 0):
        self.appconf["remote_protocol"] = "https://"
    else:
        self.appconf["remote_protocol"] = "http://"
    self.appconf["remote_ip"] = remote_ip.get_text()
    self.appconf["remote_port"] = remote_port.get_text()
    self.appconf["remote_secret"] = remote_secret.get_text()
    self.appconf["remote_location"] = remote_location.get_text()

    if ((self.appconf["remote_protocol"] == "") or (self.appconf["remote_ip"] == "") or (self.appconf["remote_port"] == "") or (self.appconf["remote_location"] == "")):
        switch.set_sensitive(False)
    else:
        switch.set_sensitive(True)

    self.save_appconf()

    if (switch.get_active()):
        restart_varia_dialog(preferencesWindow)

def on_switch_remote(switch, state, self, preferencesWindow):
    if state:
        self.appconf["remote"] = "1"
    else:
        self.appconf["remote"] = "0"

    self.save_appconf()
    restart_varia_dialog(preferencesWindow)

def cookies_txt_import(self, do_import, cookies_txt_import_button, cookies_txt_remove_button, cookies_txt_action_switch):
    if do_import == True:
        file_filter = Gtk.FileFilter()
        file_filter.add_pattern("*.txt")
        dialog = Gtk.FileDialog(default_filter=file_filter)
        dialog.open(self, None, on_cookies_txt_import, cookies_txt_import_button, cookies_txt_remove_button, cookies_txt_action_switch, self)
    else:
        os.remove(os.path.join(self.appdir, 'cookies.txt'))
        cookies_txt_action_switch.set_active(False)
        cookies_txt_action_switch.set_sensitive(False)
        cookies_txt_import_button.set_visible(True)
        cookies_txt_remove_button.set_visible(False)
        self.appconf["cookies_txt"] = "0"
        self.save_appconf()

def on_cookies_txt_import(file_dialog, result, cookies_txt_import_button, cookies_txt_remove_button, cookies_txt_action_switch, self):
    try:
        file = file_dialog.open_finish(result).get_path()
    except:
        return
    if file.endswith(".txt"):
        with open(file, 'r') as file:
            data = file.read()
        with open(os.path.join(self.appdir, 'cookies.txt'), 'w') as cookies_txt_file:
            cookies_txt_file.write(data)
        cookies_txt_action_switch.set_sensitive(True)
        cookies_txt_import_button.set_visible(False)
        cookies_txt_remove_button.set_visible(True)

def on_switch_cookies_txt(switch, state, self):
    state = switch.get_active()
    if state:
        self.appconf["cookies_txt"] = "1"
    else:
        self.appconf["cookies_txt"] = "0"
    set_aria2c_cookies(self)
    self.save_appconf()

def torrent_settings_set_sensitive(self):
    if self.appconf["torrent_enabled"] == "1":
        for option in self.group_3_options:
            option.set_sensitive(True)

    else:
        for option in self.group_3_options:
            option.set_sensitive(False)

def on_switch_torrent(switch, state, self):
    state = switch.get_active()
    if state:
        self.appconf["torrent_enabled"] = "1"
        self.set_drop_target(True)

        self.torrent_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.torrent_button_box.append(Gtk.Image.new_from_icon_name("document-open-symbolic"))
        self.torrent_button_box.append(Gtk.Label(label=_("Torrent")))
        self.add_torrent_button.add_css_class("suggested-action")
        self.add_torrent_button.set_sensitive(True)

    else:
        self.appconf["torrent_enabled"] = "0"
        self.set_drop_target(False)

        self.torrent_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.torrent_button_box.append(Gtk.Label(label=_("Torrenting Disabled")))
        self.add_torrent_button.remove_css_class("suggested-action")
        self.add_torrent_button.set_sensitive(False)

    self.add_torrent_button.set_child(self.torrent_button_box)

    self.save_appconf()
    torrent_settings_set_sensitive(self)

def on_switch_torrent_seeding(switch, state, self):
    state = switch.get_active()
    if state:
        self.appconf["torrent_seeding_enabled"] = "1"
        set_aria2c_custom_global_option(self, "seed-time", "0")
        set_aria2c_custom_global_option(self, "bt-seed-unverified", "true")
        set_aria2c_custom_global_option(self, "bt-enable-lpd", "true")
        set_aria2c_custom_global_option(self, "enable-dht", "true")
        set_aria2c_custom_global_option(self, "enable-dht6", "true")

    else:
        def dialog_response_handle(dialog, response_id, self, dialog_checkbutton, switch):
            if response_id == "disable":
                if dialog_checkbutton.get_active() == True:
                    self.appconf["torrent_seeding_disable_warning_dont_show"] = "1"

                disable_torrent_seeding(self)

            elif response_id == "cancel":
                switch.set_active(True)

        def disable_torrent_seeding(self):
            self.appconf["torrent_seeding_enabled"] = "0"
            set_aria2c_custom_global_option(self, "seed-time", "")
            set_aria2c_custom_global_option(self, "bt-seed-unverified", "false")
            set_aria2c_custom_global_option(self, "bt-enable-lpd", "false")
            set_aria2c_custom_global_option(self, "enable-dht", "false")
            set_aria2c_custom_global_option(self, "enable-dht6", "false")
            self.save_appconf()

        if self.appconf["torrent_seeding_disable_warning_dont_show"] == "1":
            disable_torrent_seeding(self)

        else:
            dialog = Adw.AlertDialog()
            dialog.set_heading(_("Warning"))
            dialog.set_body(_("As torrenting relies on people seeding data, disabling seeding is very much frowned upon and may result in you getting throttled or banned by certain clients and trackers. Clients are usually expected to seed at least as much as they download (a ratio of 1). You may want to consider limiting your seeding ratio instead."))
            dialog_checkbutton = Gtk.CheckButton.new_with_label(_("Don't show again"))
            dialog_checkbutton.set_halign(Gtk.Align.CENTER)
            dialog.set_extra_child(dialog_checkbutton)
            dialog.add_response("disable",  _("Disable Seeding"))
            dialog.add_response("cancel",  _("Cancel"))
            dialog.set_default_response("cancel")
            dialog.set_close_response("cancel")
            dialog.set_response_appearance("disable", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.connect("response", dialog_response_handle, self, dialog_checkbutton, switch)
            dialog.present(self)

def on_torrent_seeding_ratio_limit_change(spinrow, self):
    self.appconf["torrent_seeding_ratio"][1] = str(floor(spinrow.get_value() * 10) / 10)
    self.save_appconf()

    if self.appconf["torrent_seeding_ratio"][0] == True:
        set_aria2c_custom_global_option(self, "seed-ratio", self.appconf["torrent_seeding_ratio"][1])

def on_switch_torrent_seeding_ratio_limit(switch, state, self):
    state = switch.get_active()
    if state:
        self.appconf["torrent_seeding_ratio"][0] = True
        set_aria2c_custom_global_option(self, "seed-ratio", self.appconf["torrent_seeding_ratio"][1])

    else:
        self.appconf["torrent_seeding_ratio"][0] = False
        set_aria2c_custom_global_option(self, "seed-ratio", "0")

    self.save_appconf()

def on_switch_custom_torrent_download_directory(switch, state, self):
    state = switch.get_active()
    if state:
        self.appconf["torrent_download_directory_custom_enabled"] = "1"

    else:
        self.appconf["torrent_download_directory_custom_enabled"] = "0"

    self.save_appconf()

def restart_varia_dialog(preferencesWindow):
    dialog = Adw.AlertDialog()
    dialog.set_body(_("Please restart Varia to apply the change."))
    dialog.add_response("ok",  _("OK"))
    dialog.set_default_response("ok")
    dialog.set_close_response("ok")
    dialog.present(preferencesWindow)
