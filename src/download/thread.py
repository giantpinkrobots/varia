import ctypes
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import GLib, Gtk
import threading
from urllib.parse import urlparse
import requests
import time
import os
import json
from stringstorage import gettext as _
from yt_dlp import YoutubeDL
import re
import base64
import multiprocessing as multiprocessing
from window.content import check_for_all_paused

class DownloadThread(threading.Thread):
    def __init__(self, app, url, actionrow, downloadname, download, mode, video_options, paused, dir):
        threading.Thread.__init__(self)
        self.api = app.api
        self.downloaddir = dir
        self.url = url
        self.speed_label = actionrow.speed_label
        self.download = download
        self.auth = app.appconf["auth"]
        self.auth_username = app.appconf["auth_username"]
        self.auth_password = app.appconf["auth_password"]
        self.progress_bar = actionrow.progress_bar
        self.pause_button = actionrow.pause_button
        self.actionrow = actionrow
        self.filename_label = actionrow.filename_label
        self.app = app
        self.cancelled = False
        self.downloadname = downloadname
        self.mode = mode
        self.speed = 0
        self.paused_because_exceeds_limit = False
        
        self.video_options = video_options
        if self.video_options == None:
            self.video_options = {}

        self.download_temp_files = []
        self.video_stop_event = threading.Event()
        self.video_pause_event = threading.Event()
        self.video_pause_event.set()
        self.video_status = "idle"
        self.video_download_combined = False
        self.video_download_stage = 0
        self.video_download_progress_previous = 0

        self.state_file = ""
        self.is_complete = False
        self.paused = paused

    def is_valid_url(self):
        try:
            result = urlparse(self.url)
            if not ((self.url[0:7] == "http://") or (self.url[0:8] == "https://")):
                self.url = "http://" + self.url
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def run(self):
        if (self.url == "sus"):
            try:
                # Lol nice - Caleb (N0tACyb0rg)
                GLib.idle_add(self.show_message("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣤⣤⣤⣀⣀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣼⠟⠉⠉⠉⠉⠉⠉⠉⠙⠻⢶⣄⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣾⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⣷⡀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⡟⠀⣠⣶⠛⠛⠛⠛⠛⠛⠳⣦⡀⠀⠘⣿⡄⠀⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⠁⠀⢹⣿⣦⣀⣀⣀⣀⣀⣠⣼⡇⠀⠀⠸⣷⠀⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⡏⠀⠀⠀⠉⠛⠿⠿⠿⠿⠛⠋⠁⠀⠀⠀⠀⣿⡄⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⡇⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⣸⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⣿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣧⠀\n⠀⠀⠀⠀⠀⠀⠀⢸⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⠀\n⠀⠀⠀⠀⠀⠀⠀⣾⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀\n⠀⠀⠀⠀⠀⠀⠀⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀\n⠀⠀⠀⠀⠀⠀⢰⣿⠀⠀⠀⠀⣠⡶⠶⠿⠿⠿⠿⢷⣦⠀⠀⠀⠀⠀⠀⠀⣿⠀\n⠀⠀⣀⣀⣀⠀⣸⡇⠀⠀⠀⠀⣿⡀⠀⠀⠀⠀⠀⠀⣿⡇⠀⠀⠀⠀⠀⠀⣿⠀\n⣠⡿⠛⠛⠛⠛⠻⠀⠀⠀⠀⠀⢸⣇⠀⠀⠀⠀⠀⠀⣿⠇⠀⠀⠀⠀⠀⠀⣿⠀\n⢻⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣼⡟⠀⠀⢀⣤⣤⣴⣿⠀⠀⠀⠀⠀⠀⠀⣿⠀\n⠈⠙⢷⣶⣦⣤⣤⣤⣴⣶⣾⠿⠛⠁⢀⣶⡟⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡟⠀\n⠀⠀⠀⠀⠉⠉⠉⠉⠉⠀⠀⠀⠀⠀⠈⣿⣆⡀⠀⠀⠀⠀⠀⠀⢀⣠⣴⡾⠃⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠛⠻⢿⣿⣾⣿⡿⠿⠟⠋⠁⠀⠀⠀"))
            except:
                pass
            GLib.idle_add(self.pause_button.set_visible, False)
            GLib.idle_add(self.progress_bar.set_visible, False)
            return
        
        download_options = {}

        if self.url.startswith("magnet:"):
            download_options["dir"] = self.app.appconf["torrent_download_directory"]
            download_options["follow_torrent"] = "true"
            self.downloaddir = self.app.appconf["torrent_download_directory"]

        else:
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

        print(self.downloadname)
        GLib.idle_add(self.update_header_pause_button)

        # Enable "Exit on Completion" and "Shutdown on Completion" options
        self.app.shutdown_action.set_enabled(True)
        self.app.exit_action.set_enabled(True)

        # Regular download, use aria2p:
        if self.mode == "regular":

            download_options["pause"] = "true"

            if self.downloadname != None:
                download_options["out"] = self.downloadname

            print(download_options)

            if self.download == None:
                self.download = self.api.add_uris([self.url], options=download_options)

            if self.app.scheduler_currently_downloading and self.paused == False and self.download.gid and self.download.is_paused:
                try:
                    self.download.resume()
                except:
                    return

            else:
                self.pause(True)
            
            print("Download added. | " + self.download.gid + "\n" + self.downloaddir + "\n" + self.url)
            
            self.previous_filename = ""

            self.app.filter_download_list("no", self.app.applied_filter)

            self.save_state(False)

            download_began = False

            while (self.cancelled == False):
                try:
                    self.download.update()

                    if download_began == False and self.download.is_active:
                        self.pause_button.get_child().set_from_icon_name("media-playback-pause-symbolic")
                        download_began = True
                    
                    if self.downloadname != self.download.name:
                        self.downloadname = self.download.name
                        self.save_state(True)
                    
                    if self.filename_label.get_text() != self.downloadname:
                        GLib.idle_add(self.filename_label.set_text, self.download.name)

                    self.update_labels_and_things(None)
                    if ((self.download.is_complete) and (self.download.is_metadata == False)):
                        print('Download complete: ' + self.download.gid)
                        if os.path.exists(os.path.join(self.downloaddir,(self.download.gid + ".varia"))):
                            os.remove(os.path.join(self.downloaddir,(self.download.gid + ".varia")))
                        GLib.idle_add(self.set_complete)
                        break
                    elif ((self.download.is_torrent) and (self.download.seeder)):
                        print('Torrent complete, seeding: ' + self.download.gid)
                        GLib.idle_add(self.set_complete)
                        break
                    elif (self.download.status == "error"):
                        GLib.idle_add(self.set_failed, None)
                        return
                except:
                    return
                
                time.sleep(0.5)
        
        # Video/audio download, use yt_dlp:
        elif self.mode == "video":

            if self.paused == True:
                self.video_pause_event.set()
            
            else:
                self.pause(False)

            video_options_final = self.video_options.copy()
            video_options_final['progress_hooks'] = [self.update_labels_and_things]
            video_options_final['outtmpl'] = os.path.join(self.downloaddir, self.downloadname)
            video_options_final['continuedl'] = True
            video_options_final['ffmpeg_location'] = self.app.ffmpegexec

            if self.app.appconf["cookies_txt"] == "1":
                video_options_final['cookiefile'] = os.path.join(self.app.appdir, 'cookies.txt')
            
            if '+' in video_options_final['format']:
                self.video_download_combined = True

            self.download = YoutubeDL(video_options_final)

            GLib.idle_add(self.filename_label.set_text, self.downloadname)

            self.save_state(False)
            
            if self.app.appconf["schedule_enabled"] == 1 and self.app.scheduler_currently_downloading == False:
                self.pause(False)
            
                while True:
                    if self.app.scheduler_currently_downloading == True:
                        self.resume()
                        break
                    time.sleep(1)
            
            GLib.idle_add(self.speed_label.set_text, _("Starting download..."))

            def youtubedl_download_start():
                try:
                    self.download.download([self.url])
                except SystemExit:
                    print("SystemExit received by yt_dlp thread")
                    self.video_stop_event.clear()
                    self.cancelled = True
                except Exception as e:
                    GLib.idle_add(self.speed_label.set_text, f"{_("An error occurred:")} {self.app.escape_special_characters(str(e))}")
                    self.video_stop_event.clear()
                    self.cancelled = True
                    GLib.idle_add(self.set_failed, None)

            self.youtubedl_thread = threading.Thread(target=youtubedl_download_start)
            self.youtubedl_thread.daemon = True
            self.youtubedl_thread.start()

            while self.video_stop_event.is_set() == False and self.cancelled == False:
                continue
            
            self.cancelled = True
            return

    def update_header_pause_button(self):
        self.app.all_paused = False
        self.app.header_pause_content.set_icon_name("media-playback-pause-symbolic")
        self.app.header_pause_content.set_label(_("Pause All"))
        self.app.header_pause_button.set_sensitive(True)

    def show_message(self, message):
        self.speed_label.set_text(message)

    def update_labels_and_things(self, video_object):
        speed_label_text = ""
        self.speed = 0
        progress = self.video_download_progress_previous
        download_remaining_string = "∞"
        speed_label_text_percentage = ""
        speed_label_text_speed = ""

        if self.mode == "regular":
            progress = self.download.progress
            speed = self.download.download_speed
            self.speed = speed

            if ((self.download.is_torrent) and (self.download.seeder)):
                GLib.idle_add(self.show_message(_("Seeding torrent")))
                return
            
            download_delta = self.download.eta
            download_speed_mb = (speed / 1024 / 1024)

            download_seconds = download_delta.total_seconds()
            download_seconds = abs(int(download_seconds))
            download_hours, download_seconds = divmod(download_seconds, 3600)
            download_minutes, download_seconds = divmod(download_seconds, 60)

            download_hours = str(download_hours).zfill(2)
            download_minutes = str(download_minutes).zfill(2)
            download_seconds = str(download_seconds).zfill(2)

            if speed != 0:
                download_remaining_string = f"{download_hours}:{download_minutes}:{download_seconds}"
            
            speed_label_text_percentage = _("{number}%").replace("{number}", str(round(progress)))
            
            if int(str(download_speed_mb)[0]) == 0:
                download_speed_kb = (speed / 1024)
                if int(str(download_speed_kb)[0]) == 0:
                    speed_label_text_speed = f"{round(speed, 2)} {_(' B/s')}"
                else:
                    speed_label_text_speed = f"{round(speed / 1024, 2)} {_(' KB/s')}"
            else:
                speed_label_text_speed = f"{round(speed / 1024 / 1024, 2)} {_(' MB/s')}"
            
            if self.download.is_torrent and hasattr(self.download, "files"):
                for file in self.download.files:
                    if file not in self.download_temp_files:
                        self.download_temp_files.append(file)
        
        elif self.mode == "video":
            if video_object['status'] == "finished":
                self.video_status = "finished"

                if self.video_download_combined == False or self.video_download_stage == 1:
                    GLib.idle_add(self.set_complete)

            elif video_object['status'] == "error":
                self.video_status = "error"
                GLib.idle_add(self.set_failed, progress / 100)
            elif video_object['status'] == "idle":
                self.video_status = "idle"

            self.video_pause_event.wait()

            if self.video_stop_event.is_set():
                raise Exception("Download stopped")
            
            if video_object['status'] == 'downloading':
                self.video_status = "downloading"

                try:
                    progress = str(video_object['_percent_str'])
                    progress = self.app.escape_special_characters(progress)
                    progress = progress.replace(" ", "")
                    progress = progress.replace("%", "")

                    speed = str(video_object['_speed_str'])
                    speed = self.app.escape_special_characters(speed)
                    speed = speed.replace("i", "")
                    speed = speed.replace(" ", "")
                    speed = re.sub(r'(\d)([A-Za-z])', r'\1 \2', speed)

                    speed_label_text_speed = speed
                    speed_label_text_percentage = _("{number}%").replace("{number}", str(progress))
                    progress = float(progress)

                    speed_bytes = 0
                    speed = speed.split(" ")
                    if speed[1] == "KB/s":
                        speed_bytes = float(speed[0]) * 1024
                    elif speed[1] == "MB/s":
                        speed_bytes = float(speed[0]) * 1024 * 1024
                    elif speed[1] == "GB/s":
                        speed_bytes = float(speed[0]) * 1024 * 1024 * 1024
                    
                    self.speed = round(speed_bytes)

                    if speed != 0:
                        download_remaining_string = str(video_object['_eta_str'])
                        download_remaining_string = self.app.escape_special_characters(download_remaining_string)
                
                except:
                    pass
            
            temp_file = video_object.get('tmpfilename')
            if temp_file and temp_file not in self.download_temp_files:
                self.download_temp_files.append(temp_file)
                self.video_options["temp_files"] = json.dumps(self.download_temp_files)
                os.remove(self.state_file)
                self.save_state(False)

            if self.video_download_progress_previous > progress + 50:
                self.video_download_stage = 1

            self.video_download_progress_previous = progress

            if self.video_download_combined == True:
                if self.video_download_stage == 0:
                    speed_label_text = _("Part {indicator}").replace("{indicator}", "1 / 2") + "  ·  "
                elif self.video_download_stage == 1:
                    speed_label_text = _("Part {indicator}").replace("{indicator}", "2 / 2") + "  ·  "

        speed_label_text = f"{speed_label_text}{speed_label_text_percentage}  ·  {speed_label_text_speed}  ·  {download_remaining_string} {_('remaining')}"

        GLib.idle_add(self.progress_bar.set_fraction, progress / 100)

        if self.is_complete == False:
            GLib.idle_add(self.speed_label.set_text, speed_label_text)

    def pause(self, change_pause_button_icon):
        if self.download:
            if change_pause_button_icon == False:

                if self.mode == "regular":
                    if self.download.is_paused == False:

                        if self.app.terminating == False:
                            self.paused = True
                            change_pause_button_icon = True
                        
                        i = 0

                        while True:
                            try:
                                self.download.pause()
                                print ("Download paused.")
                                break
                                
                            except:
                                i += 1

                                if i == 10:
                                    print("Can't pause, cancelling without deleting files")
                                    self.stop(False)

                                time.sleep(1)

                        self.save_state(True)
                
                elif self.mode == "video":
                    if self.video_pause_event.is_set():

                        if self.app.terminating == False:
                            self.paused = True
                            change_pause_button_icon = True

                        self.video_pause_event.clear()
                        print ("Download paused.")

                        self.save_state(True)
            
            self.paused_because_exceeds_limit = False
            
            if change_pause_button_icon:
                self.pause_button.get_child().set_from_icon_name("media-playback-start-symbolic")
            
            check_for_all_paused(self.app)

    def resume(self):
        if self.download:
            change_pause_button_icon = False

            if self.mode == "regular":
                if self.download.is_paused == True:

                    self.paused = False
                    change_pause_button_icon = True

                    try:
                        self.download.resume()
                        print ("Download resumed.")
                        self.save_state(True)

                    except:
                        try:
                            GLib.idle_add(self.speed_label.set_text, _("An error occurred:") + " " + self.download.error_message.split("status=")[1])
                            print ("An error occurred when resuming. " + self.download.error_message.split("status=")[1])
                        except:
                            pass
            
            elif self.mode == "video":
                if self.video_pause_event.is_set() == False:

                    self.paused = False
                    change_pause_button_icon = True

                    self.video_pause_event.set()
                    print ("Download resumed.")

                    self.save_state(True)
            
            if change_pause_button_icon:
                self.pause_button.get_child().set_from_icon_name("media-playback-pause-symbolic")
        
        check_for_all_paused(self.app)

    def stop(self, deletefiles):
        if self.download:
            if self.mode == "regular":
                downloadgid = self.download.gid
                downloadname = self.download.name
                istorrent = self.download.is_torrent

                self.download.remove(force=True)

                if (deletefiles == True):
                    if os.path.exists(os.path.join(self.app.appconf["download_directory"], (downloadgid + ".varia"))):
                        os.remove(os.path.join(self.app.appconf["download_directory"], (downloadgid + ".varia")))
                    
                    if istorrent == False:
                        if os.path.exists(os.path.join(self.downloaddir, downloadname)):
                            try:
                                os.remove(os.path.join(self.downloaddir, downloadname))
                            except:
                                pass
                    
                    for file in self.download_temp_files:
                        print(file.path)

                        if os.path.exists(file.path):
                            file_parentdir = file.path.parent.absolute()

                            if os.path.isfile(file.path):
                                try:
                                    os.remove(file.path)
                                except:
                                    pass
                            elif os.path.isdir(file.path):
                                try:
                                    os.rmdir(file.path)
                                except:
                                    pass
                            
                            if file_parentdir is not self.downloaddir and os.listdir(file_parentdir) == []:
                                os.rmdir(file_parentdir)

                print ("Download stopped.")
            
            elif self.mode == "video":
                self.video_pause_event.clear()
                self.video_stop_event.set()

                if hasattr(self, "youtubedl_thread"):
                    ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(self.youtubedl_thread.ident), ctypes.py_object(SystemExit))

                if "temp_files" in self.video_options:
                    stored_download_temp_files = json.loads(self.video_options["temp_files"])
                    print("stored temp")
                    print(stored_download_temp_files)
                    for stored_video_temp_file in stored_download_temp_files:
                        if stored_video_temp_file not in self.download_temp_files:
                            self.download_temp_files.append(stored_video_temp_file)

                for file_path in self.download_temp_files:
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            pass
            
            if os.path.exists(self.state_file):
                os.remove(self.state_file)
        
        self.download_temp_files.clear()
        self.download = None
        self.app.downloads.remove(self)

        # Disable "Exit on Completion" and "Shutdown on Completion" options if no downloads are left
        if len(self.app.downloads) == 0:
            self.app.shutdown_action.set_enabled(False)
            self.app.exit_action.set_enabled(False)

            from download.listen import raise_exit_dialog, raise_shutdown_dialog
            if (self.app.shutdown_dialog_raised == False) and (self.app.shutdown_mode == True):
                self.app.shutdown_dialog_raised = True
                raise_shutdown_dialog(self.app, self.app.variaapp)

            if (self.app.exit_mode == True) and (self.app.exit_dialog_raised == False):
                self.app.exit_dialog_raised = True
                raise_exit_dialog(self.app, self.app.variaapp)
        
        self = None
        return

    def save_state(self, override):
        if self.download:
            state = {
                'url': self.url,
                'filename': self.downloadname,
                'type': self.mode,
                'video_options': json.dumps(self.video_options),
                'paused': self.paused,
                'index': self.app.downloads.index(self),
                'dir': self.downloaddir
            }

            if self.mode == "regular":
                save_filename = self.download.gid

            elif self.mode == "video":
                save_filename = base64.b64encode(self.url.encode('ascii')).decode('ascii').replace("/", "")
            
            if override == False:
                while True:
                    if os.path.isfile(os.path.join(self.app.appconf["download_directory"], f'{save_filename}.varia')):
                        save_filename += "a"
                    else:
                        break

            with open(os.path.join(self.app.appconf["download_directory"], f'{save_filename}.varia'), 'w') as f:
                json.dump(state, f)

            print ("State saved for download.")

            if self.app.terminating == True:
                self.cancelled = True
            
            self.state_file = os.path.join(self.app.appconf["download_directory"], f'{save_filename}.varia')

    def return_gid(self):
        if self.download:
            return self.download.gid

    def return_is_paused(self):
        if self.download:
            if self.mode == "regular":
                if self.download.is_paused:
                    return True
                else:
                    return False
            
            elif self.mode == "video":
                if self.video_pause_event.is_set() == False:
                    return True
                else:
                    return False
                
    def set_complete(self):
        GLib.idle_add(self.speed_label.set_text, _("Download complete."))
        GLib.idle_add(self.pause_button.set_visible, False)
        self.cancelled = True
        self.app.filter_download_list("no", self.app.applied_filter)
        self.progress_bar.set_fraction(1)
        self.progress_bar.add_css_class("success")
        self.is_complete = True
    
    def set_failed(self, fraction):
        if fraction is not None:
            self.progress_bar.set_fraction(fraction)

        self.progress_bar.add_css_class("error")
        self.cancelled = True

        if (self.download.error_code == "24"):
            self.speed_label.set_text(_("Authorization failed."))

        else:
            self.speed_label.set_text(_("An error occurred:") + " " + str(self.download.error_code))

        self.stop(False)
        GLib.idle_add(self.pause_button.set_visible, False)
        self.app.filter_download_list("no", self.app.applied_filter)