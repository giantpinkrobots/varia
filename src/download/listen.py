import time
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, GLib, Gio
from download.actionrow import create_actionrow
from download.thread import DownloadThread
import string
import random
import textwrap
import os
from stringstorage import gettext as _

def listen_to_aria2(self, variaapp):
    if not (self.terminating) and not (self.shutdown_dialog_raised):
        currently_downloading = False

        for frontend_download_item in self.downloads:
            if hasattr(frontend_download_item, "download"):
                if frontend_download_item.download and frontend_download_item.mode == "regular":
                    if (frontend_download_item.is_alive()):
                        currently_downloading = True
                    
                    # Handle .torrent files:
                    if self.appconf["torrent_enabled"] == "1" and (frontend_download_item.download.is_metadata or frontend_download_item.download.name.endswith(".torrent")) and frontend_download_item.download.is_complete:

                        if frontend_download_item.download.is_metadata == False: # Is .torrent file and not metadata
                            torrent_file_path = os.path.join(frontend_download_item.downloaddir, frontend_download_item.downloadname)
                            
                            # Download torrent file to the set torrent download directory if that's enabled:
                            if self.appconf["torrent_download_directory_custom_enabled"] == "1":
                                self.api.add_torrent(torrent_file_path, options={"dir": self.appconf["torrent_download_directory"]})

                            else:
                                self.api.add_torrent(torrent_file_path)
                        
                        # Remove the .torrent file download itself:
                        frontend_download_item.cancelled = True
                        frontend_download_item.stop(True)
                        self.download_list.remove(frontend_download_item.actionrow)
                        self.downloads.remove(frontend_download_item)

        downloads_in_frontend_files = []
        downloads_in_frontend_gids = []

        for download_item in self.downloads:
            try:
                downloads_in_frontend_gids.append(download_item.download.gid)
            except:
                GLib.timeout_add(2000, listen_to_aria2, self, variaapp)
                return
            try:
                if (download_item.download.status == "active" or download_item.download.status == "waiting" or download_item.download.status == "paused"):
                    for download_file in download_item.files:
                        downloads_in_frontend_files.append(download_file)
            except:
                pass

        downloads_in_frontend_files = set(downloads_in_frontend_files)

        for download_item_to_be_added in self.api.get_downloads():
            new_download_files = download_item_to_be_added.files

            if ( (download_item_to_be_added.gid not in downloads_in_frontend_gids) # If the download wasn't already added
                    and (download_item_to_be_added.is_metadata == False) # If the download isn't just metadata
                    and (download_item_to_be_added.is_complete == False) # If the download is not complete
                    and ((any(item in new_download_files for item in downloads_in_frontend_files)) == False) ): # Make sure it's not a duplicate
                if not download_item_to_be_added.is_torrent:
                    print('Download added directly to aria2c, adding it to the UI: ' + download_item_to_be_added.files[0].uris[0]["uri"])
                add_download_to_ui(self, download_item_to_be_added, variaapp)

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

def deal_with_simultaneous_download_limit(self):
    while self.terminating == False:
        downloads_to_be_processed = []
        
        for download in self.downloads:
            try:
                if download and download.pause_button.get_child().get_icon_name() == "media-playback-pause-symbolic":
                    downloads_to_be_processed.append(download)

            except:
                pass

        i = int(self.appconf["download_simultaneous_amount"])
        while i < len(downloads_to_be_processed):
            if downloads_to_be_processed[i].return_is_paused() == False and \
                downloads_to_be_processed[i].paused_because_exceeds_limit == False:

                downloads_to_be_processed[i].pause()
                GLib.idle_add(downloads_to_be_processed[i].show_message, _("Simultaneous download limit exceeded, waiting."))
                downloads_to_be_processed[i].paused_because_exceeds_limit = True

            i += 1
        
        i = 0
        limit = int(self.appconf["download_simultaneous_amount"])
        if limit > len(downloads_to_be_processed):
            limit = len(downloads_to_be_processed)

        while i < limit:
            if downloads_to_be_processed[i].return_is_paused() == True and \
                downloads_to_be_processed[i].paused_because_exceeds_limit == True:

                downloads_to_be_processed[i].resume()
                downloads_to_be_processed[i].paused_because_exceeds_limit = False
            
            i += 1
        
        time.sleep(0.5)

def add_download_to_ui(self, download_item_to_be_added, variaapp):
    if download_item_to_be_added.is_torrent:
        download_item_url = "magnet:?xt=urn:btih:" + download_item_to_be_added.info_hash
    else:
        download_item_url = download_item_to_be_added.files[0].uris[0]["uri"].split("?")[0]

    notification = Gio.Notification.new(download_item_to_be_added.name)
    variaapp.send_notification(None, notification)

    actionrow = create_actionrow(self, download_item_url)
    download_thread = DownloadThread(self, download_item_url, actionrow, download_item_url, download_item_to_be_added, "regular", None, False, self.appconf["download_directory"])
    actionrow.download_thread = download_thread
    self.downloads.append(download_thread)
    download_thread.start()
    download_thread.pause_button.set_visible(True)

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
        if os.name == 'nt':
            os.system('shutdown -s -t 0')
        else:
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
