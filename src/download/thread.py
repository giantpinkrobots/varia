from __future__ import annotations
import ctypes
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
import subprocess
import pathlib
import libtorrent as lt
from typing import Any, Callable
from download.runtime import DownloadRuntime
from formatting import escape_special_characters, format_binary_size, \
    format_eta, format_percentage, format_speed, parse_ytdlp_percentage, parse_ytdlp_speed

class DownloadThread(threading.Thread):
    def __init__(
        self,
        runtime: DownloadRuntime,
        url,
        downloadname,
        download,
        mode,
        video_options,
        paused,
        dir,
        percentage,
        gid,
        on_event: Callable[[DownloadThread, str, dict[str, Any]], None] | None = None,
        request_directory: Callable[[DownloadThread], None] | None = None,
        request_torrent_selection: Callable[[DownloadThread], None] | None = None,
    ):
        threading.Thread.__init__(self)
        self.api = runtime.api
        self.downloaddir = dir
        self.url = url
        self.download = download
        self.auth = runtime.appconf["auth"]
        self.auth_username = runtime.appconf["auth_username"]
        self.auth_password = runtime.appconf["auth_password"]
        self.runtime = runtime
        self.on_event = on_event
        self.request_directory = request_directory
        self.request_torrent_selection = request_torrent_selection
        self.cancelled = False
        self.mode = mode
        self.speed = 0
        self.percentage_number = percentage
        self.download_gid = gid
        self.paused_because_exceeds_limit = False
        self.total_file_size_text = ""
        self.download_message_shown = False
        self.download_details = {
            'type': _("Regular") if mode == "regular" else _("Video / Audio"),
            'status': _("Downloading"),
            'remaining': "∞",
            'download_speed': "0 B/s",
            'percentage': format_percentage(self.percentage_number, _),
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
            self.filepath = os.path.join(self.downloaddir, downloadname)
        
        except:
            self.filepath = None
        
        self.video_options = video_options
        if self.video_options == None:
            self.video_options = {}

        self.download_temp_files = []
        self.video_stop_event = threading.Event()
        self.video_pause_event = threading.Event()
        self.video_pause_event.set()
        self.directory_selection_event = threading.Event()
        self.video_status = "idle"
        self.video_download_combined = False
        self.video_download_stage = 0
        self.video_download_progress_previous = 0
        self.video_download_is_playlist = False
        self.torrent_instance = None

        self.state_file = ""
        self.is_complete = False
        self.paused = paused
        self.currently_downloading = False
        self.extracting_archive = False
        self.cancel_extraction = False
        self.extract_complete = False

        self.retry = False
        self._save_timer = None

    def emit_event(self, event, **payload):
        if self.on_event is not None:
            self.on_event(self, event, payload)

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
                self.show_message("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣤⣤⣤⣀⣀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣼⠟⠉⠉⠉⠉⠉⠉⠉⠙⠻⢶⣄⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣾⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⣷⡀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⡟⠀⣠⣶⠛⠛⠛⠛⠛⠛⠳⣦⡀⠀⠘⣿⡄⠀⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⠁⠀⢹⣿⣦⣀⣀⣀⣀⣀⣠⣼⡇⠀⠀⠸⣷⠀⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⡏⠀⠀⠀⠉⠛⠿⠿⠿⠿⠛⠋⠁⠀⠀⠀⠀⣿⡄⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⡇⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⣸⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⣿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣧⠀\n⠀⠀⠀⠀⠀⠀⠀⢸⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⠀\n⠀⠀⠀⠀⠀⠀⠀⣾⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀\n⠀⠀⠀⠀⠀⠀⠀⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀\n⠀⠀⠀⠀⠀⠀⢰⣿⠀⠀⠀⠀⣠⡶⠶⠿⠿⠿⠿⢷⣦⠀⠀⠀⠀⠀⠀⠀⣿⠀\n⠀⠀⣀⣀⣀⠀⣸⡇⠀⠀⠀⠀⣿⡀⠀⠀⠀⠀⠀⠀⣿⡇⠀⠀⠀⠀⠀⠀⣿⠀\n⣠⡿⠛⠛⠛⠛⠻⠀⠀⠀⠀⠀⢸⣇⠀⠀⠀⠀⠀⠀⣿⠇⠀⠀⠀⠀⠀⠀⣿⠀\n⢻⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣼⡟⠀⠀⢀⣤⣤⣴⣿⠀⠀⠀⠀⠀⠀⠀⣿⠀\n⠈⠙⢷⣶⣦⣤⣤⣤⣴⣶⣾⠿⠛⠁⢀⣶⡟⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡟⠀\n⠀⠀⠀⠀⠉⠉⠉⠉⠉⠀⠀⠀⠀⠀⠈⣿⣆⡀⠀⠀⠀⠀⠀⠀⢀⣠⣴⡾⠃⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠛⠻⢿⣿⣾⣿⡿⠿⠟⠋⠁⠀⠀⠀")
            except:
                pass
            self.emit_event("hide_row_controls")
            return
        
        download_options = {}

        if self.url.lower().startswith("magnet:") or self.mode == "torrent": # Is torrent

            if self.runtime.appconf["torrent_enabled"] == "1":
                if self.downloaddir == None:
                    if self.runtime.appconf["download_directory_always_ask"] in ("1", "2"):
                        if not self.select_download_directory():
                            self.cancel_pending_download()
                            return

                    elif self.runtime.appconf["torrent_download_directory_custom_enabled"] == "1":
                        self.downloaddir = self.runtime.appconf["torrent_download_directory"]

                    else:
                        self.downloaddir = self.runtime.appconf["download_directory"]
            
                self.download_details['type'] = _("Torrent")
                self.mode = "torrent"

            else:
                self.show_message(_("Torrenting is disabled."))
                print("Error: Can't add magnet link because torrenting is disabled.")
                return

        else: # Normal download
            if not (self.is_valid_url()):
                try:
                    self.show_message(_("This is not a valid URL."))
                    print("Error: Not a valid url.")
                except:
                    print("Error: Couldn't display 'not a valid url' error, for some reason.")
                return
            try:
                response = requests.head(self.url)
            except Exception as e:
                self.set_failed(None, f"{_("An error occurred:")} {escape_special_characters(str(e))}")
                return

            if ((response.status_code == 401) and (self.auth == '1')):
                if (self.url[0:7] == "http://"):
                    self.url = self.url[:7] + self.auth_username + ":" + self.auth_password + "@" + self.url[7:]
                elif (self.url[0:8] == "https://"):
                    self.url = self.url[:8] + self.auth_username + ":" + self.auth_password + "@" + self.url[8:]
                else:
                    self.url = self.auth_username + ":" + self.auth_password + "@" + self.url
                print ("Authentication enabled.")

            if self.runtime.appconf["remote"] == "1":
                self.downloaddir = self.runtime.appconf["remote_location"]

            elif (self.downloaddir == None) and ((self.runtime.appconf["download_directory_always_ask"] == "1") or (self.runtime.appconf["download_directory_always_ask"] == "3")):
                if not self.select_download_directory():
                    self.cancel_pending_download()
                    return

            elif self.downloaddir == None:
                self.downloaddir = self.runtime.appconf["download_directory"]

        self.emit_event("collection_changed")

        if self.percentage_number > 0:
            self.emit_event("progress", fraction=self.percentage_number / 100, percentage=self.download_details['percentage'])

        self.schedule_state_save()

        # Regular download, use aria2p:
        if self.mode == "regular":

            if self.downloadname != None:
                download_options["out"] = self.downloadname

            if self.downloaddir != None:
                download_options["dir"] = self.downloaddir

            if self.download_gid != None:
                download_options["gid"] = self.download_gid

            if self.download == None:
                self.download = self.api.add_uris([self.url], options=download_options)

            if self.download.gid:
                if self.paused == False and self.runtime.scheduler_currently_downloading == False:
                    self.pause(True)
                
                elif self.paused:
                    self.pause(force=True, save=False)
                    print("Download added in paused state. | " + self.download.gid + "\n" + self.downloaddir + "\n" + self.url)
                
                else:
                    try:
                        self.download.resume()
                    except:
                        pass
                    self.download_details['status'] = _("Downloading")
                    self.currently_downloading = True

            self.download_details['type'] = _("Regular")
            self.change_download_type_icon("regular")
            
            self.previous_filename = ""
            self.emit_event("filter_downloads")
            download_began = False
            self.filepath = os.path.join(self.downloaddir, self.downloadname)

            if self.retry == False:
                self.save_state()

            print("Download added. | " + self.download.gid + "\n" + self.downloaddir + "\n" + self.url)

            self.download_gid = self.download.gid

            while (self.cancelled == False):
                try:
                    self.download.update()

                    try:
                        self.total_file_size_text = self.download.total_length_string(True) # Get human readable format
                    except:
                        pass

                    if download_began == False and self.download.is_active:
                        self.emit_event("pause_button", paused=False)
                        download_began = True
                    
                    if self.downloadname != self.download.name:
                        self.downloadname = self.download.name
                        self.save_state()
                        self.filepath = os.path.join(self.downloaddir, self.downloadname)
                    
                    if self.downloadname:
                        self.emit_event("filename", value=self.download.name)

                    self.update_labels_and_things(None)

                    if self.download.is_torrent and len(self.download.files) > 0 and not self.torrent_file_select_completed:
                        if self.download.is_metadata:
                            while (self.download.is_metadata):
                                continue

                        self.download.pause()
                        self.select_torrent_files()

                    elif self.download.status == "complete":
                        print('Download complete: ' + self.download.gid)
                        self.set_complete()
                        return

                    elif (self.download.status == "error"):
                        self.set_failed(None)
                        return

                except:
                    return

                time.sleep(0.5)

        # Torrent download, use libtorrent
        elif self.mode == "torrent":
            self.download = True
            self.download_details['type'] = _("Torrent")
            self.change_download_type_icon("torrent")
            self.torrent_file_select_completed = False

            try:
                resume_data = base64.b64decode(self.downloadname)
                try:
                    lt.read_resume_data(resume_data)
                except RuntimeError:
                    resume_data = None
            except:
                resume_data = None

            if resume_data != None:
                torrent_params = lt.read_resume_data(resume_data)
                if self.paused:
                    torrent_params.flags |= lt.torrent_flags.paused
                else:
                    torrent_params.flags &= ~lt.torrent_flags.paused
                self.torrent_instance = self.runtime.ltsession.add_torrent(torrent_params)

            else:
                if self.url.lower().startswith("magnet:"):
                    torrent_params = {
                        "save_path": self.downloaddir
                    }

                    self.torrent_instance = lt.add_magnet_uri(
                        self.runtime.ltsession,
                        self.url,
                        torrent_params
                    )

                else:
                    print(self.url)
                    torrent_params = {
                        "save_path": self.downloaddir,
                        "ti": lt.torrent_info(self.url)
                    }

                    self.torrent_instance = self.runtime.ltsession.add_torrent(torrent_params)

                while(self.torrent_instance.status().has_metadata == False):
                    continue

                if self.torrent_instance.torrent_file():
                    self.url = lt.make_magnet_uri(self.torrent_instance.torrent_file())

                self.torrent_instance.pause()
                self.select_torrent_files()

            if self.paused == False and self.runtime.scheduler_currently_downloading == False:
                self.pause(True)

            elif self.paused:
                self.pause(force=True, save=False)

            if self.retry == False:
                self.save_state()

            while (self.cancelled == False and self.runtime.terminating == False):
                self.update_labels_and_things(None)

                time.sleep(0.5)

        # Video/audio download, use yt_dlp:
        elif self.mode == "video" or self.mode == "playlist":
            self.video_object = None
            video_options_final = self.video_options.copy()

            if self.mode == "playlist":
                self.mode = "video"

                self.change_download_type_icon("playlist")

                if os.path.exists(os.path.join(self.downloaddir, self.downloadname)) == False:
                    os.mkdir(os.path.join(self.downloaddir, self.downloadname))

                self.downloaddir = os.path.join(self.downloaddir, self.downloadname)
                self.video_download_is_playlist = True
                self.video_download_playlist_length = self.video_options['length']
                self.video_download_playlist_completed_ids = []
                video_options_final['outtmpl'] = os.path.join(self.downloaddir, "%(title)s.%(ext)s")

                if self.runtime.appconf["playlist_skip_errors"] == "1":
                    video_options_final['ignoreerrors'] = True

                if video_options_final['type'] == 0:
                    self.video_download_combined = True
                
                self.video_playlist_download_stage = 1
            
            else:
                self.change_download_type_icon("video")

                self.video_download_is_playlist = False
                if '+' in video_options_final['format']:
                    self.video_download_combined = True
                video_options_final['outtmpl'] = os.path.join(self.downloaddir, self.downloadname)

            self.download_details['type'] = _("Video / Audio")
            self.total_file_size_text = self.video_options['filesize_to_show']

            # Use setdefault so explicit video_options passed in by callers are respected
            video_options_final.setdefault('progress_hooks', [self.update_labels_and_things])
            video_options_final.setdefault('continuedl', True)
            # Network/download robustness
            video_options_final.setdefault('retries', 3)
            video_options_final.setdefault('fragment_retries', 3)
            video_options_final.setdefault('skip_unavailable_fragments', True)
            video_options_final.setdefault('no_warnings', True)

            video_options_final.setdefault('ffmpeg_location', self.runtime.ffmpegexec)
            video_options_final.setdefault('js_runtimes', {
                self.runtime.jsruntimeexec['name']: {'path': self.runtime.jsruntimeexec['exec']}
            })

            if os.path.exists(os.path.join(self.runtime.appdir, "cookies_for_ytdlp.txt")):
                video_options_final['cookiefile'] = os.path.join(self.runtime.appdir, "cookies_for_ytdlp.txt")

            if self.runtime.appconf["remote_time"] == '1':
                video_options_final['updatetime'] = True

            self.download = YoutubeDL(video_options_final)
            self.emit_event("filename", value=self.downloadname)

            if self.retry == False:
                self.save_state()
            
            if self.paused == False and self.runtime.scheduler_currently_downloading == False:
                self.pause(True)
            
            elif self.paused:
                self.pause(force=True, save=False)
            
            else:
                self.download_details['status'] = _("Downloading")
                self.currently_downloading = True
            
            self.emit_event("speed_text", value=_("Starting download..."))

            def youtubedl_download_start():
                quit_before_success = False

                try:
                    self.download.download([self.url])

                except SystemExit:
                    print("SystemExit received by yt_dlp thread")
                    self.video_stop_event.clear()
                    self.cancelled = True
                    quit_before_success = True
                    return

                except Exception as e:
                    self.show_message(f"{_("An error occurred:")} {escape_special_characters(str(e))}")
                    self.video_stop_event.clear()
                    self.cancelled = True
                    self.set_failed(None)
                    quit_before_success = True
                    return

                finally:
                    if quit_before_success == False and self.video_object['status'] == "finished":
                        self.set_complete()

            self.youtubedl_thread = threading.Thread(target=youtubedl_download_start)
            self.youtubedl_thread.daemon = True
            self.youtubedl_thread.start()

            while self.video_stop_event.is_set() == False and self.cancelled == False:
                time.sleep(0.5)
            
            self.cancelled = True
            return
    
    def change_download_type_icon(self, type):
        self.emit_event("download_type", value=type)

    def show_message(self, message):
        print(f'Download message shown: {message}')
        self.download_details['message'] = message
        self.download_message_shown = True
        self.emit_event("message", value=message)
    
    def emit_tooltip(self):
        self.emit_event(
            "tooltip",
            value=_("Download item")
            + "\n" + _("File Name") + ": " + self.downloadname
            + "\n" + _("Type") + ": " + self.download_details['type']
            + "\n" + _("Status") + ": " + self.download_details['status']
            + "\n" + self.download_details['percentage'],
        )

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
                
                download_delta = self.download.eta
                if speed != 0:
                    download_remaining_string = format_eta(download_delta.total_seconds())
                
                percentage_label_text = format_percentage(progress, _)
                speed_label_text_speed = format_speed(speed, _)
                
                if self.download.is_torrent and hasattr(self.download, "files"):
                    for file in self.download.files:
                        if file not in self.download_temp_files:
                            self.download_temp_files.append(file)

        elif self.mode == "torrent":
            if self.torrent_instance:
                status = self.torrent_instance.status()

                if self.downloadname != status.name:
                    self.downloadname = status.name
                self.emit_event("filename", value=self.downloadname)

                self.filepath = os.path.join(status.save_path, status.name)

                progress = status.progress * 100.0
                self.speed = status.download_rate

                if self.speed > 0:
                    remaining = status.total_wanted - status.total_wanted_done
                    eta = int(remaining / self.speed)
                    download_remaining_string = format_eta(eta)

                percentage_label_text = format_percentage(progress, _)
                speed_label_text_speed = format_speed(self.speed, _)
                self.total_file_size_text = format_binary_size(status.total_wanted)

                self.download_details["completed_length"] = status.total_wanted_done
                self.download_details["upload_length"] = status.total_upload
                self.download_details["torrent_peers"] = self.torrent_instance.get_peer_info()
                self.download_details["torrent_seeding_speed"] = format_speed(status.upload_rate, _)

                if status.progress == 1.0:
                    self.set_complete()

                elif status.errc.value() != 0:
                    self.set_failed(None)

        elif self.mode == "video":
            self.video_object = video_object

            if (not video_object['status']) or (video_object['status'] == "error"):
                if self.video_download_is_playlist and self.runtime.appconf["playlist_skip_errors"] == "1":
                    pass

                else:
                    self.video_status = "error"
                    self.set_failed(progress / 100)

            elif video_object['status'] == "finished":
                if self.video_download_is_playlist == False:
                    if self.video_download_combined == True:
                        if self.video_download_stage == 0:
                            self.video_download_stage = 1
                        
                        else:
                            self.video_status = "finished"
                            self.set_complete()

                    else:
                        self.video_status = "finished"
                        self.set_complete()

            elif video_object['status'] == "idle":
                self.video_status = "idle"

            self.video_pause_event.wait()

            if self.video_stop_event.is_set():
                raise Exception("Download stopped")
            
            if video_object['status'] == 'downloading':
                self.video_status = "downloading"

                try:
                    progress = parse_ytdlp_percentage(video_object['_percent_str'])
                    percentage_label_text = format_percentage(progress, _)
                    speed_label_text_speed = escape_special_characters(str(video_object['_speed_str']))
                    speed_bytes = parse_ytdlp_speed(video_object['_speed_str'])
                    if speed_bytes is not None:
                        self.speed = round(speed_bytes)
                        speed_label_text_speed = format_speed(self.speed, _)

                    if self.speed > 0:
                        download_remaining_string = escape_special_characters(str(video_object['_eta_str']))
                
                except:
                    pass
            
            temp_file = video_object.get('tmpfilename')
            if temp_file and temp_file not in self.download_temp_files:
                self.download_temp_files.append(temp_file)
                self.video_options["temp_files"] = json.dumps(self.download_temp_files)
                os.remove(self.state_file)
                self.save_state()

            if self.video_download_is_playlist == False and self.video_download_progress_previous > progress + 50:
                self.video_download_stage = 1

            self.video_download_progress_previous = progress
            
            if self.video_download_is_playlist:
                percentage_label_text = _("Part {indicator}").replace("{indicator}", f"{str(video_object["info_dict"].get("playlist_index", ""))} / {self.video_download_playlist_length}") + "  ·  " + percentage_label_text

            elif self.video_download_combined:
                if self.video_download_stage == 0:
                    percentage_label_text = _("Part {indicator}").replace("{indicator}", "1 / 2") + "  ·  " + percentage_label_text
                elif self.video_download_stage == 1:
                    percentage_label_text = _("Part {indicator}").replace("{indicator}", "2 / 2") + "  ·  " + percentage_label_text

        speed_label_text = f"{speed_label_text}{self.total_file_size_text}  ·  {speed_label_text_speed}  ·  {download_remaining_string} {_('remaining')}"
        self.download_details['message'] = ""

        self.emit_tooltip()

        if progress > 0:
            self.percentage_number = progress

        if self.is_complete == False:
            if progress > 0:
                self.emit_event("progress", fraction=progress / 100, percentage=percentage_label_text)
                self.download_details['percentage'] = percentage_label_text

            self.emit_event("speed_text", value=speed_label_text)
            self.download_details['remaining'] = download_remaining_string
            self.download_details['download_speed'] = speed_label_text_speed

    def pause(self, called_by_scheduler = False, force = False, save = True):
        if self.paused and not force:
            return

        if self.download and self.is_complete == False:
            if self.mode == "regular":
                self.download.pause()

            elif self.mode == "torrent":
                self.torrent_instance.pause()
            
            elif self.mode == "video":
                self.video_pause_event.clear()
            
            if self.runtime.terminating == False:
                if called_by_scheduler and self.runtime.scheduler_currently_downloading == False and self.paused == False:
                    self.download_details['status'] = _("Scheduled")

                else:
                    self.download_details['status'] = _("Paused")
                    self.emit_event("pause_button", paused=True)
                    self.paused = True

                self.currently_downloading = False
                self.paused_because_exceeds_limit = False
        
        if self.mode == "video":
            self.emit_tooltip()

        if save:
            self.save_state()
        self.emit_event("collection_changed")

    def resume(self, called_by_scheduler = False):
        if self.download and self.is_complete == False:
            change_button = False

            if called_by_scheduler and self.runtime.scheduler_currently_downloading and self.paused:
                self.download_details['status'] = _("Paused")
            
            elif self.runtime.scheduler_currently_downloading == False and self.paused:
                self.download_details['status'] = _("Scheduled")
                self.paused = False
                change_button = True

            else:
                if self.mode == "regular":
                    if self.download.is_paused:
                        self.download.resume()

                elif self.mode == "torrent":
                    self.torrent_instance.resume()

                elif self.mode == "video":
                    if self.video_pause_event.is_set() == False:
                        self.video_pause_event.set()

                self.currently_downloading = True
                self.download_details['status'] = _("Downloading")
                self.paused = False
                change_button = True
            
            if change_button:
                self.emit_event("pause_button", paused=False)

            self.emit_event("collection_changed")
            self.save_state()

    def stop(self):
        if self.extracting_archive == True:
            self.cancel_extraction = True
            return

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

                    if os.path.exists(os.path.join(self.runtime.appdir, (downloadgid + ".varia"))):
                        os.remove(os.path.join(self.runtime.appdir, (downloadgid + ".varia")))
                    
                    if istorrent == False:
                        if self.downloaddir is not None and os.path.exists(os.path.join(self.downloaddir, downloadname)):
                            try:
                                os.remove(os.path.join(self.downloaddir, downloadname))
                            except:
                                pass
                    
                    for file in self.download_temp_files:
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
                            
                            if self.downloaddir is not None and pathlib.Path(file_parentdir).resolve() != pathlib.Path(self.downloaddir).resolve() and os.listdir(file_parentdir) == []:
                                os.rmdir(file_parentdir)

                print ("Download stopped.")

            elif self.mode == "torrent":
                if self.torrent_instance is not None:
                    self.runtime.ltsession.remove_torrent(self.torrent_instance)
                self.torrent_instance = None
            
            elif self.mode == "video":
                self.video_pause_event.clear()
                self.video_stop_event.set()

                if hasattr(self, "youtubedl_thread"):
                    ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(self.youtubedl_thread.ident), ctypes.py_object(SystemExit))

                self.video_remove_temp_files()

            if os.path.exists(self.state_file):
                os.remove(self.state_file)
        
        self.download_temp_files.clear()

        self.runtime.downloads.remove(self)
        self.download = None
        self.emit_event("removed")
        self.emit_event("collection_changed")

        self = None
        return

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

    def save_state(self):
        if self.download and self.is_complete == False:
            if self.video_download_is_playlist:
                download_type = "playlist"
                download_dir = os.path.join(self.downloaddir, "..")
            else:
                download_type = self.mode
                download_dir = self.downloaddir

            if self.mode == "regular":
                save_filename = self.download.gid
                download_file_name = self.downloadname

            elif self.mode == "torrent":
                self.torrent_instance.save_resume_data()
                resume_data = None
                deadline = time.monotonic() + 2

                while resume_data == None and time.monotonic() < deadline:
                    for alert in self.runtime.ltsession.pop_alerts():
                        if (
                            isinstance(alert, lt.save_resume_data_alert)
                            and alert.handle == self.torrent_instance
                        ):
                            resume_data = lt.write_resume_data_buf(alert.params)
                            break

                    if resume_data != None:
                        break
                    time.sleep(0.01)

                if resume_data == None:
                    print("Timed out waiting for torrent resume data; keeping the previous saved state.")
                    return
                    
                save_filename = base64.b64encode(self.url.encode('ascii')).decode('ascii').replace("/", "")[-20:]
                download_file_name = base64.b64encode(resume_data).decode("ascii")

            elif self.mode == "video":
                save_filename = base64.b64encode(self.url.encode('ascii')).decode('ascii').replace("/", "")[-20:]
                download_file_name = self.downloadname

            state = {
                'url': self.url,
                'filename': download_file_name,
                'type': download_type,
                'video_options': json.dumps(self.video_options),
                'paused': self.paused,
                'index': self.runtime.downloads.index(self),
                'dir': download_dir,
                'percentage': math.floor(self.percentage_number),
                'gid': self.download_gid
            }
            
            if os.path.isfile(os.path.join(self.runtime.appdir, f'{save_filename}.varia')):
                os.remove(os.path.join(self.runtime.appdir, f'{save_filename}.varia'))

            with open(os.path.join(self.runtime.appdir, f'{save_filename}.varia'), 'w') as f:
                json.dump(state, f)

            print ("State saved for download.")

            if self.runtime.terminating == True:
                self.cancelled = True
            
            self.state_file = os.path.join(self.runtime.appdir, f'{save_filename}.varia')
    
    def extract_archive(self):
        self.emit_event("extraction_started")
        self.download_details["status"] = _("Extracting")
        self.extracting_archive = True
        extract_folder = self.downloadname.rsplit(".", 1)[0]

        while(True):
            if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(self.filepath)), extract_folder)):
                extract_folder = extract_folder + "-1"

            else:
                extract_folder = os.path.join(os.path.dirname(os.path.abspath(self.filepath)), extract_folder)
                break

        sevenzip_extract_command = [
            self.runtime.sevenzexec,
            "x", self.filepath,
            "-o" + extract_folder,
            "-y",
            "-bsp1",
            "-bso1"
        ]

        process = subprocess.Popen(
            sevenzip_extract_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        buffer = ""

        while process.poll() is None:
            if self.cancel_extraction: # If the user presses stop during extraction
                process.kill()
                break

            char = process.stdout.read(1)

            if not char:
                time.sleep(0.01)
                continue

            if char == "\x08": # Remove backspace character
                buffer = buffer[:-1]
                continue

            if char in ("\r", "\n"):
                buffer = ""
                continue

            buffer += char

            match = re.search(r"(\d{1,3})\s*%", buffer)
            if match:
                percent = int(match.group(1))
                percentage_label_text = format_percentage(percent, _)
                self.emit_event("progress", fraction=percent / 100, percentage=percentage_label_text)

        self.extracting_archive = False

        if self.cancel_extraction == False:
            if self.runtime.appconf["extract_archives_delete_archives"] == "1":
                os.remove(self.filepath)
            
            self.filepath = extract_folder

        self.emit_event("extraction_finished")
        self.extract_complete = True
        self.set_complete()
                
    def set_complete(self):
        self.is_complete = True
        self.emit_event("filter_downloads")
        self.download_details['remaining'] = ""
        self.download_details['download_speed'] = ""

        if self.mode == "video":
            self.video_remove_temp_files()
        
        if self.extract_complete == False and self.runtime.appconf["extract_archives"] == "1":
            file_extension = self.downloadname.split('.')[-1].lower()

            if file_extension in self.runtime.supported_archive_formats:
                thread = threading.Thread(target=self.extract_archive, daemon=True)
                thread.start()
                return

        self.emit_tooltip()
        self.download_details['status'] = _("Completed")

        if self.mode == "torrent" and self.torrent_instance.status().is_seeding and self.runtime.appconf["torrent_seeding_enabled"] == "1":
            self.emit_event("speed_text", value=_("Seeding"))
        else:
            self.emit_event("speed_text", value=_("Download complete."))
            self.cancelled = True

            if os.path.exists(self.state_file):
                os.remove(self.state_file)
        
        self.emit_event("completed")
    
    def set_failed(self, fraction, message=None):
        self.cancelled = True

        if message is not None:
            self.show_message(message)

        else:
            if self.mode == "regular":
                if (self.download.error_code == "24"):
                    self.show_message(_("Authorization failed."))

                else:
                    self.show_message(_("An error occurred:") + " " + str(self.download.error_code))
            
            elif self.video_download_is_playlist == True:
                self.mode = "playlist"
        
        self.download_details['status'] = _("Failed")
        self.download_details['remaining'] = ""
        self.download_details['download_speed'] = ""

        self.emit_event("failed", fraction=fraction)
        self.emit_event("filter_downloads")

    def periodically_save_state(self):
        if self.cancelled or self.runtime.terminating:
            return

        self.save_state()
        self.schedule_state_save()

    def schedule_state_save(self):
        if self._save_timer is not None:
            self._save_timer.cancel()
        self._save_timer = threading.Timer(360, self.periodically_save_state)
        self._save_timer.daemon = True
        self._save_timer.start()

    def select_download_directory(self):
        self.new_selected_directory = None
        self.directory_selection_event.clear()
        if self.request_directory is None:
            return False
        self.request_directory(self)
        self.directory_selection_event.wait()
        if self.new_selected_directory is None:
            return False

        self.downloaddir = self.new_selected_directory

        if self.download and self.mode == "regular" and not self.url.lower().startswith("magnet:"):
            self.download.api.client.change_option(self.download.gid, {"dir": self.downloaddir})
            self.download.update()

        return True

    def select_torrent_files(self):
        if self.request_torrent_selection is None:
            raise RuntimeError("Torrent file selection requires a presentation handler.")
        self.selection_event = threading.Event()
        self.request_torrent_selection(self)
        self.selection_event.wait()

    def cancel_pending_download(self):
        self.cancelled = True
        self.stop()