import requests
import json
import http.cookiejar
import os
from stringstorage import gettext as _

def set_speed_limit(self, download_limit):
    try:
        self.sidebar_content_box.remove(self.sidebar_speed_limited_label)
    except:
        pass

    if ((download_limit[:-1] != "0") and (self.appconf["download_speed_limit_enabled"] == "1")):
        self.sidebar_content_box.append(self.sidebar_speed_limited_label)
    else:
        download_limit = "0K"

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

def set_aria2c_download_simultaneous_amount(self): # Now an unused function, will remove if everything else works.
    downloads_that_will_restart = []

    for download_thread in self.downloads:
        if (download_thread.download):
            if (download_thread.return_is_paused() == False):
                downloads_that_will_restart.append(download_thread.return_gid())
                download_thread.pause()

    token = "token:" + self.appconf['remote_secret']
    json_request = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "aria2.changeGlobalOption",
        "params": [
            token,
            {"max-concurrent-downloads": str(self.appconf["download_simultaneous_amount"])}
        ]
    }

    response = requests.post(self.aria2cLocation + '/jsonrpc', headers={'Content-Type': 'application/json'}, data=json.dumps(json_request))

def set_aria2c_cookies(self):
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
