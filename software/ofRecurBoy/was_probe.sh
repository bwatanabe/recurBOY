#!/bin/sh
# Read-only diagnostic probe for stock recurBOY on a Raspberry Pi Zero 2 W.
# Does not write to the system, enable GPIO, or depend on the original shield.
set -u

section() { printf '\n=== %s ===\n' "$1"; }

section "Hardware"
if [ -r /proc/device-tree/model ]; then
    tr -d '\000' </proc/device-tree/model
    printf '\n'
fi
uname -a
if command -v vcgencmd >/dev/null 2>&1; then
    vcgencmd get_throttled 2>/dev/null || true
fi

section "OS"
if [ -r /etc/os-release ]; then
    cat /etc/os-release
fi

section "Memory / disk"
free -m 2>/dev/null || true
df -h / 2>/dev/null || true

section "Network"
hostname -I 2>/dev/null || true
if command -v ip >/dev/null 2>&1; then
    ip -brief addr 2>/dev/null || true
fi

section "Expected recurBOY app locations"
for p in \
    "$HOME/openframeworks10.1/apps/myApps/ofRecurBoy" \
    "$HOME/openFrameworks/apps/myApps/ofRecurBoy" \
    "$HOME/openframeworks10.1/apps/myApps/recurBOY"; do
    if [ -d "$p" ]; then
        printf 'FOUND %s\n' "$p"
        ls -ld "$p/src" "$p/bin" "$p/Makefile" 2>/dev/null || true
    else
        printf 'NOT FOUND %s\n' "$p"
    fi
done

section "FX and PATTERN asset folders (counts)"
for p in "$HOME/EFFECT" "$HOME/Fx" "$HOME/PATTERN" "$HOME/Shaders"; do
    if [ -d "$p" ]; then
        printf '%s: ' "$p"
        find "$p" -maxdepth 1 -type f 2>/dev/null | wc -l | tr -d ' '
    else
        printf '%s: not present\n' "$p"
    fi
done

section "I2C availability (no bus scan)"
if [ -e /dev/i2c-1 ]; then
    ls -l /dev/i2c-1
else
    printf 'I2C bus 1 is not exposed yet (check raspi-config)\n'
fi
section "Capture devices (no capture adapter needed yet)"
ls -l /dev/video* 2>/dev/null || printf 'No /dev/video devices\n'
if command -v v4l2-ctl >/dev/null 2>&1; then
    v4l2-ctl --list-devices 2>/dev/null || true
fi

section "Existing automatic boot launch"
crontab -l 2>/dev/null | grep -i -E 'recur|ofrecur|make run' || printf 'No matching user crontab entry\n'
if command -v systemctl >/dev/null 2>&1; then
    systemctl list-unit-files 2>/dev/null | grep -i 'recur' || true
fi

section "Probe complete"
printf 'No hardware pin state or files were changed.\n'
