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

if [ ! -f ./aria2c.exe ]; then
	echo "aria2c.exe does not exist. You need to copy it here before you can run this."
	exit
fi

echo "Installing dependencies..."

pacman -S --noconfirm --needed mingw-w64-x86_64-python
pacman -S --noconfirm --needed mingw-w64-x86_64-gtk4
pacman -S --noconfirm --needed mingw-w64-x86_64-libadwaita
pacman -S --noconfirm --needed mingw-w64-x86_64-python-pillow
pacman -S --noconfirm --needed mingw-w64-x86_64-python-gobject
pacman -S --noconfirm --needed mingw-w64-x86_64-python-pip
pip install aria2p
pip install pyinstaller

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

cp -r windows/* src/
cd src
pyinstaller varia.spec
cd ..
cp -r locale src/dist/variamain/
cp data/icons/hicolor/symbolic/apps/io.github.giantpinkrobots.varia-symbolic.svg src/dist/variamain/
cp data/icons/hicolor/scalable/apps/io.github.giantpinkrobots.varia.svg src/dist/variamain/
cp -r dependencies_information src/dist/variamain/
cp ./aria2c.exe src/dist/variamain/

if [ $updater -eq 1 ]; then
	touch src/dist/variamain/updater-function-enabled
fi

echo "Build complete."
echo "src/dist/variamain/variamain.exe"