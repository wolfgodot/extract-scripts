import os
import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from PIL import Image

from palette import RGB, WolfPal, SodPal
from version_defs import *


@dataclass
class wl_picture:
    width: int
    height: int

@dataclass
class VGAContext:
    TotalChunks: int = 0
    HeadName: Path = Path()
    DictName: Path = Path()
    FileName: Path = Path()
    offset: List[int] = field(default_factory=list)
    hufftable: List[tuple[int, int]] = field(default_factory=list)


def File_HuffExpand(source, target, expanded_size, compressed_size, dictionary):
    # Current bit position in the source buffer
    bit_pos = 0
    # Current position in the target buffer
    target_pos = 0

    # Head node is always node 254
    current_node = 254

    # Process until we've filled the target buffer
    while target_pos < expanded_size:
        # Get the byte that contains the current bit
        byte_idx = bit_pos // 8
        bit_idx = bit_pos % 8

        # Check if we're still within the compressed data bounds
        if byte_idx >= len(source) or byte_idx >= compressed_size:
            break

        # Extract the current bit (LSB-first)
        current_bit = (source[byte_idx] >> bit_idx) & 1
        bit_pos += 1

        # Navigate the Huffman tree
        if current_bit == 0:
            next_node = dictionary[current_node][0]
        else:
            next_node = dictionary[current_node][1]

        # Check if we've reached a leaf node (character)
        if next_node < 256:
            # It's a character, write it to the target buffer
            target[target_pos] = next_node
            target_pos += 1
            # Reset to the head node
            current_node = 254
        else:
            # It's an internal node, continue traversal
            current_node = next_node - 256

    return


def File_VGA_ReadChunk(ctx: VGAContext, n, chunk_type: VGAChunkType):
    if n < 0 or n >= ctx.TotalChunks:
        print(f"FileIO: VGA chunk index out of bounds [0, {ctx.TotalChunks}]: {n}")
        return None

    # Find next valid chunk to determine compressed size
    next_chunk = n + 1
    while next_chunk < ctx.TotalChunks and ctx.offset[next_chunk] == -1:
        next_chunk += 1

    if next_chunk >= ctx.TotalChunks:
        compressed_size = os.path.getsize(ctx.FileName) - ctx.offset[n]
    else:
        compressed_size = ctx.offset[next_chunk] - ctx.offset[n]

    # Read compressed data
    with open(ctx.FileName, 'rb') as fp:
        fp.seek(ctx.offset[n])
        src = fp.read(compressed_size)

    if not src:
        return None

    if chunk_type == VGAChunkType.STRUCTPIC:
        expanded = ctx.TotalChunks * 4
    elif chunk_type == VGAChunkType.TILE8:
        expanded = 35 * 64 # BLOCK * NUMTILE8
    else:
        expanded = struct.unpack('<L', src[:4])[0]

    if expanded == 0:
        return None

    # Skip length bytes
    if chunk_type != VGAChunkType.TILE8:
        src = src[4:]

    target = bytearray(expanded)

    File_HuffExpand(src, target, expanded, compressed_size, ctx.hufftable)
    return target


