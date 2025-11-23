#!/bin/sh

set -e

ARCH="$1"
if [ -z "$ARCH" ]; then
  exit 1
fi

sign_all_binaries() {
    find "$1" -type f | while read -r file; do
        if file "$file" | grep -q "Mach-O"; then
            codesign -f -s - "$file" 2>/dev/null || true
        fi
    done
}

cd "$(dirname "$0")"

DEPS_DIR="dependencies-$ARCH"
BUILD_DIR="build-$ARCH"

rm -rf $BUILD_DIR/Varia.app
mkdir -p $BUILD_DIR/Varia.app/Contents/MacOS
swiftc launch-varia.swift -o $BUILD_DIR/Varia.app/Contents/MacOS/Varia
mkdir -p $BUILD_DIR/Varia.app/Contents/Resources/tray
cp varia.icns $BUILD_DIR/Varia.app/Contents/Resources
cp -r $DEPS_DIR/* $BUILD_DIR/Varia.app/Contents/Resources

codesign --remove-signature $BUILD_DIR/Varia.app/Contents/Resources/ffmpeg
codesign --remove-signature $BUILD_DIR/Varia.app/Contents/Resources/ffprobe
codesign --remove-signature $BUILD_DIR/Varia.app/Contents/Resources/aria2c
codesign --remove-signature $BUILD_DIR/Varia.app/Contents/Resources/7zz
codesign --remove-signature $BUILD_DIR/Varia.app/Contents/Resources/deno

cp Info.plist $BUILD_DIR/Varia.app/Contents
cp varia.spec ../src
cd ../src/tray
pyinstaller -n varia-tray --noconsole --noconfirm tray_windows.py
mv dist/varia-tray/* ../../mac/$BUILD_DIR/Varia.app/Contents/Resources/tray
cp tray.png ../../mac/$BUILD_DIR/Varia.app/Contents/Resources/tray/_internal
cd ..
pyinstaller --noconfirm varia.spec
mv dist/variamain/* ../mac/$BUILD_DIR/Varia.app/Contents/Resources

sign_all_binaries "$BUILD_DIR/Varia.app"
codesign -f -s - "$BUILD_DIR/Varia.app"

cd ../mac
create-dmg --volname 'Varia' --volicon 'dmg-icon.icns' --background ./dmg-background.png --window-size 700 478 --icon Varia.app 175 200 --app-drop-link 525 200 Varia-$ARCH.dmg ./Varia.app