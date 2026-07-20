from stringstorage import gettext as _
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
import threading
from concurrent.futures import ThreadPoolExecutor
import os
import time
import yt_dlp
import base64
import json
import re

from download.actionrow import on_download_clicked
from download.thread import DownloadThread

def format_filesize(filesize):
    try:
        if filesize is None:
            filesize = 0

        if isinstance(filesize, str):
            filesize = float(filesize) if filesize.strip() != "" else 0
        filesize = float(filesize)

    except Exception:
        filesize = 0

    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if filesize < 1024.0:
            return f"{filesize:.2f} {unit}"
        filesize /= 1024.0

    return f"{filesize:.2f} TB"


def format_bitrate(bitrate):
    try:
        if bitrate is None:
            return None

        if isinstance(bitrate, str):
            if bitrate.strip() == "":
                return None
            bitrate = float(bitrate)

        bitrate = float(bitrate)

        # Assume kbps for bitrate
        if bitrate >= 1000:
            return f"{bitrate/1000:.2f} Mbps"
        else:
            return f"{int(round(bitrate))} kbps"

    except Exception:
        return None

def resolution_height(resolution):
    try:
        if not resolution:
            return 0

        m = re.search(r"(\d{2,4})p", str(resolution))
        if m:
            return int(m.group(1))

        nums = re.findall(r"(\d+)", str(resolution))
        if nums:
            return int(nums[-1])

    except Exception:
        pass

    return 0

def cookies_to_netscape(cookies, app):
    if app.appconf["cookies_txt"] == "1":
        with open(os.path.join(app.appdir, 'cookies.txt'), 'r') as file:
            lines = file.readlines()
        cookies_included = True
    else:
        lines = ["# Netscape HTTP Cookie File"]
        cookies_included = False

    try:
        cookies = json.loads(base64.b64decode(cookies).decode("utf-8"))

        for cookie in cookies:
            domain = cookie["domain"]
            include_subdomains = "TRUE" if domain.startswith(".") else "FALSE"
            path = cookie.get("path", "/")
            secure = "TRUE" if cookie.get("secure") else "FALSE"
            expiry = int(cookie.get("expirationDate", 0))

            lines.append("\t".join([
                domain,
                include_subdomains,
                path,
                secure,
                str(expiry),
                cookie["name"],
                cookie["value"]
            ]))
        
        cookies_included = True
    except:
        pass

    if cookies_included:
        final_file_contents = "\n".join(lines)

        with open(os.path.join(app.appdir, "cookies_for_ytdlp.txt"), "w") as text_file:
            text_file.write(final_file_contents)
    
    return cookies_included

