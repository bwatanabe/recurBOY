#!/usr/bin/env python3
"""Small cross-platform OSC client for the WAS output video processor.

Only Python standard library is required (including on macOS). Sends a
single UDP OSC message; check the recurBOY OLED/video to confirm delivery.
"""
import argparse
import math
import socket
import struct


def osc_string(value):
    value = value.encode("utf-8") + b"\0"
    return value + b"\0" * ((-len(value)) % 4)


def send_osc(host, port, address, signature, arg):
    packet = osc_string(address) + osc_string("," + signature)
    if signature == "i":
        packet += struct.pack(">i", int(arg))
    elif signature == "f":
        packet += struct.pack(">f", float(arg))
    elif signature == "s":
        packet += osc_string(arg)
    else:
        raise ValueError("Unsupported OSC value type")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(packet, (host, port))


def unit_value(raw):
    value = float(raw)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise argparse.ArgumentTypeError("expected a number between 0 and 1")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1",
                        help="recurBOY's LAN IP (default: localhost)")
    parser.add_argument("--port", type=int, default=8000)
    commands = parser.add_subparsers(dest="command")
    commands.required = True

    commands.add_parser("next", help="select next installed FX")
    enabled = commands.add_parser("enable", help="FX on (1) or bypass (0)")
    enabled.add_argument("value", type=int, choices=[0, 1])
    load = commands.add_parser("load", help="load FX shader by name")
    load.add_argument("filename")
    param = commands.add_parser("param", help="set parameter 0, 1 or 2")
    param.add_argument("index", type=int, choices=[0, 1, 2])
    param.add_argument("value", type=unit_value)
    speed = commands.add_parser("speed", help="set FX speed")
    speed.add_argument("value", type=unit_value)

    # A single, classic video-mixer character generator overlay.
    title = commands.add_parser("title", help="show/replace text overlay")
    title.add_argument("message", help="text; use quoted string (\\n for line breaks)")
    title_toggle = commands.add_parser("title-show", help="show or hide existing title")
    title_toggle.add_argument("value", type=int, choices=[0, 1])
    commands.add_parser("title-clear", help="clear and hide title")

    title_font = commands.add_parser("title-font", help="select installed .ttf/.otf font")
    title_font.add_argument("filename", help="filename in Pi /home/pi/FONT")

    for attribute in ("x", "y", "size", "hue", "sat", "brightness", "alpha"):
        setting = commands.add_parser("title-" + attribute,
                                      help="set text " + attribute + " (0..1)")
        setting.add_argument("value", type=unit_value)

    args = parser.parse_args()

    if args.command == "next":
        address, signature, value = "/was/video/fx/next", "i", 1
    elif args.command == "enable":
        address, signature, value = "/was/video/fx/enabled", "i", args.value
    elif args.command == "load":
        address, signature, value = "/was/video/fx/load", "s", args.filename
    elif args.command == "param":
        address = "/was/video/fx/param/{}".format(args.index)
        signature, value = "f", args.value
    elif args.command == "speed":
        address, signature, value = "/was/video/fx/speed", "f", args.value
    elif args.command == "title":
        address, signature, value = "/was/video/text/set", "s", args.message.replace("\\n", "\n")
        if len(value.encode("utf-8")) > 512:
            parser.error("title must be 512 UTF-8 bytes or shorter")
    elif args.command == "title-show":
        address, signature, value = "/was/video/text/enabled", "i", args.value
    elif args.command == "title-clear":
        # Our generic sender supports one argument per OSC message. The
        # receiver intentionally ignores this int for the clear command.
        address, signature, value = "/was/video/text/clear", "i", 1
    elif args.command == "title-font":
        address, signature, value = "/was/video/text/font", "s", args.filename
    elif args.command.startswith("title-"):
        address = "/was/video/text/" + args.command[len("title-"):]
        signature, value = "f", args.value
    else:
        parser.error("unknown OSC command")

    send_osc(args.host, args.port, address, signature, value)
    print("Sent {} {} to {}:{} (UDP, no acknowledgement)".format(
        address, value, args.host, args.port))


if __name__ == "__main__":
    main()
