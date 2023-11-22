variaVersion = "v2023.11.22"

import gi
import sys
import time
from io import BytesIO
from urllib.parse import unquote, urlparse
import json
import os
import time
import aria2p
import subprocess
import threading
from pathlib import Path
from urllib.parse import urlparse
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio
import multiprocessing

class DownloadThread(threading.Thread):
    def __init__(self, api, url, progress_bar, speed_label, downloaddir):
        threading.Thread.__init__(self)
        self.api = api
        self.downloaddir = downloaddir
        self.download = None
        self.url = url
        self.progress_bar = progress_bar
        self.speed_label = speed_label
        self.stop_event = threading.Event()

    def is_valid_url(self, url):
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def run(self):
        if not (self.is_valid_url(self.url)):
            try:
                GLib.idle_add(self.show_message("This is not a valid URL."))
            except:
                return
        else:
            self.download = self.api.add_uris([self.url])
            downloadname = self.download.name
            while (True):
                try:
                    self.download.update()
                    GLib.idle_add(self.update_labels_and_things)
                    if (self.download.is_complete):
                        if os.path.exists(os.path.join(self.downloaddir,(self.download.gid + ".varia.json"))):
                            os.remove(os.path.join(self.downloaddir,(self.download.gid + ".varia.json")))
                        break
                    elif (self.download.status == "error"):
                        return
                except:
                    return
                time.sleep(1)

    def show_message(self, message):
        self.speed_label.set_text(message)

    def update_labels_and_things(self):
        self.progress_bar.set_fraction(self.download.progress / 100)
        download_speed_mb = (self.download.download_speed / 1024 / 1024)
        if int(str(download_speed_mb)[0]) == 0:
            download_speed_kb = (self.download.download_speed / 1024)
            if int(str(download_speed_kb)[0]) == 0:
                self.speed_label.set_text(f"{round(self.download.progress)}%  |  {round(self.download.download_speed, 2)} B/s")
            else:
                self.speed_label.set_text(f"{round(self.download.progress)}%  |  {round(self.download.download_speed / 1024, 2)} KB/s")
        else:
            self.speed_label.set_text(f"{round(self.download.progress)}%  |  {round(self.download.download_speed / 1024 / 1024, 2)} MB/s")

    def pause(self):
        if self.download:
            if self.download.is_paused == False:
                try:
                    self.download.pause()
                except:
                    try:
                        self.download.pause([self.download.gid])
                    except:
                        self.stop(False)

    def resume(self):
        if self.download:
            if self.download.is_paused == True:
                try:
                    self.download.resume()
                except:
                    return

    def stop(self, deletefiles):
        if self.download:
            downloadgid = self.download.gid
            downloadname = self.download.name
            self.download.remove(force=True)
            if not self.download.is_complete:
                if (deletefiles == True):
                    if os.path.exists(os.path.join(self.downloaddir,(downloadgid + ".varia.json"))):
                        os.remove(os.path.join(self.downloaddir,(downloadgid + ".varia.json")))
                    if os.path.exists(os.path.join(self.downloaddir, downloadname)):
                        os.remove(os.path.join(self.downloaddir, downloadname))

    def save_state(self):
        if self.download:
            try:
                self.download.update()
            except:
                return
            state = {
                'url': self.url,
                'downloaded': self.download.completed_length,
            }
            with open(os.path.join(self.downloaddir, f'{self.download.gid}.varia.json'), 'w') as f:
                json.dump(state, f)

    @classmethod
    def load_state(cls, api, downloaddir, filename, progress_bar, speed_label):
        with open(os.path.join(downloaddir, filename), 'r') as f:
            state = json.load(f)
            os.remove(os.path.join(downloaddir, filename))
        instance = cls(api, state['url'], progress_bar, speed_label, downloaddir)
        return instance

