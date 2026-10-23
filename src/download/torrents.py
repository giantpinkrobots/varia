import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GObject, GLib
from stringstorage import gettext as _
from pathlib import Path
import libtorrent as lt
from download.listen import add_download_to_ui

class FileNode(GObject.Object):
    name = GObject.Property(type=str)
    is_dir = GObject.Property(type=bool, default=False)
    selected = GObject.Property(type=bool, default=True)
    file_index = GObject.Property(type=int, default=-1)

    def __init__(self, name, is_dir=False, parent=None, file_index=-1):
        super().__init__()
        self.name = name
        self.is_dir = is_dir
        self.parent = parent
        self.file_index = file_index
        self.children = Gio.ListStore.new(FileNode) if is_dir else None # Only directories will have children

def torrent_select_files_dialog(self):
    torrent_info = self.torrent_instance.torrent_file()
    storage = self.torrent_instance.torrent_file().files()
    root_store = Gio.ListStore.new(FileNode)

    tree_model = Gtk.TreeListModel.new(
        root_store,
        False,
        False,
        lambda item: item.children if item.is_dir else None
    )

    selection = Gtk.NoSelection.new(tree_model)
    factory = Gtk.SignalListItemFactory()
    nodes = {}

    updating = False # To prevent recursive updates when toggling checkboxes

    for file_index in range(storage.num_files()):
        parts = Path(storage.file_path(file_index)).parts

        current_store = root_store
        current_parent = None
        current_path = Path()

        for i, part in enumerate(parts):
            current_path /= part
            key = str(current_path)

            is_last = i == len(parts) - 1
            is_dir = not is_last

            if key not in nodes:
                node = FileNode(
                    name=part,
                    is_dir=is_dir,
                    parent=current_parent,
                    file_index=file_index if is_last else -1
                )

                nodes[key] = node
                current_store.append(node)

            node = nodes[key]

            if node.is_dir:
                current_store = node.children

            current_parent = node
    
    def on_checkbox_toggled(button):
        nonlocal updating

        if updating:
            return

        updating = True

        node = button._node
        new_value = button.get_active()
        set_selected_recursive(node, new_value)

        if node.parent != None:
            update_parent_state(node.parent)

        updating = False

        ok_button.set_sensitive(bool(get_selected_files(root_store))) # Disable the OK button if nothing is selected
    
    def update_parent_state(parent):
        if not parent.is_dir:
            return
        
        total = parent.children.get_n_items()
        selected = 0

        for i in range(total):
            child = parent.children.get_item(i)

            if child.props.selected:
                selected += 1
        
        if selected == total:
            parent.props.selected = True
            parent._checkbox.set_inconsistent(False)

        elif selected == 0:
            parent.props.selected = False
            parent._checkbox.set_inconsistent(False)

        else:
            parent.props.selected = True
            parent._checkbox.set_inconsistent(True)

        if parent.parent:
            update_parent_state(parent.parent)
    
    def set_selected_recursive(node, value):
        node.props.selected = value

        if node.is_dir:
            for i in range(node.children.get_n_items()):
                child = node.children.get_item(i)
                set_selected_recursive(child, value)
            
            node._checkbox.set_inconsistent(False)

    def setup(factory, list_item):
        expander = Gtk.TreeExpander()

        box = Gtk.Box(spacing=6)
        checkbox = Gtk.CheckButton()
        label = Gtk.Label(xalign=0)

        box.append(checkbox)
        box.append(label)

        expander.set_child(box)
        list_item.set_child(expander)

        # Connect the checkbox signal and store handler ID for later blocking and unblocking
        handler_id = checkbox.connect("toggled", on_checkbox_toggled)
        checkbox._handler_id = handler_id

    def bind(factory, list_item):
        row = list_item.get_item()
        node = row.get_item()

        expander = list_item.get_child()
        expander.set_list_row(row)

        box = expander.get_child()
        checkbox = box.get_first_child()
        label = box.get_last_child()

        label.set_label(node.name)

        checkbox.bind_property(
            "active",
            node,
            "selected",
            GObject.BindingFlags.BIDIRECTIONAL
        )

        # Block the signal handler temporarily to prevent it from firing when we set the active state based on the node's selected property
        checkbox.handler_block(checkbox._handler_id)
        checkbox.set_active(node.selected)
        checkbox.handler_unblock(checkbox._handler_id)

        checkbox._node = node
        node._checkbox = checkbox

    factory.connect("setup", setup)
    factory.connect("bind", bind)

    def get_selected_files(root_store):
        selected_files = []
        def traverse(node):
            if node.is_dir:
                for i in range(node.children.get_n_items()):
                    child = node.children.get_item(i)
                    traverse(child)

            else:
                if node.props.selected:
                    selected_files.append(node.file_index)

        for i in range(root_store.get_n_items()):
            node = root_store.get_item(i)
            traverse(node)

        return selected_files

    list_view = Gtk.ListView.new(selection, factory)

    scrolled_list_view = Gtk.ScrolledWindow(vexpand=True, hexpand=True, propagate_natural_height=True, propagate_natural_width=True)
    scrolled_list_view.set_child(list_view)

    dialog_header = Adw.HeaderBar()
    dialog_header.add_css_class('flat')
    dialog_header.set_show_start_title_buttons(False)
    dialog_header.set_show_end_title_buttons(False)

    button_box = Gtk.Box(spacing=6)
    button_box.set_halign(Gtk.Align.END)
    button_box.set_margin_top(12)
    button_box.set_margin_bottom(12)
    button_box.set_margin_start(12)
    button_box.set_margin_end(12)

    cancel_button = Gtk.Button(label=_("Cancel"))
    cancel_button.add_css_class('flat')
    ok_button = Gtk.Button(label=_("OK"))
    ok_button.add_css_class('suggested-action')

    button_box.append(cancel_button)
    button_box.append(ok_button)

    dialog_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    dialog_box.append(dialog_header)
    dialog_box.append(scrolled_list_view)
    dialog_box.append(button_box)
    
    dialog = Adw.AlertDialog(title=_("Select Files to Download"))
    dialog.set_child(dialog_box)
    dialog.set_can_close(False)

    selected_files = []
    download_commence = False
    download_stopped = False

    def on_dialog_close(button):
        nonlocal download_commence

        try:
            if download_commence == False:
                self.cancelled = True
                download_stop()

        finally:
            self.selection_event.set()
            dialog.set_can_close(True)
            dialog.close()

    def on_ok_clicked(dialog):
        nonlocal selected_files
        nonlocal download_commence
        selected_files = get_selected_files(root_store)

        if selected_files:
            info = self.torrent_instance.torrent_file()
            storage = info.files()

            priorities = []

            for file_index in range(storage.num_files()):
                if file_index in selected_files:
                    priorities.append(4) # Priority is normal
                else:
                    priorities.append(0) # Exclude

            self.torrent_instance.prioritize_files(priorities)
            self.torrent_instance.resume()

            self.torrent_file_select_completed = True
            download_commence = True

        else:
            download_stop()
            download_commence = False

        self.selection_event.set()
        on_dialog_close(None)

    def download_stop():
        nonlocal download_stopped

        if download_stopped == False:
            if self.torrent_instance:
                self.app.ltsession.remove_torrent(
                    self.torrent_instance,
                    lt.options_t.delete_files
                )
                self.torrent_instance = None

            self.stop()

            download_stopped = True

    ok_button.connect("clicked", on_ok_clicked)
    cancel_button.connect("clicked", on_dialog_close)

    if self.app.appconf['torrent_always_download_all'] == '0':
        GLib.idle_add(dialog.present, self.app)

    else:
        on_dialog_close(None)

def show_torrent_not_enabled_error(self):
    dialog = Adw.AlertDialog()
    dialog.set_body(_("Torrenting is disabled."))
    dialog.add_response("ok",  _("OK"))
    dialog.set_default_response("ok")
    dialog.set_close_response("ok")
    dialog.present(self)

def add_torrent_file(self, filepath):
    if filepath.endswith(".torrent"):
        if self.appconf['torrent_enabled'] == '0':
            show_torrent_not_enabled_error(self)

        else:
            class torrent_instance_object(object):
                pass
            
            torrent_instance = torrent_instance_object
            torrent_instance.url = filepath
            torrent_instance.name = filepath
            add_download_to_ui(self, torrent_instance, self, "torrent", False)
            self.check_all_status()