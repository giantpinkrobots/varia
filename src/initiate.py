import aria2p
import os
import json
import gi
import requests
import sys
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
from gettext import gettext as _

def initiate(self):
    self.downloaddir = self.appconf["download_directory"]

    self.applied_filter = "show_all"

    remote_successful = False

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
                remote_successful = True
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
        if (remote_successful == False):
            self.appconf["remote"] = "0"
            self.save_appconf()
            dialog = Adw.MessageDialog()
            dialog.set_body(_("Couldn't connect to remote aria2c instance. Disabling remote mode. Please restart Varia."))
            dialog.add_response("ok",  _("OK"))
            dialog.set_default_response("ok")
            dialog.set_close_response("ok")
            dialog.connect("response", on_dialog_dismiss)
            dialog.show()
            return -1
    else:
        self.api = aria2p.API(
            aria2p.Client(
                host="http://localhost",
                port=6801
            )
        )

        self.aria2cLocation = "http://localhost:6801"

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

def on_dialog_dismiss(dialog, response_id):
    dialog.destroy()
