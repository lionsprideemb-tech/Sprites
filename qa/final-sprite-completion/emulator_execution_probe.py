#!/usr/bin/env python3
"""Original synthetic DS execution probe; no commercial ROM or assets."""
import argparse
import json
import struct
import tempfile
from pathlib import Path
from desmume.emulator import DeSmuME


def crc16(data):
    c = 0xffff
    for v in data:
        c ^= v
        for _ in range(8):
            c = (c >> 1) ^ (0xa001 if c & 1 else 0)
    return c


def make_probe(path):
    b = bytearray(131072)
    b[:12] = b'MERCURY TEST'
    b[12:16] = b'QAAA'
    b[16:18] = b'00'
    # ARM9 writes an original marker to RAM, then loops; ARM7 loops.
    arm9 = struct.pack('<6I', 0xe59f0008, 0xe59f1008, 0xe5801000,
                       0xeafffffe, 0x02010000, 0x4d455243)
    arm7 = struct.pack('<I', 0xeafffffe)
    struct.pack_into('<4I', b, 0x20, 0x4000, 0x02000000, 0x02000000, len(arm9))
    struct.pack_into('<4I', b, 0x30, 0x8000, 0x03800000, 0x03800000, len(arm7))
    struct.pack_into('<II', b, 0x80, len(b), 0x4000)
    b[0x4000:0x4000 + len(arm9)] = arm9
    b[0x8000:0x8000 + len(arm7)] = arm7
    struct.pack_into('<H', b, 0x15c, crc16(b[0xc0:0x15c]))
    struct.pack_into('<H', b, 0x15e, crc16(b[:0x15e]))
    path.write_bytes(b)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--screenshot', type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as td:
        rom = Path(td) / 'probe.nds'
        make_probe(rom)
        emu = DeSmuME()
        try:
            emu.open(str(rom))
            assert emu.is_running()
            before = emu.memory.unsigned.read_long(0x02010000)
            assert before == 0
            for _ in range(120):
                emu.cycle(False)
                assert emu.is_running()
            after = emu.memory.unsigned.read_long(0x02010000)
            assert after == 0x4d455243
            screenshot = emu.screenshot()
            assert screenshot.size == (256, 384)
            if args.screenshot:
                screenshot.save(args.screenshot)
            print(json.dumps({'result': 'PASS', 'frames': 120, 'before': hex(before),
                              'after': hex(after), 'screenshot': list(screenshot.size),
                              'commercial_rom_loaded': False, 'gameplay_verified': False}))
        finally:
            emu.destroy()


if __name__ == '__main__':
    main()
