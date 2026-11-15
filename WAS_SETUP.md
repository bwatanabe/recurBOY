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
Existing SquishBox OLED and two buttons are **not** configured in v0.1 and may
later be used for diagnostics. Keep them physically connected if safe, but do
not assume their pin mappings without checking the actual wiring.

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

## Hardware notes: salvaged SquishBox Pi

The Pi Zero 2 W already has an SSD1306 OLED and two arcade buttons. An
SSD1306 I²C screen typically uses GPIO2/SDA (physical pin 3) and GPIO3/SCL
(physical pin 5), often address `0x3c`; **these are not yet verified for this
actual SquishBox build**. Button GPIO mappings, ground and pull-up conventions
must likewise be identified before writing a GPIO diagnostic daemon.
No new pins are allocated by WAS headless v0.1.

Potential future maintenance use:
- OLED: selected shader, OSC connection state, video capture availability, FPS.
- Button A: toggle effects/bypass.
- Button B: cycle through effects.
- Hold both: diagnostic overlay (not power-off until safeguards tested).

## Acceptance tests

- [ ] Pi Zero 2 W boots the image and displays HDMI output.
- [ ] `ofRecurBoy` builds successfully with the bundled addons.
- [ ] No TFT/Python display application or MCP3008 ADC is needed.
- [ ] Capture adapter is detected and live video appears in bypass.
- [ ] One bundled effect processes live capture.
- [ ] Changing `/was/video/fx/param/0` produces visible changes.
- [ ] Toggling `/was/video/fx/enabled` switches between dry and processed video.
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
