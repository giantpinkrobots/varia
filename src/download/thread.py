import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import GLib
import threading
from urllib.parse import urlparse
import requests
import time
import os
import json
from gettext import gettext as _
from download.actionrow import on_pause_clicked

class DownloadThread(threading.Thread):
    def __init__(self, app, url, progress_bar, speed_label, pause_button, actionrow, filename_label, download, downloadname):
        threading.Thread.__init__(self)
        self.api = app.api
        self.downloaddir = app.appconf["download_directory"]
        self.download = download
        self.url = url
        self.speed_label = speed_label
        self.stop_event = threading.Event()
        self.auth = app.appconf["auth"]
        self.auth_username = app.appconf["auth_username"]
        self.auth_password = app.appconf["auth_password"]
        self.progress_bar = progress_bar
        self.pause_button = pause_button
        self.actionrow = actionrow
        self.filename_label = filename_label
        self.app = app
        self.cancelled = False
        self.downloadname = downloadname

    def is_valid_url(self):
        try:
            result = urlparse(self.url)
            if not ((self.url[0:7] == "http://") or (self.url[0:8] == "https://")):
                self.url = "http://" + self.url
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def run(self):
        if (self.download == None):
            if (self.url == "sus"):
                try:
                    # Lol nice - Caleb (N0tACyb0rg)
                    GLib.idle_add(self.show_message("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣤⣤⣤⣀⣀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣼⠟⠉⠉⠉⠉⠉⠉⠉⠙⠻⢶⣄⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣾⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⣷⡀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⡟⠀⣠⣶⠛⠛⠛⠛⠛⠛⠳⣦⡀⠀⠘⣿⡄⠀⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⠁⠀⢹⣿⣦⣀⣀⣀⣀⣀⣠⣼⡇⠀⠀⠸⣷⠀⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⡏⠀⠀⠀⠉⠛⠿⠿⠿⠿⠛⠋⠁⠀⠀⠀⠀⣿⡄⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⡇⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⣸⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⣿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣧⠀\n⠀⠀⠀⠀⠀⠀⠀⢸⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⠀\n⠀⠀⠀⠀⠀⠀⠀⣾⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀\n⠀⠀⠀⠀⠀⠀⠀⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀\n⠀⠀⠀⠀⠀⠀⢰⣿⠀⠀⠀⠀⣠⡶⠶⠿⠿⠿⠿⢷⣦⠀⠀⠀⠀⠀⠀⠀⣿⠀\n⠀⠀⣀⣀⣀⠀⣸⡇⠀⠀⠀⠀⣿⡀⠀⠀⠀⠀⠀⠀⣿⡇⠀⠀⠀⠀⠀⠀⣿⠀\n⣠⡿⠛⠛⠛⠛⠻⠀⠀⠀⠀⠀⢸⣇⠀⠀⠀⠀⠀⠀⣿⠇⠀⠀⠀⠀⠀⠀⣿⠀\n⢻⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣼⡟⠀⠀⢀⣤⣤⣴⣿⠀⠀⠀⠀⠀⠀⠀⣿⠀\n⠈⠙⢷⣶⣦⣤⣤⣤⣴⣶⣾⠿⠛⠁⢀⣶⡟⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡟⠀\n⠀⠀⠀⠀⠉⠉⠉⠉⠉⠀⠀⠀⠀⠀⠈⣿⣆⡀⠀⠀⠀⠀⠀⠀⢀⣠⣴⡾⠃⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠛⠻⢿⣿⣾⣿⡿⠿⠟⠋⠁⠀⠀⠀"))
                except:
                    pass
                GLib.idle_add(self.pause_button.set_visible, False)
                GLib.idle_add(self.progress_bar.set_visible, False)
                return

            if (self.url.startswith("magnet:") == False):
                if not (self.is_valid_url()):
                    try:
                        GLib.idle_add(self.show_message, _("This is not a valid URL."))
                        print("Error: Not a valid url.")
                    except:
                        print("Error: Couldn't display 'not a valid url' error, for some reason.")
                    return
                response = requests.head(self.url)
                if ((response.status_code == 401) and (self.auth == '1')):
                    if (self.url[0:7] == "http://"):
                        self.url = self.url[:7] + self.auth_username + ":" + self.auth_password + "@" + self.url[7:]
                    elif (self.url[0:8] == "https://"):
                        self.url = self.url[:8] + self.auth_username + ":" + self.auth_password + "@" + self.url[8:]
                    else:
                        self.url = self.auth_username + ":" + self.auth_password + "@" + self.url
                    print ("Authentication enabled.")

            download_options = {"pause": "true"}

            if self.downloadname != None:
                download_options["out"] = self.downloadname

            print(download_options)

            self.download = self.api.add_uris([self.url], options=download_options)

        print(self.downloadname)

        if self.app.scheduler_currently_downloading == True:
            if self.download.is_paused:
                self.download.resume()
        else:
            on_pause_clicked(self.app, self.app, self.pause_button, self.actionrow, True)
        
        print("Download added. | " + self.download.gid + "\n" + self.downloaddir + "\n" + self.url)
        GLib.idle_add(self.update_header_pause_button)
        self.previous_filename = ""

        self.app.filter_download_list("no", self.app.applied_filter)
        while (self.cancelled == False):
            try:
                self.download.update()
                self.set_filename_label()
                self.update_labels_and_things()
                if ((self.download.is_complete) and (self.download.is_metadata == False)):
                    print('Download complete: ' + self.download.gid)
                    if os.path.exists(os.path.join(self.downloaddir,(self.download.gid + ".varia"))):
                        os.remove(os.path.join(self.downloaddir,(self.download.gid + ".varia")))
                    break
                elif ((self.download.is_torrent) and (self.download.seeder)):
                    print('Torrent complete, seeding: ' + self.download.gid)
                    break
                elif (self.download.status == "error"):
                    return
            except:
                return
            time.sleep(1)

    def set_filename_label(self):
        filename_shortened = self.download.name[:40]
        if (self.download.name != filename_shortened):
            filename_shortened = filename_shortened + "..."
        if (filename_shortened != self.previous_filename):
            GLib.idle_add(self.filename_label.set_text, filename_shortened)
            self.previous_filename = filename_shortened

    def update_header_pause_button(self):
        self.app.all_paused = False
        self.app.header_pause_content.set_icon_name("media-playback-pause-symbolic")
        self.app.header_pause_content.set_label(_("Pause All"))
        self.app.header_pause_button.set_sensitive(True)

    def show_message(self, message):
        self.speed_label.set_text(message)

    def update_labels_and_things(self):
        GLib.idle_add(self.progress_bar.set_fraction, self.download.progress / 100)

        if ((self.download.is_torrent) and (self.download.seeder)):
            GLib.idle_add(self.show_message(_("Seeding torrent")))
            return

        download_speed_mb = (self.download.download_speed / 1024 / 1024)

        download_delta = self.download.eta

        download_seconds = download_delta.total_seconds()
        download_seconds = abs(int(download_seconds))
        download_hours, download_seconds = divmod(download_seconds, 3600)
        download_minutes, download_seconds = divmod(download_seconds, 60)

        download_hours = str(download_hours).zfill(2)
        download_minutes = str(download_minutes).zfill(2)
        download_seconds = str(download_seconds).zfill(2)

        if self.download.download_speed == 0:
            download_remaining_string = "∞"
        else:
            download_remaining_string = f"{download_hours}:{download_minutes}:{download_seconds}"

        if int(str(download_speed_mb)[0]) == 0:
            download_speed_kb = (self.download.download_speed / 1024)
            if int(str(download_speed_kb)[0]) == 0:
                GLib.idle_add(self.speed_label.set_text, f"{round(self.download.progress)}%  |  {round(self.download.download_speed, 2)} {_(' B/s')}  |  {download_remaining_string} {_('remaining')}")
            else:
                GLib.idle_add(self.speed_label.set_text, f"{round(self.download.progress)}%  |  {round(self.download.download_speed / 1024, 2)} {_(' KB/s')}  |  {download_remaining_string} {_('remaining')}")
        else:
            GLib.idle_add(self.speed_label.set_text, f"{round(self.download.progress)}%  |  {round(self.download.download_speed / 1024 / 1024, 2)} {_(' MB/s')}  |  {download_remaining_string} {_('remaining')}")

    def pause(self):
        if self.download:
            if self.download.is_paused == False:
                try:
                    self.download.pause()
                    print ("Download paused.")
                except:
                    try:
                        self.download.pause([self.download.gid])
                        print ("Download paused.")
                    except:
                        self.stop(False)
                        print ("Something went wrong when pausing. Stopping download without removing files.")

    def resume(self):
        if self.download:
            if self.download.is_paused == True:
                try:
                    self.download.resume()
                    print ("Download resumed.")
                except:
                    try:
                        self.download.pause([self.download.gid])
                        print ("Download paused.")
                    except:
                        try:
                            GLib.idle_add(self.speed_label.set_text, _("An error occurred:") + " " + self.download.error_message.split("status=")[1])
                            print ("An error occurred when resuming. " + self.download.error_message.split("status=")[1])
                        except:
                            pass

    def stop(self, deletefiles):
        if self.download:
            try:
                downloadgid = self.download.gid
                downloadname = self.download.name
                self.download.remove(force=True)
                if not self.download.is_complete:
                    if (deletefiles == True):
                        if os.path.exists(os.path.join(self.downloaddir,(downloadgid + ".varia"))):
                            os.remove(os.path.join(self.downloaddir,(downloadgid + ".varia")))
                        if os.path.exists(os.path.join(self.downloaddir, downloadname)):
                            os.remove(os.path.join(self.downloaddir, downloadname))
                print ("Download stopped.")
            except:
                pass
        self.stop_event.set()

    def save_state(self):
        if self.download:
            try:
                self.download.update()
            except:
                print ("Couldn't update the status of the download. Skipping state saving.")
                return
            state = {
                'url': self.url,
                'filename': self.download.name
            }
            with open(os.path.join(self.downloaddir, f'{self.download.gid}.varia'), 'w') as f:
                json.dump(state, f)
            print ("State saved for download.")

    def return_gid(self):
        if self.download:
            return self.download.gid

    def return_is_paused(self):
        if (self.pause_button.get_child().get_icon_name() == "media-playback-pause-symbolic"):
            return False
        else:
            return True

    @classmethod
    def load_state(cls, app, filename, url, progress_bar, speed_label, pause_button, actionrow, filename_label, download, downloadname):
        with open(os.path.join(app.appconf["download_directory"], filename), 'r') as f:
            state = json.load(f)
            os.remove(os.path.join(app.appconf["download_directory"], filename))
        instance = cls(app, state['url'], progress_bar, speed_label, pause_button, actionrow, filename_label, None, downloadname)
        return instance
