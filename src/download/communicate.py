import requests
import json
import http.cookiejar
import os
from stringstorage import gettext as _
import libtorrent as lt

def set_speed_limit(self, download_limit):
    try:
        self.sidebar_content_box.remove(self.sidebar_speed_limited_label)
    except:
        pass

    if ((download_limit[:-1] != "0") and (self.appconf["download_speed_limit_enabled"] == "1")):
        self.sidebar_content_box.append(self.sidebar_speed_limited_label)
    else:
        download_limit = "0K"

    # Apply to aria2:
    token = "token:" + self.appconf['remote_secret']
    json_request = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "aria2.changeGlobalOption",
        "params": [
            token,
            {"max-overall-download-limit": download_limit}
        ],
    }

    response = requests.post(self.aria2cLocation + '/jsonrpc', headers={'Content-Type': 'application/json'}, data=json.dumps(json_request))

    # Apply to libtorrent:
    if download_limit.endswith("K"):
        lt_download_limit = int(download_limit.replace("K", "")) * 1024
    elif download_limit.endswith("M"):
        lt_download_limit = int(download_limit.replace("M", "")) * 1024 * 1024
    elif download_limit.endswith("G"):
        lt_download_limit = int(download_limit.replace("G", "")) * 1024 * 1024 * 1024

    self.ltsession.apply_settings({
        "download_rate_limit": lt_download_limit,
        "upload_rate_limit": lt_download_limit
    })

def set_aria2c_download_directory(self):
    token = "token:" + self.appconf['remote_secret']
    if (self.appconf["remote"] == '0'):
        json_request = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "aria2.changeGlobalOption",
            "params": [
                token,
                {"dir": self.appconf["download_directory"]}
            ],
        }
    else:
        json_request = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "aria2.changeGlobalOption",
            "params": [
                token,
                {"dir": self.appconf["remote_location"]}
            ],
        }

    response = requests.post(self.aria2cLocation + '/jsonrpc', headers={'Content-Type': 'application/json'}, data=json.dumps(json_request))

def set_aria2c_cookies(*args):
    self = args[-1]
    header_string = ""
    if self.appconf["cookies_txt"] == "1":
        cookie_jar = http.cookiejar.MozillaCookieJar(os.path.join(self.appdir, 'cookies.txt'))
        cookie_jar.load(ignore_discard=True, ignore_expires=True)
        all_cookies = "; ".join([f"{item.name}={item.value}" for item in cookie_jar])
        header_string = "Cookie: " + all_cookies
    set_aria2c_custom_global_option(self, "header", header_string)

def set_aria2c_custom_global_option(self, key, value):
    token = "token:" + self.appconf['remote_secret']
    json_request = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "aria2.changeGlobalOption",
        "params": [
            token,
            {key: value}
        ]
    }

    response = requests.post(self.aria2cLocation + '/jsonrpc', headers={'Content-Type': 'application/json'}, data=json.dumps(json_request))

def set_lt_seeding(self, *args):
    settings = self.ltsession.get_settings()

    if self.appconf["torrent_seeding_enabled"] == '0':
        settings["unchoke_slots_limit"] = 0
        settings["num_optimistic_unchoke_slots"] = 0
        settings["share_ratio_limit"] = 0.0
        settings["upload_rate_limit"] = 1  # Upload speed set to 1 bytes per second as an extra safety measure

    else:
        settings["unchoke_slots_limit"] = -1
        settings["num_optimistic_unchoke_slots"] = 1
        settings["share_ratio_limit"] = -1
        settings["upload_rate_limit"] = -1

        if self.appconf["torrent_seeding_ratio"][0] == True:
            settings["share_ratio_limit"] = self.appconf["torrent_seeding_ratio"][1]

    self.ltsession.apply_settings(settings)

    if hasattr(self, "downloads"):
        for download in self.downloads:
            if download.mode == "torrent" and download.is_complete and download.cancelled == False:
                download.set_complete()

def set_lt_encryption(self, *args):
    if self.appconf["torrent_require_encryption"] == 'true':
        self.ltsession.apply_settings({
            "in_enc_policy": lt.enc_policy.pe_forced,
            "out_enc_policy": lt.enc_policy.pe_forced,
            "allowed_enc_level": lt.enc_level.pe_rc4,
            "prefer_rc4": True
        })

    else:
        self.ltsession.apply_settings({
            "in_enc_policy": lt.enc_policy.pe_enabled,
            "out_enc_policy": lt.enc_policy.pe_enabled,
            "allowed_enc_level": lt.enc_level.pe_both,
            "prefer_rc4": False
        })