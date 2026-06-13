#!/usr/bin/env python3
"""
HHKB Professional Hybrid / Hybrid Type-S - HID Tool (Windows / macOS / Linux)

Install:
    pip install hid
    # Windows also needs hidapi.dll next to python.exe (libusb/hidapi releases)

Usage:
    python hhkb_hid.py list           # list connected HHKB interfaces
    python hhkb_hid.py info           # keyboard info (read-only, safe)
    python hhkb_hid.py dump-firmware [output.bin]
    python hhkb_hid.py get-keymap     [output.json]
    python hhkb_hid.py probe-keymap   # raw GET_KEYMAP dump (JIS structure check)

Notes:
    - macOS may require sudo.
    - Windows: run terminal as Administrator.
"""

import hid
import sys
import time
import json
from pathlib import Path

# -- Device constants --------------------------------------
VENDOR_ID    = 0x04FE
# 0x0020-0x0021: ANSI confirmed
# 0x0022: JIS (confirmed via real hardware, PID=0x0022)
PRODUCT_IDS  = [0x0020, 0x0021, 0x0022]
USAGE_PAGE   = 0xFF00   # Interface #2 (vendor-specific)
MAGIC        = 0xAA
BUF_SIZE     = 65       # report ID(1) + payload(64)

# -- Command IDs -------------------------------------------
CMD_GET_INFO      = 0x02
CMD_GET_DIP       = 0x05
CMD_GET_MODE      = 0x06
CMD_WRITE_KEYMAP  = 0x86
CMD_GET_KEYMAP    = 0x87
CMD_DUMP_FIRMWARE = 0xD0
CMD_FIRMUP_START  = 0xE1
CMD_FIRMUP_SEND   = 0xE2
CMD_FIRMUP_END    = 0xE3


# -- Device discovery --------------------------------------

def enumerate_hhkb():
    """List all connected HHKB interfaces."""
    found = []
    for pid in PRODUCT_IDS:
        for dev in hid.enumerate(VENDOR_ID, pid):
            found.append(dev)
    return found


def find_programming_interface():
    """
    Find the keymap/firmware interface (#2).
    Identified by usage_page == 0xFF00. Returns path or None.
    """
    for pid in PRODUCT_IDS:
        for dev in hid.enumerate(VENDOR_ID, pid):
            if dev.get('usage_page') == USAGE_PAGE:
                return dev['path']
    return None


# -- Packet helpers ----------------------------------------

def make_packet(cmd: int, payload: bytes = b'') -> bytes:
    """Build a 65-byte HID output packet."""
    buf = bytearray(BUF_SIZE)
    buf[0] = 0x00   # report ID
    buf[1] = MAGIC
    buf[2] = MAGIC
    buf[3] = cmd
    for i, b in enumerate(payload[:61]):
        buf[4 + i] = b
    return bytes(buf)


# -- Operations --------------------------------------------

def get_info(dev: hid.Device) -> dict:
    """GET_KEYBOARD_INFO (0x02) - read keyboard info."""
    dev.write(make_packet(CMD_GET_INFO))
    time.sleep(0.05)
    r = dev.read(64, timeout=2000)
    if not r:
        raise RuntimeError("No response from keyboard")
    return {
        'type_number':    r[4],
        'revision':       r[5],
        'serial':         bytes(r[6:18]).decode('ascii', errors='replace').rstrip('\x00'),
        'app_firmware':   f"{r[18]}.{r[19]}.{r[20]}",
        'boot_firmware':  f"{r[21]}.{r[22]}.{r[23]}",
        'running':        'app' if r[24] == 0 else 'bootloader',
    }


