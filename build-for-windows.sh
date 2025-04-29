updater=0

while getopts "hu" flag; do
	case $flag in
		h)
		echo "No flags - Build without the updater function"
		echo "-u - Enable the updater function"
		exit
		;;
		u)
		updater=1
		;;
	esac
done

echo "Installing dependencies..."

pacman -S --noconfirm --needed mingw-w64-ucrt-x86_64-python
pacman -S --noconfirm --needed mingw-w64-ucrt-x86_64-gtk4
pacman -S --noconfirm --needed mingw-w64-ucrt-x86_64-libadwaita
pacman -S --noconfirm --needed mingw-w64-ucrt-x86_64-python-pillow
pacman -S --noconfirm --needed mingw-w64-ucrt-x86_64-python-gobject
pacman -S --noconfirm --needed mingw-w64-ucrt-x86_64-python-pip
pacman -S --noconfirm --needed mingw-w64-ucrt-x86_64-yt-dlp
pacman -S --noconfirm --needed mingw-w64-ucrt-x86_64-pyinstaller
pacman -S --noconfirm --needed unzip
pip install aria2p
pip install pystray

echo "Downloading aria2 and ffmpeg..."

aria2="aria2-1.37.0-win-64bit-build1"
ffmpeg="ffmpeg-n7.1-latest-win64-lgpl-shared-7.1"

rm -rf "./$aria2.zip"
rm -rf "./$ffmpeg.zip"
rm -rf "./aria2"
rm -rf "./ffmpeg"

wget "https://github.com/aria2/aria2/releases/download/release-1.37.0/$aria2.zip"
wget "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/$ffmpeg.zip"
mkdir aria2
unzip -d aria2 $aria2.zip
mkdir ffmpeg
unzip -d ffmpeg $ffmpeg.zip

echo "Generating locales..."

rm -rf locale
mkdir locale
for po in po/*.po; do
	lang=$(basename "$po" .po)
	mkdir locale/$lang
	mkdir locale/$lang/LC_MESSAGES
	msgfmt -o "locale/$lang/LC_MESSAGES/varia.mo" "$po"
done

echo "Building PyInstaller distributable..."

rm -rf src/dist
cp -r windows/* src/
cd src
pyinstaller varia.spec
cd ..
cp -r locale src/dist/variamain/
mkdir src/dist/variamain/icons/
cp data/icons/hicolor/symbolic/apps/io.github.giantpinkrobots.varia-symbolic.svg src/dist/variamain/icons/
cp data/icons/hicolor/scalable/apps/io.github.giantpinkrobots.varia.svg src/dist/variamain/icons/
cp -r data/icons/hicolor/symbolic/ui/* src/dist/variamain/icons/
cp -r dependencies_information src/dist/variamain/
cp ./aria2/$aria2/aria2c.exe src/dist/variamain/
cp -r ./ffmpeg/$ffmpeg/bin/* src/dist/variamain/
cp src/tray/tray.png src/dist/variamain/

if [ $updater -eq 1 ]; then
	touch src/dist/variamain/updater-function-enabled
fi

echo "Build complete."
echo "src/dist/variamain/variamain.exe"
