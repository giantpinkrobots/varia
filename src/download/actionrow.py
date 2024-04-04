import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from gettext import gettext as _

def on_download_clicked(button, self, entry, DownloadThread):
    url = entry.get_text()
    entry.set_text("")
    if url:
        objectlist = create_actionrow(self, url)
        download_thread = DownloadThread(self, url, objectlist[0], objectlist[1], objectlist[2], objectlist[3], objectlist[4], None, None)
        self.downloads.append(download_thread)
        download_thread.start()

def create_actionrow(self, filename):
    filename_shortened = filename[:40]
    if (filename != filename_shortened):
        filename_shortened = filename_shortened + "..."

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

    filename_label = Gtk.Label(label=filename_shortened)
    filename_label.set_halign(Gtk.Align.START)
    box.append(filename_label)

    progress_bar = Gtk.ProgressBar()

    speed_label = Gtk.Label()
    speed_label.set_halign(Gtk.Align.START)
    box.append(speed_label)

    button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

    pause_button = Gtk.Button.new_from_icon_name("media-playback-pause-symbolic")
    pause_button.set_valign(Gtk.Align.CENTER)
    pause_button.get_style_context().add_class("circular")
    pause_button.connect("clicked", on_pause_clicked, self, pause_button, download_item, False)

    self.pause_buttons.append(pause_button)
    button_box.append(pause_button)

    stop_button = Gtk.Button.new_from_icon_name("process-stop-symbolic")
    stop_button.set_valign(Gtk.Align.CENTER)
    stop_button.get_style_context().add_class("circular")
    stop_button.connect("clicked", on_stop_clicked, self, download_item)
    button_box.append(stop_button)

    box_1.append(box)

    box_1_expanding_box = Gtk.Box()
    Gtk.Widget.set_hexpand(box_1_expanding_box, True)
    box_1.append(box_1_expanding_box)

    box_1.append(button_box)
    box_2.append(box_1)
    box_2.append(progress_bar)

    self.download_list.append(download_item)
    download_item.index = len(self.downloads)

    return [progress_bar, speed_label, self.pause_buttons[len(self.pause_buttons)-1], download_item, filename_label]

def on_pause_clicked(button, self, pause_button, download_item, force_pause):
    download_thread = self.downloads[download_item.index]
    if download_thread.download.is_paused and force_pause == False:
        download_thread.resume()
        image = Gtk.Image.new()
        image.set_from_icon_name("media-playback-pause-symbolic")
        pause_button.set_child(image)
        self.all_paused = False
        self.header_pause_content.set_icon_name("media-playback-pause-symbolic")
        self.header_pause_content.set_label(_("Pause All"))
        self.header_pause_button.set_sensitive(True)
    else:
        download_thread.pause()
        image = Gtk.Image.new()
        image.set_from_icon_name("media-playback-start-symbolic")
        pause_button.set_child(image)
        download_thread.save_state()

        all_paused = True

        for download_thread in self.downloads.copy():
            if (download_thread.download) and (download_thread.is_alive()) and (download_thread.download.is_paused == False):
                all_paused = False

        if (all_paused == True):
            self.all_paused = True
            self.header_pause_content.set_icon_name("media-playback-start-symbolic")
            self.header_pause_content.set_label(_("Resume All"))
            self.header_pause_button.set_sensitive(True)

def on_stop_clicked(button, self, download_item):
    index = download_item.index
    download_thread = self.downloads[index]
    deletefiles = True
    if (download_thread.download) and ((download_thread.download.is_torrent) and (download_thread.download.seeder)):
        deletefiles = False
    try:
        download_thread.stop(deletefiles)
    except:
        pass
    self.download_list.remove(download_item)
    if (download_item in self.downloads):
        self.downloads.remove(download_item)
    if (self.download_list.get_first_child() == None):
        self.header_pause_content.set_icon_name("media-playback-pause-symbolic")
        self.header_pause_content.set_label(_("Pause All"))
        self.header_pause_button.set_sensitive(False)
