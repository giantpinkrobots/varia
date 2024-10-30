import aria2p
import os
import json
import gi
import requests
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from gettext import gettext as _

def initiate(self, variaapp, variaVersion, first_run):
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
    self.set_default_size(800, 600)
    self.set_size_request(650, 450)

    self.total_download_speed = ""
    self.terminating = False

    if ("dev" in variaVersion):
        self.get_style_context().add_class("devel")
        Gtk.Settings.get_default().set_property("gtk-icon-theme-name", "Adwaita")

    self.overlay_split_view = Adw.OverlaySplitView.new()
    self.set_content(self.overlay_split_view)

    self.downloads = []
    self.all_paused = False

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
