# WAS recurBOY — First boot on a fresh Raspberry Pi Zero 2 W card

**Target:** Fresh microSD, Pi Zero 2 W, mini-HDMI monitor, built-in Wi-Fi,
salvaged SSD1306 I²C OLED and two arcade buttons. No recurBOY shield.

**Current status:** The official v3.1.0 image booted successfully on the
Pi Zero 2 W, with SSH/Wi-Fi functioning. On 2026-11-16, the WAS-modified
C++ app **compiled and linked successfully** on that Pi (`make -j1`, exit
code `0`, created `bin/ofRecurBoy`). Runtime video capture, GLSL effects, OSC and arcade buttons are **not yet verified**.
The existing SSD1306 OLED **has displayed the new WAS diagnostic screen**
after enabling I²C, as confirmed by the on-device test.
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

## Verified stock-image probe (2026-11-16)

The first on-device `was_probe.sh` report confirms:

| Item | Measured result |
|---|---|
| Hardware | Raspberry Pi Zero 2 Rev 1.0 |
| Kernel | `5.4.81-v7+`, ARMv7 |
| OS | Raspbian GNU/Linux 9 Stretch |
| Power/throttling | `throttled=0x0` |
| Storage | 29 GB root, 25 GB free |
| App directory | `/home/pi/openframeworks10.1/apps/myApps/ofRecurBoy` |
| Effects folder | `/home/pi/EFFECT`, 32 top-level files |
| Generative patterns | `/home/pi/PATTERN`, 30 top-level files |
| I²C | `/dev/i2c-1` not yet available |
| Video nodes | Internal bcm2835 codec/ISP only; external UVC not connected |
| Auto-start | `@reboot /home/pi/openframeworks10.1/apps/myApps/ofRecurBoy/startRecurBoy` |

These assets **are already present**; do not reinstall openFrameworks or
replace the working OS with a modern image. Stretch is end-of-life, so
keep the device on a trusted private network, avoid exposing services
to the internet, and do not run a broad distribution upgrade while
we rely on the legacy video stack.

### Next command sequence on this verified image

1. Disable the known stock cron job so it cannot relaunch the TFT/shield
   UI. Run `crontab -e` and comment the exact `@reboot ...startRecurBoy`
   line with `#`. Save, then verify `crontab -l`.
2. Inspect running processes with
   `ps -eo pid,comm,args | grep -E '[o]fRecurBoy|[d]isplay.py'`.
   Stop the old `ofRecurBoy` application with
   `sudo killall ofRecurBoy 2>/dev/null || true`.
   If `display.py` remains active, stop its specific PID using `kill PID`.
   **Do not `killall python3`**, which can terminate unrelated services.
3. Refresh the cloned branch and deploy the WAS source:

```sh
cd /home/pi/recurBOY-was
git pull --ff-only
sh software/ofRecurBoy/installWASIntoImage.sh

cd /home/pi/openframeworks10.1/apps/myApps/ofRecurBoy
make -j1 > /home/pi/was_build.log 2>&1
echo "Build exit code: $?"
tail -n 60 /home/pi/was_build.log
```

If the build fails, the most useful debugging evidence is the **first**
actual C++ error in `/home/pi/was_build.log` and the last 60 lines.
Because the Zero 2 W has limited RAM, use `-j1`.

4. Once compilation succeeds, enable I²C in `sudo raspi-config`
   (Interfacing Options → I²C → Enable on this older OS). Reboot if
   prompted. Confirm `/dev/i2c-1` appears, and if available run
   `i2cdetect -y 1` to look for address `3c`. Then run the independent
   OLED diagnostic using `python3 was_diagnostics.py`.

The first integrated video test comes **after** successful compilation
and OLED verification. Do not connect a capture adapter during the
initial compiler test.

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

## Verified diagnostic OLED (2026-11-16)

On the Raspberry Pi Zero 2 W with the custom SSD1306 attached and I²C
enabled, the independent `python3 was_diagnostics.py` successfully displayed
its status interface. The I²C/OLED code is therefore functioning on the
actual hardware, not merely syntax-checked.

