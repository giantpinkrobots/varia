<p align="center"><img src="https://raw.githubusercontent.com/giantpinkrobots/varia/main/data/icons/hicolor/scalable/apps/io.github.giantpinkrobots.varia.svg" width=200 /></p>
<h1 align="center">Varia</h1>
<h3 align="center">Download manager based on aria2</h3>
<br>

<p align="center">
  
![](https://img.shields.io/github/commits-since/giantpinkrobots/varia/latest/main?label=commits%20since%20latest%20release)  ![](https://img.shields.io/github/forks/giantpinkrobots/varia.svg)  ![](https://img.shields.io/github/stars/giantpinkrobots/varia.svg)  ![](https://img.shields.io/github/watchers/giantpinkrobots/varia.svg)  ![](https://img.shields.io/github/issues/giantpinkrobots/varia.svg)  ![](https://img.shields.io/github/issues-closed/giantpinkrobots/varia.svg)  ![](https://img.shields.io/github/issues-pr/giantpinkrobots/varia.svg)  ![](https://img.shields.io/github/issues-pr-closed/giantpinkrobots/varia.svg)  ![](https://img.shields.io/github/license/giantpinkrobots/varia.svg)  ![](https://img.shields.io/github/followers/giantpinkrobots.svg?style=social&label=Follow&maxAge=2592000)

</p>

<p align="center"><a href="https://flathub.org/apps/io.github.giantpinkrobots.varia"><img src="https://dl.flathub.org/assets/badges/flathub-badge-i-en.svg" width=300 /></a></p>

Varia is a simple download manager that conforms to the latest Libadwaita design guidelines, integrating nicely with GNOME. It uses the amazing aria2 to handle the downloads.

<p float="left" align="middle">
  <img src="https://raw.githubusercontent.com/giantpinkrobots/varia/main/screenshots/Screenshot-Varia-1.png" width=400 />
  <img src="https://raw.githubusercontent.com/giantpinkrobots/varia/main/screenshots/Screenshot-Varia-2.png" width=400 />
</p>

It supports basic functionality like continuing incomplete downloads from the previous session upon startup, pausing/cancelling all downloads at once, setting a speed limit, authentication with a username/password, and setting the download directory.

## Get Varia

### Flatpak
The main way to get Varia that is supported by me is via [Flathub](https://flathub.org/apps/io.github.giantpinkrobots.varia).
```
flatpak install flathub io.github.giantpinkrobots.varia
```
This requires you to have Flatpak and the Flathub Flatpak repository installed on your system.

### AUR (Arch Linux)
You can get Varia via the [AUR](https://aur.archlinux.org/packages/varia) as well, but it is not distributed by me.

## Building

The easiest way of building Varia is to use GNOME Builder. Just clone this repository, and open the folder using Builder. Then, press run.

If you don't want to utilize Flatpak to build Varia you need:
- meson
- python-setuptools
- Gtk4 and its development libraries
- Libadwaita
- gettext
- aria2 and the aria2p python package.
To install the ones besides aria2p on some Linux systems:
```
Ubuntu, Debian, Mint etc: sudo apt install meson ninja-build aria2 python-setuptools libgtk-4-dev libadwaita-1-0 gettext
Fedora, RHEL etc: sudo dnf install meson ninja-build aria2 python-setuptools gtk4-devel libadwaita gettext
Arch, EndeavourOS, Manjaro etc: sudo pacman -S meson aria2 python-setuptools gtk4 libadwaita gettext
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

## License

<a href=https://github.com/giantpinkrobots/varia/blob/main/LICENSE>Varia is licensed under the Mozilla Public License 2.0.</a>

But, it also application relies on the following pieces of software:
- aria2: GPL v2 License (aria2 itself relies on OpenSSL: OpenSSL License)
- aria2p: ISC License

The licenses of all of these pieces of software can be found in the dependencies_information directory in this application's app directory.

## Contributing

Contributions are always welcome, of course! In the case of translations, they are done with .po files that you can create with a program like Poedit for example. Keep in mind that Varia is kind of a simple app at the moment, and I will keep adding new features so the translations you add right now can become incomplete when I add new features.

Also, I really want to change the logo as it's something I hastly hacked together in Krita. If you can make a logo that conforms to the GNOME logo design guidelines, that would be amazing!

## The name

The name "Varia" comes from the aria2 software it is based on, and I added a "V" to make it "Varia". In the Metroid series of games, there is a special suit you eventually get named a "<a href=https://metroid.fandom.com/wiki/Varia_Suit>Varia Suit</a>" with its main feature being allowing Samus to withstand extreme temperatures. I spent some time thinking about how to connect the Varia Suit to my app, but couldn't, soooo... I think it just sounds cool.


