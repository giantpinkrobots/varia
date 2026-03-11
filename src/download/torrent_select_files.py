import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GObject, GLib
from stringstorage import gettext as _
from pathlib import Path
import os
import shutil

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
    files = self.download.files
    downloaddir_path = Path(self.downloaddir)
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

    for file_index, file in enumerate(files):
        parts = Path(file.path).relative_to(downloaddir_path).parts
        current_store = root_store
        current_parent = None
        current_path = Path()

        for i, part in enumerate(parts):
            current_path = current_path / part
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

    dialog_header = Adw.HeaderBar()
    dialog_header.add_css_class('flat')
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
    dialog_box.append(list_view)
    dialog_box.append(button_box)
    
    dialog = Adw.AlertDialog(title=_("Select Files to Download"))
    dialog.set_child(dialog_box)
    dialog.set_can_close(False)

    selected_files = []

    def on_ok_clicked(button):
        nonlocal selected_files
        selected_files = get_selected_files(root_store)
        dialog.set_can_close(True)
        dialog.close()

    def on_cancel_clicked(button):
        dialog.set_can_close(True)
        dialog.close()

    ok_button.connect("clicked", on_ok_clicked)
    cancel_button.connect("clicked", on_cancel_clicked)

    GLib.idle_add(dialog.present, self.app)

    def on_dialog_closed(dialog):
        if selected_files:
            file_indices = [str(idx + 1) for idx in selected_files] # aria2 file indices start with 1
            select_file_option = ",".join(file_indices)

            if self.download:
                self.api.client.call("aria2.changeOption", [self.download.gid, {"select-file": select_file_option}])

                while True:
                    try:
                        self.download.resume()
                        break

                    except:
                        pass

                self.torrent_file_select_completed = True

                # Remove the unselected files
                for download_file in self.download.files:
                    if (str(download_file.index) not in file_indices) and (download_file.path.exists()):
                        os.remove(download_file.path)

        else: # Cancelled
            if self.download:
                shutil.rmtree(os.path.join(self.downloaddir, self.download.files[0].path.relative_to(self.downloaddir).parts[0]))
                self.stop()

        self.selection_event.set()

    dialog.connect("closed", on_dialog_closed)