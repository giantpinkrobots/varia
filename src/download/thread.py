import ctypes
from gi.repository import GLib
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
import math

class DownloadThread(threading.Thread):
    def __init__(self, app, url, actionrow, downloadname, download, mode, video_options, paused, dir, percentage):
        threading.Thread.__init__(self)
        self.api = app.api
        self.downloaddir = dir
        self.url = url
        self.speed_label = actionrow.speed_label
        self.download = download
        self.auth = app.appconf["auth"]
        self.auth_username = app.appconf["auth_username"]
        self.auth_password = app.appconf["auth_password"]
        self.actionrow = actionrow
        self.app = app
        self.cancelled = False
        self.mode = mode
        self.speed = 0
        self.percentage_number = percentage
        self.paused_because_exceeds_limit = False
        self.total_file_size_text = ""
        self.download_message_shown = False
        self.download_details = {
            'type': _("Regular") if mode == "regular" else _("Video / Audio"),
            'status': _("Downloading"),
            'remaining': "∞",
            'download_speed': "0 B/s",
            'percentage': _("{number}%").replace("{number}", str(self.percentage_number)),
            'message': "",
            'completed_length': 0,
            'upload_length': 0,
            'torrent_seeding_speed': "0 B/s",
            'torrent_peers': []
        }

        if downloadname:
            self.downloadname = downloadname
        else:
            self.downloadname = ""

        try:
            self.filepath = os.path.join(app.appconf["download_directory"], downloadname)
        
        except:
            self.filepath = None
        
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

        self.retry = False

    def is_valid_url(self):
        try:
            result = urlparse(self.url)
            if not ((self.url[0:7] == "http://") or (self.url[0:8] == "https://")):
                self.url = "http://" + self.url
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def run(self):
        self.download_message_shown = False

        if (self.url == "sus"):
            try:
                # Lol nice - Caleb (N0tACyb0rg)
                GLib.idle_add(self.show_message("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣤⣤⣤⣀⣀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣼⠟⠉⠉⠉⠉⠉⠉⠉⠙⠻⢶⣄⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣾⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⣷⡀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⡟⠀⣠⣶⠛⠛⠛⠛⠛⠛⠳⣦⡀⠀⠘⣿⡄⠀⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⠁⠀⢹⣿⣦⣀⣀⣀⣀⣀⣠⣼⡇⠀⠀⠸⣷⠀⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⡏⠀⠀⠀⠉⠛⠿⠿⠿⠿⠛⠋⠁⠀⠀⠀⠀⣿⡄⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⡇⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⣸⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⣿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣧⠀\n⠀⠀⠀⠀⠀⠀⠀⢸⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⠀\n⠀⠀⠀⠀⠀⠀⠀⣾⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀\n⠀⠀⠀⠀⠀⠀⠀⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀\n⠀⠀⠀⠀⠀⠀⢰⣿⠀⠀⠀⠀⣠⡶⠶⠿⠿⠿⠿⢷⣦⠀⠀⠀⠀⠀⠀⠀⣿⠀\n⠀⠀⣀⣀⣀⠀⣸⡇⠀⠀⠀⠀⣿⡀⠀⠀⠀⠀⠀⠀⣿⡇⠀⠀⠀⠀⠀⠀⣿⠀\n⣠⡿⠛⠛⠛⠛⠻⠀⠀⠀⠀⠀⢸⣇⠀⠀⠀⠀⠀⠀⣿⠇⠀⠀⠀⠀⠀⠀⣿⠀\n⢻⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣼⡟⠀⠀⢀⣤⣤⣴⣿⠀⠀⠀⠀⠀⠀⠀⣿⠀\n⠈⠙⢷⣶⣦⣤⣤⣤⣴⣶⣾⠿⠛⠁⢀⣶⡟⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡟⠀\n⠀⠀⠀⠀⠉⠉⠉⠉⠉⠀⠀⠀⠀⠀⠈⣿⣆⡀⠀⠀⠀⠀⠀⠀⢀⣠⣴⡾⠃⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠛⠻⢿⣿⣾⣿⡿⠿⠟⠋⠁⠀⠀⠀"))
            except:
                pass
            GLib.idle_add(self.actionrow.pause_button.set_visible, False)
            GLib.idle_add(self.actionrow.progress_bar.set_visible, False)
            GLib.idle_add(self.actionrow.info_button.set_visible, False)
            return
        
        download_options = {}

        if self.url.startswith("magnet:"):
            if self.app.appconf["torrent_enabled"] == "1":
                download_options["dir"] = self.app.appconf["torrent_download_directory"]
                download_options["follow_torrent"] = "true"
                self.downloaddir = self.app.appconf["torrent_download_directory"]
                self.download_details['type'] = _("Torrent")

            else:
                try:
                    GLib.idle_add(self.show_message, _("Torrenting is disabled."))
                    print("Error: Can't add magnet link because torrenting is disabled.")
                except:
                    pass
                return

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
        self.app.check_all_status()

        if self.percentage_number > 0:
            GLib.idle_add(self.actionrow.progress_bar.set_fraction, self.percentage_number / 100)
            GLib.idle_add(self.actionrow.percentage_label.set_text, self.download_details['percentage'])

        # Regular download, use aria2p:
        if self.mode == "regular":

            if self.downloadname != None:
                download_options["out"] = self.downloadname

            if self.download == None:
                self.download = self.api.add_uris([self.url], options=download_options)

            if self.app.scheduler_currently_downloading and self.paused == False and self.download.gid:
                if self.download.is_paused:
                    self.download.resume()

                self.download_details['status'] = _("Downloading")

            else:
                self.pause(True)

            if self.download.is_torrent:
                self.download_details['type'] = _("Torrent")

            else:
                self.download_details['type'] = _("Regular")
            
            self.previous_filename = ""
            self.app.filter_download_list("no", self.app.applied_filter)
            download_began = False
            self.filepath = os.path.join(self.app.appconf["download_directory"], self.downloadname)

            if self.retry == False:
                self.save_state()

            print("Download added. | " + self.download.gid + "\n" + self.downloaddir + "\n" + self.url)
            print(download_options)

            while (self.cancelled == False):
                try:
                    self.download.update()

                    if self.download.is_paused:
                        self.download_details['status'] = _("Paused")
                    
                    else:
                        self.download_details['status'] = _("Downloading")

                    try:
                        self.total_file_size_text = self.download.total_length_string(True) # Get human readable format
                    except:
                        pass

                    if download_began == False and self.download.is_active:
                        self.actionrow.pause_button.get_child().set_from_icon_name("media-playback-pause-symbolic")
                        download_began = True
                    
                    if (self.download.is_torrent and self.download.name.startswith("[METADATA]")) == False and self.downloadname != self.download.name:
                        self.downloadname = self.download.name
                        self.save_state()
                        self.filepath = os.path.join(self.app.appconf["download_directory"], self.downloadname)
                    
                    if self.actionrow.filename_label.get_text() != self.downloadname:
                        GLib.idle_add(self.actionrow.filename_label.set_text, self.download.name)

                    self.update_labels_and_things(None)
                    if ((self.download.is_complete) and (self.download.is_metadata == False)):
                        print('Download complete: ' + self.download.gid)
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

            self.download_details['type'] = _("Video / Audio")

            self.total_file_size_text = self.video_options['filesize_to_show']

            video_options_final = self.video_options.copy()
            video_options_final['progress_hooks'] = [self.update_labels_and_things]
            video_options_final['outtmpl'] = os.path.join(self.downloaddir, self.downloadname)
            video_options_final['continuedl'] = True
            video_options_final['ffmpeg_location'] = self.app.ffmpegexec

            if self.app.appconf["remote_time"] == "0": # Don't take the video's timestamp if Remote Time is disabled
                video_options_final['no-mtime'] = True

            if self.app.appconf["cookies_txt"] == "1":
                video_options_final['cookiefile'] = os.path.join(self.app.appdir, 'cookies.txt')
            
            if '+' in video_options_final['format']:
                self.video_download_combined = True

            self.download = YoutubeDL(video_options_final)
            GLib.idle_add(self.actionrow.filename_label.set_text, self.downloadname)

            if self.retry == False:
                self.save_state()
            
            if self.app.appconf["schedule_enabled"] == 1 and self.app.scheduler_currently_downloading == False:
                self.pause(False)
            
                while True:
                    if self.app.scheduler_currently_downloading == True:
                        self.resume()
                        break
                    time.sleep(1)
            
            if self.paused:
                self.pause(True)
            
            while self.paused:
                time.sleep(0.25)
            
            GLib.idle_add(self.speed_label.set_text, _("Starting download..."))

            def youtubedl_download_start():
                try:
                    self.download.download([self.url])
                except SystemExit:
                    print("SystemExit received by yt_dlp thread")
                    self.video_stop_event.clear()
                    self.cancelled = True
                except Exception as e:
                    self.show_message(f"{_("An error occurred:")} {self.app.escape_special_characters(str(e))}")
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

    def show_message(self, message):
        print(f'Download message shown: {message}')
        GLib.idle_add(self.speed_label.set_text, message)
        self.download_details['message'] = message
        self.download_message_shown = True
    
    def set_actionrow_tooltip_text(self):
        GLib.idle_add(self.actionrow.set_tooltip_text, _("Download item")
                            + "\n" + _("File Name") + ": " + self.downloadname
                            + "\n" + _("Type") + ": " + self.download_details['type']
                            + "\n" + _("Status") + ": " + self.download_details['status']
                            + "\n" + self.download_details['percentage'])

    def update_labels_and_things(self, video_object):
        speed_label_text = ""
        self.speed = 0
        progress = self.video_download_progress_previous
        download_remaining_string = "∞"
        percentage_label_text = ""
        speed_label_text_speed = ""

        if self.mode == "regular":
            progress = self.download.progress

            if progress > 0.0:
                speed = self.download.download_speed
                self.speed = speed

                if self.download.is_torrent:
                    self.download_details['torrent_peers'] = self.app.api.client.call("aria2.getPeers", [self.download.gid])
                    self.download_details['completed_length'] = self.download.completed_length
                    self.download_details['upload_length'] = self.download.upload_length

                    if self.download.seeder:
                        if self.app.appconf["torrent_seeding_enabled"] == "1":
                            GLib.idle_add(self.show_message(_("Seeding torrent")))
                        else:
                            GLib.idle_add(self.set_complete)
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
                
                percentage_label_text = _("{number}%").replace("{number}", str(round(progress)))
                
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
                    percentage_label_text = _("{number}%").replace("{number}", str(progress))
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
                self.save_state()

            if self.video_download_progress_previous > progress + 50:
                self.video_download_stage = 1

            self.video_download_progress_previous = progress

            if self.video_download_combined == True:
                if self.video_download_stage == 0:
                    percentage_label_text = _("Part {indicator}").replace("{indicator}", "1 / 2") + "  ·  " + percentage_label_text
                elif self.video_download_stage == 1:
                    percentage_label_text = _("Part {indicator}").replace("{indicator}", "2 / 2") + "  ·  " + percentage_label_text
        
        speed_label_text = f"{speed_label_text}{self.total_file_size_text}  ·  {speed_label_text_speed}  ·  {download_remaining_string} {_('remaining')}"
        self.download_details['message'] = ""

        self.set_actionrow_tooltip_text()

        if progress > 0:
            self.percentage_number = progress

        if self.is_complete == False:
            if progress > 0:
                GLib.idle_add(self.actionrow.progress_bar.set_fraction, progress / 100)
                GLib.idle_add(self.actionrow.percentage_label.set_text, percentage_label_text)
                self.download_details['percentage'] = percentage_label_text

            GLib.idle_add(self.speed_label.set_text, speed_label_text)
            self.download_details['remaining'] = download_remaining_string
            self.download_details['download_speed'] = speed_label_text_speed

    def pause(self, change_pause_button_icon):
        if self.download and self.is_complete == False:
            if self.mode == "regular":
                try:
                    self.download.pause()
                except:
                    pass
            
            elif self.mode == "video":
                self.video_pause_event.clear()

            if self.app.terminating == False:
                self.paused = True
                self.app.check_all_status()
                change_pause_button_icon = True

            print ("Download paused.")
            self.save_state()
            
            self.paused_because_exceeds_limit = False
            
            if change_pause_button_icon:
                self.actionrow.pause_button.get_child().set_from_icon_name("media-playback-start-symbolic")
                self.actionrow.pause_button.set_tooltip_text(_("Resume"))

            self.download_details['status'] = _("Paused")

    def resume(self):
        if self.download and self.is_complete == False:
            change_pause_button_icon = False

            if self.mode == "regular":
                if self.download.is_paused == True:

                    self.paused = False
                    change_pause_button_icon = True

                    try:
                        self.download.resume()
                        print ("Download resumed.")
                        self.save_state()

                    except:
                        try:
                            self.show_message(_("An error occurred:") + " " + self.download.error_message.split("status=")[1])
                            print ("An error occurred when resuming. " + self.download.error_message.split("status=")[1])
                        except:
                            pass
            
            elif self.mode == "video":
                if self.video_pause_event.is_set() == False:

                    self.paused = False
                    change_pause_button_icon = True

                    self.video_pause_event.set()
                    print ("Download resumed.")

                    self.save_state()
            
            if change_pause_button_icon:
                self.actionrow.pause_button.get_child().set_from_icon_name("media-playback-pause-symbolic")
                self.actionrow.pause_button.set_tooltip_text(_("Pause"))
        
        self.app.check_all_status()

        self.download_details['status'] = _("Downloading")

    def video_remove_temp_files(self):
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

    def stop(self):
        if self.download:
            if self.mode == "regular":
                downloadgid = self.download.gid
                downloadname = self.download.name
                istorrent = self.download.is_torrent

                try:
                    self.download.remove(force=True)
                except:
                    print('Download couldn\'t be removed, probably already removed.')

                if ((istorrent and self.download.seeder) or self.download.is_complete) == False: # Delete files if incomplete

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

                self.video_remove_temp_files()

            if os.path.exists(self.state_file):
                os.remove(self.state_file)
        
        self.download_temp_files.clear()

        self.app.download_list.remove(self.actionrow)
        self.app.downloads.remove(self)
        self.download = None

        self.app.check_all_status()

        self = None
        return

    def save_state(self):
        if self.download:
            state = {
                'url': self.url,
                'filename': self.downloadname,
                'type': self.mode,
                'video_options': json.dumps(self.video_options),
                'paused': self.paused,
                'index': self.app.downloads.index(self),
                'dir': self.downloaddir,
                'percentage': math.floor(self.percentage_number)
            }

            if self.mode == "regular":
                save_filename = self.download.gid

            elif self.mode == "video":
                save_filename = base64.b64encode(self.url.encode('ascii')).decode('ascii').replace("/", "")
            
            if os.path.isfile(os.path.join(self.app.appconf["download_directory"], f'{save_filename}.varia')):
                os.remove(os.path.join(self.app.appconf["download_directory"], f'{save_filename}.varia'))

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
        self.is_complete = True
        self.cancelled = True
        GLib.idle_add(self.speed_label.set_text, _("Download complete."))
        self.cancelled = True
        self.app.filter_download_list("no", self.app.applied_filter)
        self.actionrow.progress_bar.set_fraction(1)
        self.actionrow.progress_bar.add_css_class("success")

        self.download_details['status'] = _("Completed")
        self.download_details['remaining'] = ""
        self.download_details['download_speed'] = ""

        if self.mode == "regular":
            is_seeding = self.download.is_torrent and self.download.seeder
            if is_seeding == False and os.path.exists(os.path.join(self.downloaddir,(self.download.gid + ".varia"))):
                os.remove(os.path.join(self.downloaddir,(self.download.gid + ".varia")))

        elif self.mode == "video":
            self.video_remove_temp_files()

        if os.path.exists(self.state_file):
            os.remove(self.state_file)
        
        GLib.idle_add(self.actionrow.stop_button.remove_css_class, "destructive-action")
        GLib.idle_add(self.actionrow.stop_button.set_icon_name, "process-stop-symbolic")
        GLib.idle_add(self.actionrow.percentage_label.set_visible, False)
        GLib.idle_add(self.actionrow.pause_button.set_open_mode, self.actionrow.pause_button, self.app, self)
    
    def set_failed(self, fraction):
        if fraction is not None:
            self.actionrow.progress_bar.set_fraction(fraction)

        self.actionrow.progress_bar.add_css_class("error")
        self.cancelled = True

        if self.mode == "regular":
            if (self.download.error_code == "24"):
                self.show_message(_("Authorization failed."))

            else:
                self.show_message(_("An error occurred:") + " " + str(self.download.error_code))
        
        self.download_details['status'] = _("Failed")
        self.download_details['remaining'] = ""
        self.download_details['download_speed'] = ""

        GLib.idle_add(self.actionrow.pause_button.set_retry_mode, self.actionrow.pause_button, self.app, self)
        self.app.filter_download_list("no", self.app.applied_filter)
