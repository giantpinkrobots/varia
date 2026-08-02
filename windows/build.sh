shopt -s extglob
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

cd "$(dirname "$0")"
cd ..

echo -e "\n\n\n      -   Installing dependencies...\n"

pacman -S --noconfirm --needed mingw-w64-ucrt-x86_64-python \
	mingw-w64-ucrt-x86_64-gtk4 \
	mingw-w64-ucrt-x86_64-libadwaita \
	mingw-w64-ucrt-x86_64-python-pillow \
	mingw-w64-ucrt-x86_64-python-gobject \
	mingw-w64-ucrt-x86_64-python-pip \
	mingw-w64-ucrt-x86_64-yt-dlp \
	mingw-w64-ucrt-x86_64-pyinstaller \
	mingw-w64-ucrt-x86_64-upx \
	mingw-w64-ucrt-x86_64-7zip \
	mingw-w64-ucrt-x86_64-python-winsdk \
	mingw-w64-ucrt-x86_64-python-pywin32 \
	mingw-w64-ucrt-x86_64-gcc \
	mingw-w64-ucrt-x86_64-openssl \
	mingw-w64-ucrt-x86_64-cmake \
	mingw-w64-ucrt-x86_64-ninja \
	mingw-w64-ucrt-x86_64-git \
	mingw-w64-ucrt-x86_64-boost \
	mingw-w64-ucrt-x86_64-boost-libs \
	unzip

pip install --break-system-packages aria2p \
	pystray \
	emoji-country-flag \
	winsdk-toast

echo -e "\n\n\n      -   Downloading aria2, ffmpeg, 7z and deno...\n"

aria2="aria2-1.37.0-win-64bit-build1"
ffmpeg="ffmpeg-n8.1.2-34-g9b6c8969e0-win64-lgpl-8.1"
ffmpeg_tag="autobuild-2026-08-02-13-17"
sevenzip="7z2600-x64"

rm -rf "./$aria2.zip"
rm -rf "./$ffmpeg.zip"
rm -rf "./deno-x86_64-pc-windows-msvc.zip"
rm -rf "./aria2"
rm -rf "./ffmpeg"
rm -rf "./deno"
rm -rf "./7zr.exe"
rm -rf "./$sevenzip.exe"
rm -rf "./7zip"

wget "https://github.com/aria2/aria2/releases/download/release-1.37.0/$aria2.zip"
wget "https://github.com/BtbN/FFmpeg-Builds/releases/download/$ffmpeg_tag/$ffmpeg.zip"
wget "https://github.com/denoland/deno/releases/download/v2.5.2/deno-x86_64-pc-windows-msvc.zip"
wget "https://7-zip.org/a/$sevenzip.exe"
mkdir aria2
unzip -d aria2 $aria2.zip
mkdir ffmpeg
unzip -d ffmpeg $ffmpeg.zip
mkdir deno
unzip -d deno deno-x86_64-pc-windows-msvc.zip
7z x -o7zip "./$sevenzip.exe"

echo -e "\n\n\n      -   Building and installing Libtorrent from source...\n"

git clone --recursive "http://github.com/arvidn/libtorrent"
cd libtorrent
git switch --detach 578e06824c3546f3371ab43967ab288a7e253eca
mkdir build
cd build
cmake .. -G Ninja -DCMAKE_BUILD_TYPE=Release -Dpython-bindings=ON -DBUILD_SHARED_LIBS=OFF -Dstatic_runtime=ON -DPython3_EXECUTABLE="$(which python)"
cmake --build .
cmake --install . --prefix /ucrt64
cd ../..

echo -e "\n\n\n      -   Generating locales...\n"

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

echo -e "\n\n\n      -   Building PyInstaller distributable of the main application\n"

pyinstaller varia.spec

cd tray

echo -e "\n\n\n      -   Building PyInstaller distributable of the tray process\n"

if [ $debug -eq 1 ]; then
	pyinstaller -n varia-tray --noconfirm tray_win_mac.py
else
	pyinstaller -n varia-tray --noconsole --noconfirm tray_win_mac.py
fi

cd ../..
cp -r locale src/dist/variamain/
mkdir src/dist/variamain/icons/
cp data/icons/symbolic/apps/io.github.giantpinkrobots.varia-symbolic.svg src/dist/variamain/icons/
cp data/icons/scalable/apps/io.github.giantpinkrobots.varia.svg src/dist/variamain/icons/
cp -r data/icons/actions/* src/dist/variamain/icons/
cp -r dependencies_information src/dist/variamain/
cp ./aria2/$aria2/aria2c.exe src/dist/variamain/
cp -r ./ffmpeg/$ffmpeg/bin/!(ffplay.exe) src/dist/variamain/
cp ./deno/deno.exe src/dist/variamain/
cp ./7zip/7z.exe src/dist/variamain/
cp ./7zip/7-zip.dll src/dist/variamain/
cp ./7zip/7-zip32.dll src/dist/variamain/
cp ./7zip/7z.dll src/dist/variamain/

mkdir src/dist/variamain/tray
cp -r src/tray/dist/varia-tray/* src/dist/variamain/tray/
cp src/tray/trayicon_win.png src/dist/variamain/tray/_internal/

if [ $updater -eq 1 ]; then
	touch src/dist/variamain/updater-function-enabled
fi

echo -e "\n\n\n      -   Build complete."
echo "      -   src/dist/variamain/variamain.exe"