The `ENGINE: OFFLINE` message is expected until `ofRecurBoy` starts.
The arcade buttons cannot visibly control video while the C++ process
is offline; test their effect-bypass/cycle actions during integrated runtime.

### Preparing to identify the UVC capture adapter

Stop a standalone `was_diagnostics.py` session using Ctrl+C before
launching `startWASHeadless` with `WAS_DIAGNOSTICS=1` to avoid duplicate
monitor processes and OSC port 9010 conflicts.

Connect the HDMI source to the UVC HDMI-to-USB capture adapter, connect
the capture adapter to the Pi Zero 2 W **USB DATA / OTG** port (not the
PWR IN port), and retain Pi mini-HDMI output to a monitor.

```sh
# Inspect V4L2 devices before/after connecting the adapter:
v4l2-ctl --list-devices
ls -l /dev/video*
# Optional, for supported format/capture modes of the external device:
v4l2-ctl -d /dev/videoN --list-formats-ext
```

IMPORTANT: `/dev/videoN` **is a Linux V4L2 node number**, whereas
`WAS_CAPTURE_ID` is the **zero-based index of the device returned by
openFrameworks ofVideoGrabber::listDevices()**. They need not match. The
legacy video grabber path supports SD capture; start testing at 640×480
and approx. 25–30 fps if offered.

The original system reports internal bcm2835 codec and ISP V4L2 nodes
even with no USB capture adapter connected. Identify the **new device
by its capture-adapter name**, not simply by the presence of `/dev/video*`.

## Verified MiraBox USB capture enumeration (2026-11-16)

The user identified a passive USB cable as the cause of the initial failure to
enumerate the HDMI capture dongle. Replacing it with a **USB OTG adapter**
solved the problem without changing the Pi's boot configuration. On-device
`v4l2-ctl --list-devices` now reports:

```text
MiraBox Video Capture: MiraBox (usb-3f980000.usb-1):
    /dev/video0
    /dev/video1
```

Internal `bcm2835-codec` and `bcm2835-isp` nodes remain at
`/dev/video10` through `/dev/video16`. The MiraBox is recognized
by Linux but **no actual video frames have been verified yet**.

### First live-capture validation

With the MiraBox still on the Pi's USB DATA port and receiving
a normal HDMI signal (not protected HDCP content):

```sh
v4l2-ctl -d /dev/video0 --list-formats-ext
# Check whether the source supports a 640x480 mode, ideally ~25/30 fps.
# The original captur.cpp requests fixed 640x480.

# Ensure the standalone OLED test was stopped with Ctrl+C.
cd /home/pi/openframeworks10.1/apps/myApps/ofRecurBoy
WAS_CAPTURE_ID=2 WAS_DIAGNOSTICS=1 sh startWASHeadless
```

On first launch, use the OLED's active-low **Button 1** to bypass FX and
look for **unprocessed video** on the Pi mini-HDMI output. Button 2 cycles
the available installed shaders. Observe whether OLED switches to
`ENGINE: ONLINE`, `UVC: READY`, and whether a real image displays.

If anything fails, capture the terminal output (the C++ renderer logs
device enumeration, shader loading, and initialization errors). The
Linux node `/dev/video0` does **not guarantee** openFrameworks
`WAS_CAPTURE_ID=0`; the latter indexes the list of available
`ofVideoGrabber` devices. Try a different index only after seeing
the device list/log.

If the Pi mini-HDMI only shows the login screen, investigate whether
openFrameworks starts graphics rendering at all before changing
shader settings.

## Verified first WAS runtime / MiraBox device index (2026-11-16)

The **WAS-modified C++ renderer starts on the Pi Zero 2 W** with
OpenGL ES 2.0 / VideoCore IV, and the installed shader
`/home/pi/EFFECT/ANSIlike.frag` successfully compiles and links.
The OLED displays `ENGINE: ONLINE` and `UVC: READY`.

