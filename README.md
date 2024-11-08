<center>
<p><img src="https://raw.githubusercontent.com/giantpinkrobots/varia/main/windows/icon.ico" width=200 /></p>

# Varia

<h3>Download manager based on aria2</h3>

<h3><a href="https://giantpinkrobots.github.io/varia">🌐 Homepage</a></h3>

<br>

| Download for Linux | Download for Windows | Browser Extension |
| -------- | ------- | ------- |
| [⬇ Flathub](https://flathub.org/apps/io.github.giantpinkrobots.varia) | [⬇ Installer](https://github.com/giantpinkrobots/varia/releases/download/v2024.11.7-1/varia-windows-setup-amd64.exe) | [❖ Firefox](https://addons.mozilla.org/firefox/addon/varia-integrator/) |
| [⬇ AUR (unofficial)](https://aur.archlinux.org/packages/varia) | [⬇ Portable](https://github.com/giantpinkrobots/varia/releases/download/v2024.11.7-1/varia-windows-portable-amd64.zip) | [❖ Chrome](https://chrome.google.com/webstore/detail/dacakhfljjhgdfdlgjpabkkjhbpcmiff) |

<br>

Varia is a simple download manager that conforms to the latest Libadwaita design guidelines, integrating nicely with GNOME. It uses the amazing aria2 to handle the downloads.

</center>

<p float="left" align="middle">
  <img src="https://raw.githubusercontent.com/giantpinkrobots/varia/main/screenshots/Screenshot-Varia-1.png" width=400 />
  <img src="https://raw.githubusercontent.com/giantpinkrobots/varia/main/screenshots/Screenshot-Varia-2.png" width=400 />
</p>

<p>
  
![](https://img.shields.io/github/commits-since/giantpinkrobots/varia/latest/main?label=commits%20since%20latest%20release)  ![](https://img.shields.io/github/forks/giantpinkrobots/varia.svg)  ![](https://img.shields.io/github/stars/giantpinkrobots/varia.svg)  ![](https://img.shields.io/github/watchers/giantpinkrobots/varia.svg)  ![](https://img.shields.io/github/issues/giantpinkrobots/varia.svg)  ![](https://img.shields.io/github/issues-closed/giantpinkrobots/varia.svg)  ![](https://img.shields.io/github/issues-pr/giantpinkrobots/varia.svg)  ![](https://img.shields.io/github/issues-pr-closed/giantpinkrobots/varia.svg)  ![](https://img.shields.io/github/license/giantpinkrobots/varia.svg)  ![](https://img.shields.io/github/followers/giantpinkrobots.svg?style=social&label=Follow&maxAge=2592000)

</p>

It supports basic functionality like continuing incomplete downloads from the previous session upon startup, pausing/cancelling all downloads at once, setting a speed limit, authentication with a username/password, setting the simultaneous download amount and setting the download directory.

## Get Varia

### Flatpak
The main way to get Varia that is supported by me is via [Flathub](https://flathub.org/apps/io.github.giantpinkrobots.varia).
```
flatpak install flathub io.github.giantpinkrobots.varia
```
This requires you to have Flatpak and the Flathub Flatpak repository installed on your system.

### AUR (Arch Linux)
You can get Varia via the [AUR](https://aur.archlinux.org/packages/varia) as well, but it is not distributed by me.

### Windows
You can find amd64 builds of Varia in the Releases section in both installer and portable forms. The installer version is recommended and it includes an auto updater function.

## Browser Extension
Download it for [Firefox](https://addons.mozilla.org/firefox/addon/varia-integrator/) or [Chrome](https://chrome.google.com/webstore/detail/dacakhfljjhgdfdlgjpabkkjhbpcmiff).

## Building

There are two branches here: 'main' and 'next'. 'next' is where the feature developments for the next version happen.

The 'main' branch can be built with the instructions below. The 'next' branch may also be built with these instructions, but it's not guaranteed. If you want to build the 'next' branch, it can be built with GNOME Builder on Linux.

### for Linux

The easiest way of building Varia is to use GNOME Builder. Just clone this repository, and open the folder using Builder. Then, press run. This is the way I make Varia, and the 'next' branch can only be reliably built this way.

To build Varia without Flatpak or GNOME Builder though, you'll need:
- meson
- python-setuptools
- Gtk4 and its development libraries
- Libadwaita
- gettext
- aria2 and the aria2p python package.

To install the ones besides aria2p on some Linux systems:
```
Ubuntu, Debian, Mint etc:
sudo apt install meson ninja-build aria2 python-setuptools libgtk-4-dev libadwaita-1-0 gettext

Fedora, RHEL etc:
sudo dnf install meson ninja-build aria2 python-setuptools gtk4-devel libadwaita gettext

Arch, EndeavourOS, Manjaro etc:
sudo pacman -S meson aria2 python-setuptools gtk4 libadwaita gettext
```
To install aria2p using pip (your distro probably doesn't have it in its repos - it's on the AUR for Arch):
```
pip install aria2p
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
- Open the mingw64 shell in MSYS2 and update everything before continuing:
```
pacman -Syyu
```
- Either clone Varia inside the shell or copy the folder to your MSYS2 home folder.
- [You need to get a copy of aria2c.exe](https://github.com/aria2/aria2/releases) and paste it into the root of the folder.
- Running 'build-for-windows.sh' will take care of the dependencies and everything else and build Varia WITHOUT the updater function. To enable the updater function you need to run the script with the '-u' argument. (or just create an empty file called 'updater-function-enabled' next to variamain.exe after completion)

Varia will be built into src/dist/variamain. Main executable is variamain.exe.

## Contributing

[Please refer to the contributing guide page.](https://github.com/giantpinkrobots/varia/blob/main/CONTRIBUTING.md)

## License

<a href=https://github.com/giantpinkrobots/varia/blob/main/LICENSE>Varia is licensed under the Mozilla Public License 2.0.</a>

But, it also relies on the following pieces of software and libraries:
- aria2
- OpenSSL
- aria2p
- GTK4
- Libadwaita
- Meson
- Python-appdirs
- Python-certifi
- Python-charset-normalizer
- Python-gettext
- Python-idna
- Python-loguru
- Python-requests
- Python-setuptools
- Python-urllib3
- Python-websocket-client

The licenses of all of these pieces of software can be found in the dependencies_information directory.

## The name

The name "Varia" comes from the aria2 software it is based on, and I added a "V" to make it "Varia". In the Metroid series of games, there is a special suit you eventually get named a "<a href=https://metroid.fandom.com/wiki/Varia_Suit>Varia Suit</a>" with its main feature being allowing Samus to withstand extreme temperatures. I spent some time thinking about how to connect the Varia Suit to my app, but couldn't, soooo... I think it just sounds cool.


