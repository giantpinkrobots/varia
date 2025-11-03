import aria2p
import os
import json
import gi
import requests
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, Gdk
from stringstorage import gettext as _

def initiate(self, variaapp, variaVersion, first_run, issnap):
    self.downloaddir = self.appconf["download_directory"]

    self.applied_filter = "show_all"

    if (self.appconf['remote'] == '1'):
        self.aria2cLocation = self.appconf['remote_protocol'] + self.appconf['remote_ip'] + ':' + self.appconf['remote_port']
        token = "token:" + self.appconf['remote_secret']
        json_request = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "aria2.tellActive",
            "params":[token]
        }
        try:
            response = requests.post(self.aria2cLocation + '/jsonrpc', headers={'Content-Type': 'application/json'}, data=json.dumps(json_request))
            print(response)
            if (response.status_code == 200):
                self.remote_successful = True
                self.api = aria2p.API(
                    aria2p.Client(
                        host=self.appconf['remote_protocol'] + self.appconf['remote_ip'],
                        port=self.appconf['remote_port'],
                        secret=self.appconf['remote_secret']
                    )
                )
        except:
            pass

    if (self.appconf['remote'] == '1'):
        if (self.remote_successful == False):
            self.appconf["remote"] = "0"
            self.save_appconf()
            dialog = Adw.AlertDialog()
            dialog.set_body(_("Couldn't connect to remote aria2c instance. Disabling remote mode. Please restart Varia."))
            dialog.add_response("ok",  _("OK"))
            dialog.set_default_response("ok")
            dialog.set_close_response("ok")
            dialog.connect("response", on_dialog_dismiss, self)
            dialog.present()
            return -1
    else:
        self.api = aria2p.API(
            aria2p.Client(
                host="http://localhost",
                port=6801
            )
        )

        self.aria2cLocation = "http://localhost:6801"

    self.set_title("Varia")
    self.set_default_size(self.appconf["window_size"][0], self.appconf["window_size"][1])
    self.set_size_request(400, 360)

    self.total_download_speed = ""
    self.terminating = False
    
    Gtk.Settings.get_default().set_property("gtk-icon-theme-name", "Adwaita")

    if ("dev" in variaVersion):
        self.add_css_class("devel")

    # DragDrop area that covers the entire window for torrent files
    self.drop_target = Gtk.DropTarget.new(Gio.File, Gdk.DragAction.COPY)
    self.add_controller(self.drop_target)

    def set_drop_target(enable):
        if enable:
            self.drag_drop_enter_handler_id = self.drop_target.connect("enter", self.on_drag_enter)
            self.drag_drop_leave_handler_id = self.drop_target.connect("leave", self.on_drag_leave, 250)
            self.drag_drop_drop_handler_id = self.drop_target.connect("drop", self.on_file_drop)

        else:
            self.drop_target.disconnect(self.drag_drop_enter_handler_id)
            self.drop_target.disconnect(self.drag_drop_leave_handler_id)
            self.drop_target.disconnect(self.drag_drop_drop_handler_id)

    self.set_drop_target = set_drop_target

    self.set_drop_target(True)

    self.root_window_overlay = Gtk.Overlay()
    self.overlay_split_view = Adw.OverlaySplitView.new()
    self.root_window_overlay.set_child(self.overlay_split_view)

    if os.name == 'nt': # Gtk.Window (used on Windows) doesn't have set_content
        self.set_child(self.root_window_overlay)

    else:
        self.set_content(self.root_window_overlay)

    self.drag_drop_status_page = Adw.StatusPage()
    self.drag_drop_status_page.set_icon_name("document-send-symbolic")
    self.drag_drop_status_page.set_title(_("Torrent"))
    self.drag_drop_status_page.add_css_class("drag_drop_status_page")
    self.drag_drop_revealer = Gtk.Revealer()
    self.drag_drop_revealer.set_transition_type(Gtk.RevealerTransitionType.CROSSFADE)
    self.drag_drop_revealer.set_child(self.drag_drop_status_page)

    drag_drop_status_page_class_css = """
        .drag_drop_status_page {
            background-color: color-mix(in srgb, var(--accent-bg-color) 90%, transparent);
        }

        .drag_drop_status_page_success {
            background-color: color-mix(in srgb, var(--success-color) 90%, transparent);
        }

        .drag_drop_status_page_error {
            background-color: color-mix(in srgb, var(--error-color) 90%, transparent);
        } """

    drag_drop_status_page_class_css_provider = Gtk.CssProvider()
    drag_drop_status_page_class_css_provider.load_from_data(drag_drop_status_page_class_css)

    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(),
        drag_drop_status_page_class_css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    self.downloads = []

    self.shutdown_mode = False
    self.shutdown_dialog_raised = False
    self.shutdown_id = ""

    self.exit_mode = False
    self.exit_dialog_raised = False

    if (os.name == 'nt') and (first_run == True) and (os.path.exists("./updater-function-enabled")):
        dialog = Adw.AlertDialog()
        dialog.set_body(_("Do you want to check for updates on startup?"))
        dialog.add_response("yes",  _("Yes"))
        dialog.add_response("no",  _("No"))
        dialog.set_response_appearance("yes", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", set_auto_updates, self, variaapp, variaVersion)
        dialog.set_close_response("no")
        dialog.present(self)

    elif issnap and first_run:
        dialog_commands_label = Gtk.Label()
        dialog_commands_label.set_wrap(True)
        dialog_commands_label.set_selectable(True)
        dialog_commands_label.set_markup("<b>$</b> sudo snap connect varia:dbus-varia-tray"
                                    + "\n<b>$</b> sudo snap connect varia:dbusmenu"
                                    + "\n<b>$</b> sudo snap connect varia:shutdown")

        dialog = Adw.AlertDialog()
        dialog.set_body(_("You are using Varia as a Snap package. There are some functions that you can't use without manually giving Varia some extra permissions. These are:")
                        + "\n\n - " + _("Background Mode")
                        + "\n - " + _("Shutdown on Completion")
                        + "\n\n" + _("To enable these functions you must run these commands in a terminal to give the required permissions and then restart Varia:"))
        dialog.set_extra_child(dialog_commands_label)
        dialog.add_response("ok",  _("OK"))
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_close_response("ok")
        dialog.present(self)

def set_auto_updates(dialog, response_id, self, variaapp, variaVersion):
    if response_id == "yes":
        self.appconf["check_for_updates_on_startup_enabled"] = "1"
    else:
        self.appconf["check_for_updates_on_startup_enabled"] = "0"
    
    self.save_appconf()
    
    from window.updater import windows_updater
    windows_updater(None, self, variaapp, None, variaVersion, 0)

def on_dialog_dismiss(dialog, response_id, self):
    dialog.force_close()
    self.destroy()
