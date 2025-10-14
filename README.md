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

| Download for Linux | Download for Windows | Browser Extension |
| -------- | ------- | ------- |
| [⬇ Flathub](https://flathub.org/apps/io.github.giantpinkrobots.varia) | [⬇ Installer](https://github.com/giantpinkrobots/varia/releases/download/v2025.10.14/varia-windows-setup-amd64.exe) | [❖ Firefox](https://addons.mozilla.org/firefox/addon/varia-integrator/) |
| [⬇ Snap Store](https://snapcraft.io/varia) | [⬇ Portable](https://github.com/giantpinkrobots/varia/releases/download/v2025.10.14/varia-windows-portable-amd64.zip) | [❖ Chrome](https://chrome.google.com/webstore/detail/dacakhfljjhgdfdlgjpabkkjhbpcmiff) |
| [⬇ AUR (unofficial)](https://aur.archlinux.org/packages/varia) | | |

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

#### AUR (Arch Linux) (Unofficial)
You can get Varia via the [AUR](https://aur.archlinux.org/packages/varia) as well, but it is **unofficial** and not handled by me.

### Windows
You can find amd64 builds of Varia in the Releases section in both installer and portable forms. The installer version is recommended and it includes an auto updater function.

## Browser Extension
Download it for [Firefox](https://addons.mozilla.org/firefox/addon/varia-integrator/) or [Chrome](https://chrome.google.com/webstore/detail/dacakhfljjhgdfdlgjpabkkjhbpcmiff).

## Building

There are two branches here: 'main' and 'next'. 'next' is where the feature developments for the next version happen.

The 'main' branch can be built with the instructions below. The 'next' branch may also be built with these instructions, but it's not guaranteed. If you want to build the 'next' branch, it can be built with GNOME Builder on Linux.

### for Linux

The easiest way of building Varia is to use GNOME Builder. Just clone this repository, and open the folder using Builder. Then, press run. This is the way I make Varia, and the 'next' branch can only be reliably built this way.

Varia is developed to be Flatpak-first, so it can be built with GNOME Builder with a single click on the Run button. You can also run it directly using flatpak-builder:
```
flatpak-builder --force-clean --install --user ./_build ./io.github.giantpinkrobots.varia.json && flatpak run io.github.giantpinkrobots.varia
```

To build Varia without Flatpak or GNOME Builder though, you'll need:
- meson
- python-setuptools
- Gtk4 and its development libraries
- Libadwaita
- gettext
- aria2 and the aria2p python package.
- yt-dlp python package
- FFmpeg (without GPL is okay)
- python-dbus-next

To install the ones besides aria2p on some Linux systems:
```
Ubuntu, Debian, Mint etc:
sudo apt install meson ninja-build aria2 python3-setuptools libgtk-4-dev libadwaita-1-0 gettext ffmpeg python3-dbus-next

Fedora, RHEL etc:
sudo dnf install meson ninja-build aria2 python3-setuptools gtk4-devel libadwaita gettext ffmpeg python3-dbus-next

Arch, EndeavourOS, Manjaro etc:
sudo pacman -S meson aria2 python-setuptools gtk4 libadwaita gettext ffmpeg python-dbus-next
```
To install aria2p and yt-dlp using pip (your distro probably doesn't have them in its repos - they're on the AUR for Arch):
```
pip install aria2p
pip install yt-dlp
```
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
- Run the build script:
```
./build-for-windows.sh
```
Or with the updater function enabled: (it just creates an empty file in the dist directory named 'updater-function-enabled')
```
./build-for-windows.sh -u
```

Varia will be built into src/dist/variamain. Main executable is variamain.exe.

## Contributing

[Please refer to the contributing guide page.](https://github.com/giantpinkrobots/varia/blob/main/CONTRIBUTING.md)

## License

<a href=https://github.com/giantpinkrobots/varia/blob/main/LICENSE>Varia is licensed under the Mozilla Public License 2.0.</a>

But it also relies on many other libraries each with their own licenses, all of whom can be found in the dependencies_information directory.

## The name

The name "Varia" comes from the aria2 software it is based on, and I added a "V" to make it "Varia". In the Metroid series of games, there is a special suit you eventually get named a "<a href=https://metroid.fandom.com/wiki/Varia_Suit>Varia Suit</a>" with its main feature being allowing Samus to withstand extreme temperatures. I spent some time thinking about how to connect the Varia Suit to my app, but couldn't, soooo... I think it just sounds cool.
