import time
from stringstorage import gettext as _
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import GLib

def pause_all(self, called_by_scheduler):
    if len(self.downloads) > 0:
        if self.all_paused:
            for download_thread in self.downloads:
                download_thread.resume(called_by_scheduler)

        else:
            for download_thread in self.downloads:
                download_thread.pause(called_by_scheduler)

def stop_all(self, app, variaapp):
    while self.downloads != []:
        for download_item in self.downloads:
            download_item.stop()

    self.header_pause_content.set_icon_name("media-playback-pause-symbolic")
    self.header_pause_content.set_label(_("Pause All"))
    self.header_pause_button.set_sensitive(False)
    self.content_root_overlay.add_overlay(self.status_page_widget)

def check_all_status(self):
    any_ongoing_downloads = False
    all_paused = True

    for download_item in self.downloads.copy():
        if download_item.is_complete == False and download_item.cancelled == False:
            any_ongoing_downloads = True

            if download_item.paused == False:
                all_paused = False
                break

    if any_ongoing_downloads:
        if all_paused:
            self.all_paused = True
            self.header_pause_content.set_icon_name("media-playback-start-symbolic")
            self.header_pause_content.set_label(_("Resume All"))
            self.header_pause_button.set_sensitive(True)
        
        else:
            self.all_paused = False
            self.header_pause_content.set_icon_name("media-playback-pause-symbolic")
            self.header_pause_content.set_label(_("Pause All"))
            self.header_pause_button.set_sensitive(True)
    
    else:
        self.all_paused = False
        self.header_pause_content.set_icon_name("media-playback-pause-symbolic")
        self.header_pause_content.set_label(_("Pause All"))
        self.header_pause_button.set_sensitive(False)

        GLib.idle_add(self.header_pause_button.set_sensitive, False)

        if len(self.downloads) == 0:
            self.content_root_overlay.add_overlay(self.status_page_widget)

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