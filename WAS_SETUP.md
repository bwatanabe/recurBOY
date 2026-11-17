# WAS recurBOY — shared video-effects processor (v0.2)

> **Status (Nov 16, 2026): Pi Zero 2 W build and first end-to-end HDMI test succeeded.** Live HDMI-in from a MiraBox through an **externally powered USB hub**, GLSL color-negative processing, OLED status, button-1 bypass, and OSC FX parameters have been tested on device. The v0.2 default FX settings, quieter logging, diagnostics cleanup, and experimental encoder code are **committed but still need on-device rebuild and verification**.

> **Architectural role: this is not a WAS cartridge.** It is a permanent shared output-stage processor. Any WAS cartridge (PS-2600, Naninovel, emulator, etc.) can feed its HDMI content through this unit; the processor applies global effects irrespective of the selected cartridge.
>
> **Start here on a fresh SD card:** [WAS_FIRST_BOOT.md](WAS_FIRST_BOOT.md)
> follows the official v3.1.0 image installation, SSH setup, safe source deployment,
> and first hardware diagnostics.
> This is a development branch intended to preserve the original recurBOY implementation.
> Do not replace your working SquishBox microSD card without imaging/backing it up.

## Objective

Use a **Raspberry Pi Zero 2 W** as an optional outboard video processor in the
Watanabe Autotainment System (WAS):

```text
Active WAS cartridge video HDMI -> MiraBox UVC HDMI capture
                                  -> externally powered USB hub
                                  -> Pi Zero 2 W USB OTG
                                  -> recurBOY FX/GLSL processor
                                  -> Pi mini-HDMI -> monitor/projector

WAS orchestration / AI output / local buttons -> OSC control of FX processor
```

No custom recurBOY shield, ADC, extra MIDI controller, or TFT display is required.
The salvaged SSD1306 OLED and two buttons have their historical pinout
documented below. An **optional** diagnostic daemon uses these connections;
the core video processor does not require that daemon or any GPIO hardware.

## What changed

- `WAS_HEADLESS=1` switches on an opt-in application startup path.
- Suppresses the recurBOY ADC/GPIO and keyboard/MIDI polling initialization,
  but leaves the original interactive mode unchanged.
- Selects source `EXTERNAL`, initializes a USB video-grabber, and enables live display.
- Uses the existing `conjur` engine and installed `/home/pi/EFFECT` or legacy
  `/home/pi/Fx` GLSL shaders. Select a shader by name or filename.
- Accepts a small OSC vocabulary to select and manipulate the effect.
- Adds `software/ofRecurBoy/startWASHeadless`, which does not launch
  `display.py`. The original startup script is untouched.

## Before modifying the Pi

