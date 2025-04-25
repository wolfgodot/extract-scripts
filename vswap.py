import os
import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from PIL import Image

from palette import WolfPal, SodPal
from version_defs import gen_vswap_lookup_table

@dataclass
class Shape:
    leftpix: int
    rightpix: int
    dataofs: List[int]  # Array of 64 unsigned short offsets

@dataclass
class Chunk:
    offset: int = 0
    length: int = 0

@dataclass
class VSwapContext:
    ChunksInFile: int = 0
    SpriteStart: int = 0
    SoundStart: int = 0
    Pages: List[Chunk] = field(default_factory=list)
    FileName: Path = Path()
    names: List[str] = field(default_factory=list)


def Img_ExpandPalette(dst, src, w, h, pal=None, transparent=True):
    ssrc = src[:]
    for y in range(h):
        for x in range(w):
            srcp = src[y * w + x]
            if transparent and srcp == 255:
                r = g = b = c = 0
                for v in range(y - 1, y + 2):
                    for u in range(x - 1, x + 2):
                        if 0 <= u < w and 0 <= v < h:
                            i = ssrc[v * w + u]
                            if i != 255:
                                r += pal[i][0]
                                g += pal[i][1]
                                b += pal[i][2]
                                c += 1
                c = max(c, 1)
                dst.extend([r // c, g // c, b // c, 0])
            else:
                dst.extend([pal[srcp][0], pal[srcp][1], pal[srcp][2]])
                if transparent:
                    dst.append(255)


def File_PML_OpenPageFile(ctx: VSwapContext, filename: Path):
    try:
        with open(filename, 'rb') as fp:
            ctx.FileName = filename

            header = fp.read(6)
            ctx.ChunksInFile, ctx.SpriteStart, ctx.SoundStart = struct.unpack('<HHH', header)

            print(f"FileIO: Page File")
            print(f"-> Total Chunks : {ctx.ChunksInFile}")
            print(f"-> Sprites start: {ctx.SpriteStart}")
            print(f"-> Sounds start : {ctx.SoundStart}")

            ctx.Pages = [Chunk() for _ in range(ctx.ChunksInFile)]

            for i in range(ctx.ChunksInFile):
                ctx.Pages[i].offset = struct.unpack('<L', fp.read(4))[0]

            for i in range(ctx.ChunksInFile):
                tmp = struct.unpack('<H', fp.read(2))[0]
                ctx.Pages[i].length = tmp

        return 1
    except FileNotFoundError:
        print(f"FileIO: Unable to open page file: {filename}")
        return 0


def File_PML_ReadPage(ctx: VSwapContext, n, data):
    if not ctx.FileName:
        print("FileIO: Page file not opened")
        return 0
    if n >= ctx.ChunksInFile:
        print(f"FileIO: Wrong chunk num {n}")
        return 0
    if not ctx.Pages[n].length or not ctx.Pages[n].offset:
        print(f"FileIO: Page {n} wrong header data")
        return 0
    if data is None:
        print("FileIO: Bad Pointer!")
        return 0

    with open(ctx.FileName, 'rb') as fp:
        fp.seek(ctx.Pages[n].offset)
        chunk_data = fp.read(ctx.Pages[n].length)
        data[:] = chunk_data
        if len(chunk_data) != ctx.Pages[n].length:
            print(f"FileIO: Page {n} read error")
            return 0
    return 1


def File_PML_LoadWall(ctx: VSwapContext, n, block, palette=WolfPal):
    if n >= ctx.SpriteStart:
        print(f"FileIO: Wall index ({n}) out of bounds [0-{ctx.SpriteStart}]")
        return 0

    data = bytearray(ctx.Pages[n].length)
    if not File_PML_ReadPage(ctx, n, data):
        return 0

    for x in range(64):
        for y in range(64):
            val = data[(x << 6) + y]
            idx = ((y << 6) + x) * 3
            block[idx + 0] = palette[val][0]
            block[idx + 1] = palette[val][1]
            block[idx + 2] = palette[val][2]
    return 1


def File_PML_LoadSprite(ctx: VSwapContext, n, block, palette=WolfPal):
    if n < ctx.SpriteStart or n >= ctx.SoundStart:
        print(f"FileIO: Sprite index ({n}) out of bounds [{ctx.SpriteStart}-{ctx.SoundStart}]")
        return 0

    sprite = bytearray(ctx.Pages[n].length)
    if not File_PML_ReadPage(ctx, n, sprite):
        return 0

    # Initialize all as transparent
    tmp = bytearray([255] * (64 * 64))

    shape = Shape(
        leftpix=int.from_bytes(sprite[0:2], byteorder='little', signed=False),
        rightpix=int.from_bytes(sprite[2:4], byteorder='little', signed=False),
        dataofs=[int.from_bytes(sprite[4 + i * 2:6 + i * 2], byteorder='little', signed=False) for i in range(64)]
    )

    # Process each column from leftpix to rightpix
    for x in range(shape.leftpix, shape.rightpix + 1):
        # Get command pointer offset
        cmd_offset = shape.dataofs[x - shape.leftpix]

        # Process line commands
        pos = cmd_offset
        while True:
            # Read command values (3 shorts)
            cmd0 = int.from_bytes(sprite[pos:pos + 2], byteorder='little', signed=True)
            if cmd0 == 0:  # End of commands for this column
                break

            cmd1 = int.from_bytes(sprite[pos + 2:pos + 4], byteorder='little', signed=True)
            cmd2 = int.from_bytes(sprite[pos + 4:pos + 6], byteorder='little', signed=True)
            pos += 6  # Move to next command

            i = cmd2 // 2 + cmd1
            for y in range(cmd2 // 2, cmd0 // 2):
                tmp[y * 64 + x] = sprite[i]
                i += 1

    # Clear block before expanding palette
    block.clear()

    # Now expand the palette
    Img_ExpandPalette(block, tmp, 64, 64, palette, True)

    return 1


def extract_vswap(vswap_path):
    spear = True if vswap_path.suffix.lower() == ".sod" else False

    ctx = VSwapContext()
    ctx.names = gen_vswap_lookup_table(spear=spear)

    palette = SodPal if spear else WolfPal

    walls_path = Path("vswap/walls")
    walls_path.mkdir(parents=True, exist_ok=True)

    sprites_path = Path("vswap/sprites")
    sprites_path.mkdir(parents=True, exist_ok=True)

    digisounds_path = Path("vswap/digisounds")
    digisounds_path.mkdir(parents=True, exist_ok=True)

    if not os.path.isfile(vswap_path):
        print(f"Error: Input file not found: {vswap_path}")
        sys.exit(1)

    if not File_PML_OpenPageFile(ctx, vswap_path):
        print("Failed to open page file.")
        sys.exit(1)

    for i in range(ctx.SpriteStart):
        block = bytearray(64 * 64 * 3)
        if File_PML_LoadWall(ctx, i, block, palette):
            im = Image.frombytes('RGB', (64, 64), block, 'raw')
            idx, shaded = divmod(i, 2)  # every second texture is a shaded variant
            im.save(walls_path / f"{idx}.png" if shaded == 0 else walls_path / f"{idx}_shaded.png")
        else:
            print(f"Failed to load wall {i}.")

    for i in range(ctx.SpriteStart, ctx.SoundStart):
        block = bytearray(64 * 64 * 4)
        if File_PML_LoadSprite(ctx, i, block, palette):
            im = Image.frombytes('RGBA', (64, 64), block, 'raw')
            shapenum = i - ctx.SpriteStart
            im.save(sprites_path / f"{shapenum}_{ctx.names[shapenum]}.png")
        else:
            print(f"Failed to load sprite {i}.")

    digimap_n = ctx.ChunksInFile - 1
    digimap = bytearray(ctx.Pages[digimap_n].length)
    if not File_PML_ReadPage(ctx, digimap_n, digimap):
        print("Failed to load digimap page.")
        sys.exit(1)

    with open(digisounds_path / "digimap.bin", "wb") as digimap_file:
        digimap_file.write(digimap)

    for i in range(ctx.SoundStart, digimap_n):
        block = bytearray(ctx.Pages[i].length)
        soundnum = i - ctx.SoundStart
        if not File_PML_ReadPage(ctx, i, block):
            print(f"Failed to load sound {soundnum}.")
        with open(digisounds_path / f"{soundnum}.bin", "wb") as sound_file:
            sound_file.write(block)
