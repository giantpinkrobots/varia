import aria2p
import requests
import json
import gi
from gi.repository import GLib
from download.actionrow import create_actionrow
from download.thread import DownloadThread
import threading

def listen_to_aria2(self):
    if not self.terminating:
        for frontend_download_item in self.downloads.copy():
            if ( (frontend_download_item.download) and ( ((frontend_download_item.download.is_metadata) or (frontend_download_item.download.name.endswith(".torrent"))) and (frontend_download_item.download.is_complete) ) ):
                frontend_download_item.cancelled = True
                frontend_download_item.stop(True)
                self.download_list.remove(frontend_download_item.actionrow)
                self.downloads.remove(frontend_download_item)

        try:
            downloads_in_frontend = set(download_item.download.info_hash for download_item in self.downloads.copy())
            for download_item_to_be_added in self.api.get_downloads():
                if ((download_item_to_be_added.info_hash not in downloads_in_frontend) and (download_item_to_be_added.is_metadata == False) and (download_item_to_be_added.is_complete == False)):
                    if not download_item_to_be_added.is_torrent:
                        print('Download added directly to aria2c, adding it to the UI: ' + download_item_to_be_added.files[0].uris[0]["uri"])
                    add_download_to_ui(self, download_item_to_be_added)
        except:
            pass

        GLib.timeout_add(2000, listen_to_aria2, self)

def add_download_to_ui(self, download_item_to_be_added):
    if download_item_to_be_added.is_torrent:
        download_item_url = "magnet:?xt=urn:btih:" + download_item_to_be_added.info_hash
    else:
        download_item_url = download_item_to_be_added.files[0].uris[0]["uri"].split("?")[0]

    objectlist = create_actionrow(self, download_item_url)
    download_thread = DownloadThread(self, download_item_url, *objectlist, download_item_to_be_added, None)
    self.downloads.append(download_thread)
    download_thread.start()
    download_thread.pause_button.show()
