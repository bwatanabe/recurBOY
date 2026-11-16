#!/usr/bin/env python3
"""Optional WAS OLED and button diagnostics for the repurposed Pi Zero 2 W.

The main recurBOY video engine runs independently of this process.

Confirmed salvaged wiring:
  SSD1306 128x64: I2C-1 addr 0x3C; SDA=BCM2, SCL=BCM3; 3.3V
  Button A: BCM17 (physical 11), active LOW to GND
  Button B: BCM27 (physical 13), active LOW to GND
The encoder on BCM22/23/4 is NOT enabled in this version.
"""
import argparse
import threading
import time

OLED_ADDRESS = 0x3C
BUTTON_BYPASS = 17
BUTTON_NEXT = 27
STATUS_PORT = 9010
CONTROL_PORT = 8000
I2C_BUS = 1
DEBOUNCE_SECONDS = 0.065
REDRAW_SECONDS = 0.5


class SSD1306Display:
    """Minimal SSD1306 I2C driver using the image's smbus/Pillow packages."""

    def __init__(self):
        from smbus import SMBus
        from PIL import Image, ImageDraw, ImageFont

        self.bus = SMBus(I2C_BUS)
        self.Image = Image
        self.ImageDraw = ImageDraw
        self.font = ImageFont.load_default()
        self._initialize()

    def _command(self, value):
        self.bus.write_byte_data(OLED_ADDRESS, 0x00, value)

    def _initialize(self):
        # SSD1306, 128x64, horizontal addressing, charge-pump enabled.
        init_commands = (
            0xAE, 0xD5, 0x80, 0xA8, 0x3F, 0xD3, 0x00, 0x40,
            0x8D, 0x14, 0x20, 0x00, 0xA1, 0xC8, 0xDA, 0x12,
            0x81, 0x7F, 0xD9, 0xF1, 0xDB, 0x40, 0xA4, 0xA6, 0xAF
        )
        for command in init_commands:
            self._command(command)

    def render(self, lines):
        img = self.Image.new("1", (128, 64), 0)
        draw = self.ImageDraw.Draw(img)
        for index, line in enumerate(lines[:5]):
            draw.text((0, index * 12), str(line)[:21],
                      font=self.font, fill=255)
        pixels = img.load()
        buffer = bytearray(1024)
        for page in range(8):
            for x in range(128):
                byte = 0
                for bit in range(8):
                    if pixels[x, page * 8 + bit]:
                        byte |= 1 << bit
                buffer[page * 128 + x] = byte
        self._command(0x21)
        self._command(0)
        self._command(127)
        self._command(0x22)
        self._command(0)
        self._command(7)
        # SMBus block transactions support at most 32 data bytes.
        for offset in range(0, len(buffer), 32):
            self.bus.write_i2c_block_data(
                OLED_ADDRESS, 0x40, list(buffer[offset:offset + 32])
            )

    def close(self):
        try:
            self._command(0xAE)
        finally:
            self.bus.close()


def print_wiring():
    print("WAS diagnostics wiring (BCM numbering)")
    print("OLED: SSD1306 128x64 I2C bus 1, addr 0x3C")
    print("      VCC=3.3V (physical 1), GND (6)")
    print("      SDA=GPIO2 (3), SCL=GPIO3 (5)")
    print("Button 1: GPIO17 (11), active-low to GND -> effect bypass")
    print("Button 2: GPIO27 (13), active-low to GND -> next effect")
    print("Encoder reserved: GPIO22 (15), GPIO23 (16), GPIO4 (7)")
    print("I2S DAC unused: GPIO18 (12), GPIO19 (35), GPIO21 (40)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--print-wiring", action="store_true",
                        help="Show pinout without touching Raspberry Pi hardware")
    parser.add_argument("--control-port", type=int, default=CONTROL_PORT,
                        help="C++ video engine UDP OSC port (default: 8000)")
    args = parser.parse_args()
    if args.print_wiring:
        print_wiring()
        return

    import RPi.GPIO as GPIO
    from pythonosc import dispatcher, osc_server, udp_client

    state = {
        "effect": "none",
        "enabled": False,
        "capture": False,
        "fps": 0.0,
        "last_rx": 0.0,
    }
    lock = threading.Lock()

    def receive_status(address, effect, enabled, capture, fps):
        with lock:
            state.update(
                effect=str(effect),
                enabled=bool(enabled),
                capture=bool(capture),
                fps=float(fps),
                last_rx=time.monotonic(),
            )

    events = dispatcher.Dispatcher()
    events.map("/was/video/status", receive_status)
    server = osc_server.ThreadingOSCUDPServer(("127.0.0.1", STATUS_PORT), events)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    sender = udp_client.SimpleUDPClient("127.0.0.1", args.control_port)

    GPIO.setmode(GPIO.BCM)
    for pin in (BUTTON_BYPASS, BUTTON_NEXT):
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # Software debounce protects against the mechanical arcade-switch bounce.
    buttons = {
        pin: {"raw": GPIO.input(pin), "stable": GPIO.input(pin),
              "changed": time.monotonic()}
        for pin in (BUTTON_BYPASS, BUTTON_NEXT)
    }

    screen = None
    try:
        screen = SSD1306Display()
        last_render = 0.0
        while True:
            now = time.monotonic()
            for pin, button in buttons.items():
                raw = GPIO.input(pin)
                if raw != button["raw"]:
                    button["raw"] = raw
                    button["changed"] = now
                if raw != button["stable"] and now - button["changed"] >= DEBOUNCE_SECONDS:
                    button["stable"] = raw
                    if raw == GPIO.LOW:
                        if pin == BUTTON_BYPASS:
                            with lock:
                                new_state = not state["enabled"]
                            sender.send_message("/was/video/fx/enabled", int(new_state))
                        elif pin == BUTTON_NEXT:
                            sender.send_message("/was/video/fx/next", 1)

            if now - last_render >= REDRAW_SECONDS:
                with lock:
                    snapshot = state.copy()
                online = (now - snapshot["last_rx"]) < 3.0
                lines = [
                    "WAS  /  recurBOY",
                    "ENGINE: " + ("ONLINE" if online else "OFFLINE"),
                    "UVC: " + ("READY" if snapshot["capture"] and online else "WAIT"),
                    "FX: " + (snapshot["effect"][:16] if online else "--"),
                    ("ON" if snapshot["enabled"] and online else "BYPASS")
                    + "  FPS: " + (str(round(snapshot["fps"])) if online else "--"),
                ]
                screen.render(lines)
                last_render = now
            time.sleep(0.025)
    except KeyboardInterrupt:
        pass
    finally:
        if screen is not None:
            screen.close()
        GPIO.cleanup([BUTTON_BYPASS, BUTTON_NEXT])
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
