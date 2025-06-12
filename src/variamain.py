variaVersion = "v2025.5.14"

import ctypes
import gi
import sys
import time
import json
import os
import threading
import subprocess
from operator import itemgetter
import re
import stringstorage
import atexit
import signal
from multiprocessing.connection import Listener

from download.actionrow import on_download_clicked
from download.listen import deal_with_simultaneous_download_limit
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
    def __init__(self, variaapp, appdir, appconf, first_run, aria2c_subprocess, aria2cexec, ffmpegexec, issnap, *args, **kwargs):
        super().__init__(*args, **kwargs)

        from window.sidebar import window_create_sidebar
        from window.content import window_create_content
        from window.updater import windows_updater
        from download.communicate import set_speed_limit, set_aria2c_download_directory, set_aria2c_custom_global_option, set_aria2c_cookies
        from initiate import initiate
        from download.listen import listen_to_aria2
        from download.scheduler import schedule_downloads

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

        # Set up variables and all:
        aria2_connection_successful = initiate(self, variaapp, variaVersion, first_run, issnap)

        if (aria2_connection_successful == -1):
            return

        # Create window contents:
        window_create_sidebar(self, variaapp, variaVersion)
        window_create_content(self)

        if self.appconf["schedule_enabled"] == 1:
            self.sidebar_scheduler_label.set_label(_("Scheduler enabled"))

        # Check if the download path still exists:
        if not (os.path.exists(self.appconf["download_directory"])):
            if (os.path.exists(GLib.get_user_special_dir(GLib.DIRECTORY_DOWNLOAD))):
                self.appconf["download_directory"] = GLib.get_user_special_dir(GLib.DIRECTORY_DOWNLOAD)
            else:
                self.appconf["download_directory"] = GLib.get_user_special_dir(GLib.DIRECTORY_HOME)
            self.save_appconf()

        # Check if the custom torrent download path still exists:
        if not (os.path.exists(self.appconf["torrent_download_directory"])):
            if (os.path.exists(GLib.get_user_special_dir(GLib.DIRECTORY_DOWNLOAD))):
                self.appconf["torrent_download_directory"] = GLib.get_user_special_dir(GLib.DIRECTORY_DOWNLOAD)
            else:
                self.appconf["torrent_download_directory"] = GLib.get_user_special_dir(GLib.DIRECTORY_HOME)
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

        set_aria2c_custom_global_option(self, "split", str(self.appconf["download_segments"]))

        # Start checking for simultaneous download amount limit:
        thread = threading.Thread(target=lambda: deal_with_simultaneous_download_limit(self))
        thread.start()

        # Set the remote time setting:
        if self.appconf["remote_time"] == "1":
            set_aria2c_custom_global_option(self, "remote-time", "true")
        else:
            set_aria2c_custom_global_option(self, "remote-time", "false")

        # Set cookies.txt:
        set_aria2c_cookies(self)

        # Listen to aria2c:
        thread = threading.Thread(target=lambda: listen_to_aria2(self, variaapp))
        thread.start()

        # Begin the scheduler:
        thread = threading.Thread(target=lambda: schedule_downloads(self, True))
        thread.start()

        # Windows only stuff:
        if (os.name == 'nt'):
            os.environ['GTK_CSD'] = '0'
            icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
            icon_theme.add_search_path("./icons")
            if (self.appconf["check_for_updates_on_startup_enabled"] == '1') and (os.path.exists("./updater-function-enabled")):
                windows_updater(None, self, variaapp, None, variaVersion, 0)

        # Load incomplete downloads:
        default_state = {"url": None, "filename": None, "type": "regular", "video_options": {}, "paused": False, "index": 0, "dir": self.appconf["download_directory"]}
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
            on_download_clicked(None, self, download["url"], download["filename"], None, download["type"], download["video_options"], download["paused"], download["dir"])

        self.check_all_status() # Set Pause All / Resume All button

        self.connect('close-request', self.exit_or_tray, variaapp)

        # Start in background mode if it was enabled in preferences:
        if (self.appconf["default_mode"] == "background"):
            self.suppress_startup_notification = True
            self.exitProgram(app=self, variaapp=variaapp, background=True)
        else:
            self.suppress_startup_notification = False

        if self.appconf["tray_always_visible"] == "true":
            self.start_tray_process(variaapp)

        self.connect("notify::default-width", self.on_window_resize)
        self.on_window_resize(None, None)

        self.tray_notification = False

    def start_tray_process(self, variaapp):
        if self.tray_process == None: # If tray process is not already running
            if os.name == 'nt':

                if os.path.exists(os.path.join(os.getcwd(), 'tray', 'varia-tray.exe')): # Built with PyInstaller
                    tray_subprocess_input = [os.path.join(os.getcwd(), 'tray', 'varia-tray.exe'), _("Show"), _("Quit")]

                else: # Running standalone
                    tray_subprocess_input = [sys.executable, os.path.join(os.path.dirname(__file__), 'tray', 'tray_windows.py'), _("Show"), _("Quit")]

            else:
                tray_subprocess_input = [sys.executable, os.path.join(os.path.dirname(__file__), 'tray', 'tray_linux.py'), _("Show"), _("Quit")]

            def tray_process_connection():
                address = ('localhost', 6802)
                listener = Listener(address, authkey=b'varia-tray-process')

                print("Waiting for tray process connection...")
                conn = listener.accept()
                print("Connected to the tray icon process.")

                self.tray_connection_thread_stop = False

                while True:
                    if self.tray_connection_thread_stop:
                        break

                    try:
                        message = conn.recv()
                        print("Tray icon pressed function: ", message)

                        if message == "show":
                            self.unminimize()
                            self.set_visible(True)
                            self.present()
                            if self.appconf["tray_always_visible"] != "true":
                                self.tray_process.kill()
                                self.tray_process = None

                        elif message == "quit":
                            self.exitProgram(self, variaapp, False)
                            break

                    except EOFError:
                        break

            # Tray icon process must be separate as libayatana-appindicator relies on Gtk 3.
            self.tray_process = subprocess.Popen(
                tray_subprocess_input
            )

            self.tray_process_connection_thread = threading.Thread(target=tray_process_connection, daemon=True).start()

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

    # Drag and drop:

    def on_drag_enter(self, target, x, y):
        self.root_window_overlay.add_overlay(self.drag_drop_revealer)
        self.drag_drop_revealer.set_reveal_child(True)
        return 0

    def on_drag_leave(self, target, timeout_milliseconds):
        GLib.timeout_add(timeout_milliseconds - 250, self.drag_drop_revealer.set_reveal_child, False)
        GLib.timeout_add(timeout_milliseconds, self.root_window_overlay.remove_overlay, self.drag_drop_revealer)
        GLib.timeout_add(timeout_milliseconds, self.drag_drop_status_page.remove_css_class, "drag_drop_status_page_error")
        GLib.timeout_add(timeout_milliseconds, self.drag_drop_status_page.remove_css_class, "drag_drop_status_page_success")
        GLib.timeout_add(timeout_milliseconds, self.drag_drop_status_page.add_css_class, "drag_drop_status_page")
        GLib.timeout_add(timeout_milliseconds, self.drag_drop_status_page.set_icon_name, "document-send-symbolic")

        return 0

    def on_file_drop(self, target, value, x, y):
        timeout_milliseconds = 1000

        if isinstance(value, Gio.File) and \
            value.get_path() and \
            value.query_info("standard::content-type", Gio.FileQueryInfoFlags.NONE, None).get_content_type() == "application/x-bittorrent":

            try:
                if self.appconf["torrent_download_directory_custom_enabled"] == "1":
                    self.api.add_torrent(value.get_path(), options={"dir": self.appconf["torrent_download_directory"]})

                else:
                    self.api.add_torrent(value.get_path())

                print(f"Torrent file dragged: {value.get_path()}")
                timeout_milliseconds = 600
                self.drag_drop_status_page.remove_css_class("drag_drop_status_page")
                self.drag_drop_status_page.add_css_class("drag_drop_status_page_success")

            except:
                pass

        if timeout_milliseconds == 1000:
            self.drag_drop_status_page.remove_css_class("drag_drop_status_page")
            self.drag_drop_status_page.add_css_class("drag_drop_status_page_error")
            self.drag_drop_status_page.set_icon_name("media-playback-stop-symbolic")

        GLib.idle_add(self.on_drag_leave, None, timeout_milliseconds)
        return 0

    # Adaptive layout stuff:

    def on_window_resize(self, widget, param):
        if self.get_default_size()[0] < 550:
            self.header_show_sidebar_button_revealer.set_reveal_child(True)
            self.status_page_begin_button_revealer.set_reveal_child(True)
            self.overlay_split_view.set_show_sidebar(False)

        else:
            self.header_show_sidebar_button_revealer.set_reveal_child(False)
            self.status_page_begin_button_revealer.set_reveal_child(False)
            self.overlay_split_view.set_collapsed(False)
            self.overlay_split_view.set_show_sidebar(True)

    def total_download_speed_get(self, downloads, total_download_speed_label):
        while (self.terminating == False):
            total_download_speed = 0
            total_completed_download_amount = 0

            for download_thread in downloads:
                total_download_speed += download_thread.speed

                if download_thread.is_complete:
                    total_completed_download_amount += 1

            if (total_download_speed == 0):
                download_speed_text = "0" + _(" B/s")
            elif (total_download_speed < 1024):
                download_speed_text = str(total_download_speed) + _(" B/s")
            elif ((total_download_speed >= 1024) and (total_download_speed < 1048576)):
                download_speed_text = str(round(total_download_speed / 1024, 2)) + _(" KB/s")
            else:
                download_speed_text = str(round(total_download_speed / 1024 / 1024, 2)) + _(" MB/s")

            if len(downloads) > 0:
                download_speed_text = f"{download_speed_text}  ·  {total_completed_download_amount}/{len(downloads)}"

            GLib.idle_add(total_download_speed_label.set_text, download_speed_text)

            time.sleep(0.5)

    def pause_all(self):
        if len(self.downloads) > 0:
            if self.all_paused:
                for download_thread in self.downloads:
                    download_thread.resume()

            else:
                for download_thread in self.downloads:
                    download_thread.pause(False)

            self.check_all_status()

    def check_all_status(self):
        def set_header_button(mode):
            if mode:
                GLib.idle_add(self.header_pause_content.set_icon_name, "media-playback-start-symbolic")
                GLib.idle_add(self.header_pause_content.set_label, _("Resume All"))

            else:
                GLib.idle_add(self.header_pause_content.set_icon_name, "media-playback-pause-symbolic")
                GLib.idle_add(self.header_pause_content.set_label, _("Pause All"))

        if len(self.downloads) > 0:
            self.all_paused = True

            for download_thread in self.downloads:
                if download_thread.paused == False:
                    self.all_paused = False

            if self.all_paused:
                set_header_button(True)
                print("All downloads are paused")

            else:
                set_header_button(False)

            GLib.idle_add(self.header_pause_button.set_sensitive, True)

        else:
            set_header_button(False)
            GLib.idle_add(self.header_pause_button.set_sensitive, False)

    def stop_all(self, app, variaapp):
        while (self.downloads != []):
            child = self.download_list.get_first_child()
            while child is not None:
                next_child = child.get_next_sibling()
                self.download_list.remove(child)
                child = next_child
            for download_thread in self.downloads:
                download_thread.stop()
                self.downloads.remove(download_thread)
        self.header_pause_content.set_icon_name("media-playback-pause-symbolic")
        self.header_pause_content.set_label(_("Pause All"))
        self.header_pause_button.set_sensitive(False)
        self.content_root_overlay.add_overlay(self.status_page_widget)

    def save_appconf(self):
        with open(os.path.join(self.appdir, 'varia.conf'), 'w') as f:
            json.dump(self.appconf, f)
        print("Config saved")

    def save_window_size(self):
        self.appconf['window_size'] = self.get_default_size()
        self.save_appconf()

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
                self.pause_all()
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
                    subprocess.Popen([self.update_executable, "/SILENT", "SUPPRESSMSGBOXES", "SP-", "/NOICONS", "/MERGETASKS=\"!desktopicon\"", "&&", os.path.join(os.getcwd(), "variamain.exe")], shell=True)

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
                subprocess.Popen([self.update_executable, "/SILENT", "SUPPRESSMSGBOXES", "SP-", "/NOICONS", "/MERGETASKS=\"!desktopicon\"", "&&", os.path.join(os.getcwd(), "variamain.exe")], shell=True)

            return

    def quit_action_received(self, variaapp):
        if (self.terminating == False):
            self.exitProgram(variaapp, variaapp, False)

