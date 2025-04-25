import os
import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from PIL import Image

from palette import WolfPal, SodPal

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
    ctx = VSwapContext()

    spear = True if vswap_path.suffix.lower() == ".sod" else False
    palette = SodPal if spear else WolfPal

    Path("vswap/walls").mkdir(parents=True, exist_ok=True)
    Path("vswap/sprites").mkdir(parents=True, exist_ok=True)
    Path("vswap/digisounds").mkdir(parents=True, exist_ok=True)

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
            im.save(f"vswap/walls/{idx}.png" if shaded == 0 else f"vswap/walls/{idx}_shaded.png")
        else:
            print(f"Failed to load wall {i}.")

    for i in range(ctx.SpriteStart, ctx.SoundStart):
        block = bytearray(64 * 64 * 4)
        if File_PML_LoadSprite(ctx, i, block, palette):
            im = Image.frombytes('RGBA', (64, 64), block, 'raw')
            shapenum = i - ctx.SpriteStart
            im.save(f"vswap/sprites/{shapenum}_{GetSpriteName(shapenum, spear=spear)}.png")
        else:
            print(f"Failed to load sprite {i}.")

    digimap_n = ctx.ChunksInFile - 1
    digimap = bytearray(ctx.Pages[digimap_n].length)
    if not File_PML_ReadPage(ctx, digimap_n, digimap):
        print("Failed to load digimap page.")
        sys.exit(1)

    with open("vswap/digisounds/digimap.bin", "wb") as digimap_file:
        digimap_file.write(digimap)

    for i in range(ctx.SoundStart, digimap_n):
        block = bytearray(ctx.Pages[i].length)
        soundnum = i - ctx.SoundStart
        if not File_PML_ReadPage(ctx, i, block):
            print(f"Failed to load sound {soundnum}.")
        with open(f"vswap/digisounds/{soundnum}.bin", "wb") as sound_file:
            sound_file.write(block)

