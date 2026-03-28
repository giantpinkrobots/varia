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
        "\n\n- aria2\n- yt-dlp\n- FFmpeg\n- Deno\n- 7zip\n- GTK4\n- Libadwaita\n- Meson\n- OpenSSL\n- Libayatana-AppIndicator\n- Python-appdirs\n- Python-aria2p\n- Python-certifi\n- Python-charset-normalizer\n- Python-gettext\n- Python-idna\n- Python-loguru\n- Python-requests\n- Python-setuptools\n- Python-urllib3\n- Python-websocket-client\n- Python-pystray\n- Python-emoji-country-flag\n- Python-winsdk-toast\n- PyInstaller\n\n" +
        _("The licenses of all of these pieces of software can be found in the dependencies_information directory in this application's app directory."))
    dialog.set_developers(["Giant Pink Robots! (@giantpinkrobots) https://github.com/giantpinkrobots"])
    dialog.set_application_icon("io.github.giantpinkrobots.varia")
    dialog.set_translator_credits(_("translator-credits"))
    dialog.set_artists(["Jakub Steiner"])
    dialog.set_release_notes_version(variaVersion)
    dialog.set_release_notes('''
        <p>v2026.3.27-1</p>
        <ul><li>Windows only: Fix FFmpeg dependencies on Windows</li></ul>
        <p>v2026.3.27</p>
        <ul><li>Ability to download playlists through the same Video/Audio functionality</li>
        <li>Ability to select individual files and folders to download through torrenting</li>
        <li>Option to dynamically send browser cookies through the browser extension upon each download (separate from cookies.txt file import support)</li></ul>''')
    
    if (os.uname().sysname == 'Linux'):
        dialog.add_other_app("io.github.giantpinkrobots.flatsweep",
                            "Flatsweep",
                            "Flatpak leftover cleaner")
        dialog.add_other_app("io.github.giantpinkrobots.bootqt",
                            "Bootqt",
                            "Create bootable drives")

    if self.use_ssd:
        dialog.set_content_width(self.get_default_size()[0])
        dialog.set_content_height(self.get_default_size()[1])
    dialog.present(self)