However, the **first image was black**. The runtime log identifies the
cause of at least one problem: `WAS_CAPTURE_ID=0` selected the internal
`bcm2835-isp` at `/dev/video14`, not the MiraBox.

The captured `ofGstVideoGrabber::listDevices()` numbering was:

| WAS_CAPTURE_ID | openFrameworks capture device |
|---|---|
| `0` | internal `/dev/video14` bcm2835-isp |
| `1` | internal `/dev/video15` bcm2835-isp |
| **`2`** | **MiraBox UVC `/dev/video0`** |
| `3` | MiraBox UVC `/dev/video1` |

Therefore this Pi + MiraBox combination must be started using **index
`2`** rather than the previously suggested provisional index `0`.

Additionally, the initial source was an iPad playing Hulu. Licensed Hulu
video can output black due to HDMI HDCP/DRM protection. Use the iPad
home screen, a personally recorded Photos video, or another unprotected
source for the first capture test. Do not attempt to circumvent HDCP.

Stop the prior process and start:

```sh
cd /home/pi/openframeworks10.1/apps/myApps/ofRecurBoy
WAS_CAPTURE_ID=2 WAS_DIAGNOSTICS=1 sh startWASHeadless
```

On successful source selection, the runtime log should say it selected
MiraBox, not bcm2835-isp. The ready indicator only confirms
`ofVideoGrabber` initialized, **not** that live frames are actually being
received. Check the video image in bypass with arcade Button 1.

The existing `startWASHeadless` script already defaults to capture
index `2`; do not change the C++ code or recompile for this correction.
We should later add robust capture selection by hardware identifier
instead of relying on index order.

## First live-video issue: frozen scrambled bypass, black default FX

On the Pi + MiraBox with the correct openFrameworks capture index `2`,
the video application runs, OLED reports ONLINE/READY and the renderer
reports approximately 30 FPS. The user observes a **static scrambled**
output when FX is bypassed and a **black image with FX on**. The bypassed
image **does not change** when the unprotected iPad Photos source is stopped
or changed. This implies the renderer is not yet receiving a continuously
updated video feed; the OLED currently reports GL render FPS and the
grabber's initialization state, **not incoming frames**.

The initial effect `ANSIlike.frag` contains calculations which divide by
`fparams[0]` and `fparams[1]`. These begin at zero in upstream
`conjur::setup()`. Thus a black shader output can be caused by undefined
shader math independently of the capture problem. Use `invert.frag`
for further testing rather than debugging ANSIlike and capture together.

### Isolate whether the MiraBox streams on Linux

Stop `startWASHeadless` with Ctrl+C to release `/dev/video0`.
Display the iPad home screen, a self-recorded video, or another
**non-HDCP-protected** HDMI source. Then:

```sh
v4l2-ctl -d /dev/video0 --get-fmt-video
v4l2-ctl -d /dev/video0 --list-formats-ext

# Probe the V4L2 capture device independently of openFrameworks.
# Expected: 60 buffers dequeued and exit 0; errors/timeouts mean capture
# has not been established below the video-engine layer.
v4l2-ctl -d /dev/video0 --stream-mmap=3 --stream-count=60 --stream-to=/dev/null
echo "V4L2 exit code: $?"
```

This test does not save or redistribute captured content; /dev/null
discards the frames. If successful, use the reported formats to diagnose
GStreamer negotiation. The existing `captur.cpp` requests 640×480 at
25 fps and the Pi USB2 bus may favor MJPEG rather than uncompressed YUYV.
Test the shader independently after confirming capture by launching with
`WAS_FX_SHADER=invert.frag`.

If V4L2 fails, inspect `dmesg | tail -n 50` for UVC resets,
bandwidth warnings, and capture timeouts and check the capture dongle's
power via powered USB hub if appropriate.

## Confirmed USB reconnect loop (2026-11-16)

When the WAS renderer was stopped, the Pi reported the MiraBox moved
from `/dev/video0`+`/dev/video1` to `/dev/video1`+`/dev/video2`.
More importantly, `dmesg` showed repeated **physical USB disconnect
followed by re-enumeration** at ~1–2 second intervals, with device
numbers 28–33 and the stable USB hardware ID `1bcf:2c99` (VXIS Inc,
MiraBox Video Capture).

