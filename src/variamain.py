variaVersion = "dev" # Also update actions-inno-install-script.iss

import ctypes
import gi
import sys
import json
import os
import threading
import subprocess
from operator import itemgetter
import re
import stringstorage
import atexit
import signal
import traceback

from download.actionrow import on_download_clicked
from download.listen import deal_with_simultaneous_download_limit, listen_to_aria2
from download.actionrow import create_actionrow
from download.thread import DownloadThread
from download.communicate import set_speed_limit, set_aria2c_download_directory, set_aria2c_custom_global_option, set_aria2c_cookies
from download.scheduler import schedule_downloads
from download.manage_downloads import pause_all, stop_all, check_all_status, total_download_speed_get

from window.sidebar import window_create_sidebar
from window.content import window_create_content
from window.updater import windows_updater
from window.drag_and_drop import on_drag_enter, on_drag_leave, on_file_drop
from window.window_management import on_window_resize, apply_window_resize, save_window_size

from tray.start_tray_process import start_tray_process

from initiate import initiate

global start_varia_server
global send_to_varia_instance
from server import start_varia_server, send_to_varia_instance

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk

if os.name == 'nt':
    application_window = Gtk.ApplicationWindow

else:
    application_window = Adw.ApplicationWindow
    stringstorage.setstrings_linux()
    from stringstorage import gettext as _