def on_video_clicked(button, self, entry, header):
    self.video_loading_cancelled = False

    if isinstance(entry, str):
        url = entry
    
    else:
        url = entry.get_text()
        entry.set_text("")
    
    cookies_included = cookies_to_netscape(header, self) # Generate final cookies file
    
    def loading_dialog_cancel_pressed(dialog, response_id, self):
        self.video_loading_cancelled = True
        GLib.idle_add(dialog.set_can_close, True)
        GLib.idle_add(dialog.close)

    # Show loading screen
    loading_dialog = Adw.AlertDialog()
    loading_dialog_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=25)
    loading_dialog.set_extra_child(loading_dialog_box)
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

    loading_dialog.add_response("cancel",  _("Cancel"))
    loading_dialog.connect("response", loading_dialog_cancel_pressed, self)
    loading_dialog.set_response_appearance("cancel", Adw.ResponseAppearance.DESTRUCTIVE)

    loading_dialog.set_can_close(False)
    loading_dialog.present(self)

    def ytdlp_startsubprocess():
        ytdlp_options_base = {
            'js_runtimes': {self.jsruntimeexec['name']: {'path': self.jsruntimeexec['exec']}},
            'skip_download': True,
        }

        if cookies_included:
            ytdlp_options_base['cookiefile'] = os.path.join(self.appdir, "cookies_for_ytdlp.txt")

        def ytdlp_get_data(options):
            try:
                with yt_dlp.YoutubeDL(options) as ydl:
                    return {
                        "data": ydl.sanitize_info(ydl.extract_info(url, download=False)),
                        "ytdlp_error": ""
                    }

            except Exception as error:
                return {
                    "data": None,
                    "ytdlp_error": str(error)
                }

        data = None
        ytdlp_error = ""

        # Use extract_flat to quickly determine if this is a single video or a playlist
        ytdlp_options_detects = ytdlp_options_base.copy()
        ytdlp_options_detects['extract_flat'] = True

        ytdlp_executor_1 = ThreadPoolExecutor(max_workers=1)
        ytdlp_executor_1_future = ytdlp_executor_1.submit(ytdlp_get_data, ytdlp_options_detects)

        while not ytdlp_executor_1_future.done():
            if self.video_loading_cancelled:
                return

        try:
            result = ytdlp_executor_1_future.result(timeout=10)
            data = result.get("data")
            ytdlp_error = result.get("ytdlp_error", "")

        except Exception:
            # If detection fails quickly, fall back to trying a full extract (single video)
            ytdlp_options_final = ytdlp_options_base.copy()
            ytdlp_options_final['extract_flat'] = False
            ytdlp_executor_2 = ThreadPoolExecutor(max_workers=1)
            ytdlp_executor_2_future = ytdlp_executor_2.submit(ytdlp_get_data, ytdlp_options_final)

            while not ytdlp_executor_2_future.done():
                if self.video_loading_cancelled:
                    return

            try:
                result = ytdlp_executor_2_future.result(timeout=20)
                data = result.get("data")
                ytdlp_error = result.get("ytdlp_error", "")
            except Exception:
                data = None
                ytdlp_error = "Extraction failed"

        # If it's not a playlist but lacks formats (since extract_flat returns limited info)
        # do a full extract for that single video to get the format details:
        if data and data.get("_type") != "playlist" and not data.get("formats"):
            ytdlp_options_final2 = ytdlp_options_base.copy()
            ytdlp_options_final2['extract_flat'] = False
            ytdlp_executor_3 = ThreadPoolExecutor(max_workers=1)
            ytdlp_executor_3_future = ytdlp_executor_3.submit(ytdlp_get_data, ytdlp_options_final2)

            while not ytdlp_executor_3_future.done():
                if self.video_loading_cancelled:
                    return

            try:
                result = ytdlp_executor_3_future.result(timeout=20)
                data = result.get("data")
                ytdlp_error = result.get("ytdlp_error", "")
            except Exception:
                pass

        video_formats = []
        audio_formats = []
        combined_formats = [] # Combined formats will end up in matched formats at the end
        matched_formats = []

        video_download_options_preferences_dialog = Adw.PreferencesDialog()

        if data:
            video_title = self.escape_special_characters(data.get("title", "?"))
            if data.get("_type") == "video":
                uploader_name = data.get("uploader", "?")

                for fmt in data.get("formats", []):
                    print(fmt)
                    filesize = fmt.get("filesize")
                    filesize_approx = fmt.get("filesize_approx", 0)
                    if (not filesize or filesize == 0) and filesize_approx:
                        fmt["filesize"] = filesize_approx
                    elif not filesize:
                        fmt["filesize"] = 0

                    # Throw out unnecessary formats
                    if fmt.get("ext") == "mhtml":
                        continue
                    
                    # Video only
                    elif fmt["audio_ext"] == "none" and fmt["resolution"]:
                        bitrate = fmt.get("vbr", 0)
                        if bitrate == 0 and fmt.get("tbr", 0) != 0:
                            bitrate = fmt.get("tbr", 0)
                        if bitrate != 0:
                            video_formats.append({
                                "id": fmt["format_id"],
                                "ext": fmt["ext"],
                                "resolution": fmt["resolution"],
                                "framerate": fmt.get("fps", None),
                                "filesize": fmt["filesize"],
                                "url": fmt["url"],
                                "bitrate": bitrate,
                            })

                    # Audio only
                    elif fmt["video_ext"] == "none":
                        bitrate = fmt.get("abr", 0)
                        if bitrate == 0 and fmt.get("tbr", 0) != 0:
                            bitrate = fmt.get("tbr", 0)
                        if bitrate != 0:
                            audio_formats.append({
                                "id": fmt["format_id"],
                                "ext": fmt["ext"],
                                "bitrate": bitrate,
                                "filesize": fmt["filesize"],
                                "url": fmt["url"],
                            })

                    # Video and audio
                    elif fmt["video_ext"] != "none" and fmt["audio_ext"] != "none" and fmt["resolution"]:
                        if fmt.get("tbr", 0) != 0:
                            combined_formats.append({
                                "id": fmt["format_id"],
                                "ext": fmt["ext"],
                                "resolution": fmt["resolution"],
                                "framerate": fmt.get("fps", None),
                                "filesize": fmt["filesize"],
                                "url": fmt["url"],
                                "bitrate": fmt.get("tbr", 0)
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
                    bitrate = combined["bitrate"]
                    matched_formats.append([combined, None, combined_size_bytes, bitrate])

                video_formats.sort(key=lambda x: (resolution_height(x.get("resolution")), x.get("filesize", 0) or 0), reverse=True)
                audio_formats.sort(key=lambda x: (x.get("filesize", 0) or 0), reverse=True)
                matched_formats.sort(key=lambda x: (resolution_height(x[0].get("resolution")), x[2] or 0), reverse=True)

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

                options_available = False

                if len(matched_formats) > 0:
                    page_video_and_audio = Adw.PreferencesPage(title=_("Video and audio"), icon_name="media-playback-start-symbolic")
                    video_download_options_preferences_dialog.add(page_video_and_audio)
                    group_video_and_audio = Adw.PreferencesGroup(title="\"" + video_title + "\" - " + uploader_name)
                    page_video_and_audio.add(group_video_and_audio)

                    video_download_options_preferences_dialog.set_title(_("Video and audio"))
                    options_available = True

                if len(video_formats) > 0:
                    page_video_only = Adw.PreferencesPage(title=_("Video only"), icon_name="camera-video-symbolic")
                    video_download_options_preferences_dialog.add(page_video_only)
                    group_video_only = Adw.PreferencesGroup(title="\"" + video_title + "\" - " + uploader_name)
                    page_video_only.add(group_video_only)

                    video_download_options_preferences_dialog.set_title(_("Video only"))
                    options_available = True

                if len(audio_formats) > 0:
                    page_audio_only = Adw.PreferencesPage(title=_("Audio only"), icon_name="folder-music-symbolic")
                    video_download_options_preferences_dialog.add(page_audio_only)
                    group_audio_only = Adw.PreferencesGroup(title="\"" + video_title + "\" - " + uploader_name)
                    page_audio_only.add(group_audio_only)

                    video_download_options_preferences_dialog.set_title(_("Audio only"))
                    options_available = True

                def build_actionrow_title(download_type, resolution=None, framerate=None):
                    title = download_type

                    if resolution:
                        title += "  ·  " + str(resolution)

                    if framerate is not None:
                        try:
                            title += "@" + str(round(float(framerate)))
                        except Exception:
                            pass

                    return title

                def build_actionrow_subtitle(ext=None, filesize=None, video_bitrate=None, audio_bitrate=None, audio_ext=None, uncertain=False, combined_bitrate_text=None):
                    parts = []

                    # Extensions - Video and audio
                    if ext:
                        parts.append(str(ext))
                    elif audio_ext:
                        parts.append(str(audio_ext))

                    # Filesize
                    if filesize is not None:
                        formatted_filesize = str(format_filesize(filesize))
                        if '0.00' in formatted_filesize:
                            formatted_filesize = _("Unknown filesize")
                        parts.append(formatted_filesize)

                    # Uncertain size marker
                    if uncertain:
                        if parts:
                            parts[-1] = parts[-1] + "?"
                        else:
                            parts.append("?")

                    # Bitrates: video then audio
                    bitrate_video = format_bitrate(video_bitrate)
                    bitrate_audio = format_bitrate(audio_bitrate)

                    if bitrate_video and bitrate_audio:
                        parts.append(_("Bitrate:") + " 🎞 " + bitrate_video + " &amp; 🕪 " + bitrate_audio)
                    
                    elif bitrate_video:
                        parts.append(_("Bitrate:") + " 🎞 " + bitrate_video)

                    elif bitrate_audio:
                        parts.append(_("Bitrate:") + " 🕪 " + bitrate_audio)

                    # Combined bitrate text fallback (show only if specific bitrates weren't available)
                    if combined_bitrate_text and not (bitrate_video or bitrate_audio):
                        parts.append(_("Bitrate:") + " " + str(combined_bitrate_text))

                    return "  ·  ".join(parts)

                def create_option_actionrow(self, group, title, subtitle, type, download_object, download_name, video_download_options_preferences_dialog, url, DownloadThread):
                    video_option_actionrow = Adw.ActionRow()
                    video_download_button = Gtk.Button(label=_("Download"))
                    video_download_button.add_css_class("suggested-action")
                    video_download_button.set_halign(Gtk.Align.START)
                    video_download_button.set_valign(Gtk.Align.CENTER)
                    video_download_button.connect("clicked", lambda clicked, type=type, download_object=download_object, download_name=download_name: on_video_option_download_clicked(self, video_download_options_preferences_dialog, type, download_object, download_name, url))

                    video_option_actionrow.set_title(title)
                    video_option_actionrow.set_subtitle(subtitle)
                    video_option_actionrow.add_suffix(video_download_button)

                    group.add(video_option_actionrow)

                # For video only formats
                for video_only_format in video_formats:
                    actionrow_title = build_actionrow_title(_("Video only"), video_only_format.get("resolution"), video_only_format.get("framerate"))
                    actionrow_subtitle = build_actionrow_subtitle(video_only_format.get("ext"), video_only_format.get("filesize"), video_bitrate=video_only_format.get("bitrate"))

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
                    actionrow_title = build_actionrow_title(_("Audio only"))
                    actionrow_subtitle = build_actionrow_subtitle(audio_only_format.get("ext"), audio_only_format.get("filesize"), audio_bitrate=audio_only_format.get("bitrate"))

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
                    vid = complete_format[0]
                    audio = complete_format[1]
                    total_size = complete_format[2]
                    bitrate_text = complete_format[3]
                    uncertain_flag = bool(complete_format[4]) if len(complete_format) > 4 else False

                    actionrow_title = build_actionrow_title(_("Video and audio"), vid.get("resolution"), vid.get("framerate"))
                    actionrow_subtitle = build_actionrow_subtitle(
                        vid.get("ext"),
                        total_size,
                        video_bitrate=vid.get("bitrate"),
                        audio_bitrate=(audio.get("bitrate") if audio else None),
                        audio_ext=(audio.get("ext") if audio else None),
                        uncertain=uncertain_flag,
                        combined_bitrate_text=bitrate_text
                    )

                    create_option_actionrow(self,
                        group_video_and_audio,
                        actionrow_title,
                        actionrow_subtitle,
                        "complete",
                        complete_format,
                        video_title,
                        video_download_options_preferences_dialog, url, DownloadThread
                    )
            
            elif data.get("_type") == "playlist":
                if data["entries"] and len(data["entries"]) > 0:
                    options_available = True

                    all_height_qualities = [
                        _("Maximum available quality"),
                        "2160p",
                        "1440p",
                        "1080p",
                        "720p",
                        "480p",
                        "360p",
                        "240p",
                        "144p"
                    ]
                    all_height_qualities_dropdown = Gtk.DropDown.new_from_strings(all_height_qualities)

                    max_quality_actionrow = Adw.ActionRow(title=_("Maximum Quality"))
                    max_quality_actionrow.add_suffix(all_height_qualities_dropdown)

                    mode_toggle_video_and_audio = Adw.Toggle(label=_("Video and audio"))
                    mode_toggle_video_only = Adw.Toggle(label=_("Video only"))
                    mode_toggle_audio_only = Adw.Toggle(label=_("Audio only"))
                    mode_toggle_group = Adw.ToggleGroup()
                    mode_toggle_group.add(mode_toggle_video_and_audio)
                    mode_toggle_group.add(mode_toggle_video_only)
                    mode_toggle_group.add(mode_toggle_audio_only)

                    playlist_download_button = Gtk.Button(label=_("Download"))
                    playlist_download_button.add_css_class("suggested-action")
                    playlist_download_button.add_css_class("pill")
                    playlist_download_button.connect("clicked", lambda clicked: on_playlist_download_clicked(self, video_download_options_preferences_dialog, mode_toggle_group.get_active(), len(data["entries"]), all_height_qualities, all_height_qualities_dropdown.get_selected(), video_title, url))
                    
                    playlist_page = Adw.PreferencesPage()
                    playlist_page_group_1 = Adw.PreferencesGroup()
                    playlist_page_group_2 = Adw.PreferencesGroup()
                    playlist_page_group_3 = Adw.PreferencesGroup()

                    playlist_page_group_1.set_title(video_title)
                    
                    playlist_page_group_1.add(mode_toggle_group)
                    playlist_page_group_2.add(max_quality_actionrow)
                    playlist_page_group_3.add(playlist_download_button)

                    playlist_page.add(playlist_page_group_1)
                    playlist_page.add(playlist_page_group_2)
                    playlist_page.add(playlist_page_group_3)

                    video_download_options_preferences_dialog.set_title(_("Playlist Download"))
                    video_download_options_preferences_dialog.add(playlist_page)
                
                else:
                    options_available = False

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

            if self.use_ssd:
                video_download_options_preferences_dialog.set_content_width(self.get_default_size()[0])
                video_download_options_preferences_dialog.set_content_height(self.get_default_size()[1])

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

    thread = threading.Thread(target=ytdlp_startsubprocess, daemon=True)
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
                'format': download_object[0]["id"],
                'filesize_to_show': str(format_filesize(download_object[0].get("filesize", 0)))
            }

        else: # Video and audio formats are separate
            video_options = {
                'format': download_object[0]["id"] + "+" + download_object[1]["id"],
                'filesize_to_show': str(format_filesize(download_object[0].get("filesize", 0) + download_object[1].get("filesize", 0)))
            }
        
        file_ext = download_object[0]["ext"]

    else:
        video_options = {
            'format': download_object["id"],
            'filesize_to_show': str(format_filesize(download_object.get("filesize", 0)))
        }

        file_ext = download_object["ext"]
    
    filename = download_name + "." + file_ext

    def unique_filename(directory, base_name, ext):
        filename = f"{base_name}.{ext}"
        suffix = 1

        while os.path.exists(os.path.join(directory, filename)):
            filename = f"{base_name}-{suffix}.{ext}"
            suffix += 1

        return filename

    filename = unique_filename(self.appconf["download_directory"], download_name, file_ext)

    on_download_clicked(None, self, url, filename, None, "video", video_options, False, self.appconf["download_directory"], 0)

def on_playlist_download_clicked(self, prefswindow, type, length, qualities, selected_quality_index, download_name, url):
    prefswindow.close()
    
    if selected_quality_index == 0:
        format_quality_text = ""
    else:
        quality_resolution = qualities[selected_quality_index].replace("p", "")
        format_quality_text = f"[height<={quality_resolution}]"
    
    if type == 0:
        format_text = f"bestvideo{format_quality_text}+bestaudio/best{format_quality_text}"
    elif type == 1:
        format_text = f"bestvideo{format_quality_text}"
    elif type == 2:
        format_text = f"bestaudio/best{format_quality_text}"

    video_options = {
        'length': length,
        'filesize_to_show': "...",
        'format': format_text,
        'type': type
    }

    on_download_clicked(None, self, url, download_name, None, "playlist", video_options, False, self.appconf["download_directory"], 0)