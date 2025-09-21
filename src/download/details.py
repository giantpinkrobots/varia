import gi
import os
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Pango, GLib, Gio, GObject
from stringstorage import gettext as _
from urllib.parse import unquote

def show_download_details_dialog(button, self, download_item):
    details_dialog_shown = True

    details_dialog = Adw.PreferencesDialog(title=_("Download Details"))

    prefs_page = Adw.PreferencesPage()
    details_dialog.add(prefs_page)

    group_1 = Adw.PreferencesGroup()
    prefs_page.add(group_1)

    actionrow_download_type = Adw.ActionRow(title=_("Type"))
    label_download_type = Gtk.Label(label=download_item.download_thread.download_details.get('type', ''))
    actionrow_download_type.add_suffix(label_download_type)
    group_1.add(actionrow_download_type)

    actionrow_download_status = Adw.ActionRow(title=_("Status"))
    label_download_status = Gtk.Label(label=download_item.download_thread.download_details.get('status', ''))
    actionrow_download_status.add_suffix(label_download_status)
    group_1.add(actionrow_download_status)

    actionrow_download_url = Adw.ActionRow(title=_("URL"))
    label_url = Gtk.Label(label=download_item.download_thread.url)
    label_url.set_ellipsize(Pango.EllipsizeMode.END)
    label_url.set_selectable(True)
    actionrow_download_url.add_suffix(label_url)
    group_1.add(actionrow_download_url)

    actionrow_download_percentage = Adw.ActionRow(title=_("Percentage Downloaded"))
    label_percentage = Gtk.Label()
    actionrow_download_percentage.add_suffix(label_percentage)
    group_1.add(actionrow_download_percentage)

    actionrow_download_remaining = Adw.ActionRow(title=_("Remaining"))
    label_remaining = Gtk.Label()
    actionrow_download_remaining.add_suffix(label_remaining)
    group_1.add(actionrow_download_remaining)

    actionrow_download_download_speed = Adw.ActionRow(title=_("Download Speed"))
    label_download_speed = Gtk.Label()
    actionrow_download_download_speed.add_suffix(label_download_speed)
    group_1.add(actionrow_download_download_speed)

    # Peers

    scrolled_window = None

    if download_item and download_item.download_thread and download_item.download_thread.mode == "regular" and download_item.download_thread.download.is_torrent:
        actionrow_download_seeding_speed = Adw.ActionRow(title=_("Seeding Speed"))
        label_seeding_speed = Gtk.Label()
        actionrow_download_seeding_speed.add_suffix(label_seeding_speed)
        group_1.add(actionrow_download_seeding_speed)

        if download_item.download_thread.download.is_torrent:
            group_2 = Adw.PreferencesGroup(title=_("Torrent Peers"))
            prefs_page.add(group_2)

            scrolled_window = Gtk.ScrolledWindow()
            scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
            group_2.add(scrolled_window)

            class Peer(GObject.GObject):
                peerId = GObject.Property(type=str, default="")
                downloadSpeed = GObject.Property(type=str, default="")
                uploadSpeed = GObject.Property(type=str, default="")
                ip = GObject.Property(type=str, default="")
                seeder = GObject.Property(type=str, default="")

            peer_store = Gio.ListStore.new(Peer)
            peer_model = Gtk.SingleSelection(model=peer_store)
            peer_view = Gtk.ColumnView(model=peer_model)

            scrolled_window.set_child(peer_view)

            def add_column(title, prop_name):
                factory = Gtk.SignalListItemFactory()

                def setup(factory, list_item):
                    label = Gtk.Label(xalign=0)
                    list_item.set_child(label)

                def bind(factory, list_item):
                    peer = list_item.get_item()
                    label = list_item.get_child()
                    value = peer.get_property(prop_name)
                    label.set_text(str(value))

                factory.connect("setup", setup)
                factory.connect("bind", bind)

                column = Gtk.ColumnViewColumn(title=title, factory=factory)
                column.set_resizable(True)
                peer_view.append_column(column)
            
            add_column("Client", "peerId")
            add_column("IP", "ip")
            add_column("DL", "downloadSpeed")
            add_column("UL", "uploadSpeed")
            add_column("Seeder", "seeder")

            def equalize_columns(view):
                columns_amount = len(view.get_columns())
                if columns_amount == 0:
                    return

                width = view.get_allocated_width()
                column_width = width // columns_amount

                for column in view.get_columns():
                    column.set_fixed_width(column_width)

                scrolled_window.set_max_content_width(prefs_page.get_width() - 50)
                scrolled_window.set_min_content_width(prefs_page.get_width() - 50)

            peer_view.connect_after("realize", lambda view: equalize_columns(view))

    def update_details():
        close_dialog = True

        try:
            if details_dialog_shown and download_item and download_item.download_thread and download_item.download_thread.download_details:
                details = download_item.download_thread.download_details
                label_download_status.set_text(details.get('status', ''))
                label_percentage.set_text(details.get('percentage', ''))
                label_remaining.set_text(details.get('remaining', ''))
                label_download_speed.set_text(details.get('download_speed', ''))

                if download_item.download_thread.mode == "regular" and download_item.download_thread.download.is_torrent:
                    label_seeding_speed.set_text(details.get('torrent_seeding_speed', ''))

                updated_peers = []

                for peer_data in details.get("torrent_peers", []):
                    
                    peer_id = unquote(peer_data.get("peerId", ""))
                    if peer_id.startswith("-AR"):
                        peer_id = f"Aria2 ({peer_id[3:]})"
                    elif peer_id.startswith("-TR"):
                        peer_id = f"Transmission ({peer_id[3:]})"
                    elif peer_id.startswith("-qB"):
                        peer_id = f"qBittorrent ({peer_id[3:]})"
                    elif peer_id.startswith("-DE"):
                        peer_id = f"Deluge ({peer_id[3:]})"
                    elif peer_id.startswith("-UT"):
                        peer_id = f"µTorrent ({peer_id[3:]})"
                    elif peer_id.startswith("-AZ"):
                        peer_id = f"Azureus/Vuze ({peer_id[3:]})"
                    elif peer_id.startswith("-LT"):
                        peer_id = f"libtorrent ({peer_id[3:]})"

                    peer = Peer(
                        peerId = peer_id,
                        ip = peer_data.get("ip", ""),
                        downloadSpeed = peer_data.get("downloadSpeed", ""),
                        uploadSpeed = peer_data.get("uploadSpeed", ""),
                        seeder = str(peer_data.get("seeder", "")),
                    )

                    updated_peers.append(peer)

                peer_store.splice(0, peer_store.get_n_items(), updated_peers)

                close_dialog = False
            
            else:
                close_dialog = True
        
        except:
            close_dialog = True

        if close_dialog:
            details_dialog.close()
            return False

        else:
            GLib.timeout_add(1000, update_details)

    def update_size(*_):
        details_dialog.set_content_width(self.get_width())
        details_dialog.set_content_height(self.get_height())

        if scrolled_window:
            scrolled_window.set_max_content_width(prefs_page.get_width() - 50)
            scrolled_window.set_min_content_width(prefs_page.get_width() - 50)

    self.connect("notify::default-width", update_size)
    self.connect("notify::default-height", update_size)
    update_size()

    if os.name == 'nt':
        details_dialog.set_content_width(self.get_default_size()[0])
        details_dialog.set_content_height(self.get_default_size()[1])
    details_dialog.present(self)

    GLib.idle_add(update_details)