class MainWindow(Gtk.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.downloaddir = GLib.get_user_special_dir(GLib.USER_DIRECTORY_DOWNLOAD)

        self.api = aria2p.API(
            aria2p.Client(
                host="http://localhost",
                port=6801,
                secret="ARIA2CFORVARIA"
            )
        )

        self.set_default_size(800, 600)
        self.set_size_request(650, 450)
        self.set_titlebar(Gtk.Box())

        self.total_download_speed = ""
        self.terminating = False

        self.set_title("Varia")
        Gtk.Settings.get_default().set_property("gtk-icon-theme-name", "Adwaita")

        self.overlay_split_view = Adw.OverlaySplitView.new()
        self.set_child(child=self.overlay_split_view)

        self.downloads = []
        self.pause_buttons = []
        self.all_paused = False

        # Sidebar
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sidebar_content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        header_bar = Adw.HeaderBar()
        header_bar.get_style_context().add_class('flat')
        sidebar_box.append(header_bar)

        about_button = Gtk.Button(label="About")
        header_bar.pack_start(about_button)
        about_button.connect("clicked", self.show_about)
        about_button.set_icon_name("help-about-symbolic")

        download_entry = Gtk.Entry()
        download_entry.set_placeholder_text("URL")
        download_button = Gtk.Button(label="Download")
        download_button.get_style_context().add_class("pill")
        download_button.get_style_context().add_class("suggested-action")
        download_button.connect("clicked", self.on_download_clicked, download_entry)

        sidebar_content_box.set_margin_start(10)
        sidebar_content_box.set_margin_end(10)
        sidebar_content_box.set_margin_top(10)
        sidebar_content_box.set_margin_bottom(10)

        sidebar_content_box.append(download_entry)
        sidebar_content_box.append(download_button)
        sidebar_box.append(sidebar_content_box)

        self.overlay_split_view.set_sidebar(sidebar_box)

        # Content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        self.total_download_speed_label = Gtk.Label(label=self.total_download_speed)

        header_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        header_pause_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        header_pause_label = Gtk.Label(label = "Pause all")
        header_pause_image = Gtk.Image.new()
        header_pause_image.set_from_icon_name("media-playback-pause-symbolic")
        header_pause_box.append(header_pause_image)
        header_pause_box.append(header_pause_label)
        header_pause_button = Gtk.Button()
        header_pause_button.set_child(header_pause_box)
        header_pause_button.connect("clicked", lambda button: self.pause_all(header_pause_label, header_pause_image))

        header_button_box.append(header_pause_button)

        header_stop_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        header_stop_label = Gtk.Label(label = "Cancel all")
        header_stop_image = Gtk.Image.new()
        header_stop_image.set_from_icon_name("process-stop-symbolic")
        header_stop_box.append(header_stop_image)
        header_stop_box.append(header_stop_label)
        header_stop_button = Gtk.Button()
        header_stop_button.set_child(header_stop_box)
        header_stop_button.connect("clicked", lambda button: self.stop_all())

        header_button_box.append(header_stop_button)

        header_expanding_box = Gtk.Box()
        Gtk.Widget.set_hexpand(header_expanding_box, True)
        header_expanding_box_1 = Gtk.Box()
        Gtk.Widget.set_hexpand(header_expanding_box_1, True)

        header_box.append(header_expanding_box)
        header_box.append(self.total_download_speed_label)
        header_box.append(header_expanding_box_1)
        header_box.append(header_button_box)

        header_bar = Adw.HeaderBar()
        header_bar.get_style_context().add_class('flat')
        header_bar.set_title_widget(header_box)
        content_box.append(header_bar)

        self.download_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.download_list.set_margin_start(10)
        self.download_list.set_margin_end(10)
        self.download_list.set_margin_bottom(10)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_child(self.download_list)
        scrolled_window.set_hexpand(True)
        scrolled_window.set_vexpand(True)

        content_box.append(scrolled_window)

        self.overlay_split_view.set_content(content_box)

        self.total_download_speed_calculator_thread = threading.Thread(target=self.total_download_speed_get, args=(self.downloads, self.total_download_speed_label))
        self.total_download_speed_calculator_thread.start()

        self.check_download_status_thread = threading.Thread(target=self.check_download_status)
        self.check_download_status_thread.start()

        for filename in os.listdir(self.downloaddir):
            if filename.endswith('.varia.json'):
                with open(os.path.join(self.downloaddir, filename), 'r') as f:
                    state = json.load(f)
                objectlist = self.create_actionrow(state['url'])
                download_thread = DownloadThread.load_state(self.api, self.downloaddir, filename, objectlist[0], objectlist[1])
                self.downloads.append(download_thread)
                download_thread.start()

    def check_download_status(self):
        while (self.terminating == False):
            for download_thread in self.downloads:
                if (download_thread.download.is_complete == 1):
                    download_thread.speed_label.set_text("Download complete.")
                elif (download_thread.download.status == "error") or (download_thread.download.status == "removed"):
                    download_thread.speed_label.set_text("An error occurred.")
            time.sleep(1)

    def total_download_speed_get(self, downloads, total_download_speed_label):
        while (self.terminating == False):
            total_download_speed = 0
            download_speed_mb = False
            download_speed_kb = False
            for download_thread in downloads:
                try:
                    download_thread.download.update()
                except:
                    continue
                speed_label_text_first_digit = download_thread.speed_label.get_text()[0]
                if (speed_label_text_first_digit.isdigit()):
                    download_speed = (float(download_thread.speed_label.get_text().split(" ")[4]))
                    if (download_thread.speed_label.get_text().split(" ")[5] == "MB/s"):
                        download_speed_mb = True
                    elif (download_thread.speed_label.get_text().split(" ")[5] == "KB/s"):
                        download_speed_kb = True
                    total_download_speed = total_download_speed + download_speed
            if (total_download_speed == 0):
                total_download_speed_label.set_text("0 B/s")
            elif (download_speed_mb == True):
                total_download_speed_label.set_text(str(round(total_download_speed, 2)) + " MB/s")
            elif (download_speed_kb == True):
                total_download_speed_label.set_text(str(round(total_download_speed, 2)) + " KB/s")
            else:
                total_download_speed_label.set_text(str(round(total_download_speed, 2)) + " B/s")
            time.sleep(1)

    def create_actionrow(self, url):
        filename = url.split("/")[-1].split("?")[0]

        download_item = Adw.Bin()
        style_context = download_item.get_style_context()
        style_context.add_class('card')

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box_1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box_1.set_margin_bottom(10)

        box_2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box_2.set_margin_start(10)
        box_2.set_margin_end(10)
        box_2.set_margin_top(10)
        box_2.set_margin_bottom(10)

        download_item.set_child(box_2)

        filename_label = Gtk.Label(label=filename)
        filename_label.set_halign(Gtk.Align.START)
        box.append(filename_label)

        progress_bar = Gtk.ProgressBar()

        speed_label = Gtk.Label()
        speed_label.set_halign(Gtk.Align.START)
        box.append(speed_label)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        self.pause_buttons.append(Gtk.Button.new_from_icon_name("media-playback-pause-symbolic"))
        self.pause_buttons[len(self.pause_buttons)-1].connect("clicked", self.on_pause_clicked, self.pause_buttons[len(self.pause_buttons)-1], download_item)
        button_box.append(self.pause_buttons[len(self.pause_buttons)-1])

        stop_button = Gtk.Button.new_from_icon_name("process-stop-symbolic")
        stop_button.connect("clicked", self.on_stop_clicked, download_item)
        button_box.append(stop_button)

        box_1.append(box)

        box_1_expanding_box = Gtk.Box()
        Gtk.Widget.set_hexpand(box_1_expanding_box, True)
        box_1.append(box_1_expanding_box)

        box_1.append(button_box)
        box_2.append(box_1)
        box_2.append(progress_bar)

        self.download_list.append(download_item)
        download_item.index = len(self.downloads)-1

        return [progress_bar, speed_label, self.pause_buttons[len(self.pause_buttons)-1], stop_button]

    def on_download_clicked(self, button, entry):
        url = entry.get_text()
        entry.set_text("")
        if url:
            objectlist = self.create_actionrow(url)
            download_thread = DownloadThread(self.api, url, objectlist[0], objectlist[1], self.downloaddir)
            self.downloads.append(download_thread)
            download_thread.start()

    def on_pause_clicked(self, button, pause_button, download_item):
        download_thread = self.downloads[download_item.index+1]
        if download_thread.download.is_paused:
            download_thread.resume()
            image = Gtk.Image.new()
            image.set_from_icon_name("media-playback-pause-symbolic")
            pause_button.set_child(image)
        else:
            download_thread.pause()
            image = Gtk.Image.new()
            image.set_from_icon_name("media-playback-start-symbolic")
            pause_button.set_child(image)
        download_thread.save_state()

    def on_stop_clicked(self, button, download_item):
        index = download_item.index
        download_thread = self.downloads[index+1]
        try:
            download_thread.stop(True)
        except:
            pass
        self.download_list.remove(download_item)
        if (download_item in self.downloads):
            self.downloads.remove(download_item)

    def pause_all(self, header_pause_label, header_pause_image):
        i = 0
        pause_button_images = []
        if (self.all_paused == False):
            for download_thread in self.downloads:
                download_thread.pause()
                download_thread.save_state()

                pause_button_images.append(Gtk.Image.new())
                pause_button_images[i].set_from_icon_name("media-playback-start-symbolic")
                self.pause_buttons[i].set_child(pause_button_images[i])

                i += 1
            if (header_pause_label != "no"):
                header_pause_image.set_from_icon_name("media-playback-start-symbolic")
                header_pause_label.set_text("Resume all")
            self.all_paused = True
        else:
            for download_thread in self.downloads:
                download_thread.resume()

                pause_button_images.append(Gtk.Image.new())
                pause_button_images[i].set_from_icon_name("media-playback-pause-symbolic")
                self.pause_buttons[i].set_child(pause_button_images[i])

                i += 1
            if (header_pause_label != "no"):
                header_pause_image.set_from_icon_name("media-playback-pause-symbolic")
                header_pause_label.set_text("Pause all")
            self.all_paused = False

    def stop_all(self):
        while (self.downloads != []):
            child = self.download_list.get_first_child()
            while child is not None:
                next_child = child.get_next_sibling()
                self.download_list.remove(child)
                child = next_child
            for download_thread in self.downloads:
                download_thread.stop(True)
                self.downloads.remove(download_thread)

    def show_about(self, app):
        dialog = Adw.AboutWindow(transient_for=self)
        dialog.set_application_name("Varia")
        dialog.set_version(variaVersion)
        dialog.set_developer_name("Giant Pink Robots!")
        dialog.set_license_type(Gtk.License(Gtk.License.MPL_2_0))
        dialog.set_comments("aria2 based download manager utilizing GTK4 and Libadwaita.")
        dialog.set_website("https://github.com/giantpinkrobots/varia")
        dialog.set_issue_url("https://github.com/giantpinkrobots/varia/issues")
        dialog.set_copyright("2023 Giant Pink Robots!\n\nThis application relies on the following pieces of software:\n\n- aria2: GPL v2 License (aria2 itself relies on OpenSSL: OpenSSL License)\n- aria2p: ISC License\n- c-ares: MIT License\n- libssh2: BSD-3-Clause License\n\nThe licenses of all of these pieces of software can be found in the dependencies_information directory in this application's app directory. A copy of aria2's source code has also been provided in that same directory in order to comply with GPL v2.")
        dialog.set_developers(["Giant Pink Robots! (@giantpinkrobots) https://github.com/giantpinkrobots"])
        dialog.set_application_icon("io.github.giantpinkrobots.varia")
        dialog.set_translator_credits("")
        dialog.show()

    def exitProgram(self, app):
        self.terminating = True
        self.all_paused = False
        self.pause_all("no","no")
        self.api.client.shutdown()
        self.destroy()

class MyApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.win = MainWindow(application=app)
        self.win.present()

def main(version):
    app = MyApp(application_id="io.github.giantpinkrobots.varia")
    try:
        app.run(sys.argv)
    finally:
        app.win.exitProgram(app)