class MainWindow(application_window):
    window_create_sidebar = window_create_sidebar
    window_create_content = window_create_content
    windows_updater = windows_updater
    on_drag_enter = on_drag_enter
    on_drag_leave = on_drag_leave
    on_file_drop = on_file_drop
    on_window_resize = on_window_resize
    apply_window_resize = apply_window_resize
    save_window_size = save_window_size

    set_speed_limit = set_speed_limit
    set_aria2c_download_directory = set_aria2c_download_directory
    set_aria2c_custom_global_option = set_aria2c_custom_global_option
    set_aria2c_cookies = set_aria2c_cookies
    listen_to_aria2 = listen_to_aria2
    schedule_downloads = schedule_downloads
    pause_all = pause_all
    stop_all = stop_all
    check_all_status = check_all_status
    total_download_speed_get = total_download_speed_get

    start_tray_process = start_tray_process

    initiate = initiate

    global tray_process_global

    def __init__(self, variaapp, appdir, appconf, first_run, aria2c_subprocess, aria2cexec, ffmpegexec, sevenzexec, denoexec, issnap, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.scheduler_currently_downloading = False
        self.appdir = appdir
        self.appconf = appconf
        self.aria2c_subprocess = aria2c_subprocess
        self.bindir = aria2cexec[:-6]
        self.aria2cexec = aria2cexec
        self.remote_successful = False
        self.update_executable = None
        self.ffmpegexec = ffmpegexec
        self.tray_connection_thread_stop = False
        self.tray_process = None
        self.ip_geolocation_cache = {}
        self.preferences_shown = False
        self.issnap = issnap
        self.sevenzexec = sevenzexec
        self.denoexec = denoexec

        # For 7-zip integration:
        self.supported_archive_formats = ["7z", "xz", "bzip2", "gzip", "tar", "zip", "wim", "apfs", "ar", "arj", "cab", "chm", "cpio", "cramfs", "dmg", "ext", "fat", "gpt", "hfs", "ihex", "iso", "lzh", "lzma", "mbr", "msi", "nsis", "ntfs", "qcow2", "rar", "rpm", "squashfs", "udf", "uefi", "vdi", "vhd", "vhdx", "vmdk", "xar", "z"]

        # Set up variables and all:
        aria2_connection_successful = initiate(self, variaapp, variaVersion, first_run, issnap)

        if aria2_connection_successful == -1:
            return

        # Create window contents:
        window_create_sidebar(self, variaapp, variaVersion)
        window_create_content(self)

        if self.appconf["schedule_enabled"] == 1:
            try:
                self.sidebar_content_box.remove(self.sidebar_scheduler_label)
            except:
                pass
            self.sidebar_content_box.append(self.sidebar_scheduler_label)

        # Check if the download path still exists:
        if not (os.path.exists(self.appconf["download_directory"])):
            if GLib.get_user_special_dir(GLib.DIRECTORY_DOWNLOAD) and os.path.exists(GLib.get_user_special_dir(GLib.DIRECTORY_DOWNLOAD)):
                self.appconf["download_directory"] = GLib.get_user_special_dir(GLib.DIRECTORY_DOWNLOAD)
            elif GLib.get_user_special_dir(GLib.DIRECTORY_HOME):
                self.appconf["download_directory"] = GLib.get_user_special_dir(GLib.DIRECTORY_HOME)
            else:
                self.appconf["download_directory"] = os.path.expanduser("~")
            self.save_appconf()

        # Check if the custom torrent download path still exists:
        if not (os.path.exists(self.appconf["torrent_download_directory"])):
            if GLib.get_user_special_dir(GLib.DIRECTORY_DOWNLOAD) and os.path.exists(GLib.get_user_special_dir(GLib.DIRECTORY_DOWNLOAD)):
                self.appconf["torrent_download_directory"] = GLib.get_user_special_dir(GLib.DIRECTORY_DOWNLOAD)
            elif GLib.get_user_special_dir(GLib.DIRECTORY_HOME):
                self.appconf["torrent_download_directory"] = GLib.get_user_special_dir(GLib.DIRECTORY_HOME)
            else:
                self.appconf["torrent_download_directory"] = os.path.expanduser("~")
            self.save_appconf()

        # Set download speed limit from appconf:
        if ((self.appconf["download_speed_limit_enabled"] == "1") and (self.appconf["download_speed_limit"][:-1] != "0")):
            set_speed_limit(self, self.appconf["download_speed_limit"])

        # Set download speed limit from appconf:
        if ((self.appconf["download_speed_limit_enabled"] == "1") and (self.appconf["download_speed_limit"][:-1] != "0")):
            set_speed_limit(self, self.appconf["download_speed_limit"])

        # Set download directory from appconf:
        set_aria2c_download_directory(self)

        # Set seeding setting:
        if self.appconf["torrent_seeding_enabled"] == "0":
            set_aria2c_custom_global_option(self, "seed-time", "")
            set_aria2c_custom_global_option(self, "bt-seed-unverified", "false")
            set_aria2c_custom_global_option(self, "bt-enable-lpd", "false")
            set_aria2c_custom_global_option(self, "enable-dht", "false")
            set_aria2c_custom_global_option(self, "enable-dht6", "false")

        # Set seeding ratio limit:
        if self.appconf["torrent_seeding_ratio"][0] == True:
            set_aria2c_custom_global_option(self, "seed-ratio", self.appconf["torrent_seeding_ratio"][1])

        # Don't save .torrent files:
        set_aria2c_custom_global_option(self, "bt-save-metadata", "false")
        set_aria2c_custom_global_option(self, "rpc-save-upload-metadata", "false")

        # Set the maximum simultaneous download amount from appconf:
        #set_aria2c_download_simultaneous_amount(self)
        set_aria2c_custom_global_option(self, "max-concurrent-downloads", str(self.appconf["download_simultaneous_amount"]))

        # Set the download segments:
        set_aria2c_custom_global_option(self, "split", str(self.appconf["download_segments"]))

        # Start checking for simultaneous download amount limit:
        thread = threading.Thread(target=lambda: deal_with_simultaneous_download_limit(self), daemon=True)
        thread.start()

        # Set the remote time setting:
        if self.appconf["remote_time"] == "1":
            set_aria2c_custom_global_option(self, "remote-time", "true")
        else:
            set_aria2c_custom_global_option(self, "remote-time", "false")

        # Set cookies.txt:
        set_aria2c_cookies(self)

        # Set bt require encryption:
        set_aria2c_custom_global_option(self, "bt-force-encryption", self.appconf["torrent_require_encryption"])

        # Listen to aria2c:
        thread = threading.Thread(target=lambda: listen_to_aria2(self, variaapp), daemon=True)
        thread.start()

        # Begin the scheduler:
        thread = threading.Thread(target=lambda: schedule_downloads(self, True), daemon=True)
        thread.start()

        icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
        icon_theme.add_search_path("./icons")

        # Use server side decorations on Windows because tiling doesn't work well otherwise:
        if (os.name == 'nt'):
            os.environ['GTK_CSD'] = '0'
        
        # Updater for Windows and Mac:
        if (os.name == 'nt' or os.uname().sysname == 'Darwin') and self.appconf["check_for_updates_on_startup_enabled"] == '1' and os.path.exists("./updater-function-enabled"):
            windows_updater(None, self, variaapp, None, variaVersion, 0)

        # Load incomplete downloads:
        default_state = {"url": None, "filename": None, "type": "regular", "video_options": {}, "paused": False, "index": 0, "dir": self.appconf["download_directory"], "percentage": 0}
        download_dicts = []

        for filename in os.listdir(self.appconf["download_directory"]):
            if (os.path.isdir(filename) == False) and ( (filename.endswith('.varia.json')) or (filename.endswith('.varia')) ):
                if (filename.endswith(".varia.json")):
                    current_filename = filename.replace(".json", "")
                    os.rename(os.path.join(self.appconf["download_directory"], filename), os.path.join(self.appconf["download_directory"], current_filename))
                else:
                    current_filename = filename

                with open(os.path.join(self.appconf["download_directory"], current_filename), 'r') as f:
                    loaded_state = json.load(f)
                    state = {**default_state, **loaded_state}

                    # Skip videos if in remote mode:
                    if self.remote_successful == True and state["video_options"] != {}:
                        continue

                    download_dicts.append(state)

                print(current_filename)
                os.remove(os.path.join(self.appconf["download_directory"], current_filename))

        download_dicts = sorted(download_dicts, key=itemgetter("index"))

        for download in download_dicts:
            on_download_clicked(None, self, download["url"], download["filename"], None, download["type"], download["video_options"], download["paused"], download["dir"], download["percentage"])

        self.check_all_status() # Set Pause All / Resume All button

        self.connect('close-request', self.exit_or_tray, variaapp)
        self.connect("notify::default-width", self.on_window_resize)
        self.connect("notify::maximized", self.on_window_resize)
        GLib.timeout_add(100, self.on_window_resize, None, None)

        self.tray_notification = False

        self.present()

        # Run on_window_resize when the window is presented:
        def on_window_map(self):
            GLib.idle_add(self.on_window_resize, None, None)

        self.connect("map", on_window_map)

        # Start in background mode if it was enabled in preferences:
        if (self.appconf["default_mode"] == "background"):
            self.suppress_startup_notification = True
            self.exitProgram(app=self, variaapp=variaapp, background=True)
        else:
            self.suppress_startup_notification = False

        if self.appconf["tray_always_visible"] == "true":
            self.start_tray_process(variaapp)

    def filter_download_list(self, button, filter_mode):
        if (button != "no"):
            self.filter_button_show_all.set_active(False)
            self.filter_button_show_downloading.set_active(False)
            self.filter_button_show_completed.set_active(False)
            self.filter_button_show_seeding.set_active(False)
            self.filter_button_show_failed.set_active(False)

            if self.overlay_split_view.get_show_sidebar() and \
                self.overlay_split_view.get_collapsed():

                self.overlay_split_view.set_show_sidebar(False)

        else:
            filter_mode = self.applied_filter

        if (filter_mode == "show_all"):
            self.applied_filter = "show_all"
            for download_thread in self.downloads:
                download_thread.actionrow.set_visible(True)
            self.filter_button_show_all.set_active(True)

        else:
            for download_thread in self.downloads:
                download_thread.actionrow.set_visible(False)

            if (filter_mode == "show_downloading"):
                self.applied_filter = "show_downloading"
                for download_thread in self.downloads:
                    if (download_thread.download):
                        if download_thread.mode == "regular":
                            if (((download_thread.download.status == "waiting") or (download_thread.download.status == "active")) and (download_thread.download.seeder != True)):
                                download_thread.actionrow.set_visible(download_thread.actionrow.is_visible)
                        elif download_thread.mode == "video":
                            if download_thread.video_status == "downloading" or download_thread.video_status == "idle":
                                download_thread.actionrow.set_visible(download_thread.actionrow.is_visible)
                self.filter_button_show_downloading.set_active(True)

            elif (filter_mode == "show_completed"):
                self.applied_filter = "show_completed"
                for download_thread in self.downloads:
                    if (download_thread.download):
                        if download_thread.mode == "regular":
                            if (download_thread.download.status == "complete"):
                                download_thread.actionrow.set_visible(download_thread.actionrow.is_visible)
                        elif download_thread.mode == "video":
                            if download_thread.video_status == "finished":
                                download_thread.actionrow.set_visible(download_thread.actionrow.is_visible)
                self.filter_button_show_completed.set_active(True)

            elif (filter_mode == "show_seeding"):
                self.applied_filter = "show_seeding"
                for download_thread in self.downloads:
                    if (download_thread.download):
                        if (download_thread.mode == "regular") and (download_thread.download.seeder == True):
                            download_thread.actionrow.set_visible(download_thread.actionrow.is_visible)
                self.filter_button_show_seeding.set_active(True)

            else:
                self.applied_filter = "show_failed"
                for download_thread in self.downloads:
                    if (download_thread.download):
                        if download_thread.mode == "regular":
                            if (download_thread.download.status == "error"):
                                download_thread.actionrow.set_visible(download_thread.actionrow.is_visible)
                        elif download_thread.mode == "video":
                            if download_thread.video_status == "error":
                                download_thread.actionrow.set_visible(download_thread.actionrow.is_visible)
                self.filter_button_show_failed.set_active(True)

    def escape_special_characters(self, string):
        return re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])').sub('', string).replace("&", "&amp;")
    
    def show_snap_permissions_required_dialog(self):
        dialog_commands_label = Gtk.Label()
        dialog_commands_label.set_wrap(True)
        dialog_commands_label.set_selectable(True)
        dialog_commands_label.set_markup("<b>$</b> sudo snap connect varia:shutdown")

        dialog = Adw.AlertDialog()
        dialog.set_body(_("You are using Varia as a Snap package. There are some functions that you can't use without manually giving Varia some extra permissions. These are:")
                        + "\n\n - " + _("Shutdown on Completion")
                        + "\n\n" + _("To enable these functions you must run these commands in a terminal to give the required permissions and then restart Varia:"))
        dialog.set_extra_child(dialog_commands_label)
        dialog.add_response("ok",  _("OK"))
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_close_response("ok")
        dialog.present(self)

    def save_appconf(self):
        with open(os.path.join(self.appdir, 'varia.conf'), 'w') as f:
            json.dump(self.appconf, f)
        print("Config saved")

    def exit_or_tray(self, app, variaapp):
        if self.appconf["use_tray"] == "true":
            self.exitProgram(self, variaapp, True)

        else:
            self.exitProgram(self, variaapp, False)

        return True

    def exitProgram(self, app, variaapp, background):
        if background:
            self.set_visible(False)
            self.start_tray_process(variaapp)

            if self.suppress_startup_notification:
                self.suppress_startup_notification = False
                return

            if not self.tray_notification:
                notification = Gio.Notification.new(_("Background Mode"))
                notification.set_body(_("Continuing the downloads in the background."))
                notification.set_title(_("Background Mode"))
                variaapp.send_notification(None, notification)
                self.tray_notification = True

            print('Background mode')

        else:
            self.terminating = True
            self.all_paused = False

            if (self.remote_successful == False):
                self.pause_all(False)
                self.api.client.shutdown()

                if (self.is_visible() == False):
                    self.set_visible(True)

                # Stop all yt_dlp threads
                for download_thread in self.downloads:
                    if hasattr(download_thread, "youtubedl_thread"):
                        download_thread.video_pause_event.set() # The thread must be resumed so it can detect the SystemExit call
                        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(download_thread.youtubedl_thread.ident), ctypes.py_object(SystemExit))

                # Kill the tray icon process
                if self.tray_process:
                    self.tray_process.kill()
                    self.tray_connection_thread_stop = True

                exiting_dialog = Adw.AlertDialog()
                exiting_dialog_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=25)
                exiting_dialog.set_child(exiting_dialog_box)
                exiting_dialog_box.set_margin_top(30)
                exiting_dialog_box.set_margin_bottom(30)
                exiting_dialog_box.set_margin_start(60)
                exiting_dialog_box.set_margin_end(60)
                exiting_dialog_spinner = Adw.Spinner()
                exiting_dialog_spinner.set_size_request(30, 30)
                exiting_dialog_box.append(exiting_dialog_spinner)
                exiting_dialog_label = Gtk.Label(label=_("Exiting Varia..."))
                exiting_dialog_label.add_css_class("title-1")
                exiting_dialog_box.append(exiting_dialog_label)
                exiting_dialog.set_can_close(False)
                GLib.idle_add(exiting_dialog.present, self)

                GLib.timeout_add(3000, self.aria2c_exiting_check, app, 0, variaapp, exiting_dialog)

            else:
                self.save_window_size()
                self.destroy()
                variaapp.quit()

                if self.update_executable != None:
                    if os.name == 'nt':
                        subprocess.Popen([self.update_executable, "/SILENT", "SUPPRESSMSGBOXES", "SP-", "/NOICONS", "/MERGETASKS=\"!desktopicon\"", "&&", os.path.join(os.getcwd(), "variamain.exe")], shell=True)
                    else: # Mac
                        subprocess.call(('open', self.update_executable))

    def aria2c_exiting_check(self, app, counter, variaapp, exiting_dialog):
        print(counter)
        if ((counter <= 20) and (self.aria2c_subprocess.poll() is None)):
            counter += 1
            GLib.timeout_add(250, self.aria2c_exiting_check, app, counter, variaapp, exiting_dialog)
        else:
            self.aria2c_subprocess.terminate()
            self.aria2c_subprocess.wait()
            if (exiting_dialog is not None):
                exiting_dialog.force_close()
            self.save_window_size()
            self.destroy()

            try:
                variaapp.quit()

            except:
                pass # No need to

            for thread in threading.enumerate():
                print(thread.name)

            if self.update_executable != None:
                if os.name == 'nt':
                    subprocess.Popen([self.update_executable, "/SILENT", "SUPPRESSMSGBOXES", "SP-", "/NOICONS", "/MERGETASKS=\"!desktopicon\"", "&&", os.path.join(os.getcwd(), "variamain.exe")], shell=True)
                else: # Mac
                    subprocess.call(('open', self.update_executable))

            return

    def quit_action_received(self, variaapp):
        if (self.terminating == False):
            self.exitProgram(variaapp, variaapp, False)