This is currently a **USB bus/peripheral stability problem**, not
evidence of a shader defect. Linux node numbers can change after
each reconnect; stop capture debugging until the USB device remains
present without disconnect/re-enumeration.

Suggested safe isolation order:

1. Stop all video processes. Keep SSH connected by Wi-Fi. Run
   `vcgencmd get_throttled`, `lsusb`, `dmesg -w`.
2. Try the MiraBox with no HDMI input. Check whether the repeated
   disconnects still occur with an idle capture card.
3. Check USB power-management setting (when device is present):
   `cat /sys/bus/usb/devices/1-1/power/control`. If it reports
   `auto`, test temporary autosuspend disable using
   `echo on | sudo tee /sys/bus/usb/devices/1-1/power/control`.
   The change is not persistent; re-enumeration may reset it.
4. Replace the USB OTG adapter with a known-good short adapter and
   power Pi through a stable supply; use an externally powered USB
   hub between Pi OTG and capture card if available. Do not
   parallel-feed unmanaged supplies into the same 5V rail.
5. If necessary, test a low-power USB flash drive using that OTG
   adapter to distinguish the MiraBox from the Pi/adapter connection.

A similar MiraBox reconnect loop on another Linux host has been
linked to USB autosuspend (different vendor/product ID;
not proof for this unit):
https://www.emadelsaid.com/MiraBox%20capture%20card%20disconnects%20endlessly%20on%20linux/

Do not update the end-of-life Stretch OS or modify `/boot/config.txt`
just to troubleshoot until basic power, cable, and power-management
tests are complete.

## Verified GStreamer decoding failure (2026-11-16)

After a reboot, the MiraBox was recognized with the expected
`WAS_CAPTURE_ID=2`. Its video capture device appeared as `/dev/video0`.
The OF/GStreamer log reports successful OpenGL initialization and correct
device selection, then:

```text
initGrabber(): selected device: MiraBox Video Capture
initGrabber(): selected format: 640x480 video/x-raw RGB framerate: 30/1
gstreamer pipeline: v4l2src ... device=/dev/video0 ! video/x-raw,format=RGB,width=640,height=480,framerate=30/1 ! appsink ...
libv4l2: error got 4 consecutive frame decode errors, last error: v4l-convert: libjpeg error: End Of Image
ofGstUtils: ... video playback halted ... Failed to allocate a buffer
```

Thus the current failure is **not merely an incorrect camera index**
and not proof of an EGL/shader problem. The GStreamer pipeline requests
an RGB stream but the UVC camera also advertises `image/jpeg` (MJPEG).
The `libv4l2` conversion layer appears to be decoding invalid or
truncated JPEG frames. A follow-on buffer-allocation failure occurs.
This could result from a UVC stream/bandwidth/power problem, broken
conversion negotiation, or bad camera output; **not yet conclusively
isolated**. The OLED's "UVC READY" is based on `isInitialized()` and
does *not* imply valid frames have arrived.

**Next isolation steps** — stop WAS first so the video device is free;
use an unprotected, ordinary iPad home screen/Photos source:

```sh
v4l2-ctl --list-devices
# Use the MiraBox's current capture-capable /dev/videoN (often /dev/video0).
v4l2-ctl -d /dev/video0 --list-formats-ext
v4l2-ctl -d /dev/video0 --get-fmt-video

# Independent kernel-side capture with data discarded:
v4l2-ctl -d /dev/video0 --stream-mmap=3 --stream-count=90 --stream-to=/dev/null
echo "exit code: $?"
dmesg | tail -n 40
vcgencmd get_throttled
```

If available formats include `MJPG` and `YUYV`, test **one explicit
format at a time**, such as:

