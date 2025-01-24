from stringstorage import gettext as _
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
import threading
import os
import yt_dlp

from download.actionrow import on_download_clicked
from download.thread import DownloadThread

def on_video_clicked(button, self, entry):
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
    loading_dialog_label.add_css_class("title-1")
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

        if self.appconf["cookies_txt"] == "1":
            youtube_dl_options = {'cookiefile': os.path.join(self.appdir, 'cookies.txt')}
        else:
            youtube_dl_options = {}

        try:
            with yt_dlp.YoutubeDL(youtube_dl_options) as ydl:
                data = ydl.sanitize_info(ydl.extract_info(url, download=False))

        except Exception as error:
            print(error)
            data = False
            ytdlp_error = str(error)

        video_formats = []
        audio_formats = []
        combined_formats = [] # Combined formats will end up in matched formats at the end
        matched_formats = []
        
        # If everything is correct, start building the lists:
        if data:
            video_title = self.escape_special_characters(data.get("title", "?"))
            uploader_name = data.get("uploader", "?")

            for fmt in data.get("formats", []):

                # If filesize is only approximate, take that as filesize
                if fmt.get("filesize_approx", 0) != 0:
                    fmt["filesize"] = fmt["filesize_approx"]

                # Throw out unnecessary formats
                if fmt.get("ext") == "mhtml" or fmt.get("filesize", 0) == 0:
                    continue
                
                # Video only
                elif fmt["audio_ext"] == "none":
                    if fmt.get("vbr", 0) != 0:
                        video_formats.append({
                            "id": fmt["format_id"],
                            "ext": fmt["ext"],
                            "resolution": fmt["resolution"],
                            "framerate": fmt.get("fps", None),
                            "filesize": fmt["filesize"],
                            "url": fmt["url"],
                            "bitrate": fmt["vbr"],
                        })

                # Audio only
                elif fmt["video_ext"] == "none":
                    if fmt.get("abr", 0) != 0:
                        audio_formats.append({
                            "id": fmt["format_id"],
                            "ext": fmt["ext"],
                            "bitrate": fmt["abr"],
                            "filesize": fmt["filesize"],
                            "url": fmt["url"],
                        })

                # Video and audio
                elif fmt["video_ext"] != "none" and fmt["audio_ext"] != "none":
                    if fmt.get("vbr", 0) != 0 and fmt.get("abr", 0) != 0:
                        combined_formats.append({
                            "id": fmt["format_id"],
                            "ext": fmt["ext"],
                            "resolution": fmt["resolution"],
                            "framerate": fmt.get("fps", None),
                            "filesize": fmt["filesize"],
                            "url": fmt["url"],
                            "bitrate-video": fmt["vbr"],
                            "bitrate-audio": fmt["abr"],
                        })

            # Match the video-only streams with the appropriate audio-only streams
            for video in video_formats:
                for audio in audio_formats:
                    if (video["ext"] == audio["ext"]) or (video["ext"] == "mp4" and audio["ext"] == "m4a"):
                        uncertain_size = False
                        if video["filesize"] == None:
                            video["filesize"] = 0
                            uncertain_size = True
                        if audio["filesize"] == None:
                            audio["filesize"] = 0
                            uncertain_size = True
                        total_size_bytes = video["filesize"] + audio["filesize"]
                        bitrate = str(video["bitrate"]) + " - " + str(audio["bitrate"])
                        matched_formats.append([video, audio, total_size_bytes, bitrate, uncertain_size])

            # Add combined formats to the matched formats list
            for combined in combined_formats:
                combined_size_bytes = combined["filesize"]
                bitrate = str(combined["bitrate-video"]) + " - " + str(combined["bitrate-audio"])
                matched_formats.append([combined, None, combined_size_bytes, bitrate])
            
            # Sort the lists based on their filesize, from biggest to smallest
            video_formats.sort(key=lambda x: x["filesize"], reverse=True)
            audio_formats.sort(key=lambda x: x["filesize"], reverse=True)
            matched_formats.sort(key=lambda x: x[2], reverse=True)

            def remove_duplicates_from_lists(list, mode):
                seen = set()
                deduplicated_list = []
                
                for item in list:
                    if mode == 0:
                        identifier = (item["resolution"], item["bitrate"], item["filesize"])
                        if identifier not in seen:
                            seen.add(identifier)
                            deduplicated_list.append(item)
                    
                    elif mode == 1:
                        identifier = (item["bitrate"], item["filesize"])
                        if identifier not in seen:
                            seen.add(identifier)
                            deduplicated_list.append(item)
                    
                    else:
                        identifier = (item[2], item[3])
                        if identifier not in seen:
                            seen.add(identifier)
                            deduplicated_list.append(item)
                
                return deduplicated_list

            # Remove unnecessary duplicates
            video_formats = remove_duplicates_from_lists(video_formats, 0)
            audio_formats = remove_duplicates_from_lists(audio_formats, 1)
            matched_formats = remove_duplicates_from_lists(matched_formats, 2)

            # Start building the video download dialog
            video_download_options_preferences_dialog = Adw.PreferencesDialog()

            options_available = False

            if len(matched_formats) > 0:
                page_video_and_audio = Adw.PreferencesPage(title=_("Video and audio"), icon_name="media-playback-start-symbolic")
                video_download_options_preferences_dialog.add(page_video_and_audio)
                group_video_and_audio = Adw.PreferencesGroup(title="\"" + video_title + "\" - " + uploader_name)
                page_video_and_audio.add(group_video_and_audio)

                video_download_options_preferences_dialog.set_title(_("Video and audio"))
                options_available = True

            if len(video_formats) > 0:
                page_video_only = Adw.PreferencesPage(title=_("Video only"), icon_name="emblem-videos-symbolic")
                video_download_options_preferences_dialog.add(page_video_only)
                group_video_only = Adw.PreferencesGroup(title="\"" + video_title + "\" - " + uploader_name)
                page_video_only.add(group_video_only)

                video_download_options_preferences_dialog.set_title(_("Video only"))
                options_available = True

            if len(audio_formats) > 0:
                page_audio_only = Adw.PreferencesPage(title=_("Audio only"), icon_name="emblem-music-symbolic")
                video_download_options_preferences_dialog.add(page_audio_only)
                group_audio_only = Adw.PreferencesGroup(title="\"" + video_title + "\" - " + uploader_name)
                page_audio_only.add(group_audio_only)

                video_download_options_preferences_dialog.set_title(_("Audio only"))
                options_available = True

            def create_option_actionrow(self, group, title, subtitle, type, download_object, download_name, video_download_options_preferences_dialog, url, DownloadThread):
                video_option_actionrow = Adw.ActionRow()
                video_download_button = Gtk.Button(label=_("Download"))
                video_download_button.add_css_class("suggested-action")
                video_download_button.set_halign(Gtk.Align.START)
                video_download_button.set_valign(Gtk.Align.CENTER)
                video_option_actionrow.set_title(title)
                video_option_actionrow.set_subtitle(subtitle)
                video_download_button.connect("clicked", lambda clicked, type=type, download_object=download_object, download_name=download_name: on_video_option_download_clicked(self, video_download_options_preferences_dialog, type, download_object, download_name, url))
                video_option_actionrow.add_suffix(video_download_button)

                group.add(video_option_actionrow)

            # For video only formats
            for video_only_format in video_formats:
                actionrow_title = _("Video only")
                if video_only_format["resolution"] is not None:
                    actionrow_title += "  ·  " + video_only_format["resolution"]
                if video_only_format["framerate"] is not None:
                    actionrow_title += "@" + str(round(float(video_only_format["framerate"])))

                actionrow_subtitle = ""
                if video_only_format["ext"] is not None:
                    actionrow_subtitle = video_only_format["ext"]
                if video_only_format["filesize"] is not None:
                    actionrow_subtitle += "  ·  " + str(format_filesize(video_only_format["filesize"]))
                if video_only_format["bitrate"] is not None:
                    actionrow_subtitle += "  ·  " + _("Bitrate:") + " " + str(format_filesize(video_only_format["bitrate"]))
                
                create_option_actionrow(self,
                    group_video_only,
                    actionrow_title,
                    actionrow_subtitle,
                    "video",
                    video_only_format,
                    video_title,
                    video_download_options_preferences_dialog, url, DownloadThread
                )
            
            # For audio only formats
            for audio_only_format in audio_formats:
                actionrow_title = _("Audio only")
                
                actionrow_subtitle = ""
                if audio_only_format["ext"] is not None:
                    actionrow_subtitle = audio_only_format["ext"]
                if audio_only_format["filesize"] is not None:
                    actionrow_subtitle += "  ·  " + str(format_filesize(audio_only_format["filesize"]))
                if audio_only_format["bitrate"] is not None:
                    actionrow_subtitle += "  ·  " + _("Bitrate:") + " " + str(format_filesize(audio_only_format["bitrate"]))
                
                create_option_actionrow(self,
                    group_audio_only,
                    actionrow_title,
                    actionrow_subtitle,
                    "audio",
                    audio_only_format,
                    video_title,
                    video_download_options_preferences_dialog, url, DownloadThread
                )
            
            # For complete (matched) formats
            for complete_format in matched_formats:
                actionrow_title = _("Video and audio")
                if complete_format[0]["resolution"] is not None:
                    actionrow_title += "  ·  " + complete_format[0]["resolution"]
                if complete_format[0]["framerate"] is not None:
                    actionrow_title += "@" + str(round(float(complete_format[0]["framerate"])))
                
                actionrow_subtitle = ""
                if complete_format[0]["ext"] is not None:
                    actionrow_subtitle = complete_format[0]["ext"]
                if complete_format[2] is not None:
                    actionrow_subtitle += "  ·  " + format_filesize(complete_format[2])
                if complete_format[4] == True:
                    actionrow_subtitle += "?"
                if complete_format[3] is not None:
                    actionrow_subtitle += "  ·  " + _("Bitrate:") + " " + str(complete_format[3])
                
                create_option_actionrow(self,
                    group_video_and_audio,
                    actionrow_title,
                    actionrow_subtitle,
                    "complete",
                    complete_format,
                    video_title,
                    video_download_options_preferences_dialog, url, DownloadThread
                )
            
            # If there are no options available:

            if options_available == False:
                video_download_options_preferences_dialog.set_title("")
                page_error = Adw.PreferencesPage()
                video_download_options_preferences_dialog.add(page_error)
                group_error = Adw.PreferencesGroup()
                page_error.add(group_error)

                error_status_page = Adw.StatusPage(icon_name="dialog-error-symbolic")
                error_status_page.set_title(_("No video or audio streams found"))
                error_status_page.set_hexpand(True)
                error_status_page.set_vexpand(True)

                group_error.add(error_status_page)
            
            GLib.idle_add(loading_dialog.set_can_close, True)
            GLib.idle_add(loading_dialog.close)
            GLib.idle_add(video_download_options_preferences_dialog.present, self)

        else:
            # Show error dialog if something went wrong
            error_body = (
                f"{_("An error occurred:")}\n\n"
                f"{_("The video platform may not be supported or you may be being blocked by the platform. If you have an active VPN connection that might be the cause, or you can try importing your browser's cookies through a cookies.txt file.")}\n\n\n"
                "────────────────────────────\n\n\n"
                f"{self.escape_special_characters(ytdlp_error)}"
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

def on_video_option_download_clicked(self, prefswindow, type, download_object, download_name, url):
    # Start downloading once the user clicks download on an option

    prefswindow.close()
    print(url)

    # Unless they were already complete streams before getting matched,
    # complete formats require both a video and audio streams
    if type == "complete":
        if download_object[1] == None: # Format already includes an audio stream
            video_options = {
                'format': download_object[0]["id"]
            }

        else: # Video and audio formats are separate
            video_options = {
                'format': download_object[0]["id"] + "+" + download_object[1]["id"]
            }
        
        file_ext = download_object[0]["ext"]

    else:
        video_options = {
            'format': download_object["id"]
        }

        file_ext = download_object["ext"]
    
    filename = download_name + "." + file_ext
    
    # Check if filename already exists
    while True:
        if os.path.exists(os.path.join(self.appconf["download_directory"], filename)):
            filename = download_name + "-1." + file_ext

        else:
            break

    on_download_clicked(None, self, url, filename, None, "video", video_options, False, self.appconf["download_directory"])