def dump_firmware(dev: hid.Device, output_path: str = 'firmware.bin') -> bytes:
    """
    DUMP_FIRMWARE (0xD0) - dump the whole firmware.
    Data is 56 bytes/packet starting at offset +8.
    A packet shorter than 56 bytes ends the stream.
    """
    print("Sending DUMP_FIRMWARE command...")
    dev.write(make_packet(CMD_DUMP_FIRMWARE))
    time.sleep(0.1)

    firmware = bytearray()
    packet_count = 0
    MAX_PACKETS = 6000   # 300KB / 56bytes ~= 5357, with margin

    while packet_count < MAX_PACKETS:
        resp = dev.read(64, timeout=3000)
        if not resp:
            print(f"\nTimeout after {packet_count} packets")
            break

        chunk = bytes(resp[8:8 + 56])
        actual_len = next(
            (i for i in range(56, 0, -1) if resp[8 + i - 1] != 0),
            56
        )
        firmware.extend(chunk[:actual_len])
        packet_count += 1

        if packet_count % 100 == 0:
            print(f"  {len(firmware):,} bytes received...", end='\r')

        if actual_len < 56:
            break

    print(f"\nDone: {len(firmware):,} bytes ({packet_count} packets)")
    Path(output_path).write_bytes(firmware)
    print(f"Saved -> {output_path}")
    return bytes(firmware)


def probe_keymap_raw(dev: hid.Device):
    """
    Dump the raw GET_KEYMAP response as-is.
    JIS layout may differ from ANSI; run this first to check
    pass count and byte structure.
    """
    dev.write(make_packet(CMD_GET_KEYMAP))
    time.sleep(0.05)

    total = bytearray()
    for i in range(6):
        resp = dev.read(64, timeout=500)
        if not resp:
            print(f"Pass {i+1}: timeout (no more data)")
            break
        print(f"Pass {i+1}: {bytes(resp[:20]).hex()} ...")
        total.extend(resp)

    print(f"Total: {len(total)} bytes received across passes")
    return bytes(total)


def get_keymap(dev: hid.Device, output_path: str = None) -> list:
    """
    GET_KEYMAP (0x87) - read the keymap.

    ANSI: 128 bytes (3 passes: 58+58+12, each offset +6)
    JIS:  unverified. Run probe-keymap first.
    """
    dev.write(make_packet(CMD_GET_KEYMAP))
    time.sleep(0.05)

    keymap_raw = bytearray()
    read_sizes = [58, 58, 12]   # ANSI defaults; JIS may differ

    for expected_size in read_sizes:
        resp = dev.read(64, timeout=2000)
        if not resp:
            raise RuntimeError("No response while reading keymap")
        keymap_raw.extend(resp[6:6 + expected_size])
        time.sleep(0.02)

    keymap = list(keymap_raw[:128])

    if output_path:
        Path(output_path).write_text(json.dumps(keymap, indent=2))
        print(f"Keymap saved -> {output_path}")
    return keymap


# -- CLI ---------------------------------------------------

def cmd_list():
    devices = enumerate_hhkb()
    if not devices:
        print("HHKB not found.")
        return
    for i, d in enumerate(devices):
        print(f"[{i}] PID={d['product_id']:#06x}  usage_page={d.get('usage_page'):#06x}"
              f"  usage={d.get('usage'):#06x}  path={d['path']}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == 'list':
        cmd_list()
        return

    path = find_programming_interface()
    if not path:
        print("Programming interface (usage_page=0xFF00) not found.")
        print("Try 'list' to see all connected HHKB interfaces.")
        sys.exit(1)

    with hid.Device(path=path) as dev:
        if cmd == 'info':
            info = get_info(dev)
            print(json.dumps(info, indent=2))

        elif cmd == 'dump-firmware':
            out = sys.argv[2] if len(sys.argv) > 2 else 'firmware.bin'
            dump_firmware(dev, out)

        elif cmd == 'get-keymap':
            out = sys.argv[2] if len(sys.argv) > 2 else None
            km = get_keymap(dev, out)
            if not out:
                print(json.dumps(km))

        elif cmd == 'probe-keymap':
            probe_keymap_raw(dev)

        else:
            print(f"Unknown command: {cmd}")
            print("Commands: list, info, dump-firmware [out.bin], get-keymap [out.json], probe-keymap")
            sys.exit(1)


if __name__ == '__main__':
    main()