```sh
# Do NOT run simultaneously with the video engine; requests 640x480 MJPG.
v4l2-ctl -d /dev/video0 --set-fmt-video=width=640,height=480,pixelformat=MJPG
v4l2-ctl -d /dev/video0 --set-parm=30
v4l2-ctl -d /dev/video0 --stream-mmap=3 --stream-count=90 --stream-to=/dev/null
```

These commands read and discard frames; they do not require a GUI and
do not modify the user's permanent video settings. If the device
drops off USB again (`dmesg` disconnect/re-enumeration), first test a
known-good short OTG cable and **powered USB 2.0 hub** to isolate USB
power/signal stability. If standalone frames are stable yet
openFrameworks fails, adjust how it selects a raw/decoded format and
provide a better true-new-frame indicator on the OLED. Avoid
recompiling until after independent V4L2 tests.

## First successful independent V4L2 MJPEG capture, with USB errors (2026-11-16)

After stopping the app (at least apparently), the user found MiraBox at
`/dev/video0` and `/dev/video1`, and used `v4l2-ctl` to request
**MJPG at 640×480 and 30fps**. The direct streaming command

```sh
v4l2-ctl -d /dev/video0 --stream-mmap=3 --stream-count=90 --stream-to=/dev/null
```

completed with **exit code 0**, 90 markers, about 25.74 to 28.57 fps.
This verifies **compressed frame delivery** via V4L2, not JPEG decode
or decoded image correctness. The prior `--list-formats-ext` attempt
reported `Device or resource busy`; check for leftover
`ofRecurBoy`, GStreamer, or another V4L2 process before subsequent
testing.

The same `dmesg` tail contained:

```text
usb 1-1: reset high-speed USB device number 6 using dwc2
dwc2 3f980000.usb: NYET/NAK/ACK/other in non-error case
usb 1-1: device descriptor read/64, error -71
uvcvideo: Failed to query (GET_DEF) UVC control 11 ... -32
```

The Pi reports `vcgencmd get_throttled` = `throttled=0x0`.
**Interpretation**: initial compressed capture is now proven possible,
but the bus recorded USB protocol/reset errors. Pi-reported healthy 5V
does *not* rule out unstable power to a USB capture card. Avoid claiming
the card is consistently reliable or that direct 90 compressed frames
prove MJPEG decoding works.

### Controlled next steps

Stop app and verify `pgrep -af 'ofRecurBoy|was_diagnostics|gst-launch|v4l2-ctl'`.
Then run a *decoded* MJPEG test (if `gst-launch-1.0` is available):

```sh
gst-launch-1.0 -v v4l2src device=/dev/video0 num-buffers=90 \
    ! image/jpeg,width=640,height=480,framerate=30/1 \
    ! jpegdec ! videoconvert ! video/x-raw,format=RGB \
    ! fakesink sync=false
echo "GStreamer exit: $?"
```

If `jpegdec` is missing, collect the exact missing-plugin message;
do not perform a system-wide OS update. Independently recheck
`dmesg | tail` and whether `/dev/video0` remains stable.
A short known-good OTG adapter and a **powered USB hub** are justified
if USB reset errors persist, before rewriting the WAS renderer.
Once compressed+decoded frames are stable, inspect whether the stock
openFrameworks V4L2/libv4l2 picks MJPEG and erroneously uses its
`video/x-raw,format=RGB` negotiation path; implement explicit MJPEG
decode pipeline and frame counters as needed.

## GStreamer CLI unavailable, OLED process still running (2026-11-16)

The first proposed manual GStreamer decode test could **not run** on
the stock image:

```text
-bash: gst-launch-1.0: command not found
GStreamer exit code: 127
```

This is **missing diagnostic CLI**, not a video decode result and
not proof that GStreamer libraries are absent. The C++ runtime uses
GStreamer already.

`pgrep -af 'ofRecurBoy|was_diagnostics|gst-launch'` reported only
`python3 ./was_diagnostics.py --control-port 8000` (PID 1342). Thus
the previous video engine was gone but an OLED helper was still
running. Stop that process before launching a new helper to avoid
GPIO channel-in-use warnings and OSC port conflicts:

