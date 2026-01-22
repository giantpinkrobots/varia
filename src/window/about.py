import os
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from stringstorage import gettext as _

def show_about(app, variaapp, self, variaVersion):
    if self.overlay_split_view.get_show_sidebar() and \
        self.overlay_split_view.get_collapsed():

        self.overlay_split_view.set_show_sidebar(False)

    dialog = Adw.AboutDialog()
    dialog.set_application_name("Varia")
    dialog.set_version(variaVersion)
    dialog.set_developer_name("Giant Pink Robots!")
    dialog.set_license_type(Gtk.License(Gtk.License.MPL_2_0))
    #dialog.set_comments(_("aria2 based download manager utilizing GTK4 and Libadwaita.")) # Disabling details page
    dialog.set_website("https://giantpinkrobots.github.io/varia")
    dialog.set_issue_url("https://github.com/giantpinkrobots/varia/issues")
    dialog.set_copyright("2023 Giant Pink Robots!\n\n" + _("This application relies on the following pieces of software:") +
        "\n\n- aria2\n- yt-dlp\n- FFmpeg\n- Deno\n- 7zip\n- GTK4\n- Libadwaita\n- Meson\n- OpenSSL\n- Libayatana-AppIndicator\n- Python-appdirs\n- Python-aria2p\n- Python-certifi\n- Python-charset-normalizer\n- Python-gettext\n- Python-idna\n- Python-loguru\n- Python-requests\n- Python-setuptools\n- Python-urllib3\n- Python-websocket-client\n- Python-pystray\n- Python-emoji-country-flag\n- PyInstaller\n\n" +
        _("The licenses of all of these pieces of software can be found in the dependencies_information directory in this application's app directory."))
    dialog.set_developers(["Giant Pink Robots! (@giantpinkrobots) https://github.com/giantpinkrobots"])
    dialog.set_application_icon("io.github.giantpinkrobots.varia")
    dialog.set_translator_credits(_("translator-credits"))
    dialog.set_artists(["Jakub Steiner"])
    dialog.set_release_notes_version(variaVersion)
    dialog.set_release_notes('''
        <p>v2026.1.5</p>
        <ul><li>Option to automatically extract downloaded archives</li>
        <li>Inclusion of the Deno JavaScript engine as required by yt-dlp</li>
        <li>Newly added tooltip text for various options and better keyboard navigation to improve accessibility</li>
        <li>The scheduler is now much more reliable</li>
        <li>Paused downloads show their download percentages when reloaded upon app startup before resume</li>
        <li>Download details window layout no longer breaks with very long URLs</li>
        <li>New languages: Hebrew and Cornish</li>
        <li>(Snap version) The tray icon on Snap is fully functional</li>
        <li>(Mac version) Initial experimental release on macOS</li></ul>
        <p>***</p>
        <p>v2026.1.5-1</p>
        <ul><li>Fix for macOS Tahoe where a library couldn't be found</li></ul>
        <p>***</p>
        <p>v2026.1.5-2</p>
        <ul><li>Fix for Linux where toggling Open on Startup causes a crash</li></ul>
        <p>***</p>
        <p>v2026.1.5-3</p>
        <ul><li>Fix for Windows where 7z wouldn't be included</li>
        <li>Fix where Varia wouldn't automatically start in background mode</li>
        <li>Better handling of external processes like aria2c and tray to minimize the possibility of having a zombie process left running if Varia crashes</li></ul>''')
    
    if (os.uname().sysname == 'Linux'):
        dialog.add_other_app("io.github.giantpinkrobots.flatsweep",
                            "Flatsweep",
                            "Flatpak leftover cleaner")
        dialog.add_other_app("io.github.giantpinkrobots.bootqt",
                            "Bootqt",
                            "Create bootable drives")

    if os.name == 'nt':
        dialog.set_content_width(self.get_default_size()[0])
        dialog.set_content_height(self.get_default_size()[1])
    dialog.present(self)