# TODO: cache lookup table!
def GetSpriteName(shapenum, apogee_1_0=False, apogee_1_1=False, spear=False, upload=False):
    sprite_names = []

    # Basic mapping that's always present
    sprite_names.append("SPR_DEMO")

    if not apogee_1_0:
        sprite_names.append("SPR_DEATHCAM")

    # Static sprites (0-47)
    for i in range(48):
        sprite_names.append(f"SPR_STAT_{i}")

    if spear:
        # Additional static sprites for SPEAR
        for i in range(48, 52):
            sprite_names.append(f"SPR_STAT_{i}")

    # Guard sprites
    for suffix in ["S", "W1", "W2", "W3", "W4"]:
        for i in range(1, 9):
            sprite_names.append(f"SPR_GRD_{suffix}_{i}")

    sprite_names.extend([
        "SPR_GRD_PAIN_1", "SPR_GRD_DIE_1", "SPR_GRD_DIE_2", "SPR_GRD_DIE_3",
        "SPR_GRD_PAIN_2", "SPR_GRD_DEAD", "SPR_GRD_SHOOT1", "SPR_GRD_SHOOT2", "SPR_GRD_SHOOT3"
    ])

    # Dog sprites
    for suffix in ["W1", "W2", "W3", "W4"]:
        for i in range(1, 9):
            sprite_names.append(f"SPR_DOG_{suffix}_{i}")

    sprite_names.extend([
        "SPR_DOG_DIE_1", "SPR_DOG_DIE_2", "SPR_DOG_DIE_3", "SPR_DOG_DEAD",
        "SPR_DOG_JUMP1", "SPR_DOG_JUMP2", "SPR_DOG_JUMP3"
    ])

    # SS sprites
    for suffix in ["S", "W1", "W2", "W3", "W4"]:
        for i in range(1, 9):
            sprite_names.append(f"SPR_SS_{suffix}_{i}")

    sprite_names.extend([
        "SPR_SS_PAIN_1", "SPR_SS_DIE_1", "SPR_SS_DIE_2", "SPR_SS_DIE_3",
        "SPR_SS_PAIN_2", "SPR_SS_DEAD", "SPR_SS_SHOOT1", "SPR_SS_SHOOT2", "SPR_SS_SHOOT3"
    ])

    # Mutant sprites
    for suffix in ["S", "W1", "W2", "W3", "W4"]:
        for i in range(1, 9):
            sprite_names.append(f"SPR_MUT_{suffix}_{i}")

    sprite_names.extend([
        "SPR_MUT_PAIN_1", "SPR_MUT_DIE_1", "SPR_MUT_DIE_2", "SPR_MUT_DIE_3",
        "SPR_MUT_PAIN_2", "SPR_MUT_DIE_4", "SPR_MUT_DEAD",
        "SPR_MUT_SHOOT1", "SPR_MUT_SHOOT2", "SPR_MUT_SHOOT3", "SPR_MUT_SHOOT4"
    ])

    # Officer sprites
    for suffix in ["S", "W1", "W2", "W3", "W4"]:
        for i in range(1, 9):
            sprite_names.append(f"SPR_OFC_{suffix}_{i}")

    sprite_names.extend([
        "SPR_OFC_PAIN_1", "SPR_OFC_DIE_1", "SPR_OFC_DIE_2", "SPR_OFC_DIE_3",
        "SPR_OFC_PAIN_2", "SPR_OFC_DIE_4", "SPR_OFC_DEAD",
        "SPR_OFC_SHOOT1", "SPR_OFC_SHOOT2", "SPR_OFC_SHOOT3"
    ])

    if not spear:
        # Ghosts
        sprite_names.extend([
            "SPR_BLINKY_W1", "SPR_BLINKY_W2", "SPR_PINKY_W1", "SPR_PINKY_W2",
            "SPR_CLYDE_W1", "SPR_CLYDE_W2", "SPR_INKY_W1", "SPR_INKY_W2"
        ])

        # Hans
        sprite_names.extend([
            "SPR_BOSS_W1", "SPR_BOSS_W2", "SPR_BOSS_W3", "SPR_BOSS_W4",
            "SPR_BOSS_SHOOT1", "SPR_BOSS_SHOOT2", "SPR_BOSS_SHOOT3", "SPR_BOSS_DEAD",
            "SPR_BOSS_DIE1", "SPR_BOSS_DIE2", "SPR_BOSS_DIE3"
        ])

        # Schabbs
        sprite_names.extend([
            "SPR_SCHABB_W1", "SPR_SCHABB_W2", "SPR_SCHABB_W3", "SPR_SCHABB_W4",
            "SPR_SCHABB_SHOOT1", "SPR_SCHABB_SHOOT2", "SPR_SCHABB_DIE1", "SPR_SCHABB_DIE2",
            "SPR_SCHABB_DIE3", "SPR_SCHABB_DEAD", "SPR_HYPO1", "SPR_HYPO2", "SPR_HYPO3", "SPR_HYPO4"
        ])

        # Fake
        sprite_names.extend([
            "SPR_FAKE_W1", "SPR_FAKE_W2", "SPR_FAKE_W3", "SPR_FAKE_W4",
            "SPR_FAKE_SHOOT", "SPR_FIRE1", "SPR_FIRE2", "SPR_FAKE_DIE1", "SPR_FAKE_DIE2",
            "SPR_FAKE_DIE3", "SPR_FAKE_DIE4", "SPR_FAKE_DIE5", "SPR_FAKE_DEAD"
        ])

        # Hitler
        sprite_names.extend([
            "SPR_MECHA_W1", "SPR_MECHA_W2", "SPR_MECHA_W3", "SPR_MECHA_W4",
            "SPR_MECHA_SHOOT1", "SPR_MECHA_SHOOT2", "SPR_MECHA_SHOOT3", "SPR_MECHA_DEAD",
            "SPR_MECHA_DIE1", "SPR_MECHA_DIE2", "SPR_MECHA_DIE3", "SPR_HITLER_W1",
            "SPR_HITLER_W2", "SPR_HITLER_W3", "SPR_HITLER_W4", "SPR_HITLER_SHOOT1",
            "SPR_HITLER_SHOOT2", "SPR_HITLER_SHOOT3", "SPR_HITLER_DEAD", "SPR_HITLER_DIE1",
            "SPR_HITLER_DIE2", "SPR_HITLER_DIE3", "SPR_HITLER_DIE4", "SPR_HITLER_DIE5",
            "SPR_HITLER_DIE6", "SPR_HITLER_DIE7", "SPR_GIFT_W1", "SPR_GIFT_W2",
            "SPR_GIFT_W3", "SPR_GIFT_W4", "SPR_GIFT_SHOOT1", "SPR_GIFT_SHOOT2",
            "SPR_GIFT_DIE1", "SPR_GIFT_DIE2", "SPR_GIFT_DIE3", "SPR_GIFT_DEAD"
        ])

    # Rocket, smoke and explosion
    for i in range(1, 9):
        sprite_names.append(f"SPR_ROCKET_{i}")

    for i in range(1, 5):
        sprite_names.append(f"SPR_SMOKE_{i}")

    for i in range(1, 4):
        sprite_names.append(f"SPR_BOOM_{i}")

    if spear:
        # Additional rocket/smoke/boom for SPEAR
        for i in range(1, 9):
            sprite_names.append(f"SPR_HROCKET_{i}")

        for i in range(1, 5):
            sprite_names.append(f"SPR_HSMOKE_{i}")

        for i in range(1, 4):
            sprite_names.append(f"SPR_HBOOM_{i}")

        for i in range(1, 5):
            sprite_names.append(f"SPR_SPARK{i}")

    if not spear:
        # Gretel
        sprite_names.extend([
            "SPR_GRETEL_W1", "SPR_GRETEL_W2", "SPR_GRETEL_W3", "SPR_GRETEL_W4",
            "SPR_GRETEL_SHOOT1", "SPR_GRETEL_SHOOT2", "SPR_GRETEL_SHOOT3", "SPR_GRETEL_DEAD",
            "SPR_GRETEL_DIE1", "SPR_GRETEL_DIE2", "SPR_GRETEL_DIE3"
        ])

        # Fat face
        sprite_names.extend([
            "SPR_FAT_W1", "SPR_FAT_W2", "SPR_FAT_W3", "SPR_FAT_W4",
            "SPR_FAT_SHOOT1", "SPR_FAT_SHOOT2", "SPR_FAT_SHOOT3", "SPR_FAT_SHOOT4",
            "SPR_FAT_DIE1", "SPR_FAT_DIE2", "SPR_FAT_DIE3", "SPR_FAT_DEAD"
        ])

        # BJ sprites
        if apogee_1_0:
            sprite_names.extend([
                "SPR_BJ_W1", "SPR_BJ_W2", "SPR_BJ_W3", "SPR_BJ_W4",
                "SPR_BJ_JUMP1", "SPR_BJ_JUMP2", "SPR_BJ_JUMP3", "SPR_BJ_JUMP4"
            ])
        elif apogee_1_1 and upload:
            # Skip to 406
            while len(sprite_names) < 406:
                sprite_names.append(None)
            sprite_names.extend([
                "SPR_BJ_W1", "SPR_BJ_W2", "SPR_BJ_W3", "SPR_BJ_W4",
                "SPR_BJ_JUMP1", "SPR_BJ_JUMP2", "SPR_BJ_JUMP3", "SPR_BJ_JUMP4"
            ])
        else:
            sprite_names.extend([
                "SPR_BJ_W1", "SPR_BJ_W2", "SPR_BJ_W3", "SPR_BJ_W4",
                "SPR_BJ_JUMP1", "SPR_BJ_JUMP2", "SPR_BJ_JUMP3", "SPR_BJ_JUMP4"
            ])
    else:
        # SPEAR sprites
        # Trans Grosse
        sprite_names.extend([
            "SPR_TRANS_W1", "SPR_TRANS_W2", "SPR_TRANS_W3", "SPR_TRANS_W4",
            "SPR_TRANS_SHOOT1", "SPR_TRANS_SHOOT2", "SPR_TRANS_SHOOT3", "SPR_TRANS_DEAD",
            "SPR_TRANS_DIE1", "SPR_TRANS_DIE2", "SPR_TRANS_DIE3"
        ])

        # Wilhelm
        sprite_names.extend([
            "SPR_WILL_W1", "SPR_WILL_W2", "SPR_WILL_W3", "SPR_WILL_W4",
            "SPR_WILL_SHOOT1", "SPR_WILL_SHOOT2", "SPR_WILL_SHOOT3", "SPR_WILL_SHOOT4",
            "SPR_WILL_DIE1", "SPR_WILL_DIE2", "SPR_WILL_DIE3", "SPR_WILL_DEAD"
        ])

        # UberMutant
        sprite_names.extend([
            "SPR_UBER_W1", "SPR_UBER_W2", "SPR_UBER_W3", "SPR_UBER_W4",
            "SPR_UBER_SHOOT1", "SPR_UBER_SHOOT2", "SPR_UBER_SHOOT3", "SPR_UBER_SHOOT4",
            "SPR_UBER_DIE1", "SPR_UBER_DIE2", "SPR_UBER_DIE3", "SPR_UBER_DIE4", "SPR_UBER_DEAD"
        ])

        # Death Knight
        sprite_names.extend([
            "SPR_DEATH_W1", "SPR_DEATH_W2", "SPR_DEATH_W3", "SPR_DEATH_W4",
            "SPR_DEATH_SHOOT1", "SPR_DEATH_SHOOT2", "SPR_DEATH_SHOOT3", "SPR_DEATH_SHOOT4",
            "SPR_DEATH_DIE1", "SPR_DEATH_DIE2", "SPR_DEATH_DIE3", "SPR_DEATH_DIE4",
            "SPR_DEATH_DIE5", "SPR_DEATH_DIE6", "SPR_DEATH_DEAD"
        ])

        # Ghost
        sprite_names.extend([
            "SPR_SPECTRE_W1", "SPR_SPECTRE_W2", "SPR_SPECTRE_W3", "SPR_SPECTRE_W4",
            "SPR_SPECTRE_F1", "SPR_SPECTRE_F2", "SPR_SPECTRE_F3", "SPR_SPECTRE_F4"
        ])

        # Angel of Death
        sprite_names.extend([
            "SPR_ANGEL_W1", "SPR_ANGEL_W2", "SPR_ANGEL_W3", "SPR_ANGEL_W4",
            "SPR_ANGEL_SHOOT1", "SPR_ANGEL_SHOOT2", "SPR_ANGEL_TIRED1", "SPR_ANGEL_TIRED2",
            "SPR_ANGEL_DIE1", "SPR_ANGEL_DIE2", "SPR_ANGEL_DIE3", "SPR_ANGEL_DIE4",
            "SPR_ANGEL_DIE5", "SPR_ANGEL_DIE6", "SPR_ANGEL_DIE7", "SPR_ANGEL_DEAD"
        ])

    # Player attack frames
    sprite_names.extend([
        "SPR_KNIFEREADY", "SPR_KNIFEATK1", "SPR_KNIFEATK2", "SPR_KNIFEATK3", "SPR_KNIFEATK4",
        "SPR_PISTOLREADY", "SPR_PISTOLATK1", "SPR_PISTOLATK2", "SPR_PISTOLATK3", "SPR_PISTOLATK4",
        "SPR_MACHINEGUNREADY", "SPR_MACHINEGUNATK1", "SPR_MACHINEGUNATK2", "MACHINEGUNATK3", "SPR_MACHINEGUNATK4",
        "SPR_CHAINREADY", "SPR_CHAINATK1", "SPR_CHAINATK2", "SPR_CHAINATK3", "SPR_CHAINATK4"
    ])

    # Handle the special case for SPR_BJ_W1
    if apogee_1_0:
        # Find and update SPR_BJ_W1 position
        for i, name in enumerate(sprite_names):
            if name == "SPR_BJ_W1":
                # Move it to position 360
                if i < 360:
                    # Remove from current position and insert at 360
                    sprite_names.pop(i)
                    while len(sprite_names) < 360:
                        sprite_names.append(None)
                    sprite_names.insert(360, "SPR_BJ_W1")
                break

    # Check if shapenum is within bounds
    if shapenum < 0 or shapenum >= len(sprite_names):
        return None

    return sprite_names[shapenum]