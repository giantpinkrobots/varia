import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Pango, GLib, Gio
from stringstorage import gettext as _
from download.thread import DownloadThread
from download.details import show_download_details_dialog
import json
import os
import subprocess

def on_download_clicked(button, self, entry, downloadname, download, mode, video_options, paused, dir, percentage):
    if isinstance(entry, str):
        url = entry
    else:
        url = entry.get_text()
        entry.set_text("")
    
    if isinstance(video_options, str):
        video_options = json.loads(video_options)

    if url:
        if downloadname:
            download_item = create_actionrow(self, downloadname)
        
        else:
            download_item = create_actionrow(self, url)

        download_thread = DownloadThread(self, url, download_item, downloadname, download, mode, video_options, paused, dir, percentage)
        download_item.download_thread = download_thread
        # Route via QueueManager so the download lands in the active queue
        if hasattr(self, 'queue_manager'):
            self.queue_manager.add_download(download_thread)
        else:
            self.downloads.append(download_thread)
        download_thread.start()

        if paused == False:
            self.all_paused = False
    
    return download_thread

def create_actionrow(self, filename):
    download_item = Adw.Bin()

    download_item.add_css_class('card')

    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    box_1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    box_1.set_margin_bottom(6)

    box_2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    box_2.set_margin_start(10)
    box_2.set_margin_end(10)
    box_2.set_margin_top(8)
    box_2.set_margin_bottom(10)
    download_item.set_child(box_2)

    percentage_and_filename_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    percentage_and_filename_box.set_margin_bottom(2)

    download_spinner = Adw.Spinner()
    download_spinner.set_margin_end(6)

    download_type_icon = Gtk.Image()
    download_type_icon.add_css_class("dimmed")
    download_type_icon.set_margin_end(6)
    download_type_icon.set_visible(False)

    percentage_and_filename_box.append(download_spinner)
    percentage_and_filename_box.append(download_type_icon)

    percentage_label = Gtk.Label(label=_("{number}%").replace("{number}", "0"))
    percentage_label.set_halign(Gtk.Align.START)
    percentage_label.add_css_class("dim-label")
    percentage_label.set_margin_end(4)
    percentage_and_filename_box.append(percentage_label)

    filename_label = Gtk.Label(label=str(filename))
    filename_label.set_ellipsize(Pango.EllipsizeMode.END)
    filename_label.set_halign(Gtk.Align.START)
    percentage_and_filename_box.append(filename_label)

    box.append(percentage_and_filename_box)

    progress_bar = Gtk.ProgressBar()

    speed_label = Gtk.Label()
    speed_label.set_ellipsize(Pango.EllipsizeMode.END)
    speed_label.set_halign(Gtk.Align.START)
    speed_label.add_css_class("dim-label")
    box.append(speed_label)

    button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
    button_box.set_margin_start(10)

    info_button = Gtk.Button.new_from_icon_name("info-outline-symbolic")
    info_button.set_valign(Gtk.Align.CENTER)
    info_button.add_css_class("circular")
    info_button.connect("clicked", show_download_details_dialog, self, download_item)
    info_button.set_tooltip_text(_("Download Details"))
    button_box.append(info_button)

    pause_button = Gtk.Button.new_from_icon_name("media-playback-pause-symbolic")
    pause_button.set_valign(Gtk.Align.CENTER)
    pause_button.add_css_class("circular")
    pause_button.connect_handler_id = pause_button.connect("clicked", on_pause_clicked, self, pause_button, download_item, False, True)
    pause_button.set_retry_mode = pause_button_set_retry_mode
    pause_button.set_open_mode = pause_button_set_open_mode
    pause_button.set_tooltip_text(_("Pause"))
    button_box.append(pause_button)

    stop_button = Gtk.Button.new_from_icon_name("media-playback-stop-symbolic")
    stop_button.set_valign(Gtk.Align.CENTER)
    stop_button.add_css_class("circular")
    stop_button.add_css_class("destructive-action")
    stop_button.connect("clicked", on_stop_clicked, self, download_item)
    stop_button.set_tooltip_text(_("Stop"))
    button_box.append(stop_button)
    # Secondary menu: move to queue / move to folder
    menu_button = Gtk.MenuButton()
    menu_button.set_valign(Gtk.Align.CENTER)
    menu_button.add_css_class("circular")
    menu_button.set_icon_name("open-menu-symbolic")
    menu_button.set_tooltip_text(_("More"))
    _attach_actionrow_popover(menu_button, self, download_item)
    button_box.append(menu_button)
    download_item.menu_button = menu_button

    box_1.append(box)

    box_1_expanding_box = Gtk.Box()
    Gtk.Widget.set_hexpand(box_1_expanding_box, True)
    box_1.append(box_1_expanding_box)

    box_1.append(button_box)
    box_2.append(box_1)
    box_2.append(progress_bar)

    self.download_list.prepend(download_item)
    GLib.idle_add(self.content_root_overlay.remove_overlay, self.status_page_widget)

    download_item.spinner = download_spinner
    download_item.type_icon = download_type_icon
    download_item.percentage_label = percentage_label
    download_item.progress_bar = progress_bar
    download_item.speed_label = speed_label
    download_item.pause_button = pause_button
    download_item.stop_button = stop_button
    download_item.filename_label = filename_label
    download_item.info_button = info_button

    return download_item

def on_pause_clicked(button, self, pause_button, download_item, force_pause, run_pause_function):
    if download_item.download_thread.paused and force_pause == False:
        download_item.download_thread.resume()

    else:
        download_item.download_thread.pause()