def deplane(buf, width, height, palette):
    buf1 = bytearray(len(buf))

    hw = width * height
    quarter = hw // 4

    # Reorganize the planar data
    for n in range(hw):
        buf1[n] = buf[(n % 4) * quarter + n // 4]

    # Convert to RGB data
    buf2 = bytearray(hw * 3)

    for n in range(hw):
        color_idx = buf1[n]
        buf2[n * 3 + 0] = palette[color_idx][0]
        buf2[n * 3 + 1] = palette[color_idx][1]
        buf2[n * 3 + 2] = palette[color_idx][2]

    return buf2


def File_VGA_OpenVgaFiles(ctx: VGAContext, dict_path: Path, header_path: Path, vga_path: Path):
    if not os.path.isfile(dict_path):
        print(f"FileIO: graphics dictionary missed: {dict_path}")
        return 0
    if not os.path.isfile(header_path):
        print(f"FileIO: graphics header missed: {header_path}")
        return 0
    if not os.path.isfile(vga_path):
        print(f"FileIO: VGA graphics file missed: {vga_path}")
        return 0

    ctx.HeadName = header_path
    ctx.DictName = dict_path
    ctx.FileName = vga_path

    # Read dictionary file (huffman nodes) (1024 bytes)
    with open(dict_path, 'rb') as fp:
        for _ in range(256):
            bit0, bit1 = struct.unpack('<HH', fp.read(4))
            ctx.hufftable.append((bit0, bit1))

    # Read header file to get chunks info
    header_size = os.path.getsize(header_path)
    ctx.TotalChunks = header_size // 3

    with open(header_path, 'rb') as fp:
        for _ in range(ctx.TotalChunks):
            temp = fp.read(3)
            offset = temp[0] + (temp[1] << 8) + (temp[2] << 16)
            if offset == 0xFFFFFF:
                offset = -1
            ctx.offset.append(offset)

    print("FileIO: VGA graphics files")
    print(f"-> dict: {dict_path}")
    print(f"-> head: {header_path}")
    print(f"-> main: {vga_path}")
    print(f"-> Total Chunks: {ctx.TotalChunks}")
    return 1


def extract_vga(dict_path: Path, header_path: Path, vga_path: Path):
    # Create output directories
    font_path = Path("vga/fonts")
    font_path.mkdir(parents=True, exist_ok=True)

    pics_path = Path("vga/pics")
    pics_path.mkdir(parents=True, exist_ok=True)

    tile8_path = Path("vga/tile8")
    tile8_path.mkdir(parents=True, exist_ok=True)

    endscreens_path = Path("vga/endscreens")
    endscreens_path.mkdir(parents=True, exist_ok=True)

    demos_path = Path("vga/demos")
    demos_path.mkdir(parents=True, exist_ok=True)

    endarts_path = Path("vga/endarts")
    endarts_path.mkdir(parents=True, exist_ok=True)

    palettes_path = Path("vga/palettes")
    palettes_path.mkdir(parents=True, exist_ok=True)

    spear = True if dict_path.suffix.lower() == ".sod" else False

    ctx = VGAContext()

    palette = SodPal if spear else WolfPal
    names = gen_vgagraph_name_lookup_table(wl6=not spear, sod=spear)
    range_map = sod_vga_type_range_map if spear else wl6_vga_type_range_map

    if not File_VGA_OpenVgaFiles(ctx, dict_path, header_path, vga_path):
        print("Failed to open VGA files")
        sys.exit(1)

    # Read picture definitions from chunk 0
    buf = File_VGA_ReadChunk(ctx, range_map[VGAChunkType.STRUCTPIC][0], VGAChunkType.STRUCTPIC)
    if buf is None:
        print("Failed to read picture definitions chunk")
        return

    pictable = []
    for i in range(ctx.TotalChunks):
        width = struct.unpack('<H', buf[i * 4:i * 4 + 2])[0]
        height = struct.unpack('<H', buf[i * 4 + 2:i * 4 + 4])[0]
        pictable.append(wl_picture(width, height))

    # Read palettes ahead of time for SOD
    external_palettes = []
    for chunk in range_to_array(VGAChunkType.PALETTE, range_map):
        buf = File_VGA_ReadChunk(ctx, chunk, VGAChunkType.PALETTE)
        with open(palettes_path / f"{names[chunk]}.lmp", 'wb') as fp:
            fp.write(buf)

        v = memoryview(buf)

        external_palette = []
        for i in range(0, 256):
            r = struct.unpack('<B', v[i * 3 + 0:i * 3 + 1])[0]
            g = struct.unpack('<B', v[i * 3 + 1:i * 3 + 2])[0]
            b = struct.unpack('<B', v[i * 3 + 2:i * 3 + 3])[0]
            external_palette.append(RGB(r, g, b))

        external_palettes.append(external_palette)


    for chunk in range(1, ctx.TotalChunks - 1):
        chunk_type, chunk_idx = get_chunk_type_and_index(chunk, range_map)
        if chunk_type is None:
            print(f"unknown vgagraph chunk: {chunk}")
            continue

        name = names[chunk]

        # REFACTOR: move File_VGA_ReadChunk outside, DRY
        if chunk_type == VGAChunkType.FONT:
            font = File_VGA_ReadChunk(ctx, chunk, chunk_type)
            v = memoryview(font)

            font_chars = []

            height = struct.unpack('<h', v[0:2])[0]
            for i in range(256):
                loc = struct.unpack('<h', v[2 + (i * 2):2 + (i * 2 + 2)])[0]
                width = struct.unpack('<b', v[(2 + 256 * 2) + i:(2 + 256 * 2) + i + 1])[0]

                if loc == 0 or width == 0:
                    continue

                font_chars.append({
                    "letter": chr(i),
                    "buf": memoryview(v[loc:loc + width * height]),
                    "width": width,
                })

            # TODO: save as optimized "power of two" cells instead of one line

            total_width = sum(fc["width"] for fc in font_chars)
            buf = bytearray(height * total_width * 4)

            for y in range(height):
                stride = 0
                for fc in font_chars:
                    for x in range(fc["width"]):
                        i = y * fc["width"] + x
                        j = (y * total_width + x + stride) * 4
                        if fc["buf"][i] != 0x00:  # alternatively: == 0x0F, holds for WL6
                            buf[j + 0] = 255
                            buf[j + 1] = 255
                            buf[j + 2] = 255
                            buf[j + 3] = 255
                        else:
                            buf[j + 0] = 0
                            buf[j + 1] = 0
                            buf[j + 2] = 0
                            buf[j + 3] = 0

                    stride += fc["width"]

            tex_name = f"{name}.png"
            im = Image.frombytes('RGBA', (total_width, height), bytes(buf), 'raw')
            im.save(font_path / tex_name)

            # https://www.angelcode.com/products/bmfont/doc/file_format.html
            bmfont = [
                {
                    "info": {
                        "face": name,
                        "size": height,
                        "bold": 0,
                        "italic": 0,
                        "charset": "",
                        "unicode": 1,
                        "stretchH": 100,
                        "smooth": 0,
                        "aa": 1,
                        "padding": [0, 0, 0, 0],
                        "spacing": [0, 0],  # [1,1] ?
                        "outline": 0
                    }
                },
                {
                    "common": {
                        "lineHeight": height,
                        "base": height,
                        "scaleW": total_width,
                        "scaleH": height,
                        "pages": 1,
                        "packed": 0,
                        "alphaChnl": 2,
                        "redChnl": 0,
                        "greenChnl": 0,
                        "blueChnl": 0,
                    },
                },
                {
                    "page": {
                        "id": 0,
                        "file": tex_name
                    },
                },
                {
                    "chars": {
                        "count": len(font_chars)
                    }
                },
            ]

            x = 0
            for fc in font_chars:
                bmfont.append({"char": {
                    "id": ord(fc["letter"]),
                    "x": x,
                    "y": 0,
                    "width": fc["width"],
                    "height": height,
                    "xoffset": 0,
                    "yoffset": 0,
                    "xadvance": fc["width"],
                    "page": 0,
                    "chnl": 15
                }})
                x += fc["width"]

            with open(font_path / f"{name}.fnt", 'w') as fnt_file:
                for i in range(len(bmfont)):
                    for tag, attributes in bmfont[i].items():
                        parts = [tag]
                        for key, value in attributes.items():
                            if isinstance(value, list):
                                parts.append(f"{key}={','.join(map(str, value))}")
                            elif isinstance(value, str):
                                parts.append(f'{key}="{value}"')
                            else:
                                parts.append(f"{key}={value}")

                        fnt_file.write(' '.join(parts) + '\n')

        elif chunk_type == VGAChunkType.PICTURE:
            def read_pic(chunk_idx_, chunk_):
                wl_pic = pictable[chunk_idx_]
                assert (320 >= wl_pic.width >= 1 <= wl_pic.height <= 200)

                buf_ = File_VGA_ReadChunk(ctx, chunk_, chunk_type)

                palette_ = palette

                if spear:
                    pal_idx = sod_pic_palette_map.get(chunk_idx_)
                    if pal_idx is not None:
                        palette_ = external_palettes[pal_idx]

                return (wl_pic.width, wl_pic.height), deplane(buf_, wl_pic.width, wl_pic.height, palette_)

            # Skip second part of the picture
            if spear and chunk_idx - 1 in sod_half_pics:
                continue

            size, buf = read_pic(chunk_idx, chunk)

            # Merge two parts into one picture (320x80 + 320x120 = 320x200)
            if spear and chunk_idx in sod_half_pics:
                size1, buf1 = read_pic(chunk_idx + 1, chunk + 1)
                assert (size[0] == size1[0] == 320)
                assert (size[1] == 80 and size1[1] == 120)
                buf.extend(buf1)
                size = (size[0], size[1] + size1[1])

            im = Image.frombytes('RGB', size, bytes(buf), 'raw')
            im.save(pics_path / f"{chunk_idx}_{name}.png")


        elif chunk_type == VGAChunkType.TILE8:
            buf = File_VGA_ReadChunk(ctx, chunk, chunk_type)
            v = memoryview(buf)

            tiles = []

            for tile in range(0, 35): #define NUMTILE8 35
                tile_buf = deplane(v[64 * tile:64 * tile + 64], 8, 8, palette)
                tiles.append(tile_buf)

            # Generate nine-patch (3x3 tiles) rectangle texture for window borders
            # Assume white background for the missing middle tile
            # TODO: Consider extracting TILE8 font (it's not used anywhere in WOLF3D code)

            blank_tile = bytearray(b'\xFF') * (8 ** 2) * 3

            window_tiles = [
                tiles[0], tiles[1], tiles[2],
                tiles[3], blank_tile, tiles[4],
                tiles[5], tiles[6], tiles[7],
            ]

            patch_buf = bytearray(((8 * 3) ** 2) * 3)

            for tiley in range(0, 3):
                for tilex in range(0, 3):
                    window_tile = window_tiles[tiley * 3 + tilex]
                    for y in range(0, 8):
                        patchy = tiley * 8 + y
                        for x in range(0, 8):
                            patchx = tilex * 8 + x
                            i = y * 8 + x
                            j = patchy * (8 * 3) + patchx
                            patch_buf[j * 3 + 0] = window_tile[i * 3 + 0]
                            patch_buf[j * 3 + 1] = window_tile[i * 3 + 1]
                            patch_buf[j * 3 + 2] = window_tile[i * 3 + 2]

            im = Image.frombytes('RGB', (8 * 3, 8 * 3), bytes(patch_buf), 'raw')
            im.save(tile8_path / f"WINDOW.png")

        elif chunk_type == VGAChunkType.ENDSCREEN:
            endscreen = File_VGA_ReadChunk(ctx, chunk, chunk_type)
            with open(endscreens_path / f"{name}.bin", 'wb') as fp:
                fp.write(endscreen)

        elif chunk_type == VGAChunkType.ENDART:
            endart = File_VGA_ReadChunk(ctx, chunk, chunk_type)
            with open(endarts_path / f"{name}.txt", 'wb') as fp:
                fp.write(endart)

        elif chunk_type == VGAChunkType.DEMO:
            demo = File_VGA_ReadChunk(ctx, chunk, chunk_type)
            with open(demos_path / f"{name}.bin", 'wb') as fp:
                fp.write(demo)

        elif chunk_type == VGAChunkType.PALETTE:
            # Already saved
            continue