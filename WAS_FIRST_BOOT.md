# WAS recurBOY — First boot on a fresh Raspberry Pi Zero 2 W card

**Target:** Fresh microSD, Pi Zero 2 W, mini-HDMI monitor, built-in Wi-Fi,
salvaged SSD1306 I²C OLED and two arcade buttons. No recurBOY shield.

**Current status:** Prepared deployment instructions; no on-device tests yet.
See [WAS_SETUP.md](WAS_SETUP.md) for the shader/video/OSC architecture.

## 1. Flash the official image

Download upstream [recurBOY v3.1.0s image (ZIP, ~1.8 GB)](
https://s3.eu-central-1.wasabisys.com/underscores-storage/recurboy_v3_1_0.zip).
The official [release notes](
https://github.com/cyberboy666/recurBOY/releases/tag/v3.1.0s_v1_1_1h)
recommend Etcher or Raspberry Pi Imager to flash to an SD card of **8 GB or more**.
A 16–32 GB card gives comfortable space for development.

Do **not** first flash a generic Raspberry Pi OS image: recurBOY contains
legacy openFrameworks graphics and capture dependencies installed in the
official image. The developer reports testing original recurBOY on Zero 2 W
successfully; the exact stock image and this WAS fork still require validation.

## 2. Set up remote access before first boot

A complete stock recurBOY image may attempt to start its unmodified TFT/
shield-based UI, which does not exist on the repurposed Pi. Plan to access
the Pi through **SSH**, not the original recurBOY panel.

After flashing, eject/reinsert the card if needed and open its FAT boot
partition on the Mac (usually `boot` or `bootfs`).

- Create a completely empty file named `ssh` (no filename extension),
  unless SSH has already been enabled.
- For older Raspberry Pi OS images, `wpa_supplicant.conf` on the boot
  partition can preconfigure the Pi's wireless connection:

```ini
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="YOUR_2.4GHZ_WIFI_SSID"
    psk="YOUR_WIFI_PASSWORD"
}
```

Edit those placeholders **on the local card**, not in the GitHub repo.
This older boot-file method does not work on Bookworm+; if this image
has changed OS families, use a USB-gadget or other supported access method.
The Raspberry Pi Zero 2 W Wi-Fi radio supports 2.4 GHz networks.

Insert card, connect mini-HDMI monitor, power through micro-USB **PWR IN**.
First boot may include partition expansion and restart.

The v3.1.0 release documents initial account `pi`, initial password
`cyberboy666`. Try:

```sh
ssh pi@recurboy.local
# or use the IP address assigned by your router:
ssh pi@<PI_IP_ADDRESS>
```

If SSH warns of a changed host key and you've connected to a different
machine at this address before, verify the identity before updating
`known_hosts`. Once you can log in, change the public image default password:

```sh
passwd
```

No custom OLED display activity is expected yet: stock recurBOY uses a
different TFT controller. A blank screen is **not proof the Pi failed to boot**.

## 3. Read-only hardware and image assessment

Before changing auto-start, cloning the WAS fork, or compiling anything:

```sh
uname -a
cat /etc/os-release
crontab -l
ls -ld /home/pi/openframeworks10.1/apps/myApps/ofRecurBoy
ls /home/pi/EFFECT /home/pi/Fx 2>/dev/null
ls -l /dev/i2c-1
```

We are checking OS/kernel compatibility, the actual openFrameworks app path,
and where the bundled shader library lives.

For a consolidated report, if `git` works on the image:

```sh
git clone --single-branch --branch was/headless-v0.1 \
  https://github.com/bwatanabe/recurBOY.git \
  /home/pi/recurBOY-was

sh /home/pi/recurBOY-was/software/ofRecurBoy/was_probe.sh
```

This probe is read-only and **does not configure GPIO, disable boot services,
or alter any video settings**. If `git clone` does not work with the legacy
image, transfer the script from your Mac via `scp`, or paste the shell
commands above.

**First checkpoint:** Capture the report and OS version before installing
the modified C++ app. If the screen is black or Wi-Fi is missing, debug this
stock-image boot stage before attempting the WAS modifications.

## 4. Disable the stock recurBOY UI before using WAS

After identifying the active stock startup entry, disable its automatic
execution **only** (do not remove any add-ons or system services).
Historical recurBOY images launch a shell command from user crontab, so
look for a line resembling:

```text
@reboot sh /home/pi/openframeworks10.1/apps/myApps/ofRecurBoy/startRecurBoy
```

If you find that line, run `crontab -e` and comment it out with `#`.
If there is no such line, inspect the startup mechanism before making
changes. Do not delete the original start script.

If it already launched, stop the old `ofRecurBoy` and `display.py`
processes before starting our modified version; don't run both concurrently.

## 5. Deploy the WAS application

From the cloned branch, run:

```sh
sh /home/pi/recurBOY-was/software/ofRecurBoy/installWASIntoImage.sh
```

The script checks the stock application path and **backs up its original
C++ app sources** before copying the WAS versions and new scripts.
It does not modify `bin/data`, the original settings, addons, or video
assets, and does not attempt a build automatically.

Compile carefully on a 512 MB Pi:

```sh
cd /home/pi/openframeworks10.1/apps/myApps/ofRecurBoy
make -j1
```

If `make` reports missing libraries/addons or compiler problems, capture
the log and resolve the compatibility issue before continuing.

## 6. Start the optional OLED diagnostics

This can be tested **without USB video capture**:

```sh
cd /home/pi/openframeworks10.1/apps/myApps/ofRecurBoy
python3 was_diagnostics.py --print-wiring
# Confirm the I2C OLED appears at 0x3c, if i2c-tools is installed:
i2cdetect -y 1
python3 was_diagnostics.py
```

Expect `ENGINE: OFFLINE` until the C++ renderer starts. CTRL-C ends
the OLED diagnostic process. Button 1 is BCM17 and Button 2 BCM27,
both active-low to ground. Rotary encoder BCM22/23/4 is reserved;
PCM5102 DAC BCM18/19/21 is unused.

## 7. Launch WAS video FX mode (only after C++ builds)

With a compatible HDMI-to-USB UVC capture dongle connected to the Pi's
**USB** OTG port, and a source HDMI feed attached to the dongle:

```sh
cd /home/pi/openframeworks10.1/apps/myApps/ofRecurBoy
WAS_CAPTURE_ID=0 WAS_DIAGNOSTICS=1 sh startWASHeadless
```

The value `WAS_CAPTURE_ID=0` is only a first guess; inspect UVC device
enumeration to find the actual openFrameworks device index.
The script itself defaults to index 2 for compatibility with the upstream
code, but hardware enumeration differs.

The optional OLED shows effect name, reported frame rate, and capture
readiness. Button 1 toggles bypass and Button 2 cycles through top-level
FX shaders. The rest is controlled over OSC on UDP 8000.

**Do not enable production auto-start yet.** Test cold boot, capture
disconnection, FX performance, and HDMI stability first.

## Staged checklist

- [ ] Official image successfully flashed
- [ ] Pi Zero 2 W starts and is reachable via SSH
- [ ] Initial login password changed
- [ ] Stock app path, OS version, effects folders established
- [ ] Stock auto-start safely disabled
- [ ] WAS source installed, original C++ source backed up
- [ ] `make -j1` succeeds
- [ ] SSD1306 I2C OLED and both arcade buttons tested
- [ ] Compatible UVC capture device identified
- [ ] USB capture -> shader -> HDMI tested and OSC verified
