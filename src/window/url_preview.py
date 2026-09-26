"""Preview dialog for batch URL addition from files or clipboard."""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gdk
from stringstorage import gettext as _
from url_file_parser import extract_urls_from_text, extract_urls_from_file, parse_urls_for_preview


class URLPreviewDialog(Adw.Dialog):
    """Dialog showing extracted URLs with checkboxes for selective batch addition."""

    def __init__(self, parent, urls, callback):
        super().__init__()
        self.set_title(_("Select URLs to Add"))
        self.set_default_size(500, 400)
        self.parent = parent
        self.urls = urls
        self.callback = callback

        self._build_ui()

    def _build_ui(self):
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_margin_start(12)
        content.set_margin_end(12)

        # Summary label
        summary = Gtk.Label(
            label=_("{count} URLs found in source.").replace("{count}", str(len(self.urls)))
        )
        summary.add_css_class("heading")
        content.append(summary)

        # List box with checkboxes
        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        list_box.add_css_class("view")
        list_box.set_margin_start(4)
        list_box.set_margin_end(4)

        self.url_checkboxes = []
        for url_info in parse_urls_for_preview(self.urls):
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            row.set_valign(Gtk.Align.CENTER)
            row.set_margin_top(4)
            row.set_margin_bottom(4)

            checkbox = Gtk.CheckButton()
            checkbox.set_active(True)  # Default: all selected
            row.append(checkbox)

            label = Gtk.Label()
            label.set_markup('<span font_size="small">{}</span>'.format(
                GLib.markup_escape_text(url_info['url'][:200] + "..." if len(url_info['url']) > 200 else url_info['url'])
            ))
            label.set_halign(Gtk.Align.START)
            label.set_selectable(True)
            row.append(label)

            list_box.append(row)
            self.url_checkboxes.append((checkbox, url_info['url']))

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_child(list_box)
        content.append(scrolled)

        # Selection info
        self.selection_label = Gtk.Label(label=_("{n} selected").replace("{n}", str(len(self.urls))))
        self.selection_label.add_css_class("dim-label")
        content.append(self.selection_label)

        self.set_child(content)

        # Connect checkbox changes to update count
        for checkbox, url in self.url_checkboxes:
            checkbox.connect("toggled", self._on_checkbox_toggled)

        # Actions
        self.add_response("cancel", _("Cancel"))
        self.add_response("add", _("Add Selected"))
        self.set_response_appearance("add", Adw.ResponseAppearance.SUGGESTED)
        self.set_default_response("add")

        self.connect("response", self._on_response)

    def _on_checkbox_toggled(self, checkbox):
        count = sum(1 for cb, _ in self.url_checkboxes if cb.get_active())
        self.selection_label.set_label(_("{n} selected").replace("{n}", str(count)))

    def _on_response(self, dialog, response_id):
        if response_id == "add":
            selected = [url for checkbox, url in self.url_checkboxes if checkbox.get_active()]
            if self.callback:
                GLib.idle_add(self.callback, selected)
        dialog.close()


def show_file_import_dialog(parent):
    """Open file chooser and show URL preview for .txt, .csv, .list files."""
    chooser = Gtk.FileChooserNative(
        title=_("Select URL File"),
        transient_for=parent,
        action=Gtk.FileChooserAction.OPEN,
        accept_label=_("Open"),
        cancel_label=_("Cancel"),
    )
    chooser.set_modal(True)

    # Filter for supported extensions
    filter_txt = Gtk.FileFilter()
    filter_txt.set_name(_("Text Files"))
    filter_txt.add_pattern("*.txt")
    filter_txt.add_pattern("*.csv")
    filter_txt.add_pattern("*.list")
    chooser.add_filter(filter_txt)

    filter_all = Gtk.FileFilter()
    filter_all.set_name(_("All Files"))
    filter_all.add_pattern("*")
    chooser.add_filter(filter_all)

    def on_response(chooser, response):
        if response == Gtk.ResponseType.ACCEPT:
            filepath = chooser.get_filename()
            if filepath:
                try:
                    urls = extract_urls_from_file(filepath)
                    if urls:
                        dialog = URLPreviewDialog(parent, urls, parent.on_batch_urls_added)
                        dialog.present()
                    else:
                        _show_no_urls_dialog(parent)
                except Exception as e:
                    _show_error_dialog(parent, str(e))
        chooser.destroy()

    chooser.connect("response", on_response)
    chooser.present()


def show_clipboard_import_dialog(parent):
    """Read clipboard asynchronously and show URL preview."""
    clipboard = parent.get_clipboard()

    def on_text_read(clipboard, result):
        try:
            text = clipboard.read_text_finish(result)
        except Exception:
            text = None
        if not text:
            _show_no_urls_dialog(parent)
            return

        urls = extract_urls_from_text(text)
        if not urls:
            _show_no_urls_dialog(parent)
        elif len(urls) == 1:
            parent.on_batch_urls_added(urls)
        else:
            dialog = URLPreviewDialog(parent, urls, parent.on_batch_urls_added)
            dialog.present()

    clipboard.read_text_async(None, on_text_read)


def _show_error_reading_clipboard(parent):
    """No-op placeholder kept for symmetry with the file path."""
    pass


def _show_no_urls_dialog(parent):
    """Show info dialog when no URLs found."""
    dialog = Adw.AlertDialog()
    dialog.set_title(_("No URLs Found"))
    dialog.set_body(_("No valid links found in source."))
    dialog.add_response("ok", _("OK"))
    dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
    dialog.set_close_response("ok")
    dialog.present(parent)


def _show_error_dialog(parent, message):
    """Show error dialog for file read failures."""
    dialog = Adw.AlertDialog()
    dialog.set_title(_("Error"))
    dialog.set_body(message)
    dialog.add_response("ok", _("OK"))
    dialog.set_response_appearance("ok", Adw.ResponseAppearance.DESTRUCTIVE)
    dialog.set_close_response("ok")
    dialog.present(parent)