```sh
kill 1342
pgrep -af 'ofRecurBoy|was_diagnostics|gst-launch'
```

PID is specific to this test and must not be hardcoded for future runs.
The shell launcher has an EXIT trap but an interactive interruption may
not always have stopped the helper; examine signal handling later.

Prefer seeing whether `ffmpeg` CLI is installed before requesting
additional packages:

```sh
command -v ffmpeg || true
command -v gst-launch-1.0 || true
```

If available, independently decode 90 MJPEG frames using:

```sh
ffmpeg -hide_banner -f v4l2 -input_format mjpeg \
  -video_size 640x480 -framerate 30 -i /dev/video0 \
  -frames:v 90 -f null -
```

If neither CLI exists, consider installing **only**
`gstreamer1.0-tools` (which supplies gst-launch-1.0) without
upgrading old OS or replacing the official recurBOY image.
Alternatively capture raw MJPEG bytes with V4L2 and decode with the
already available Pillow library.

## FFmpeg standalone MJPEG decode test (2026-11-16)

`ffmpeg` was preinstalled at `/usr/bin/ffmpeg` and successfully read
and processed **90 frames at 640×480 / 30 fps** (~29 fps effective)
from MiraBox `/dev/video0` using `-f v4l2 -input_format mjpeg`.
The source codec was detected as `mjpeg, yuvj422p`; this was **not
90 clean frames**:

```text
[mjpeg] overread 8
[mjpeg] EOI missing, emulating
[mjpeg] Found EOI before any SOF, ignoring
[mjpeg] No JPEG data found in image
Error while decoding stream #0:0: Invalid data found when processing input
frame= 90 fps=29 ... time=00:00:03.10
```

FFmpeg's native decoder tolerates malformed JPEG frames and continues,
unlike the legacy recurBOY `libv4l2`/GStreamer path, which previously
halted with repeated `End Of Image` errors and a buffer allocation error.
This strongly implicates missing/invalid MJPEG content; the causal
source remains unresolved (MiraBox JPEG encoder or firmware, USB
signal/power, or capture HDMI input), particularly given earlier
`dwc2` USB reset/protocol error `-71`.

Controlled next diagnostics:

