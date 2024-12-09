from gettext import gettext as _
import subprocess
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
import threading
import os
import json

from download.actionrow import on_download_clicked

def on_video_clicked(button, self, entry, DownloadThread):
    url = entry.get_text()
    entry.set_text("")

    # Show loading screen
    loading_dialog = Adw.AlertDialog()
    loading_dialog_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=25)
    loading_dialog.set_child(loading_dialog_box)
    loading_dialog_box.set_margin_top(30)
    loading_dialog_box.set_margin_bottom(30)
    loading_dialog_box.set_margin_start(60)
    loading_dialog_box.set_margin_end(60)
    loading_dialog_spinner = Adw.Spinner()
    loading_dialog_spinner.set_size_request(30, 30)
    loading_dialog_box.append(loading_dialog_spinner)
    loading_dialog_label = Gtk.Label(label=_("Checking video..."))
    loading_dialog_label.get_style_context().add_class("title-1")
    loading_dialog_box.append(loading_dialog_label)
    loading_dialog.set_can_close(False)
    loading_dialog.present(self)

    def format_filesize(filesize):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if filesize < 1024.0:
                return f"{filesize:.2f} {unit}"
            filesize /= 1024.0
        return f"{filesize:.2f} TB"

    def ytdlp_startsubprocess():
        if self.appconf.get("cookies_txt") == "1":
            ytdlp_subprocess_command = ["yt-dlp", "-j", "--cookies", os.path.join(self.appdir, 'cookies.txt'), url]
        else:
            ytdlp_subprocess_command = ["yt-dlp", "-j", url]

        ytdlp_subprocess = subprocess.run(
            ytdlp_subprocess_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if ytdlp_subprocess.returncode != 0:
            print("Error:", ytdlp_subprocess.stderr)

        stdout_json = ytdlp_subprocess.stdout[ytdlp_subprocess.stdout.find("{"):-1]
        
        data = False

        try:
            data = json.loads(stdout_json)
        except json.JSONDecodeError as err:
            print("Error:", err)

        video_formats = []
        audio_formats = []
        combined_formats = []
        matched_formats = []
        
        if data:
            print(data)
            video_title = data.get("title", "?")
            uploader_name = data.get("uploader", "?")

            for fmt in data.get("formats", []):
                print(fmt)
                print("\n\n")
                print(fmt.get("audio_ext"))
                print(fmt.get("video_ext"))
                print(fmt.get("resolution"))
                print("\n\n")

                if fmt.get("ext") == "mhtml" or fmt.get("filesize") == 0:
                    continue
                
                # Video only
                elif fmt.get("audio_ext") == "none":
                    if fmt.get("vbr", 0) == 0:
                        continue

                    video_formats.append({
                        "id": fmt.get("format_id"),
                        "ext": fmt.get("ext"),
                        "resolution": fmt.get("resolution"),
                        "framerate": fmt.get("fps", None),
                        "filesize": fmt.get("filesize"),
                        "url": fmt.get("url"),
                        "bitrate": fmt.get("vbr", "unknown"),
                    })
                    print("video only")

                # Audio only
                elif fmt.get("resolution") == "audio only":
                    if fmt.get("abr", 0) == 0:
                        continue

                    audio_formats.append({
                        "id": fmt.get("format_id"),
                        "ext": fmt.get("ext"),
                        "bitrate": fmt.get("abr", "unknown"),
                        "filesize": fmt.get("filesize"),
                        "url": fmt.get("url"),
                    })
                    print("audio only")

                # Video and audio
                elif fmt.get("video_ext") != "none" and fmt.get("audio_get") != "none":
                    if fmt.get("vbr", 0) == 0 or fmt.get("abr", 0) == 0:
                        continue

                    combined_formats.append({
                        "id": fmt.get("format_id"),
                        "ext": fmt.get("ext"),
                        "resolution": fmt.get("resolution"),
                        "framerate": fmt.get("fps", None),
                        "filesize": fmt.get("filesize"),
                        "url": fmt.get("url"),
                        "bitrate-video": fmt.get("vbr", "unknown"),
                        "bitrate-audio": fmt.get("vbr", "unknown"),
                    })
                    print("combined")

            # Match the video-only streams with the appropriate audio-only streams
            for video in video_formats:
                for audio in audio_formats:
                    if video["ext"] == audio["ext"]:
                        total_size_bytes = (video["filesize"] or 0) + (audio["filesize"] or 0)
                        bitrate = str(video["bitrate"] or "0") + " - " + str(audio["bitrate"] or "0")
                        matched_formats.append((video, audio, total_size_bytes, bitrate))

            for combined in combined_formats:
                combined_size_bytes = combined["filesize"] or 0
                bitrate = str(combined["bitrate-video"] or "0") + " - " + str(combined["bitrate-audio"] or "0")
                matched_formats.append((combined, None, combined_size_bytes, bitrate))
            
            video_formats.reverse()
            audio_formats.reverse()
            matched_formats.reverse()
        
            GLib.idle_add(loading_dialog.set_can_close, True)
            GLib.idle_add(loading_dialog.close)

            video_download_options_preferences_dialog = Adw.PreferencesDialog(title=_("Download Video"))

            page_video_and_audio = Adw.PreferencesPage(title=_("Video and audio"), icon_name="media-playback-start-symbolic")
            video_download_options_preferences_dialog.add(page_video_and_audio)
            group_video_and_audio = Adw.PreferencesGroup(title="\"" + video_title + "\" - " + uploader_name)
            page_video_and_audio.add(group_video_and_audio)

            page_video_only = Adw.PreferencesPage(title=_("Video only"), icon_name="emblem-videos-symbolic")
            video_download_options_preferences_dialog.add(page_video_only)
            group_video_only = Adw.PreferencesGroup(title="\"" + video_title + "\" - " + uploader_name)
            page_video_only.add(group_video_only)

            page_audio_only = Adw.PreferencesPage(title=_("Audio only"), icon_name="emblem-music-symbolic")
            video_download_options_preferences_dialog.add(page_audio_only)
            group_audio_only = Adw.PreferencesGroup(title="\"" + video_title + "\" - " + uploader_name)
            page_audio_only.add(group_audio_only)

            def create_option_actionrow(self, group, title, subtitle, type, download_object, download_name, video_download_options_preferences_dialog, url, DownloadThread):
                video_option_actionrow = Adw.ActionRow()
                video_download_button = Gtk.Button(label=_("Download"))
                video_download_button.get_style_context().add_class("suggested-action")
                video_download_button.set_halign(Gtk.Align.START)
                video_download_button.set_valign(Gtk.Align.CENTER)
                video_option_actionrow.set_title(title)
                video_option_actionrow.set_subtitle(subtitle)
                video_download_button.connect("clicked", lambda clicked, type=type, download_object=download_object, download_name=download_name: on_video_option_download_clicked(self, video_download_options_preferences_dialog, type, download_object, download_name, url, DownloadThread))
                video_option_actionrow.add_suffix(video_download_button)

                group.add(video_option_actionrow)

            for video_only_format in video_formats:
                actionrow_title = _("Video only")
                if video_only_format["resolution"] is not None:
                    actionrow_title += "  ·  " + video_only_format["resolution"]
                if video_only_format["framerate"] is not None:
                    actionrow_title += "@" + str(video_only_format["framerate"])

                actionrow_subtitle = ""
                if video_only_format["ext"] is not None:
                    actionrow_subtitle = video_only_format["ext"]
                if video_only_format["filesize"] is not None:
                    actionrow_subtitle += "  ·  " + str(format_filesize(video_only_format["filesize"]))
                if video_only_format["bitrate"] is not None:
                    actionrow_subtitle += "  ·  " + str(format_filesize(video_only_format["bitrate"]))
                
                create_option_actionrow(self,
                    group_video_only,
                    actionrow_title,
                    actionrow_subtitle,
                    "video",
                    video_only_format,
                    video_title,
                    video_download_options_preferences_dialog, url, DownloadThread
                )
            
            for audio_only_format in audio_formats:
                actionrow_title = _("Audio only")
                
                actionrow_subtitle = ""
                if audio_only_format["ext"] is not None:
                    actionrow_subtitle = audio_only_format["ext"]
                if audio_only_format["filesize"] is not None:
                    actionrow_subtitle += "  ·  " + str(format_filesize(audio_only_format["filesize"]))
                if audio_only_format["bitrate"] is not None:
                    actionrow_subtitle += "  ·  " + str(format_filesize(audio_only_format["bitrate"]))
                
                create_option_actionrow(self,
                    group_audio_only,
                    actionrow_title,
                    actionrow_subtitle,
                    "audio",
                    audio_only_format,
                    video_title,
                    video_download_options_preferences_dialog, url, DownloadThread
                )
            
            for complete_format in matched_formats:
                actionrow_title = _("Video and audio")
                if complete_format[0]["resolution"] is not None:
                    actionrow_title += "  ·  " + complete_format[0]["resolution"]
                if complete_format[0]["framerate"] is not None:
                    actionrow_title += "@" + str(complete_format[0]["framerate"])
                
                actionrow_subtitle = ""
                if complete_format[0]["ext"] is not None:
                    actionrow_subtitle = complete_format[0]["ext"]
                if complete_format[2] is not None:
                    actionrow_subtitle += "  ·  " + format_filesize(complete_format[2])
                if complete_format[3] is not None:
                    actionrow_subtitle += "  ·  " + str(complete_format[3])
                
                create_option_actionrow(self,
                    group_video_and_audio,
                    actionrow_title,
                    actionrow_subtitle,
                    "complete",
                    complete_format,
                    video_title,
                    video_download_options_preferences_dialog, url, DownloadThread
                )
            
            GLib.idle_add(video_download_options_preferences_dialog.present, self)

        else:
            error_body = (
                f"{_("An error occurred:")}\n\n"
                f"• {_("Your IP address may be being blocked. If you have an active VPN connection that might be the cause.")}\n"
                f"• {_("The video platform may not be supported.")}"
            )
            error_dialog = Adw.AlertDialog()
            error_dialog.set_body(error_body)
            error_dialog.add_response("ok",  _("OK"))
            error_dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
            error_dialog.set_close_response("ok")
            GLib.idle_add(error_dialog.present, self)
        
        GLib.idle_add(loading_dialog.set_can_close, True)
        GLib.idle_add(loading_dialog.close)

        return
    
    thread = threading.Thread(target=ytdlp_startsubprocess)
    thread.start()

def on_video_option_download_clicked(self, prefswindow, type, download_object, download_name, url, DownloadThread):
    prefswindow.close()
    print(url)

    if type == "complete":
        id = download_object[1]["id"]
        filename = download_name + "---VariaVideoDownload-AudioStream"
        id2 = download_object[0]["id"]
        filename2 = download_name + "." + download_object[0]["ext"]
    else:
        id = download_object["id"]
        filename = download_name + "." + download_object["ext"]
        id2 = None
        filename2 = None

    loading_dialog = Adw.AlertDialog()
    loading_dialog_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=25)
    loading_dialog.set_child(loading_dialog_box)
    loading_dialog_box.set_margin_top(30)
    loading_dialog_box.set_margin_bottom(30)
    loading_dialog_box.set_margin_start(60)
    loading_dialog_box.set_margin_end(60)
    loading_dialog_spinner = Adw.Spinner()
    loading_dialog_spinner.set_size_request(30, 30)
    loading_dialog_box.append(loading_dialog_spinner)
    loading_dialog_label = Gtk.Label(label=_("Starting download..."))
    loading_dialog_label.get_style_context().add_class("title-1")
    loading_dialog_box.append(loading_dialog_label)
    loading_dialog.set_can_close(False)
    loading_dialog.present(self)

    def ytdlp_startsubprocess(id, filename, id2, filename2, previous_download_thread_gid):
        ytdlp_subprocess_command = ["yt-dlp", "-f", id, "-g", url]

        if self.appconf["cookies_txt"] == "1":
            ytdlp_subprocess_command.extend(["--cookies", os.path.join(self.appdir, 'cookies.txt')])

        ytdlp_subprocess = subprocess.Popen(ytdlp_subprocess_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        ytdlp_subprocess.wait()

        video_download_link = ""

        while True:
            process_return_code = ytdlp_subprocess.poll()
            if process_return_code is not None:
                stdout, stderr = ytdlp_subprocess.communicate()

                if process_return_code == 0:
                    video_download_link = stdout
                
                else:
                    error_body = (
                        f"{_("An error occurred:")}\n\n"
                        f"• {_("Your IP address may be being blocked. If you have an active VPN connection that might be the cause.")}\n"
                        f"• {_("The video platform may not be supported.")}"
                    )
                    error_dialog = Adw.AlertDialog()
                    error_dialog.set_body(error_body)
                    error_dialog.add_response("ok",  _("OK"))
                    error_dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
                    error_dialog.set_close_response("ok")
                    GLib.idle_add(error_dialog.present, self)

                break
                
        if video_download_link != "":
            if id2 == None:
                actionrow_show = True
            else:
                actionrow_show = False
            previous_download_thread_gid = on_download_clicked(None, self, video_download_link, DownloadThread, filename, actionrow_show, previous_download_thread_gid)
            print(previous_download_thread_gid)
        else:
            GLib.idle_add(loading_dialog.set_can_close, True)
            GLib.idle_add(loading_dialog.close)
            return
        
        if id2 is not None:
            ytdlp_startsubprocess(id2, filename2, None, None, previous_download_thread_gid)
        else:
            GLib.idle_add(loading_dialog.set_can_close, True)
            GLib.idle_add(loading_dialog.close)
            return

    thread = threading.Thread(target=lambda: ytdlp_startsubprocess(id, filename, id2, filename2, None))
    thread.start()