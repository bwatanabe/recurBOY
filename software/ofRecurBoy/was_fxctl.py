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
    else:
        address, signature, value = "/was/video/fx/speed", "f", args.value

    send_osc(args.host, args.port, address, signature, value)
    print("Sent {} {} to {}:{} (UDP, no acknowledgement)".format(
        address, value, args.host, args.port))


if __name__ == "__main__":
    main()