class MyApp(Adw.Application):
    def __init__(self, appdir, appconf, first_run, aria2c_subprocess, aria2cexec, ffmpegexec, sevenzexec, denoexec, issnap, arguments, **kwargs):
        super().__init__(**kwargs)
        GLib.set_application_name("Varia")
        self.connect('activate', self.on_activate, appdir, appconf, first_run, aria2c_subprocess, aria2cexec, ffmpegexec, sevenzexec, denoexec, issnap, arguments)
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.quit_action)
        self.add_action(quit_action)
        self.initiated = False
    
    def do_open(self, files, *args):
        arguments = []

        for item in files:
            arguments.append(item.get_uri())
            print(item)
        
        self.add_downloads(arguments)

    def on_activate(self, app, appdir, appconf, first_run, aria2c_subprocess, aria2cexec, ffmpegexec, sevenzexec, denoexec, issnap, arguments):
        if not hasattr(self, 'win'):
            self.win = MainWindow(application=app, variaapp=self, appdir=appdir, appconf=appconf, first_run=first_run, aria2c_subprocess=aria2c_subprocess, aria2cexec=aria2cexec, ffmpegexec=ffmpegexec, sevenzexec=sevenzexec, denoexec=denoexec, issnap=issnap)

        try:
            if ((self.win.terminating == False) and ((appconf["default_mode"] == "visible") or (self.initiated == True))):
                self.win.present()
        except:
            return -1

        self.initiated = True

        if len(arguments) > 0:
            self.add_downloads(arguments)
        
        if os.name == 'nt':
            # On Windows we use Gtk.ApplicationWindow which causes an issue where the dialogs that are shown on top
            # don't seem to disable (unfocus) the window/widget below - even if it does. So we manually override
            # the realize and close signals of Gtk.Widget for Adw.Dialog to set the parent widget sensitivity
            # to True or False.
            class AdwDialogForWindows(Adw.Dialog):
                def __init__(self, **kwargs):
                    super().__init__(**kwargs)
                    self.connect_after("realize", dialog_show)
                    self.connect_after("closed", dialog_close)
            
                def present(self, parent=None):
                    if parent is not None:
                        self._parentwidget = parent
                    super().present(parent)
            
            def dialog_show(dialog):
                if dialog._parentwidget:
                    dialog._parentwidget.set_sensitive(False)
            
            def dialog_close(dialog):
                if dialog._parentwidget:
                    dialog._parentwidget.set_sensitive(True)

            Adw.Dialog = AdwDialogForWindows

    def add_downloads(self, arguments):
        torrent_not_enabled_error_shown = False
        
        def show_torrent_not_enabled_error():
            dialog = Adw.AlertDialog()
            dialog.set_body(_("Torrenting is disabled."))
            dialog.add_response("ok",  _("OK"))
            dialog.set_default_response("ok")
            dialog.set_close_response("ok")
            dialog.present(self.win)

        for item in arguments:
            if item.startswith("magnet:"):
                if self.win.appconf['torrent_enabled'] == '0':
                    if torrent_not_enabled_error_shown == False:
                        show_torrent_not_enabled_error()
                        torrent_not_enabled_error_shown = True
                
                else:
                    actionrow = create_actionrow(self.win, item)
                    download_thread = DownloadThread(self.win, item, actionrow, item, None, "regular", None, False, self.win.appconf["download_directory"], 0)
                    actionrow.download_thread = download_thread
                    self.win.downloads.append(download_thread)
                    download_thread.start()
                    download_thread.actionrow.pause_button.set_visible(True)
            
            elif item.endswith(".torrent"):
                if self.win.appconf['torrent_enabled'] == '0':
                    if torrent_not_enabled_error_shown == False:
                        show_torrent_not_enabled_error()
                        torrent_not_enabled_error_shown = True
                
                else:
                    if self.win.appconf["torrent_download_directory_custom_enabled"] == "1":
                        self.win.api.add_torrent(item, options={"dir": self.win.appconf["torrent_download_directory"]})

                    else:
                        self.win.api.add_torrent(item)
        
        self.win.present()

    def quit_action(self, action, parameter):
        self.win.quit_action_received(self)

