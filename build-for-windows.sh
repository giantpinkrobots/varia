updater=0
debug=0

while getopts "hud" flag; do
	case $flag in
		h)
		echo "No flags - Build without the updater function"
		echo "-u - Enable the updater function"
		echo "-d - Enable debug mode"
		exit
		;;
		u)
		updater=1
		;;
		d)
		debug=1
		;;
	esac
done

echo "      -   Installing dependencies..."

pacman -S --noconfirm --needed mingw-w64-ucrt-x86_64-python
pacman -S --noconfirm --needed mingw-w64-ucrt-x86_64-gtk4
pacman -S --noconfirm --needed mingw-w64-ucrt-x86_64-libadwaita
pacman -S --noconfirm --needed mingw-w64-ucrt-x86_64-python-pillow
pacman -S --noconfirm --needed mingw-w64-ucrt-x86_64-python-gobject
pacman -S --noconfirm --needed mingw-w64-ucrt-x86_64-python-pip
pacman -S --noconfirm --needed mingw-w64-ucrt-x86_64-yt-dlp
pacman -S --noconfirm --needed mingw-w64-ucrt-x86_64-pyinstaller
pacman -S --noconfirm --needed mingw-w64-ucrt-x86_64-upx
pacman -S --noconfirm --needed unzip
pip install aria2p
pip install pystray
pip install emoji-country-flag

#echo "      -   Downloading aria2, ffmpeg and deno..."
echo "      -   Downloading aria2 and ffmpeg..."

aria2="aria2-1.37.0-win-64bit-build1"
ffmpeg="ffmpeg-n8.0-latest-win64-lgpl-shared-8.0"

rm -rf "./$aria2.zip"
rm -rf "./$ffmpeg.zip"
#rm -rf "./deno-x86_64-pc-windows-msvc.zip"
rm -rf "./aria2"
rm -rf "./ffmpeg"
#rm -rf "./deno"

wget "https://github.com/aria2/aria2/releases/download/release-1.37.0/$aria2.zip"
wget "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/$ffmpeg.zip"
#wget "https://github.com/denoland/deno/releases/download/v2.5.2/deno-x86_64-pc-windows-msvc.zip"
mkdir aria2
unzip -d aria2 $aria2.zip
mkdir ffmpeg
unzip -d ffmpeg $ffmpeg.zip
#mkdir deno
#unzip -d deno deno-x86_64-pc-windows-msvc.zip

echo "      -   Generating locales..."

rm -rf locale
mkdir locale
for po in po/*.po; do
	lang=$(basename "$po" .po)
	mkdir locale/$lang
	mkdir locale/$lang/LC_MESSAGES
	msgfmt -o "locale/$lang/LC_MESSAGES/varia.mo" "$po"
done

rm -rf src/dist
cp windows/icon.ico src/
cp windows/version.txt src/

if [ $debug -eq 1 ]; then
	echo "      -   Debug mode enabled"
	cp windows/varia-debug.spec src/varia.spec
else
	cp windows/varia.spec src/
fi

cd src

echo "      -   Building PyInstaller distributable of the main application"

pyinstaller varia.spec

cd tray

echo "      -   Building PyInstaller distributable of the tray process"

if [ $debug -eq 1 ]; then
	pyinstaller -n varia-tray --noconfirm tray_windows.py
else
	pyinstaller -n varia-tray --noconsole --noconfirm tray_windows.py
fi

cd ../..
cp -r locale src/dist/variamain/
mkdir src/dist/variamain/icons/
cp data/icons/hicolor/symbolic/apps/io.github.giantpinkrobots.varia-symbolic.svg src/dist/variamain/icons/
cp data/icons/hicolor/scalable/apps/io.github.giantpinkrobots.varia.svg src/dist/variamain/icons/
cp -r data/icons/hicolor/symbolic/ui/* src/dist/variamain/icons/
cp -r dependencies_information src/dist/variamain/
cp ./aria2/$aria2/aria2c.exe src/dist/variamain/
cp -r ./ffmpeg/$ffmpeg/bin/* src/dist/variamain/
#cp ./deno/deno.exe src/dist/variamain/

mkdir src/dist/variamain/tray
cp -r src/tray/dist/varia-tray/* src/dist/variamain/tray/
cp src/tray/tray.png src/dist/variamain/tray/_internal/

if [ $updater -eq 1 ]; then
	touch src/dist/variamain/updater-function-enabled
fi

echo "      -   Build complete."
echo "      -   src/dist/variamain/variamain.exe"