1. With WAS stopped and a known-unprotected iPad Home/Photos frame
   shown, take a standalone **single decoded PNG**:

   ```sh
   ffmpeg -hide_banner -loglevel warning -f v4l2 \
     -input_format mjpeg -video_size 640x480 -framerate 30 \
     -i /dev/video0 -frames:v 1 -y /home/pi/mirabox_probe.png
   file /home/pi/mirabox_probe.png
   ```

   Copy to Mac via SCP and visually inspect (a valid PNG container
   doesn't guarantee visually sound capture). If one frame is corrupt,
   retest with another HDMI source and/or another host with a powered
   USB hub.
2. Collect `v4l2-ctl -d /dev/video0 --list-formats-ext` and check if
   **native uncompressed** capture (YUYV) is advertised; if yes test
   that as a separate input format, avoiding MJPEG decoding.
3. Compare MiraBox with **same source** on a full-size computer.
   If healthy on Mac but not Pi, focus on Pi USB/OTG/hub/controller;
   if bad on both, focus on MiraBox/HDMI adapter/HDMI signal.
4. Test externally powered USB hub and short known-good OTG adapter
   given prior USB resets; do not assume `vcgencmd get_throttled=0x0`
   proves the capture card has enough power.
5. Only after signal quality is proven consider patching OF's
   GStreamer capture pipeline to explicitly request MJPEG and decode
   appropriately. Also avoid default ANSIlike shader with zero
   parameters; debug with bypass or a simpler shader.

## FFmpeg decoded screenshot is near-uniform dark gray; MJPEG only (2026-11-16)

User uploaded `mirabox_probe.png` captured from the MiraBox by FFmpeg.
The actual **640×480** image was examined with Pillow:

- **307075 / 307200 pixels (99.959%) were exactly RGB (15, 15, 15)**.
- Only ~72 pixels had any RGB channel above 15, and only four above 192.
- No recognizable iPad imagery was present.

This means it is **not merely a garbled recognizable picture**:
the decoded frame is effectively uniform near-black with isolated
artifacts. Could reflect no valid HDMI signal, HDCP/handshake,
MiraBox video output when signal is absent, or damaged capture,
and does **not** alone prove the source or MiraBox is defective.

The command
`v4l2-ctl -d /dev/video0 --list-formats-ext` reported **only
`MJPG` / Motion-JPEG (compressed)**, with 640×480 at 30/60 fps
and higher resolutions; **no native uncompressed YUYV/I420** was
offered. Do not recommend V4L2 raw uncompressed fallback.

Preferred next decisive A/B hardware check:

1. Disconnect Hulu and display the iPad Home/Settings/Photos image
   (not protected streaming content). Verify the iPad HDMI adapter
   can display it directly on an ordinary external monitor/TV.
2. With the exact same HDMI source, connect the MiraBox **USB output
   to Mac** instead of the Pi, and preview using QuickTime Player >
   File > New Movie Recording > select MiraBox as Camera. If Mac sees
   proper video, focus on Pi USB signal/power/kernel and its legacy
   UVC/GStreamer code. If Mac also sees blank video, investigate
   iPad HDMI mode, MiraBox HDMI handshake, and MiraBox device.
3. If Mac test is blank, use an **unprotected Mac HDMI desktop feed**
   as the alternative MiraBox HDMI source (or another known-good
   HDMI source) to separate iPad adapter from MiraBox behavior.
4. Previously captured MJPEG data triggered FFmpeg
   `EOI missing` and `overread` messages and the Pi logged dwc2
   USB protocol error -71, so still consider a short known-good OTG
   adapter or powered USB hub after confirming source behavior.

## Controlled direct-USB vs powered-hub comparison (2026-11-16)

The user confirmed the **same MiraBox works on a Mac as a USB capture
device** when powered through the Mac, and HDMI passthrough from the
iPad through MiraBox to a monitor works while MiraBox is connected to
the Pi. HDMI passthrough is not evidence USB capture works on the Pi;
the direct Pi FFmpeg MJPEG stream has broken JPEG markers and captured
a nearly uniform dark-gray frame. The hardware is likely functional
but the Pi USB capture path remains suspect.

A known Raspberry Pi Zero 2 W `dwc2` reconnect issue (different
kernel, not proof of this exact case) is documented at:
https://github.com/raspberrypi/linux/issues/6247

Next decisive experiment: on the same unprotected iPad home/Photos
signal, compare video capture **direct over the Pi OTG adapter** with
capture **via an externally powered USB 2.0-compatible hub**.
Keep the Pi powered via PWR IN and do not backfeed uncontrolled
external +5V through the OTG cable. Do not reinstall/recompile
recurBOY between A/B tests. Stop `ofRecurBoy` first.

For either test, with the correct MiraBox current `/dev/videoN`:
```sh
# Set LABEL=direct, then repeat later with LABEL=hub.
LABEL=direct
ffmpeg -hide_banner -loglevel warning \
  -f v4l2 -input_format mjpeg -video_size 640x480 -framerate 30 \
  -i /dev/video0 -t 5 -vf fps=1 -y \
  "/home/pi/was_${LABEL}_%02d.png" \
  2> "/home/pi/was_${LABEL}.log"
echo "FFmpeg exit: $?"
grep -Eic 'overread|EOI missing|No JPEG data|Invalid data' \
  "/home/pi/was_${LABEL}.log"
dmesg | tail -n 25
```

Use existing Python Pillow to print each PNG's RGB brightness
and standard deviation; for a bright and changing iPad home screen,
mean 15,15,15 and stddev near 0 means the Pi still sees an almost
solid gray image:

```sh
python3 - <<'PY'
from PIL import Image, ImageStat
from glob import glob
for filename in sorted(glob('/home/pi/was_direct_*.png')+
                       glob('/home/pi/was_hub_*.png')):
    s=ImageStat.Stat(Image.open(filename).convert('RGB'))
    print(filename, 'mean', [round(x,1) for x in s.mean],
          'stddev', [round(x,1) for x in s.stddev])
PY
```

Interpretation:
- Powered hub yields colorful images and removes errors: USB
  power/signal/host link; retain powered hub for exhibit.
- Both black/garbled with recurrent USB errors: try other OTG cable,
  host controller compatibility and different UVC capture adapter.
- Independent Pi FFmpeg JPEG *clean* and colorful but WAS renderer
  black: resume C++/GStreamer debugging (RGB conversion,
  `ofGstVideoGrabber`, default ANSIlike shader parameters).
- Powered hub does not guarantee that source negotiation or driver
  quirks are fixed; inspect frame content and dmesg, not only FPS.

## Powered-hub still-image statistics improved (2026-11-16)

The user connected the MiraBox through an **externally powered USB
hub** and captured five 1 FPS frames via FFmpeg from /dev/video0.
Reported RGB means ranged roughly **[70–74, 61–66, 42–52]** and
per-channel standard deviations **[66–69, 56–59, 40–52]**, compared
to the earlier nearly uniform RGB (15,15,15) image.

This is **evidence of varied image data** but not yet confirmation
of a recognizable, correctly decoded, live HDMI feed. Also, the
user's FFmpeg command saved results as
`/home/pi/was_direct_01.png` through `_05.png`
while the **powered hub** was connected: the shell variable
`LABEL` remained `direct`. These files should be treated as
the **hub** trial, not an independently captured direct-to-Pi
baseline. Old files with those names may have been overwritten.

Next:
- Visually inspect `was_direct_03.png` (actually captured via hub).
- Check `grep -Eic 'overread|EOI missing|No JPEG data|Invalid data' /home/pi/was_direct.log`,
  and `dmesg | tail -n 30` to look for USB -71/reset errors
  during the new test.
- If frame is recognizable and USB is stable, relaunch
  `WAS_CAPTURE_ID=2 WAS_DIAGNOSTICS=1 WAS_FX_SHADER=invert.frag sh startWASHeadless`
  and use bypass for first live-feed validation. On devices
  re-enumerating under a hub, inspect openFrameworks device list
  before trusting capture index 2.
- If standalone images look corrupt, continue USB/source tests before
  changing the C++ app.

## 7. Launch WAS video FX mode (only after C++ builds)

With a compatible HDMI-to-USB UVC capture dongle connected to the Pi's
**USB** OTG port, and a source HDMI feed attached to the dongle:

```sh
cd /home/pi/openframeworks10.1/apps/myApps/ofRecurBoy
WAS_CAPTURE_ID=0 WAS_DIAGNOSTICS=1 sh startWASHeadless
```

On this exact Pi Zero 2 W + MiraBox setup, the runtime log confirms
openFrameworks index **2** corresponds to `/dev/video0` (MiraBox).
Index 0 was an internal Pi ISP and produced a black image.

The optional OLED shows effect name, reported frame rate, and capture
readiness. Button 1 toggles bypass and Button 2 cycles through top-level
FX shaders. The rest is controlled over OSC on UDP 8000.

**Do not enable production auto-start yet.** Test cold boot, capture
disconnection, FX performance, and HDMI stability first.

## Staged checklist

- [x] Official image successfully flashed
- [x] Pi Zero 2 W starts and is reachable via SSH
- [ ] Initial login password changed
- [x] Stock app path, OS version, effects folders established
- [ ] Stock auto-start safely disabled (verify cron entry remains commented)
- [x] WAS source installed and compiled in the stock application directory
- [x] `make -j1` succeeds (exit 0; warnings only)
- [x] SSD1306 I2C OLED screen displays WAS diagnostic status
- [ ] Arcade button 1/2 controls tested against running video engine
- [x] MiraBox USB UVC device recognized by Linux as /dev/video0 and /dev/video1 with OTG adapter
- [ ] USB capture -> shader -> HDMI tested and OSC verified
