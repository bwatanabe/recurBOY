#!/bin/sh
# Copies the experimental WAS application files into an existing recurBOY
# SD image. The stock openFrameworks installation and its addons are preserved.
# Does not install an OS, build binaries, edit startup jobs, or touch GPIO.
set -eu

SCRIPT_DIR="$(CDPATH= cd "$(dirname "$0")" && pwd)"
TARGET_DIR="${1:-$HOME/openframeworks10.1/apps/myApps/ofRecurBoy}"

if [ ! -f "$SCRIPT_DIR/src/ofApp.cpp" ] || [ ! -f "$SCRIPT_DIR/src/ofApp.h" ] || [ ! -f "$SCRIPT_DIR/src/main.cpp" ]; then
    echo "ERROR: run this script from the cloned WAS fork's software/ofRecurBoy directory." >&2
    exit 1
fi
if [ ! -d "$TARGET_DIR/src" ] || [ ! -f "$TARGET_DIR/src/ofApp.cpp" ]; then
    echo "ERROR: stock recurBOY app not found at $TARGET_DIR" >&2
    echo "Pass the actual application path as the first argument, if different." >&2
    exit 1
fi
if [ ! -f "$TARGET_DIR/Makefile" ]; then
    echo "ERROR: target application has no Makefile; stopping." >&2
    exit 1
fi

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$TARGET_DIR/.was-backup/$STAMP"
mkdir -p "$BACKUP_DIR/src"
cp -p "$TARGET_DIR/src/ofApp.cpp" "$BACKUP_DIR/src/ofApp.cpp"
cp -p "$TARGET_DIR/src/ofApp.h" "$BACKUP_DIR/src/ofApp.h"
cp -p "$TARGET_DIR/src/main.cpp" "$BACKUP_DIR/src/main.cpp"
for name in startWASHeadless runWASVideoProcessor was_diagnostics.py was_fxctl.py; do
    if [ -f "$TARGET_DIR/$name" ]; then
        cp -p "$TARGET_DIR/$name" "$BACKUP_DIR/$name"
    fi
done

cp "$SCRIPT_DIR/src/ofApp.cpp" "$TARGET_DIR/src/ofApp.cpp"
cp "$SCRIPT_DIR/src/ofApp.h" "$TARGET_DIR/src/ofApp.h"
cp "$SCRIPT_DIR/src/main.cpp" "$TARGET_DIR/src/main.cpp"
cp "$SCRIPT_DIR/startWASHeadless" "$TARGET_DIR/startWASHeadless"
cp "$SCRIPT_DIR/runWASVideoProcessor" "$TARGET_DIR/runWASVideoProcessor"
cp "$SCRIPT_DIR/was_fxctl.py" "$TARGET_DIR/was_fxctl.py"
cp "$SCRIPT_DIR/was_diagnostics.py" "$TARGET_DIR/was_diagnostics.py"
cp "$SCRIPT_DIR/was_probe.sh" "$TARGET_DIR/was_probe.sh"
chmod +x "$TARGET_DIR/startWASHeadless" "$TARGET_DIR/runWASVideoProcessor" "$TARGET_DIR/was_fxctl.py" "$TARGET_DIR/was_probe.sh"

printf 'WAS sources installed to: %s\n' "$TARGET_DIR"
printf 'Original C++ source backed up to: %s\n' "$BACKUP_DIR"
printf '\nNext steps (after disabling conflicting stock auto-start):\n'
printf '  cd "%s"\n' "$TARGET_DIR"
printf '  make -j1\n'
printf '  python3 was_diagnostics.py --print-wiring\n'
printf '  WAS_DIAGNOSTICS=1 WAS_CAPTURE_ID=2 WAS_FX_SHADER=invert.frag sh startWASHeadless\n'
printf '  (later, without compiling) WAS_ENCODER=1 sh runWASVideoProcessor\n'
printf '\nNOTE: use a powered USB hub for the MiraBox on the tested Pi Zero 2 W.\n'
