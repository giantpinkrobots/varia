### *Important for translators: There's now a Weblate instance for Varia, please refer to [the contributing page](https://github.com/giantpinkrobots/varia/blob/next/CONTRIBUTING.md).*

<br>

#
<br>

<p float="left" align="middle">
  <img src="https://raw.githubusercontent.com/giantpinkrobots/varia/main/windows/icon.ico" width=200 />
</p>

# Varia

<h3>Download manager for files, torrents and videos</h3>

<h3><a href="https://giantpinkrobots.github.io/varia">🌐 Homepage</a></h3>

<br>

| Download for Linux | Download for Windows | Download for macOS | Browser Extension |
| -------- | ------- | ------- |
| [⬇ Flathub](https://flathub.org/apps/io.github.giantpinkrobots.varia) | [⬇ Installer](https://github.com/giantpinkrobots/varia/releases/download/v2026.1.5/varia-windows-setup-amd64.exe) | [⬇ Apple Silicon arm64](https://github.com/giantpinkrobots/varia/releases/download/v2026.1.5-1/varia-mac-arm.dmg) | [❖ Firefox](https://addons.mozilla.org/firefox/addon/varia-integrator/) |
| [⬇ Snap Store](https://snapcraft.io/varia) | [⬇ Portable](https://github.com/giantpinkrobots/varia/releases/download/v2026.1.5/varia-windows-portable-amd64.zip) | [⬇ Intel amd64](https://github.com/giantpinkrobots/varia/releases/download/v2026.1.5-1/varia-mac-intel.dmg) | [❖ Chrome](https://chrome.google.com/webstore/detail/dacakhfljjhgdfdlgjpabkkjhbpcmiff) |
| [⬇ AUR (unofficial)](https://aur.archlinux.org/packages/varia) | | | | [⬇ AppImage (unofficial)](https://github.com/pkgforge-dev/Varia-AppImage) | | | |

<br>

Varia is a download manager for Linux and Windows that supports regular files as well as torrents and video/audio streams. It is a frontend for aria2 and yt-dlp.

<p float="left" align="middle">
  <img src="https://raw.githubusercontent.com/giantpinkrobots/varia/main/screenshots/Screenshot-Varia-1.png" width=350 />
  <img src="https://raw.githubusercontent.com/giantpinkrobots/varia/main/screenshots/Screenshot-Varia-2.png" width=350 />
</p>

<p float="left" align="middle">

![](https://img.shields.io/github/stars/giantpinkrobots/varia.svg) ![](https://img.shields.io/github/watchers/giantpinkrobots/varia.svg) ![](https://img.shields.io/github/followers/giantpinkrobots.svg?style=social&label=Follow&maxAge=2592000) ![](https://img.shields.io/github/license/giantpinkrobots/varia.svg)

</p>

<p float="left" align="middle">
  <a href="https://hosted.weblate.org/engage/varia/">
    <img src="https://hosted.weblate.org/widget/varia/multi-auto.svg" alt="Translation status" />
  </a>
</p>

## Get Varia

### Linux

#### Flatpak
The main way to get Varia that is supported by me is via [Flathub](https://flathub.org/apps/io.github.giantpinkrobots.varia).
```
flatpak install flathub io.github.giantpinkrobots.varia
```
This requires you to have Flatpak and the Flathub Flatpak repository installed on your system.

#### Snap
You can get Varia through the [Snap Store](https://snapcraft.io/varia).
```
sudo snap install varia
```
However, you will need to give it additional permissions through the terminal if you want to use the "Shutdown after Completion" feature:
```
sudo snap connect varia:shutdown
```

#### Unofficial methods
These are **unofficial** methods of getting Varia. They are built and distributed by others and may get updates later than official methods.

- [AUR on Arch Linux](https://aur.archlinux.org/packages/varia)
- [AppImage](https://github.com/pkgforge-dev/Varia-AppImage)

### Windows
You can find amd64 builds of Varia in the Releases section in both installer and portable forms. The installer version is recommended and it includes an auto updater function.

### macOS (experimental)
macOS version is brand new and still experimental. Available for both Apple Silicon and Intel Macs in the Releases section.

## Browser Extension
Download it for [Firefox](https://addons.mozilla.org/firefox/addon/varia-integrator/) or [Chrome](https://chrome.google.com/webstore/detail/dacakhfljjhgdfdlgjpabkkjhbpcmiff).

## Building

There are two branches here: 'next' and 'main'. The Next branch is where all new development happens before merging into the Main branch at each stable release. I develop and test for Flatpak first and tackle other platforms later, which may result in the Next branch not building on other platforms due to new platform-specific issues or newly introduced dependencies. Therefore it is recommended you use Flatpak to test out the Next branch, or at least keep this in mind in case of problems. Next is the default branch.

### for Linux

Varia is developed to be Flatpak-first, therefore the easiest way to build it from source on Linux is to run it with [GNOME Builder](https://flathub.org/en/apps/org.gnome.Builder).

Using flatpak-builder is also possible:
```
flatpak-builder --force-clean --install --user ./_build ./io.github.giantpinkrobots.varia.json && flatpak run io.github.giantpinkrobots.varia
```

To build Varia outside Flatpak, you need these dependencies:

- Meson
- Gtk4 and its development libraries
- Pango
- (Python) GObject
- Libadwaita
- aria2
- (Python) aria2p
- yt-dlp
- 7zip (7z)
- FFmpeg (without GPL is okay)
- Deno
- Libayatana-AppIndicator
- gettext
- (Python) appdirs
- (Python) requests
- (Python) emoji-country-flag

Then, you can use meson commands to build Varia:
```
git clone https://github.com/giantpinkrobots/varia
cd varia
meson setup builddir
cd builddir
meson compile
sudo meson install
```

### for Windows

- [Get MSYS2.](https://www.msys2.org/)
- Open the MSYS2 standard shell and update everything before continuing:
```
pacman -Syyu
```
- Either clone Varia inside the shell or copy the folder to your MSYS2 home folder and navigate into it:
```
cd varia
```
- Run the build script (which will also automatically install the dependencies):
```
./windows/build.sh
```
Or with the updater function enabled: (it just creates an empty file in the dist directory named 'updater-function-enabled')
```
./windows/build.sh -u
```

Varia will be built into src/dist/variamain. Main executable is variamain.exe.

### for macOS

macOS builds are handled with GitHub Actions through (this)[https://github.com/giantpinkrobots/varia/blob/next/.github/workflows/mac-package.yml] file. I will prepare a friendlier automatic build script (like on Windows) later.

## Contributing

[Please refer to the contributing guide page.](https://github.com/giantpinkrobots/varia/blob/main/CONTRIBUTING.md)

## License

<a href=https://github.com/giantpinkrobots/varia/blob/main/LICENSE>Varia is licensed under the Mozilla Public License 2.0.</a>

But it also relies on many other libraries each with their own licenses, all of whom can be found in the dependencies_information directory.

## The name

The name "Varia" comes from the aria2 software it is based on, and I added a "V" to make it "Varia". In the Metroid series of games, there is a special suit you eventually get named a "<a href=https://metroid.fandom.com/wiki/Varia_Suit>Varia Suit</a>" with its main feature being allowing Samus to withstand extreme temperatures. I spent some time thinking about how to connect the Varia Suit to my app, but couldn't, soooo... I think it just sounds cool.
