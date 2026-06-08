#!/usr/bin/env python3
"""
HHKB Professional Hybrid / Hybrid Type-S — macOS HID Tool

インストール:
    pip3 install hid

使い方:
    sudo python3 hhkb_hid.py info
    sudo python3 hhkb_hid.py list          # 接続中の HHKB インターフェース一覧
    sudo python3 hhkb_hid.py dump-firmware [output.bin]
    sudo python3 hhkb_hid.py get-keymap    [output.json]

注意: macOS では sudo が必要な場合があります。
"""

import hid
import sys
import time
import json
import struct
from pathlib import Path

# ── デバイス定数 ───────────────────────────────────────────
VENDOR_ID    = 0x04FE
PRODUCT_IDS  = [0x0020, 0x0021, 0x0022]
USAGE_PAGE   = 0xFF00   # Interface #2（ベンダー固有）
MAGIC        = 0xAA
BUF_SIZE     = 65       # report ID(1) + payload(64)

# ── コマンド ID ────────────────────────────────────────────
CMD_GET_INFO      = 0x02
CMD_GET_DIP       = 0x05
CMD_GET_MODE      = 0x06
CMD_WRITE_KEYMAP  = 0x86
CMD_GET_KEYMAP    = 0x87
CMD_DUMP_FIRMWARE = 0xD0
CMD_FIRMUP_START  = 0xE1
CMD_FIRMUP_SEND   = 0xE2
CMD_FIRMUP_END    = 0xE3


# ── デバイス検索 ───────────────────────────────────────────

def enumerate_hhkb():
    """接続中の HHKB インターフェースをすべて列挙する。"""
    found = []
    for pid in PRODUCT_IDS:
        for dev in hid.enumerate(VENDOR_ID, pid):
            found.append(dev)
    return found


def find_programming_interface():
    """
    キーマップ/ファームウェア操作用インターフェース（#2）を探す。
    macOS では usage_page=0xFF00 で識別する。
    見つからない場合は None を返す。
    """
    for pid in PRODUCT_IDS:
        for dev in hid.enumerate(VENDOR_ID, pid):
            if dev.get('usage_page') == USAGE_PAGE:
                return dev['path']
    return None


# ── パケット操作 ───────────────────────────────────────────

def make_packet(cmd: int, payload: bytes = b'') -> bytes:
    """65 バイトの HID 送信パケットを作成する。"""
    buf = bytearray(BUF_SIZE)
    buf[0] = 0x00   # report ID
    buf[1] = MAGIC
    buf[2] = MAGIC
    buf[3] = cmd
    for i, b in enumerate(payload[:61]):
        buf[4 + i] = b
    return bytes(buf)


# ── 各操作 ────────────────────────────────────────────────

def get_info(dev: hid.Device) -> dict:
    """GET_KEYBOARD_INFO (0x02) — キーボード情報を取得する。"""
    dev.write(make_packet(CMD_GET_INFO))
    time.sleep(0.05)
    r = dev.read(64, timeout_ms=2000)
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
    DUMP_FIRMWARE (0xD0) — ファームウェアを丸ごと吸い出す。
    データはオフセット +8 から 56 バイト/パケット。
    56 バイト未満のパケットで終端。
    """
    print("Sending DUMP_FIRMWARE command...")
    dev.write(make_packet(CMD_DUMP_FIRMWARE))
    time.sleep(0.1)

    firmware = bytearray()
    packet_count = 0
    MAX_PACKETS = 6000   # 300KB / 56bytes ≒ 5357、余裕を持たせる

    while packet_count < MAX_PACKETS:
        resp = dev.read(64, timeout_ms=3000)
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
    print(f"Saved → {output_path}")
    return bytes(firmware)


def get_keymap(dev: hid.Device, output_path: str = None) -> list:
    """
    GET_KEYMAP (0x87) — キーマップを読み取る（128 キー分）。
    3 回の受信: 58 + 58 + 12 bytes (各オフセット +6 から)
    """
    dev.write(make_packet(CMD_GET_KEYMAP))
    time.sleep(0.05)

    keymap_raw = bytearray()
    read_sizes = [58, 58, 12]

    for expected_size in read_sizes:
        resp = dev.read(64, timeout_ms=2000)
        if not resp:
            raise RuntimeError("No response while reading keymap")
        keymap_raw.extend(resp[6:6 + expected_size])
        time.sleep(0.02)

    keymap = list(keymap_raw[:128])

    if output_path:
        Path(output_path).write_text(json.dumps(keymap, indent=2))
        print(f"Keymap saved → {output_path}")
    return keymap


# ── CLI ───────────────────────────────────────────────────

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
        print("May need: sudo python3 hhkb_hid.py list")
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

        else:
            print(f"Unknown command: {cmd}")
            print(__doc__)
            sys.exit(1)


if __name__ == '__main__':
    main()
