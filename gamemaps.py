import json
import math
import struct
from pathlib import Path

import numpy as np
from PIL import Image

from palette import RGB, WolfPal, SodPal
from version_defs import *

def File_CarmackExpand(src):
    NEARTAG, FARTAG = 0xA7, 0xA8
    src = memoryview(src)
    expanded_len = struct.unpack_from("<H", src, 0)[0]
    src = src[2:]
    dest = []
    i = 0
    while len(dest) < expanded_len // 2:
        ch = struct.unpack_from("<H", src, i)[0]
        i += 2
        chhigh = ch >> 8
        if chhigh == NEARTAG:
            count = ch & 0xFF
            if count == 0:
                ch |= src[i]
                i += 1
                dest.append(ch)
            else:
                offset = src[i]
                i += 1
                for _ in range(count):
                    dest.append(dest[-offset])
        elif chhigh == FARTAG:
            count = ch & 0xFF
            if count == 0:
                ch |= src[i]
                i += 1
                dest.append(ch)
            else:
                offset = struct.unpack_from("<H", src, i)[0]
                i += 2
                for j in range(count):
                    dest.append(dest[offset + j])
        else:
            dest.append(ch)
    return dest


def File_RLEWexpand(src_words, rlew_tag):
    out = []
    i = 0
    while i < len(src_words):
        value = src_words[i]
        i += 1
        if value != rlew_tag:
            out.append(value)
        else:
            count = src_words[i]
            i += 1
            val = src_words[i]
            i += 1
            out.extend([val] * count)
    return out


def File_MAP_Expand(raw_bytes, rlew_tag):
    carmacked = File_CarmackExpand(raw_bytes)
    # skip 2-byte length prefix before RLEW
    return File_RLEWexpand(carmacked[1:], rlew_tag)


def extract_maps(maphead_path: Path, gamemaps_path: Path):
    print("FileIO: Map Files")

    spear = True if maphead_path.suffix.lower() == ".sod" else False
    palette = SodPal if spear else WolfPal
    ceiling_colors = sod_ceilings_colors if spear else wl6_ceilings_colors

    # Create output directories
    thumb_path = Path("maps/thumbs")
    thumb_path.mkdir(parents=True, exist_ok=True)

    json_path = Path("maps/json")
    json_path.mkdir(parents=True, exist_ok=True)

    map_offsets = []
    with open(maphead_path, "rb") as mh:
        sig = struct.unpack("<H", mh.read(2))[0]

        if sig != 0xABCD:
            print(f"FileIO: Wrong map header file: {maphead_path}")
            return 0

        # maybe just read till EOF instead?
        for _ in range((maphead_path.stat().st_size - 2) // 4):
            map_offset = struct.unpack("<L", mh.read(4))[0]
            if map_offset == 0:
                break
            map_offsets.append(map_offset)

    print(f"-> Total Levels: {len(map_offsets)}")

    idx_formant = f"{{:0{int(math.log10(len(map_offsets) - 1)) + 1}d}}"

    with open(gamemaps_path, "rb") as gm:
        for level, map_offset in enumerate(map_offsets):
            gm.seek(map_offset)
            l1_offset = struct.unpack("<L", gm.read(4))[0]
            l2_offset = struct.unpack("<L", gm.read(4))[0]
            l3_offset = struct.unpack("<L", gm.read(4))[0]

            l1_len = struct.unpack("<H", gm.read(2))[0]
            l2_len = struct.unpack("<H", gm.read(2))[0]
            l3_len = struct.unpack("<H", gm.read(2))[0]

            width = struct.unpack("<H", gm.read(2))[0]
            height = struct.unpack("<H", gm.read(2))[0]

            name = gm.read(16).decode('ascii', errors='ignore').split('\x00', 1)[0]
            sig = gm.read(4).decode('ascii', errors='ignore') # !ID!

            assert width == 64 and height == 64, f"Unexpected map size: {width}x{height}"

            def read_and_expand(offset, length):
                gm.seek(offset)
                data = gm.read(length)
                return File_MAP_Expand(data, 0xABCD)

            layer1 = read_and_expand(l1_offset, l1_len)
            layer2 = read_and_expand(l2_offset, l2_len)
            layer3 = read_and_expand(l3_offset, l3_len)

            base = np.array([tile_to_color(t) for t in layer1], dtype=np.uint8).reshape((64, 64, 3))

            if layer2:
                overlay = np.array([
                    (0, 255, 0) if t == 19 else (0, 0, 0) for t in layer2
                ], dtype=np.uint8).reshape((64, 64, 3))
                combined = np.clip(base + overlay, 0, 255)
            else:
                combined = base

            Image.fromarray(combined, "RGB").save(thumb_path / f"{idx_formant.format(level)}_{name}.png")

            map_root = {
                "Name": name,
                "CeilingColor": palette[ceiling_colors[level]],
                "FloorColor": palette[floor_color],
                "Tiles": layer1,
                "Things": layer2,
            }

            with open(json_path / f"{idx_formant.format(level)}_{name}.json", "w") as f:
                json.dump(map_root, f)

    return 1


def tile_to_color(tile):
    if tile == 0:
        return 255, 255, 255
    elif 1 <= tile <= 63:
        return 64, 64, 64
    elif 90 <= tile <= 101:
        return 0, 128, 255
    elif 106 <= tile <= 111:
        return 255, 0, 0
    else:
        return 128, 128, 128
