import aria2p
import requests
import json
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio
from download.actionrow import create_actionrow
from download.thread import DownloadThread
import threading
import string
import random
import textwrap

def listen_to_aria2(self, variaapp):
    if not (self.terminating) and not (self.shutdown_dialog_raised):
        currently_downloading = False

        for frontend_download_item in self.downloads.copy():
            if frontend_download_item.download:
                if (frontend_download_item.is_alive()):
                    currently_downloading = True
                if ( ((frontend_download_item.download.is_metadata) or (frontend_download_item.download.name.endswith(".torrent"))) and (frontend_download_item.download.is_complete) ):
                    frontend_download_item.cancelled = True
                    frontend_download_item.stop(True)
                    self.download_list.remove(frontend_download_item.actionrow)
                    self.downloads.remove(frontend_download_item)

        try:
            downloads_in_frontend = set(download_item.download.gid for download_item in self.downloads.copy())
            for download_item_to_be_added in self.api.get_downloads():
                if ((download_item_to_be_added.gid not in downloads_in_frontend) and (download_item_to_be_added.is_metadata == False) and (download_item_to_be_added.is_complete == False)):
                    if not download_item_to_be_added.is_torrent:
                        print('Download added directly to aria2c, adding it to the UI: ' + download_item_to_be_added.files[0].uris[0]["uri"])
                    add_download_to_ui(self, download_item_to_be_added)
        except:
            pass

        if currently_downloading == True:
            self.shutdown_action.set_enabled(True)
            self.exit_action.set_enabled(True)
        else:
            self.shutdown_action.set_enabled(False)
            self.exit_action.set_enabled(False)
            if (self.shutdown_dialog_raised == False) and (self.shutdown_mode == True):
                self.shutdown_dialog_raised = True
                raise_shutdown_dialog(self, variaapp)

            if (self.exit_mode == True) and (self.exit_dialog_raised == False):
                self.exit_dialog_raised = True
                raise_exit_dialog(self, variaapp)


        GLib.timeout_add(2000, listen_to_aria2, self, variaapp)

def add_download_to_ui(self, download_item_to_be_added):
    if download_item_to_be_added.is_torrent:
        download_item_url = "magnet:?xt=urn:btih:" + download_item_to_be_added.info_hash
    else:
        download_item_url = download_item_to_be_added.files[0].uris[0]["uri"].split("?")[0]

    objectlist = create_actionrow(self, download_item_url)
    download_thread = DownloadThread(self, download_item_url, *objectlist, download_item_to_be_added, None)
    self.downloads.append(download_thread)
    download_thread.start()
    download_thread.pause_button.show()

def raise_shutdown_dialog(variamain, variaapp):
    while (True):
        shutdown_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        if (shutdown_id != variamain.shutdown_id):
            variamain.shutdown_id = shutdown_id
            break

    notification = Gio.Notification.new(_("Warning"))
    notification.set_body(_("Varia is about to shut down your computer."))
    variaapp.send_notification(None, notification)

    dialog = Adw.AlertDialog()
    dialog.set_body(textwrap.fill(_("Varia is about to shut down your computer.") + " " + _("Press Cancel to cancel and disable."), 50))
    dialog.add_response("cancel",  _("Cancel"))
    dialog.set_default_response("cancel")
    dialog.set_close_response("cancel")
    dialog.connect("response", shutdown_dialog_cancel_pressed, variamain, variaapp)
    dialog.present(variamain)

    GLib.timeout_add(30000, initiate_shutdown, variamain, shutdown_id)

def shutdown_dialog_cancel_pressed(dialog, response_id, variamain, variaapp):
    variamain.shutdown_dialog_raised = False
    variamain.shutdown_mode = False
    variamain.sidebar_remote_mode_label.set_text("")
    GLib.timeout_add(2000, listen_to_aria2, variamain, variaapp)

def initiate_shutdown(variamain, shutdown_id):
    if (variamain.shutdown_dialog_raised == True) and (shutdown_id == variamain.shutdown_id):
        bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        proxy = Gio.DBusProxy.new_sync(bus, Gio.DBusProxyFlags.NONE, None,
                                       'org.freedesktop.login1', '/org/freedesktop/login1',
                                       'org.freedesktop.login1.Manager', None)
        proxy.call_sync('PowerOff', GLib.Variant('(b)', (True,)), Gio.DBusCallFlags.NONE, -1, None)
        exit()

def raise_exit_dialog(variamain, variaapp):
    notification = Gio.Notification.new(_("Warning"))
    notification.set_body(_("Varia is about to quit."))
    variaapp.send_notification(None, notification)

    dialog = Adw.AlertDialog()
    dialog.set_body(textwrap.fill(_("Varia is about to quit.") + " " + _("Press Cancel to cancel and disable."), 50))
    dialog.add_response("cancel", _("Cancel"))
    dialog.set_default_response("cancel")
    dialog.set_close_response("cancel")
    dialog.connect("response", exit_dialog_cancel, variamain, variaapp)
    dialog.present(variamain)

    GLib.timeout_add(10000, initiate_app_exit, variamain, variaapp)

def exit_dialog_cancel(dialog, response_id, variamain, variaapp):
    variamain.exit_dialog_raised = False
    variamain.exit_mode = False
    variamain.sidebar_remote_mode_label.set_text("")
    GLib.timeout_add(2000, listen_to_aria2, variamain, variaapp)

def initiate_app_exit(variamain, variaapp):
    if (variamain.exit_dialog_raised == True):
        variamain.exitProgram(variamain, variaapp, background=False)