def on_stop_clicked(button, self, download_item):
    download_item.download_thread.stop()

def pause_button_set_retry_mode(button, self, download_item):
    GLib.idle_add(button.set_icon_name, "view-refresh-symbolic")
    button.disconnect(button.connect_handler_id)
    button.connect_handler_id = button.connect("clicked", pause_button_on_retry_clicked, self, download_item)
    button.set_tooltip_text(_("Retry"))

def pause_button_set_open_mode(button, self, download_item):
    GLib.idle_add(button.set_icon_name, "application-x-executable-symbolic")
    button.disconnect(button.connect_handler_id)
    button.connect_handler_id = button.connect("clicked", pause_button_on_open_clicked, self, download_item)
    button.set_tooltip_text(_("Open File"))

def pause_button_on_retry_clicked(button, self, download_item):
    if download_item.mode == "playlist":
        downloaddir = os.path.join(download_item.downloaddir, "..") # Playlists download into a subdirectory,
                                                                    # so we need to take the above directory
    else:
        downloaddir = download_item.downloaddir

    new_download_item = on_download_clicked(None, self, download_item.url, download_item.downloadname, None, download_item.mode, download_item.video_options, False, downloaddir, 0)

    self.download_list.reorder_child_after(new_download_item.actionrow, download_item.actionrow)
    self.downloads.remove(new_download_item)
    self.downloads.insert(self.downloads.index(download_item), new_download_item)

    download_item.stop()

def pause_button_on_open_clicked(button, self, download_item):
    if os.path.exists(download_item.filepath):
        if (os.uname().sysname == 'Darwin'):
            subprocess.call(('open', download_item.filepath))
        else:
            Gio.AppInfo.launch_default_for_uri("file://" + download_item.filepath, None)
def _attach_actionrow_popover(menu_button, self, download_item):
    """Attach a popover with queue/location actions to the menu button."""
    popover = Gtk.Popover()
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    box.set_margin_top(6)
    box.set_margin_bottom(6)
    box.set_margin_start(6)
    box.set_margin_end(6)

    move_folder_button = Gtk.Button.new_with_label(_("Move to folder…"))
    move_folder_button.set_halign(Gtk.Align.FILL)
    move_folder_button.connect("clicked", _move_to_folder_clicked, self, download_item)
    box.append(move_folder_button)

    if hasattr(self, 'queue_manager') and len(self.queue_manager.get_all_queue_ids()) > 1:
        queue_label = Gtk.Label(label=_("Move to queue"))
        queue_label.add_css_class("dim-label")
        queue_label.set_halign(Gtk.Align.START)
        box.append(queue_label)
        for queue_id in self.queue_manager.get_all_queue_ids():
            queue = self.queue_manager.get_queue(queue_id)
            if queue_id == download_item.download_thread.get_queue_id():
                continue
            queue_button = Gtk.Button.new_with_label(queue.name)
            queue_button.set_halign(Gtk.Align.FILL)
            queue_button.connect("clicked", _move_to_queue_clicked, self, download_item, queue_id)
            box.append(queue_button)

    popover.set_child(box)
    popover.set_parent(menu_button)
    menu_button.set_popover(popover)


def _move_to_folder_clicked(button, self, download_item):
    download_thread = download_item.download_thread
    if not (download_thread.cancelled or download_thread.is_complete):
        # Pre-download: set the target directory for this download
        folder_chooser = Gtk.FolderChooserNative(
            title=_("Set Download Folder"),
            transient_for=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
            accept_label=_("Select"),
            cancel_label=_("Cancel"),
        )
        folder_chooser.set_modal(True)
        if os.path.exists(download_thread.downloaddir):
            folder_chooser.set_folder(download_thread.downloaddir)
        folder_chooser.set_initial_folder(GLib.get_home_dir())

        def on_folder_response(chooser, response):
            if response == Gtk.ResponseType.ACCEPT:
                new_dir = chooser.get_file().get_path()
                if new_dir:
                    download_thread.set_download_path(new_dir)
                    GLib.idle_add(download_thread.show_message, _("Download folder set."))
            chooser.destroy()

        folder_chooser.connect("response", on_folder_response)
        folder_chooser.show()
    else:
        # Post-download: move the completed file
        file_chooser = Gtk.FileChooserNative(
            title=_("Move Download To…"),
            transient_for=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
            accept_label=_("Move Here"),
            cancel_label=_("Cancel"),
        )
        file_chooser.set_modal(True)
        if os.path.exists(os.path.dirname(download_thread.filepath or "")):
            file_chooser.set_folder(os.path.dirname(download_thread.filepath))
        else:
            file_chooser.set_initial_folder(GLib.get_home_dir())

        def on_move_response(chooser, response):
            if response == Gtk.ResponseType.ACCEPT:
                new_dir = chooser.get_file().get_path()
                if new_dir and download_thread.filepath:
                    new_path = os.path.join(new_dir, os.path.basename(download_thread.filepath))
                    if download_thread.relocate_download(new_path):
                        GLib.idle_add(download_thread.show_message, _("Download moved."))
            chooser.destroy()

        file_chooser.connect("response", on_move_response)
        file_chooser.show()


def _move_to_queue_clicked(button, self, download_item, queue_id):
    download_thread = download_item.download_thread
    if hasattr(self, 'queue_manager'):
        if self.queue_manager.move_download(download_thread, queue_id):
            GLib.idle_add(download_thread.show_message, _("Moved to queue."))