import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio
from gettext import gettext as _

from download.communicate import set_speed_limit, set_aria2c_download_directory, set_aria2c_download_simultaneous_amount

def show_preferences(button, self, app):
    preferences = Adw.PreferencesDialog()

    page = Adw.PreferencesPage(title=_("Preferences"))
    preferences.add(page)
    group_extensions = Adw.PreferencesGroup()
    page.add(group_extensions)
    group_1 = Adw.PreferencesGroup()
    page.add(group_1)
    group_2 = Adw.PreferencesGroup()
    page.add(group_2)

    # Browser extensions section:

    browser_extension_actionrow = Adw.ActionRow()
    browser_extension_actionrow.set_title(_("Browser Extension"))

    browser_extension_firefox_button = Gtk.Button(label="Firefox")
    browser_extension_firefox_button.set_halign(Gtk.Align.START)
    browser_extension_firefox_button.set_valign(Gtk.Align.CENTER)
    browser_extension_chrome_button = Gtk.Button(label="Chrome")
    browser_extension_chrome_button.set_halign(Gtk.Align.START)
    browser_extension_chrome_button.set_valign(Gtk.Align.CENTER)

    browser_extension_firefox_button.connect("clicked", lambda clicked: on_extension_selected(self, preferences, 'firefox'))
    browser_extension_chrome_button.connect("clicked", lambda clicked: on_extension_selected(self, preferences, 'chrome'))

    browser_extension_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
    browser_extension_buttons_box.append(browser_extension_firefox_button)
    browser_extension_buttons_box.append(browser_extension_chrome_button)

    browser_extension_actionrow.add_suffix(browser_extension_buttons_box)

    group_extensions.add(browser_extension_actionrow)

    # Basic settings:

    download_directory_actionrow = Adw.ActionRow()
    download_directory_actionrow.set_title(_("Download Directory"))
    if (self.appconf["remote"] == "0"):
        download_directory_actionrow.set_subtitle(self.appconf["download_directory"])

    download_directory_change_button = Gtk.Button(label=_("Change"))
    download_directory_change_button.get_style_context().add_class("suggested-action")
    download_directory_change_button.set_halign(Gtk.Align.START)
    download_directory_change_button.set_valign(Gtk.Align.CENTER)
    download_directory_change_button.connect("clicked", lambda clicked: on_download_directory_change(self, preferences, download_directory_actionrow))

    download_directory_change_remote_label = Gtk.Label(label=_("Remote Mode"))
    download_directory_change_remote_label.set_halign(Gtk.Align.START)
    download_directory_change_remote_label.set_valign(Gtk.Align.CENTER)

    if (self.appconf["remote"] == "0"):
        download_directory_actionrow.add_suffix(download_directory_change_button)
    else:
        download_directory_actionrow.add_suffix(download_directory_change_remote_label)

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

    if (self.appconf["download_speed_limit"] != "0"):
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
        auth_expander_switch.set_active("active")

    auth_expander.add_action(auth_expander_switch)

    auth_expander.add_row(username_entry)
    auth_expander.add_row(password_entry)

    simultaneous_download_amount_unit_names = Gio.ListStore.new(Gtk.StringObject)
    simultaneous_download_amount_unit_names.append(Gtk.StringObject.new(" 1"))
    simultaneous_download_amount_unit_names.append(Gtk.StringObject.new(" 2"))
    simultaneous_download_amount_unit_names.append(Gtk.StringObject.new(" 3"))
    simultaneous_download_amount_unit_names.append(Gtk.StringObject.new(" 4"))
    simultaneous_download_amount_unit_names.append(Gtk.StringObject.new(" 5"))
    simultaneous_download_amount_unit_names.append(Gtk.StringObject.new(" 6"))
    simultaneous_download_amount_unit_names.append(Gtk.StringObject.new(" 7"))
    simultaneous_download_amount_unit_names.append(Gtk.StringObject.new(" 8"))
    simultaneous_download_amount_unit_names.append(Gtk.StringObject.new(" 9"))
    simultaneous_download_amount_unit_names.append(Gtk.StringObject.new(" 10"))

    simultaneous_download_amount_unit_names_box = Adw.ComboRow()
    simultaneous_download_amount_unit_names_box.set_model(simultaneous_download_amount_unit_names)
    simultaneous_download_amount_unit_names_box.set_title(_("Simultaneous Download Amount"))
    simultaneous_download_amount_unit_names_box.set_selected(int(self.appconf["download_simultaneous_amount"])- 1)
    simultaneous_download_amount_unit_names_box.connect("notify::selected", on_simultaneous_download_amount_changed, self)

    group_1.add(download_directory_actionrow)
    group_1.add(speed_limit_expander_box)
    group_1.add(auth_expander)
    group_1.add(simultaneous_download_amount_unit_names_box)

    # Advanced settings:

    remote_aria2_expander_box = Adw.ExpanderRow()
    remote_aria2_expander_box.set_title(_("Remote Mode"))

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

    group_2.add(remote_aria2_expander_box)

    preferences.present(self)

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

def on_download_directory_change(self, prefswindow, actionrow):
    Gtk.FileDialog().select_folder(None, None, on_download_directory_selected, self, prefswindow, actionrow)

def on_download_directory_selected(dialog, result, self, prefswindow, actionrow):
    try:
        folder = dialog.select_folder_finish(result)
        self.appconf["download_directory"] = folder.get_path()
        self.save_appconf()
        set_aria2c_download_directory(self)
        actionrow.set_subtitle(self.appconf["download_directory"])
    except:
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

    if (speed != "0"):
        speed_type = speed_type.get_selected()
        print(speed_type)
        match speed_type:
            case 0:
                download_limit = speed + "K"
            case 1:
                download_limit = speed + "M"
            case 2:
                download_limit = speed + "G"
    else:
        download_limit = speed

    set_speed_limit(self, download_limit)
    self.appconf['download_speed_limit'] = download_limit

    if ((self.appconf["download_speed_limit"] == "0K") or (self.appconf["download_speed_limit"] == "0M") or (self.appconf["download_speed_limit"] == "0G")):
        switch.set_active(False)
        switch.set_sensitive(False)
    else:
        switch.set_sensitive(True)

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

def on_simultaneous_download_amount_changed(comborow, parameters, self):
    self.appconf["download_simultaneous_amount"] = str(comborow.get_selected() + 1)
    print(str(comborow.get_selected() + 1))
    self.save_appconf()

    set_aria2c_download_simultaneous_amount(self)

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

def restart_varia_dialog(preferencesWindow):
    dialog = Adw.AlertDialog()
    dialog.set_body(_("Please restart Varia to apply the change."))
    dialog.add_response("ok",  _("OK"))
    dialog.set_default_response("ok")
    dialog.set_close_response("ok")
    dialog.present(preferencesWindow)
