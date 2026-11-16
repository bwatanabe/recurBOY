# WAS recurBOY — headless video-processor experiment (v0.1)

> **Status: source change prepared; NOT compiled or tested on Raspberry Pi hardware.**
> This is a development branch intended to preserve the original recurBOY implementation.
> Do not replace your working SquishBox microSD card without imaging/backing it up.

## Objective

Use a **Raspberry Pi Zero 2 W** as an optional outboard video processor in the
Watanabe Autotainment System (WAS):

```text
WAS playback host HDMI -> Linux-compatible UVC HDMI-to-USB capture adapter
                       -> Pi Zero 2 W USB OTG
                       -> recurBOY FX/GLSL processor
                       -> Pi mini-HDMI -> monitor/projector
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
   Many drivers expose additional virtual camera devices; **do not assume
   the original recurBOY camera index 2 is correct**.
5. Arrange a USB OTG adapter or powered hub as needed; keep the power supply
   appropriate for the Pi and capture dongle.

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
WAS_CAPTURE_ID=0 WAS_FX_SHADER=wobble.frag sh startWASHeadless
```

Or, to choose the first top-level effect file found:

```sh
WAS_CAPTURE_ID=0 sh startWASHeadless
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

**Only launch this script after building and verifying that the forked C++
application and its addons are actually installed.** We haven't executed
the build on Raspberry Pi hardware in this development pass.

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
video-only prototype. The encoder is **not** initialized or monitored.

### OLED/button diagnostic controller

`software/ofRecurBoy/was_diagnostics.py` runs independently from the C++
video renderer, communicates locally via OSC, and requires **no additional
custom shield**.

- Button 1 (BCM17): toggle FX bypass/enable.
- Button 2 (BCM27): load the next installed top-level shader.
- OLED: video engine online/offline, UVC grabber readiness, current shader,
  bypass state and reported frame rate.
- Diagnostic status is sent by the engine over localhost UDP `9010`;
  buttons command the engine over localhost UDP `WAS_OSC_PORT` (default `8000`).
- UVC readiness indicates that the capture object reports ready; it
  **does not certify a live HDMI signal**.
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
WAS_DIAGNOSTICS=1 WAS_CAPTURE_ID=0 sh startWASHeadless
```

If the OLED or a button is broken, simply omit `WAS_DIAGNOSTICS=1`;
the video processor starts without physical controls.

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
- GPLv3 obligations apply to distributions of this fork and its code.
