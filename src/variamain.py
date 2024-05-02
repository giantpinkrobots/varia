variaVersion = "dev"

import gi
import sys
from gettext import gettext as _
import time
import json
import os
import threading
import subprocess
from pathlib import Path
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio
import requests

from window.sidebar import window_create_sidebar
from window.content import window_create_content, create_status_page
from download.actionrow import create_actionrow, on_pause_clicked, on_stop_clicked
from download.thread import DownloadThread
from download.communicate import set_speed_limit, set_aria2c_download_directory, set_aria2c_download_simultaneous_amount, set_aria2c_custom_global_option, set_aria2c_cookies
from initiate import initiate
from download.listen import listen_to_aria2
from download.scheduler import schedule_downloads

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, variaapp, appdir, appconf, aria2c_subprocess, aria2cexec, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_hide_on_close(True)
        self.connect('close-request', self.exitProgram, variaapp, False)

        self.scheduler_currently_downloading = False
        self.appdir = appdir
        self.appconf = appconf
        self.aria2c_subprocess = aria2c_subprocess
        self.bindir = aria2cexec[:-6]

        # Set up variables and all:
        aria2_connection_successful = initiate(self, variaVersion)

        if (aria2_connection_successful == -1):
            return

        # Create window contents:
        window_create_sidebar(self, variaapp, DownloadThread, variaVersion)
        window_create_content(self, threading)

        if self.appconf["schedule_enabled"] == 1:
            self.sidebar_scheduler_label.set_label(_("Scheduler enabled"))

        # Check if the download path still exists:
        if not (os.path.exists(self.appconf["download_directory"])):
            if (os.path.exists(GLib.get_user_special_dir(GLib.USER_DIRECTORY_DOWNLOAD))):
                self.appconf["download_directory"] = GLib.get_user_special_dir(GLib.USER_DIRECTORY_DOWNLOAD)
            else:
                self.appconf["download_directory"] = GLib.get_user_special_dir(GLib.USER_DIRECTORY_HOME)
            self.save_appconf()

        # Set download speed limit from appconf:
        if ((self.appconf["download_speed_limit_enabled"] == "1") and (self.appconf["download_speed_limit"][:-1] != "0")):
            set_speed_limit(self, self.appconf["download_speed_limit"])

        # Set download speed limit from appconf:
        if ((self.appconf["download_speed_limit_enabled"] == "1") and (self.appconf["download_speed_limit"][:-1] != "0")):
            set_speed_limit(self, self.appconf["download_speed_limit"])

        # Set download directory from appconf:
        set_aria2c_download_directory(self)

        # Set the maximum simultaneous download amount from appconf:
        set_aria2c_download_simultaneous_amount(self)

        # Set the remote time setting:
        if self.appconf["remote_time"] == "1":
            set_aria2c_custom_global_option(self, "remote-time", "true")
        else:
            set_aria2c_custom_global_option(self, "remote-time", "false")

        # Set cookies.txt:
        set_aria2c_cookies(self)

        # Listen to aria2c:
        thread = threading.Thread(target=listen_to_aria2(self, variaapp))
        thread.start()

        # Begin the scheduler:
        thread = threading.Thread(target=schedule_downloads(self, True))
        thread.start()

        # Load incomplete downloads:
        default_state = {"url": None, "filename": None}

        for filename in os.listdir(self.appconf["download_directory"]):
            if filename.endswith('.varia.json'):

                with open(os.path.join(self.appconf["download_directory"], filename), 'r') as f:
                    loaded_state = json.load(f)

                state = {**default_state, **loaded_state}
                objectlist = create_actionrow(self, state['url'])
                download_thread = DownloadThread.load_state(self, filename, state['url'], objectlist[0], objectlist[1], objectlist[2], objectlist[3], objectlist[4], None, state['filename'])
                self.downloads.append(download_thread)
                download_thread.start()

        # Start in background mode if it was enabled in preferences:
        if (self.appconf["default_mode"] == "background"):
            self.exitProgram(app=self, variaapp=variaapp, background=True)

    def filter_download_list(self, button, filter_mode):
        if (button != "no"):
            self.filter_button_show_all.set_active(False)
            self.filter_button_show_downloading.set_active(False)
            self.filter_button_show_completed.set_active(False)
            self.filter_button_show_seeding.set_active(False)
            self.filter_button_show_failed.set_active(False)

        else:
            filter_mode = self.applied_filter

        if (filter_mode == "show_all"):
            self.applied_filter = "show_all"
            for download_thread in self.downloads:
                download_thread.actionrow.show()
            self.filter_button_show_all.set_active(True)

        else:
            for download_thread in self.downloads:
                download_thread.actionrow.hide()

            if (filter_mode == "show_downloading"):
                self.applied_filter = "show_downloading"
                for download_thread in self.downloads:
                    if (download_thread.download):
                        if (((download_thread.download.status == "waiting") or (download_thread.download.status == "active")) and (download_thread.download.seeder != True)):
                            download_thread.actionrow.show()
                    else:
                        download_thread.actionrow.show()
                self.filter_button_show_downloading.set_active(True)

            elif (filter_mode == "show_completed"):
                self.applied_filter = "show_completed"
                for download_thread in self.downloads:
                    if (download_thread.download):
                        if (download_thread.download.status == "complete"):
                            download_thread.actionrow.show()
                self.filter_button_show_completed.set_active(True)

            elif (filter_mode == "show_seeding"):
                self.applied_filter = "show_seeding"
                for download_thread in self.downloads:
                    if (download_thread.download):
                        if (download_thread.download.seeder == True):
                            download_thread.actionrow.show()
                self.filter_button_show_seeding.set_active(True)

            else:
                self.applied_filter = "show_failed"
                for download_thread in self.downloads:
                    if (download_thread.download):
                        if (download_thread.download.status == "error"):
                            download_thread.actionrow.show()
                self.filter_button_show_failed.set_active(True)

    def check_download_status(self):
        while (self.terminating == False):
            i = 0
            for download_thread in self.downloads:
                try:
                    if (download_thread.download):
                        if (download_thread.download.is_complete == 1):
                            download_thread.cancelled = True
                            download_thread.speed_label.set_text(_("Download complete."))
                            self.pause_buttons[i].hide()
                            self.filter_download_list("no", self.applied_filter)

                        elif (download_thread.download.status == "error") or (download_thread.download.status == "removed"):
                            download_thread.cancelled = True

                            if (download_thread.download.error_code == "24"):
                                download_thread.speed_label.set_text(_("Authorization failed."))

                            else:
                                download_thread.speed_label.set_text(_("An error occurred:") + " " + str(download_thread.download.error_code))
                            download_thread.stop(False)

                            self.pause_buttons[i].hide()
                            self.filter_download_list("no", self.applied_filter)
                except:
                    self.pause_buttons[i].hide()
                    self.filter_download_list("no", self.applied_filter)
                    pass
                i += 1
            time.sleep(1)

    def total_download_speed_get(self, downloads, total_download_speed_label):
        while (self.terminating == False):
            total_download_speed = 0
            for download_thread in downloads:
                try:
                    download_thread.download.update()
                except:
                    continue
                try:
                    speed_label_text_first_digit = download_thread.speed_label.get_text()[0]
                except:
                    speed_label_text_first_digit = "0"
                try:
                    if (speed_label_text_first_digit.isdigit()):
                        download_speed = (float(download_thread.speed_label.get_text().split(" ")[4]))
                        if (download_thread.speed_label.get_text().split(" ")[5] == _("GB/s")):
                            download_speed = download_speed * 1024 * 1024 * 1024
                        elif (download_thread.speed_label.get_text().split(" ")[5] == _("MB/s")):
                            download_speed = download_speed * 1024 * 1024
                        elif (download_thread.speed_label.get_text().split(" ")[5] == _("KB/s")):
                            download_speed = download_speed * 1024
                        total_download_speed = total_download_speed + download_speed
                except:
                    continue
            if (total_download_speed == 0):
                download_speed_text = "0" + _(" B/s")
            elif (total_download_speed < 1024):
                download_speed_text = str(total_download_speed) + _(" B/s")
            elif ((total_download_speed >= 1024) and (total_download_speed < 1048576)):
                download_speed_text = str(round(total_download_speed / 1024, 2)) + _(" KB/s")
            else:
                download_speed_text = str(round(total_download_speed / 1024 / 1024, 2)) + _(" MB/s")

            total_download_speed_label.set_text(download_speed_text)
            time.sleep(1)

    def pause_all(self, header_pause_content):
        i = 0
        pause_button_images = []
        if (self.all_paused == False):
            for download_thread in self.downloads:
                download_thread.pause()

                pause_button_images.append(Gtk.Image.new())
                pause_button_images[i].set_from_icon_name("media-playback-start-symbolic")
                self.pause_buttons[i].set_child(pause_button_images[i])

                download_thread.save_state()

                i += 1
            if ((header_pause_content != "no") and (i > 0)):
                header_pause_content.set_icon_name("media-playback-start-symbolic")
                header_pause_content.set_label(_("Resume All"))
            self.all_paused = True
        else:
            for download_thread in self.downloads:
                download_thread.resume()

                pause_button_images.append(Gtk.Image.new())
                pause_button_images[i].set_from_icon_name("media-playback-pause-symbolic")
                self.pause_buttons[i].set_child(pause_button_images[i])

                i += 1
            if ((header_pause_content != "no") and (i > 0)):
                header_pause_content.set_icon_name("media-playback-pause-symbolic")
                header_pause_content.set_label(_("Pause All"))
            self.all_paused = False

    def stop_all(self, app, variaapp):
        while (self.downloads != []):
            child = self.download_list.get_first_child()
            while child is not None:
                next_child = child.get_next_sibling()
                self.download_list.remove(child)
                child = next_child
            for download_thread in self.downloads:
                deletefiles = True
                if ((download_thread.download.is_torrent) and (download_thread.download.seeder)):
                    deletefiles = False
                download_thread.stop(deletefiles)
                self.downloads.remove(download_thread)
        self.header_pause_content.set_icon_name("media-playback-pause-symbolic")
        self.header_pause_content.set_label(_("Pause All"))
        self.header_pause_button.set_sensitive(False)
        create_status_page(self, 0)

    def save_appconf(self):
        with open(os.path.join(self.appdir, 'varia.conf'), 'w') as f:
            json.dump(self.appconf, f)
        print("Config saved")

    def exitProgram(self, app, variaapp, background):
        if (background == True):
            self.hide()
            notification = Gio.Notification.new(_("Background Mode"))
            notification.set_body(_("Continuing the downloads in the background."))
            notification.set_title(_("Background Mode")),
            variaapp.send_notification(None, notification)
            print('Background mode')
        else:
            self.terminating = True

            self.set_sensitive(False)
            self.all_paused = False

            if (self.appconf['remote'] == '0'):
                self.pause_all("no")
                self.api.client.shutdown()

                if (self.is_visible() == True):
                    self.hide()
                    exiting_dialog = Adw.MessageDialog()
                    exiting_dialog_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=25)
                    exiting_dialog.set_child(exiting_dialog_box)
                    exiting_dialog_box.set_margin_top(30)
                    exiting_dialog_box.set_margin_bottom(30)
                    exiting_dialog_spinner = Gtk.Spinner()
                    exiting_dialog_spinner.set_size_request(30, 30)
                    exiting_dialog_spinner.start()
                    exiting_dialog_box.append(exiting_dialog_spinner)
                    exiting_dialog_label = Gtk.Label(label=_("Exiting Varia..."))
                    exiting_dialog_label.get_style_context().add_class("title-1")
                    exiting_dialog_box.append(exiting_dialog_label)
                    exiting_dialog.set_transient_for(self)
                    GLib.idle_add(exiting_dialog.show)
                else:
                    exiting_dialog = None

                GLib.timeout_add(3000, self.aria2c_exiting_check, app, 0, variaapp, exiting_dialog)

            else:
                self.destroy()
                variaapp.quit()

    def aria2c_exiting_check(self, app, counter, variaapp, exiting_dialog):
        print(counter)
        if ((counter < 20) and (self.aria2c_subprocess.poll() is None)):
            counter += 1
            GLib.timeout_add(250, self.aria2c_exiting_check, app, counter, variaapp, exiting_dialog)
        else:
            self.aria2c_subprocess.terminate()
            self.aria2c_subprocess.wait()
            if (exiting_dialog is not None):
                exiting_dialog.destroy()
            self.destroy()
            variaapp.quit()
            for thread in threading.enumerate():
                print(thread.name)
            return

    def quit_action_received(self, variaapp):
        if (self.terminating == False):
            self.exitProgram(variaapp, variaapp, False)

