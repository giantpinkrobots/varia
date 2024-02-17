import aria2p
import requests
import json
import gi
from gi.repository import GLib
from download.actionrow import create_actionrow
from download.thread import DownloadThread
import threading

def listen_to_aria2(self):
    aria2_total_downloads = self.api.get_downloads()

    if (len(aria2_total_downloads) > len(self.downloads)):
        downloads_in_frontend = []
        for frontend_download_item in self.downloads:
            downloads_in_frontend.append(frontend_download_item.download.gid)

        for download_item_to_be_added in aria2_total_downloads:
            if (download_item_to_be_added.gid not in downloads_in_frontend):
                if (download_item_to_be_added.is_torrent == False):
                    print('Download added directly to aria2c, adding it to the UI: ' + download_item_to_be_added.files[0].uris[0]["uri"])
                GLib.idle_add(lambda: add_download_to_ui(self, download_item_to_be_added))

    if (self.terminating == False):
        GLib.timeout_add(1000, lambda: listen_to_aria2(self))

def add_download_to_ui(self, download_item_to_be_added):
    download_item_url = download_item_to_be_added.files[0].uris[0]["uri"].split("?")[0]
    objectlist = create_actionrow(self, download_item_url)
    download_thread = DownloadThread(self, download_item_url, objectlist[0], objectlist[1], objectlist[2], objectlist[3], download_item_to_be_added)
    self.downloads.append(download_thread)
    download_thread.start()