class MyApp(Adw.Application):
    def __init__(self, appdir, appconf, first_run, aria2c_subprocess, aria2cexec, ffmpegexec, issnap, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate, appdir, appconf, first_run, aria2c_subprocess, aria2cexec, ffmpegexec, issnap)
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.quit_action)
        self.add_action(quit_action)
        self.initiated = False

    def on_activate(self, app, appdir, appconf, first_run, aria2c_subprocess, aria2cexec, ffmpegexec, issnap):
        if not hasattr(self, 'win'):
            self.win = MainWindow(application=app, variaapp=self, appdir=appdir, appconf=appconf, first_run=first_run, aria2c_subprocess=aria2c_subprocess, aria2cexec=aria2cexec, ffmpegexec=ffmpegexec, issnap=issnap)

        try:
            if ((self.win.terminating == False) and ((appconf["default_mode"] == "visible") or (self.initiated == True))):
                self.win.present()
        except:
            return -1

        self.initiated = True

    def quit_action(self, action, parameter):
        self.win.quit_action_received(self)

def main(version, aria2cexec, ffmpegexec, issnap):
    if "FLATPAK_ID" in os.environ:
        appdir = os.path.join('/var', 'data')
    else:
        appdir = os.path.join(os.path.expanduser('~'), '.varia')
        if not os.path.exists(appdir):
            os.makedirs(appdir)

    download_directory = ''

    try:
        if (os.path.exists(GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD))):
            download_directory = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD)
        else:
            download_directory = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_HOME)
    except AttributeError:
        print("Can't find GLib user special dirs")
        download_directory = os.path.expanduser("~")

    appconf = {
        'window_size': [800, 630],
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
        'torrent_enabled': '1'}

    if os.path.exists(os.path.join(appdir, 'varia.conf')):
        first_run = False
        with open(os.path.join(appdir, 'varia.conf'), 'r') as f:
            appconf.update(json.load(f))

    else:
        first_run = True
        with open(os.path.join(appdir, 'varia.conf'), 'w') as f:
            json.dump(appconf, f)

    def stop_aria2c_on_exit(proc):
        try:
            if os.name == 'nt':
                proc.send_signal(signal.CTRL_BREAK_EVENT)

            else:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)

        except ProcessLookupError:
            pass

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

    atexit.register(stop_aria2c_on_exit, aria2c_subprocess)

    arguments = sys.argv
    if (len(arguments) > 1):
        arguments = arguments[:-3]
    app = MyApp(appdir, appconf, first_run, aria2c_subprocess, aria2cexec, ffmpegexec, issnap, application_id="io.github.giantpinkrobots.varia")
    app.run(arguments)

if ((__name__ == '__main__') and (os.name == 'nt')):
    import gettext
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

    sys.exit(main(variaVersion, os.path.join(os.getcwd(), "aria2c.exe"), os.path.join(os.getcwd(), "ffmpeg.exe"), False))