class MyApp(Adw.Application):
    def __init__(self, appdir, appconf, aria2c_subprocess, aria2cexec, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate, appdir, appconf, aria2c_subprocess, aria2cexec)
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.quit_action)
        self.add_action(quit_action)
        self.initiated = False

    def on_activate(self, app, appdir, appconf, aria2c_subprocess, aria2cexec):
        if not hasattr(self, 'win'):
            self.win = MainWindow(application=app, variaapp=self, appdir=appdir, appconf=appconf, aria2c_subprocess=aria2c_subprocess, aria2cexec=aria2cexec)
        if ((self.win.terminating == False) and ((appconf["default_mode"] == "visible") or (self.initiated == True))):
            self.win.present()
        self.initiated = True

    def quit_action(self, action, parameter):
        self.win.quit_action_received(self)

def main(version, aria2cexec):
    if "FLATPAK_ID" in os.environ:
        appdir = os.path.join('/var', 'data')
    else:
        appdir = os.path.join(os.path.expanduser('~'), '.varia')
        if not os.path.exists(appdir):
            os.makedirs(appdir)
    
    download_directory = ''
    
    try:
        if (os.path.exists(GLib.get_user_special_dir(GLib.USER_DIRECTORY_DOWNLOAD))):
            download_directory = GLib.get_user_special_dir(GLib.USER_DIRECTORY_DOWNLOAD)
        else:
            download_directory = GLib.get_user_special_dir(GLib.USER_DIRECTORY_HOME)
    except:
        download_directory = GLib.get_user_special_dir(GLib.USER_DIRECTORY_HOME)

    appconf = {
        'download_speed_limit_enabled': '0',
        'download_speed_limit': '0',
        'auth': '0',
        'auth_username': '',
        'auth_password': '',
        'download_directory': download_directory,
        'download_simultaneous_amount': '5',
        'remote': '0',
        'remote_protocol': 'https://',
        'remote_ip': '',
        'remote_port': '',
        'remote_secret': '',
        'remote_location': '',
        'schedule_enabled': '0',
        'default_mode': 'visible',
        'schedule_mode': 'inclusive',
        'schedule': [],
        'remote_time': '0',
        'cookies_txt': '0'}

    if os.path.exists(os.path.join(appdir, 'varia.conf')):
        with open(os.path.join(appdir, 'varia.conf'), 'r') as f:
            appconf.update(json.load(f))
    else:
        with open(os.path.join(appdir, 'varia.conf'), 'w') as f:
            json.dump(appconf, f)

    aria2c_subprocess = None
    if (appconf['remote'] == '0'):
        if (os.name == 'nt'):
            aria2c_subprocess = subprocess.Popen([aria2cexec, "--enable-rpc", "--rpc-listen-port=6801", "--follow-torrent=mem"], shell=True)
        else:
            aria2c_subprocess = subprocess.Popen([aria2cexec, "--enable-rpc", "--rpc-listen-port=6801", "--follow-torrent=mem"])

    arguments = sys.argv
    if (len(arguments) > 1):
        arguments = arguments[:-1]

    app = MyApp(appdir, appconf, aria2c_subprocess, aria2cexec, application_id="io.github.giantpinkrobots.varia")
    try:
        app.run(arguments)
    except:
        pass

if ((__name__ == '__main__') and (os.name == 'nt')):
    sys.exit(main(variaVersion, "aria2c"))