1. Make a complete image backup of the existing SquishBox microSD card.
2. Prepare a **second** microSD card using a recurBOY image from the
   [recurBOY releases](https://github.com/cyberboy666/recurBOY/releases).
   These historical images use a legacy Pi OS/openFrameworks environment.
   **Compatibility of a specific image with Pi Zero 2 W is unverified here.**
3. Confirm HDMI output works before adding capture hardware or modifying code.
4. Confirm USB capture is enumerated and gives a valid `ofVideoGrabber` index.
   Many drivers expose additional virtual camera devices; the tested MiraBox
   uses openFrameworks index **2**, but confirm after USB re-enumeration.
5. The **powered USB hub is required for the currently verified configuration**:
   direct MiraBox-to-Pi USB produced -71 protocol errors, black frames and
   malformed MJPEG, but the powered hub enabled live HDMI output.
   Keep the Pi separately powered through PWR IN.

### Installing this source branch

The installation path in the stock script is
`/home/pi/openframeworks10.1/apps/myApps/ofRecurBoy`. If using Git locally:

```sh
git clone -b was/headless-v0.1 https://github.com/bwatanabe/recurBOY.git
```

This repository is **not** itself a pre-built SD image. The C++ app belongs in
an openFrameworks 0.10.1 environment with the project's required addons; the
stock `software/ofRecurBoy` directory may need to be copied into the image's
`apps/myApps/ofRecurBoy` location. Keep a backup of the original app.

## Launch

From inside the Pi's `ofRecurBoy` application directory:

```sh
# Example when the UVC capture device is index 0:
WAS_CAPTURE_ID=2 WAS_DIAGNOSTICS=1 WAS_FX_SHADER=invert.frag sh startWASHeadless
```

Or, to choose the first top-level effect file found:

```sh
WAS_CAPTURE_ID=2 sh startWASHeadless
```

Environment variables:

| Variable | Default | Meaning |
|---|---|---|
| `WAS_HEADLESS` | unset | `1` activates WAS startup path |
| `WAS_CAPTURE_ID` | `2` | openFrameworks video grabber index |
| `WAS_OSC_PORT` | `8000` | UDP port for OSC controls |
| `WAS_DIAGNOSTICS` | `0` | `1` launches OLED/buttons and local status telemetry |
| `WAS_FX_SHADER` | empty | Effect name, file name, or first installed top-level effect |
| `WAS_APP_DIR` | `/home/pi/openframeworks10.1/apps/myApps/ofRecurBoy` | Launch-script app directory |
| `WAS_ENCODER` | `0` | Set `1` to enable experimental rotary encoder and press switch on GPIO22/23/4 |

**Only launch this script after building the installed forked C++
application and its addons.** The initial v0.1 build succeeded on the
Pi Zero 2 W; v0.2 must be reinstalled and recompiled.

The OLED/physical controller is *optional*: `WAS_DIAGNOSTICS=1` starts
it and should turn off the OLED on orderly shutdown. The launcher
does not automatically run at boot yet; automatic startup and WAS
lifecycle control are later deployment steps.

For a safe v0.2 refresh of the tested installation (stop the running
video process first with Ctrl+C):

```sh
cd /home/pi/recurBOY-was
git status --short
git pull --ff-only
sh software/ofRecurBoy/installWASIntoImage.sh
cd /home/pi/openframeworks10.1/apps/myApps/ofRecurBoy
make -j1 > /home/pi/was_build_v02.log 2>&1
echo "Build exit: $?"
tail -n 20 /home/pi/was_build_v02.log
# Only start when build exit is 0:
WAS_CAPTURE_ID=2 WAS_DIAGNOSTICS=1 WAS_FX_SHADER=invert.frag sh startWASHeadless
```

**Do not perform `git reset --hard`** to resolve a non-fast-forward or
local changes; review them instead. `installWASIntoImage.sh` retains
timestamped source backups and now also installs `main.cpp`.
No boot services or crontab entries are changed by this procedure.

## OSC API (initial)

Send OSC messages to the Pi's LAN IP on UDP port `8000` (or `WAS_OSC_PORT`).

| OSC address | Type | Example | Action |
|---|---|---|---|
| `/was/video/fx/load` | string | `wobble.frag` | Select installed effect |
| `/was/video/fx/enabled` | int | `0` | Bypass effect; continue showing capture |
| `/was/video/fx/next` | int | `1` | Switch to next installed top-level FX |
| `/was/video/fx/param/0` | float | `0.6` | Set first parameter, clamped 0–1 |
| `/was/video/fx/param/1` | float | `0.25` | Set second parameter |
| `/was/video/fx/param/2` | float | `0.9` | Set third parameter |
| `/was/video/fx/speed` | float | `0.5` | Set effect speed control |

Example using Python and `python-osc` from another networked machine:

```python
from pythonosc.udp_client import SimpleUDPClient

pi = SimpleUDPClient("192.168.1.50", 8000)  # Replace with Pi's IP
pi.send_message("/was/video/fx/load", "wobble.frag")
pi.send_message("/was/video/fx/param/0", 0.6)
pi.send_message("/was/video/fx/enabled", 1)
```

**Notes/limitations:** Effect discovery is currently limited to
top-level `EFFECT`/`Fx` directories; subfolders are not yet indexed in
the WAS helper. Shader names must match those actually on the Pi image.
Loading the requested shader is not yet guarded by a compile/link success
check. OSC control has no authentication; keep it on a trusted/private
network.

## Output-stage deployment: direct launcher, OSC client and optional boot service

**The shared recurBOY processor is not a cartridge and must not restart
every time WAS switches cartridges.** WAS changes only the upstream HDMI
source/content and, optionally, the processor's OSC state. The Pi remains
its own long-running output-stage device.

Following a successful v0.2 build and stable live HDMI/USB capture, the
`runWASVideoProcessor` launcher starts the **already-built**
`bin/ofRecurBoy` without running `make`. It also starts the optional
OLED / button daemon, then cleans up both children on termination.
Its defaults are `WAS_CAPTURE_ID=2`, `WAS_DIAGNOSTICS=1`,
`WAS_ENCODER=0` and `WAS_FX_SHADER=invert.frag`. The powered
USB hub remains necessary for the known-working Pi Zero 2 W setup.

```sh
# In the Pi SSH session, stop the old 'sh startWASHeadless' with Ctrl+C.
cd /home/pi/recurBOY-was
git status --short
git pull --ff-only
sh software/ofRecurBoy/installWASIntoImage.sh
# This update only deploys scripts; prior build remains usable
# if the C++ source has not changed since successful v0.2 build.

cd /home/pi/openframeworks10.1/apps/myApps/ofRecurBoy
WAS_ENCODER=1 sh runWASVideoProcessor
```

Confirm the video output, OLED and encoder function. The second
physical button is **known to remain HIGH on GPIO27 when pressed**;
its wiring needs inspection/rebuild, so do not conflate that with
the remote OSC next-FX command, which was proven working.

From the **Mac**, without installing `python-osc`, copy the
standalone OSC control script and send commands to the Pi over LAN:

```sh
scp pi@192.168.0.109:/home/pi/openframeworks10.1/apps/myApps/ofRecurBoy/was_fxctl.py ~/Desktop/
python3 ~/Desktop/was_fxctl.py --host 192.168.0.109 load invert.frag
python3 ~/Desktop/was_fxctl.py --host 192.168.0.109 param 0 1.0
python3 ~/Desktop/was_fxctl.py --host 192.168.0.109 next
python3 ~/Desktop/was_fxctl.py --host 192.168.0.109 enable 0
python3 ~/Desktop/was_fxctl.py --host 192.168.0.109 enable 1
```

The client uses only Python's standard library and implements OSC
strings, 32-bit floats and ints on UDP port 8000. Like any simple
UDP sender, success means the packet was sent; confirmation comes
from the screen/OLED or future WAS acknowledgement/status endpoint.

**Opt-in systemd service (do not enable on boot until first manual
tests succeed):** Stop the manually running launcher (Ctrl+C), then:

```sh
sudo cp /home/pi/recurBOY-was/software/ofRecurBoy/was-video-processor.service \
        /etc/systemd/system/was-video-processor.service
sudo systemctl daemon-reload
sudo systemctl start was-video-processor
sudo systemctl status --no-pager was-video-processor
sudo journalctl -u was-video-processor -f
```

The service runs as user `pi`, uses the Pi-native EGL renderer,
starts the app directly from `bin/`, and restarts after an unexpected
exit. The unit ships with `WAS_ENCODER=1` because encoder input
has been verified on the user's unit. If it fails or video does not
appear, use `sudo systemctl stop was-video-processor` and switch
back to manual launching; no persistent boot configuration has been
changed. If the service runs reliably and starts video after a
controlled reboot, optionally enable it:

```sh
sudo systemctl enable was-video-processor
# Later rollback:
sudo systemctl disable --now was-video-processor
```

Note: service-based EGL startup on legacy Raspbian Stretch is
**unverified** until tested on hardware. Do not replace the known-
working manual launcher or modify system services behind the artist's
back. The service's reconnect/watchdog behavior is still limited:
it restarts if the process exits, not if USB capture silently freezes
while the process remains alive. Future work should monitor actual
new UVC frames, not renderer FPS or `isReady()` alone.

## Hardware notes: salvaged SquishBox / MT32-Pi controls

This reuses the **confirmed historical wiring** supplied from the prior
Pi Zero 2 W synth build; no connector removal or hot-glue surgery needed.
The active-low buttons connect between the GPIO pin and GND and use
internal pull-ups.

| Component | Signal | BCM GPIO | Physical pin |
|---|---|---:|---:|
| SSD1306 0.96" 128x64 OLED (`0x3C`, I2C bus 1) | VCC 3.3V | — | 1 |
| OLED | GND | — | 6 |
| OLED | SDA | 2 | 3 |
| OLED | SCL | 3 | 5 |
| Arcade button 1 | Active LOW -> GND | 17 | 11 |
| Arcade button 2 | Active LOW -> GND | 27 | 13 |
| Rotary encoder (optional, unused) | CLK / red | 22 | 15 |
| Rotary encoder (optional, unused) | DT / green | 23 | 16 |
| Rotary encoder (optional, unused) | SW / yellow | 4 | 7 |

The former PCM5102 I2S DAC on GPIO18/BCLK (pin 12),
GPIO19/LRCLK (pin 35), GPIO21/DIN (pin 40) is not used by this
video-only prototype. By default the encoder is **not** initialized or monitored. Set
`WAS_ENCODER=1` to activate the *experimental* rotary controls on the
known historical GPIO connections: rotate for selected parameter
adjustment in steps of 0.05; press encoder switch to cycle between
parameters 0–2. The historical encoder sometimes behaved unreliably,
so test manually before relying on it in exhibition use.

### OLED/button diagnostic controller

`software/ofRecurBoy/was_diagnostics.py` runs independently from the C++
video renderer, communicates locally via OSC, and requires **no additional
custom shield**.

- Button 1 (BCM17): toggle FX bypass/enable.
- Button 2 (BCM27): load the next installed top-level shader.
- Optional encoder (BCM22/23): step selected effect parameter by 0.05.
- Optional encoder push switch (BCM4): cycle selected parameter 0–2.
- OLED: video engine online/offline, UVC link state (not actual HDMI
  frame health), current shader, bypass state, selected parameter and
  its value, and **renderer** FPS.
- Diagnostic status is sent by the engine over localhost UDP `9010`;
  buttons command the engine over localhost UDP `WAS_OSC_PORT` (default `8000`).
- UVC link indicates that the capture object reports ready; it
  **does not certify a live HDMI signal or fresh frame arrivals**.
- The OLED's selected-parameter indicator will always show parameter 0
  while the optional encoder is disabled; OSC can still set parameters
  0, 1 and 2. A later telemetry revision can track last OSC-selected
  parameter.
- Both buttons are debounced in software (65 ms) and read using internal pull-ups.

The original recurBOY TFT/display.py process is **not** used. The existing
`python3-pil`, `python3-smbus`, `RPi.GPIO`, and `python-osc`
dependencies from the documented recurBOY image setup are reused; verify
they are present on the specific image installed.

On the Pi, before running the video engine:

```sh
# This is a read-only wiring report; it does not activate GPIO.
python3 was_diagnostics.py --print-wiring

# Ensure I2C is enabled, then verify the installed OLED responds at 0x3c.
sudo raspi-config
sudo apt-get install i2c-tools
i2cdetect -y 1

# Test the display/buttons independently; OLED displays ENGINE: OFFLINE
# until the video application starts. End with Ctrl+C.
python3 was_diagnostics.py
```

For the integrated prototype:

```sh
WAS_DIAGNOSTICS=1 WAS_CAPTURE_ID=2 sh startWASHeadless
```

If the OLED or a button is broken, simply omit `WAS_DIAGNOSTICS=1`;
the video processor starts without physical controls.

Once v0.2 runs reliably without encoder input, optionally test the
physical encoder (stop the app first, then relaunch):

```sh
WAS_ENCODER=1 WAS_CAPTURE_ID=2 WAS_DIAGNOSTICS=1 \
  WAS_FX_SHADER=invert.frag sh startWASHeadless
```

Try rotating the encoder to change the selected `P0` value while
FX is enabled. Press the encoder to select `P1` or `P2`. Rotation
direction or sensitivity may need calibration for the particular
salvaged encoder.

**Do not let stock recurBOY's ADC/GPIO listener initialize alongside the
diagnostics process**: it configures unrelated shield pins, including
GPIO4/22, and could conflict with the attached encoder. The WAS headless
path intentionally bypasses that initialization. If you later attach the
encoder, add it only to the diagnostics daemon after verifying its electrical
state; this is a future option, not part of v0.1.

## Acceptance tests

- [ ] Pi Zero 2 W boots the image and displays HDMI output.
- [ ] `ofRecurBoy` builds successfully with the bundled addons.
- [ ] No TFT/Python display application or MCP3008 ADC is needed.
- [ ] Capture adapter is detected and live video appears in bypass.
- [ ] One bundled effect processes live capture.
- [ ] Changing `/was/video/fx/param/0` produces visible changes.
- [ ] Toggling `/was/video/fx/enabled` switches between dry and processed video.
- [ ] I2C OLED appears at `0x3c` on bus 1 with no additional wiring.
- [ ] Button 1 toggles bypass and Button 2 selects the next shader.
- [ ] OLED receives the current FX name, UVC readiness, and frame rate.
- [ ] Renderer operates normally with `WAS_DIAGNOSTICS=0`.
- [ ] Capture disconnection/reconnection and cold boot are tested.
- [ ] Approximate end-to-end latency and frame rate are measured.

## Known technical risks for follow-up

- The upstream dependencies use obsolete Raspberry Pi graphics/video APIs;
  the best early path is a compatible stock image, not immediate OS migration.
- USB camera indices are not stable. Add UVC device enumeration and retry.
- Current startup code also runs legacy `tvservice` and loads unrelated
  media features. Reduce those dependencies if the headless build requires it.
- `conjur` currently runs one effect per pass; effect chains are future work.
- Pi Zero 2 W processing and HDMI timing are not benchmarked.
- First-pass OSC messages require a real network connection; the capture
  adapter already consumes the Pi's USB OTG connector.
- Launching `make run` per boot is intended for prototyping, not production.
  A reliable built binary and boot service should be developed once verified.
- Internal GStreamer verbose bus messages are now hidden in WAS mode
  through a notice-level log threshold; warnings and errors remain visible.
- Loading a shader initializes 0.5 for its first 3 parameters,
  except `invert.frag`, which starts at 1.0 for a visible negative.
  Those defaults are preliminary and can be replaced by per-shader
  presets or autonomous WAS modulation.
- GPLv3 obligations apply to distributions of this fork and its code.