def main(version, aria2cexec, ffmpegexec, sevenzexec, denoexec, issnap, arguments):
    if os.name == 'nt' or os.uname().sysname == 'Darwin': # Varia server only used on Windows/Mac to send data to the already running instance.
        if not start_varia_server():
            send_to_varia_instance(arguments)
            return
            sys.exit()

    if "FLATPAK_ID" in os.environ:
        appdir = os.path.join('/var', 'data')
    else:
        appdir = os.path.join(os.path.expanduser('~'), '.varia')
        if not os.path.exists(appdir):
            os.makedirs(appdir)

    def default_download_directory():
        if GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD) and os.path.exists(GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD)):
            return GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD)
        elif os.path.exists(os.path.join(os.path.expanduser('~'), 'Downloads')):
            return os.path.join(os.path.expanduser('~'), 'Downloads')
        elif GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_HOME) and os.path.exists(GLib.UserDirectory.DIRECTORY_HOME):
            return GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_HOME)
        else:
            print("Can't find GLib user special dirs")
            return os.path.expanduser("~")
    
    download_directory = default_download_directory()

    appconf = {
        'window_size': [650, 570],
        'download_speed_limit_enabled': '0',
        'download_speed_limit': '0',
        'auth': '0',
        'auth_username': '',
        'auth_password': '',
        'download_directory': download_directory,
        'download_simultaneous_amount': '5',
        'download_segments': '5',
        'remote': '0',
        'remote_protocol': 'https://',
        'remote_ip': '',
        'remote_port': '',
        'remote_secret': '',
        'remote_location': '',
        'schedule_enabled': '0',
        'default_mode': 'visible',
        'use_tray': 'false',
        'tray_always_visible': 'false',
        'schedule_mode': 'inclusive',
        'schedule': [],
        'remote_time': '0',
        'cookies_txt': '0',
        'check_for_updates_on_startup_enabled': '0',
        'torrent_seeding_enabled': '1',
        'torrent_seeding_disable_warning_dont_show': '0',
        'torrent_seeding_ratio': [False, '1.0'],
        'torrent_download_directory_custom_enabled': '0',
        'torrent_download_directory': download_directory,
        'torrent_enabled': '1',
        'torrent_require_encryption': 'false',
        'torrent_peers_ip_lookup': '1',
        'autostart_on_boot_enabled': 'false',
        'extract_archives': '0',
        'extract_archives_delete_archives': '0'}

    if os.path.exists(os.path.join(appdir, 'varia.conf')):
        first_run = False
        with open(os.path.join(appdir, 'varia.conf'), 'r') as f:
            appconf.update(json.load(f))
        
        if os.path.exists(appconf['download_directory']) == False:
            appconf['download_directory'] = download_directory
            print("Download directory from config not found, reset to default.")
        
        if appconf['torrent_download_directory_custom_enabled'] == '1' and os.path.exists(appconf['torrent_download_directory']) == False:
            appconf['torrent_download_directory'] = download_directory
            print("Torrent download directory from config not found, reset to default.")

    else:
        first_run = True
        with open(os.path.join(appdir, 'varia.conf'), 'w') as f:
            json.dump(appconf, f)

    global aria2c_subprocess
    aria2c_subprocess = None

    aria2_config = [
        "--enable-rpc",
        "--rpc-listen-port=6801",
        "--follow-torrent=false",
        "--allow-overwrite=false",
        "--auto-file-renaming=true",
        "--min-split-size=1M",
        "--http-accept-gzip=true",
        "--disk-cache=128M",
        "--bt-enable-lpd=true",
        "--bt-hash-check-seed=true",
        "--enable-peer-exchange=true",
        "--enable-dht=true",
        "--enable-dht6=true",
        "--peer-agent=Transmission/3.00", # Some people block aria2's native user agent id because it
                                          # doesn't do any seeding by default. Thus here we change it
        "--peer-id-prefix=-TR3000-",      # to mimic Transmission instead.
        "--split=32",
        "--max-connection-per-server=16",
        "--bt-max-peers=250",
        "--bt-request-peer-speed-limit=5M",
        "--bt-tracker-connect-timeout=10",
        "--bt-tracker-interval=30",
        "--bt-save-metadata=true"]

    if (appconf['remote'] == '0'):
        if (os.name == 'nt'):
            aria2c_subprocess = subprocess.Popen([aria2cexec] + aria2_config, shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            if hasattr(os, 'posix_fallocate'):
                aria2_config.append("--file-allocation=falloc") # Set fallocate on Linux for better performance
                print("fallocate enabled.")
                aria2c_subprocess = subprocess.Popen([aria2cexec] + aria2_config, preexec_fn=os.setsid)

            else:
                aria2c_subprocess = subprocess.Popen([aria2cexec] + aria2_config, preexec_fn=os.setsid)

    atexit.register(stop_subprocesses_and_exit)

    signal.signal(signal.SIGINT, stop_subprocesses_and_exit)
    #signal.signal(signal.SIGTERM, stop_subprocesses_and_exit) # causes issues with other subprocesses
    sys.excepthook = global_exception_handler

    arguments = json.loads(arguments)
    global myapp
    myapp = MyApp(appdir, appconf, first_run, aria2c_subprocess, aria2cexec, ffmpegexec, sevenzexec, denoexec, issnap, arguments, application_id="io.github.giantpinkrobots.varia", flags=Gio.ApplicationFlags.HANDLES_OPEN)

    try:
        myapp.run()
    
    finally: # Kill subprocesses if they're running (in case of a crash)
        stop_subprocesses_and_exit()

def global_exception_handler(exctype, value, tb):
    traceback.print_exception(exctype, value, tb)
    stop_subprocesses_and_exit()

def stop_subprocesses_and_exit(*args):
    print("*** Varia has stopped ***")
    
    if "tray_process_global" in locals() and tray_process_global.poll() is None:
        tray_process_global.kill()
        myapp.win.tray_connection_thread_stop = True
    
    if "aria2c_subprocess" in locals() and aria2c_subprocess.poll() is None:
        myapp.win.api.client.shutdown()
        aria2c_subprocess.wait()
    
    try:
        myapp.win.destroy()
        myapp.quit()
        sys.exit()
    
    except:
        return

if (__name__ == '__main__'):
    import gettext

    if os.name == 'nt':
        import ctypes
        import locale

        os.chdir(os.path.dirname(sys.executable))
        windll = ctypes.windll.kernel32
        lang_id = windll.GetUserDefaultUILanguage()
        current_locale = locale.windows_locale.get(lang_id)
        print(current_locale)

        translation = gettext.translation('varia', localedir='./locale', languages=[current_locale], fallback=True)

        stringstorage.setstrings_win(translation.gettext)
        from stringstorage import gettext as _

        sys.exit(main(variaVersion, os.path.join(os.getcwd(), "aria2c.exe"), os.path.join(os.getcwd(), "ffmpeg.exe"), os.path.join(os.getcwd(), "7zz.exe"), os.path.join(os.getcwd(), "deno.exe"), False, json.dumps(sys.argv)))

    elif os.uname().sysname == 'Darwin':
        translation = gettext.translation('varia', localedir='./locale', languages=["en-US"], fallback=True)

        stringstorage.setstrings_win(translation.gettext)
        from stringstorage import gettext as _

        sys.exit(main(variaVersion, os.path.join(os.getcwd(), "aria2c"), os.path.join(os.getcwd(), "ffmpeg"), os.path.join(os.getcwd(), "7zz"), os.path.join(os.getcwd(), "deno"), False, json.dumps(sys.argv)))
