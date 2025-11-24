#!/bin/sh

set -e

sign_all_binaries() {
    find "$1" -type f | while read -r file; do
        if file "$file" | grep -q "Mach-O"; then
            codesign -f -s - "$file" 2>/dev/null || true
        fi
    done
}

MAC_DIR="$1"
cd "$MAC_DIR/"

rm -rf "$MAC_DIR/Varia.app"
mkdir -p "$MAC_DIR/Varia.app/Contents/MacOS"
swiftc launch-varia.swift -o "$MAC_DIR/Varia.app/Contents/MacOS/Varia/"
mkdir -p "$MAC_DIR/Varia.app/Contents/Resources/tray"
cp "$MAC_DIR/varia.icns" "$MAC_DIR/Varia.app/Contents/Resources/"
cp -r "$MAC_DIR/dependencies/*" "$MAC_DIR/Varia.app/Contents/Resources/"

codesign --remove-signature "$MAC_DIR/Varia.app/Contents/Resources/ffmpeg"
codesign --remove-signature "$MAC_DIR/Varia.app/Contents/Resources/ffprobe"
codesign --remove-signature "$MAC_DIR/Varia.app/Contents/Resources/aria2c"
codesign --remove-signature "$MAC_DIR/Varia.app/Contents/Resources/7zz"
codesign --remove-signature "$MAC_DIR/Varia.app/Contents/Resources/deno"

cp "$MAC_DIR/Info.plist" "$MAC_DIR/Varia.app/Contents/"
cp "$MAC_DIR/varia.spec" "$MAC_DIR/../src/"
cd "$MAC_DIR/../src/tray/"
pyinstaller -n varia-tray --noconsole --noconfirm tray_windows.py
cp -r "./dist/varia-tray/*" "$MAC_DIR/Varia.app/Contents/Resources/tray/"
cp "./tray.png" "$MAC_DIR/Varia.app/Contents/Resources/tray/_internal/"
cd "$MAC_DIR/../src"
pyinstaller --noconfirm varia.spec
cp -r "./dist/variamain/*" "$MAC_DIR/Varia.app/Contents/Resources/"

sign_all_binaries "$MAC_DIR/Varia.app/"
codesign -f -s - "$MAC_DIR/Varia.app/"

cd "$MAC_DIR"
create-dmg --volname 'Varia' --volicon 'dmg-icon.icns' --background ./dmg-background.png --window-size 700 478 --icon Varia.app 175 200 --app-drop-link 525 200 Varia-$ARCH.dmg ./Varia.app