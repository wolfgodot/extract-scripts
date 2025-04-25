import os
import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from PIL import Image

from palette import WolfPal, SodPal

@dataclass
class wl_picture:
    width: int
    height: int

@dataclass
class VF_Struct:
    TotalChunks: int = 0
    HeadName: str = ""
    DictName: str = ""
    FileName: str = ""
    offset: List[int] = field(default_factory=list)
    pictable: List[wl_picture] = field(default_factory=list)
    hufftable: List[tuple[int, int]] = field(default_factory=list)

VgaFiles = VF_Struct()


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


def File_VGA_ReadChunk(n):
    global VgaFiles

    if n < 0 or n >= VgaFiles.TotalChunks:
        print(f"FileIO: VGA chunk index out of bounds [0, {VgaFiles.TotalChunks}]: {n}")
        return None

    # Find next valid chunk to determine compressed size
    next_chunk = n + 1
    while next_chunk < VgaFiles.TotalChunks and VgaFiles.offset[next_chunk] == -1:
        next_chunk += 1

    if next_chunk >= VgaFiles.TotalChunks:
        compressed_size = os.path.getsize(VgaFiles.FileName) - VgaFiles.offset[n]
    else:
        compressed_size = VgaFiles.offset[next_chunk] - VgaFiles.offset[n]

    # Read compressed data
    with open(VgaFiles.FileName, 'rb') as fp:
        fp.seek(VgaFiles.offset[n])
        src = fp.read(compressed_size)

    if not src:
        return None

    if n == 0: # picdef
        expanded = VgaFiles.TotalChunks * 4
    elif n == 135: # tile8
        expanded = 35 * 64 # BLOCK * NUMTILE8
    else:
        expanded = struct.unpack('<L', src[:4])[0]

    if expanded == 0:
        return None

    source = src[4:]  # Skip length bytes
    target = bytearray(expanded)

    File_HuffExpand(source, target, expanded, compressed_size, VgaFiles.hufftable)
    return target


def File_VGA_ReadPic(chunk):
    global VgaFiles

    picnum = chunk - 3
    if picnum < 0:
        return None

    wl_pic = VgaFiles.pictable[picnum]
    if wl_pic.width < 1 or wl_pic.width > 320 or wl_pic.height < 1 or wl_pic.height > 200:
        return None  # Not a picture

    buf = File_VGA_ReadChunk(chunk)

    if buf is None:
        return None

    buf1 = bytearray(len(buf))

    hw = wl_pic.width * wl_pic.height
    quarter = hw // 4

    # Reorganize the planar data
    for n in range(hw):
        buf1[n] = buf[(n % 4) * quarter + n // 4]

    # Convert to RGB data
    buf2 = bytearray(hw * 3)

    for n in range(hw):
        color_idx = buf1[n]
        buf2[n * 3 + 0] = WolfPal[color_idx][0]
        buf2[n * 3 + 1] = WolfPal[color_idx][1]
        buf2[n * 3 + 2] = WolfPal[color_idx][2]

    return wl_pic, buf2


def File_VGA_OpenVgaFiles(dict_path, header_path, vga_path):
    global VgaFiles

    # Check if files exist
    if not os.path.isfile(dict_path):
        print(f"FileIO: graphics dictionary missed: {dict_path}")
        return 0
    if not os.path.isfile(header_path):
        print(f"FileIO: graphics header missed: {header_path}")
        return 0
    if not os.path.isfile(vga_path):
        print(f"FileIO: VGA graphics file missed: {vga_path}")
        return 0

    # Initialize VgaFiles structure
    VgaFiles = VF_Struct()
    VgaFiles.HeadName = str(header_path)
    VgaFiles.DictName = str(dict_path)
    VgaFiles.FileName = str(vga_path)

    # Read dictionary file (huffman nodes) (1024 bytes)
    with open(dict_path, 'rb') as fp:
        for _ in range(256):
            bit0, bit1 = struct.unpack('<HH', fp.read(4))
            VgaFiles.hufftable.append((bit0, bit1))

    # Read header file to get chunks info
    header_size = os.path.getsize(header_path)
    VgaFiles.TotalChunks = header_size // 3

    with open(header_path, 'rb') as fp:
        for _ in range(VgaFiles.TotalChunks):
            temp = fp.read(3)
            offset = temp[0] + (temp[1] << 8) + (temp[2] << 16)
            if offset == 0xFFFFFF:
                offset = -1
            VgaFiles.offset.append(offset)

    # Read picture definitions from chunk 0
    picdef = File_VGA_ReadChunk(0)
    if picdef is None:
        print("Failed to read picture definitions chunk")
        return 0

    VgaFiles.pictable = []
    for i in range(VgaFiles.TotalChunks):
        width = struct.unpack('<H', picdef[i * 4:i * 4 + 2])[0]
        height = struct.unpack('<H', picdef[i * 4 + 2:i * 4 + 4])[0]
        VgaFiles.pictable.append(wl_picture(width, height))

    print("FileIO: VGA graphics files")
    print(f"-> dict: {dict_path}")
    print(f"-> head: {header_path}")
    print(f"-> main: {vga_path}")
    print(f"-> Total Chunks: {VgaFiles.TotalChunks}")
    return 1


def extract_vga(dict_path: Path, header_path: Path, vga_path: Path):
    global VgaFiles

    if not File_VGA_OpenVgaFiles(dict_path, header_path, vga_path):
        print("Failed to open VGA files")
        sys.exit(1)

    # Create output directories
    Path("vga/fonts").mkdir(parents=True, exist_ok=True)
    Path("vga/pics").mkdir(parents=True, exist_ok=True)
    Path("vga/endscreens").mkdir(parents=True, exist_ok=True)
    Path("vga/demos").mkdir(parents=True, exist_ok=True)
    Path("vga/endarts").mkdir(parents=True, exist_ok=True)

    # Extract everything (hardcoded indexes based on vgapics.h, tested only with WL6)
    for chunk in range(0, VgaFiles.TotalChunks):
        name = GetChunkName(chunk, wl6=True)

        if 1 <= chunk <= 2: # fonts
            font = File_VGA_ReadChunk(chunk)
            with open(f"vga/fonts/{chunk - 1}.bin", 'wb') as fp:
                fp.write(font)

        elif 3 <= chunk <= 134: # pictures
            wl_pic, buf = File_VGA_ReadPic(chunk)
            im = Image.frombytes('RGB', (wl_pic.width, wl_pic.height), bytes(buf), 'raw')
            im.save(f"vga/pics/{chunk - 3}_{name}.png")

        elif chunk == 135: # TILE8
            tile8 = File_VGA_ReadChunk(chunk)
            with open(f"vga/tile8.bin", 'wb') as fp:
                fp.write(tile8)

        elif 136 <= chunk <= 137: # endscreens
            endscreen = File_VGA_ReadChunk(chunk)
            with open(f"vga/endscreens/{name}.bin", 'wb') as fp:
                fp.write(endscreen)

        elif chunk == 138 or (143 <= chunk <= 148): # endarts
            endart = File_VGA_ReadChunk(chunk)
            with open(f"vga/endarts/{name}.txt", 'wb') as fp:
                fp.write(endart)

        elif 139 <= chunk <= 148:
            demo = File_VGA_ReadChunk(chunk)
            with open(f"vga/demos/{name}.bin", 'wb') as fp:
                fp.write(demo)


# TODO: cache lookup table!
def GetChunkName(value,
                 apogee_1_0=False,
                 apogee_1_1=False,
                 apogee_1_2=False,
                 upload=False,
                 japanese=False,
                 sod=False,
                 wl6=True):
    # Common chunks that appear in multiple variants
    common_chunks = []

    # Temporarily disable WL6 if another define is active
    if japanese or sod or apogee_1_0 or apogee_1_1 or apogee_1_2:
        wl6 = False

    # WL6 chunks
    wl6_chunks = []
    if wl6:
        wl6_chunks.extend([
            "H_BJPIC", "H_CASTLEPIC", "H_BLAZEPIC", "H_TOPWINDOWPIC",
            "H_LEFTWINDOWPIC", "H_RIGHTWINDOWPIC", "H_BOTTOMINFOPIC"
        ])
        wl6_chunks.extend([
            "C_OPTIONSPIC", "C_CURSOR1PIC", "C_CURSOR2PIC", "C_NOTSELECTEDPIC",
            "C_SELECTEDPIC", "C_FXTITLEPIC", "C_DIGITITLEPIC", "C_MUSICTITLEPIC",
            "C_MOUSELBACKPIC", "C_BABYMODEPIC", "C_EASYPIC", "C_NORMALPIC",
            "C_HARDPIC", "C_LOADSAVEDISKPIC", "C_DISKLOADING1PIC", "C_DISKLOADING2PIC",
            "C_CONTROLPIC", "C_CUSTOMIZEPIC", "C_LOADGAMEPIC", "C_SAVEGAMEPIC",
            "C_EPISODE1PIC", "C_EPISODE2PIC", "C_EPISODE3PIC", "C_EPISODE4PIC",
            "C_EPISODE5PIC", "C_EPISODE6PIC", "C_CODEPIC", "C_TIMECODEPIC",
            "C_LEVELPIC", "C_NAMEPIC", "C_SCOREPIC", "C_JOY1PIC", "C_JOY2PIC"
        ])
        wl6_chunks.extend([
            "L_GUYPIC", "L_COLONPIC", "L_NUM0PIC", "L_NUM1PIC", "L_NUM2PIC",
            "L_NUM3PIC", "L_NUM4PIC", "L_NUM5PIC", "L_NUM6PIC", "L_NUM7PIC",
            "L_NUM8PIC", "L_NUM9PIC", "L_PERCENTPIC", "L_APIC", "L_BPIC",
            "L_CPIC", "L_DPIC", "L_EPIC", "L_FPIC", "L_GPIC", "L_HPIC",
            "L_IPIC", "L_JPIC", "L_KPIC", "L_LPIC", "L_MPIC", "L_NPIC",
            "L_OPIC", "L_PPIC", "L_QPIC", "L_RPIC", "L_SPIC", "L_TPIC",
            "L_UPIC", "L_VPIC", "L_WPIC", "L_XPIC", "L_YPIC", "L_ZPIC",
            "L_EXPOINTPIC", "L_APOSTROPHEPIC", "L_GUY2PIC", "L_BJWINSPIC",
            "STATUSBARPIC", "TITLEPIC", "PG13PIC", "CREDITSPIC", "HIGHSCORESPIC"
        ])
        wl6_chunks.extend([
            "KNIFEPIC", "GUNPIC", "MACHINEGUNPIC", "GATLINGGUNPIC", "NOKEYPIC",
            "GOLDKEYPIC", "SILVERKEYPIC", "N_BLANKPIC", "N_0PIC", "N_1PIC",
            "N_2PIC", "N_3PIC", "N_4PIC", "N_5PIC", "N_6PIC", "N_7PIC",
            "N_8PIC", "N_9PIC", "FACE1APIC", "FACE1BPIC", "FACE1CPIC",
            "FACE2APIC", "FACE2BPIC", "FACE2CPIC", "FACE3APIC", "FACE3BPIC",
            "FACE3CPIC", "FACE4APIC", "FACE4BPIC", "FACE4CPIC", "FACE5APIC",
            "FACE5BPIC", "FACE5CPIC", "FACE6APIC", "FACE6BPIC", "FACE6CPIC",
            "FACE7APIC", "FACE7BPIC", "FACE7CPIC", "FACE8APIC", "GOTGATLINGPIC",
            "MUTANTBJPIC", "PAUSEDPIC", "GETPSYCHEDPIC"
        ])
        wl6_chunks.append("TILE8")
        wl6_chunks.extend([
            "ORDERSCREEN", "ERRORSCREEN", "T_HELPART", "T_DEMO0", "T_DEMO1",
            "T_DEMO2", "T_DEMO3", "T_ENDART1", "T_ENDART2", "T_ENDART3",
            "T_ENDART4", "T_ENDART5", "T_ENDART6"
        ])

    # JAPANESE chunks
    japanese_chunks = []
    if japanese:
        japanese_chunks.extend([
            "H_HELP1PIC", "H_HELP2PIC", "H_HELP3PIC", "H_HELP4PIC", "H_HELP5PIC",
            "H_HELP6PIC", "H_HELP7PIC", "H_HELP8PIC", "H_HELP9PIC", "H_HELP10PIC"
        ])
        japanese_chunks.extend([
            "C_OPTIONSPIC", "C_CURSOR1PIC", "C_CURSOR2PIC", "C_NOTSELECTEDPIC",
            "C_SELECTEDPIC", "C_MOUSELBACKPIC", "C_BABYMODEPIC", "C_EASYPIC",
            "C_NORMALPIC", "C_HARDPIC", "C_LOADSAVEDISKPIC", "C_DISKLOADING1PIC",
            "C_DISKLOADING2PIC", "C_CONTROLPIC", "C_LOADGAMEPIC", "C_SAVEGAMEPIC",
            "C_EPISODE1PIC", "C_EPISODE2PIC", "C_EPISODE3PIC", "C_EPISODE4PIC",
            "C_EPISODE5PIC", "C_EPISODE6PIC", "C_CODEPIC", "C_TIMECODEPIC",
            "C_LEVELPIC", "C_NAMEPIC", "C_SCOREPIC", "C_JOY1PIC", "C_JOY2PIC",
            "C_QUITMSGPIC", "C_JAPQUITPIC", "C_UNUSED_LOADING", "C_JAPNEWGAMEPIC",
            "C_JAPSAVEOVERPIC", "C_MSCORESPIC", "C_MENDGAMEPIC", "C_MRETDEMOPIC",
            "C_MRETGAMEPIC", "C_INTERMISSIONPIC", "C_LETSSEEPIC", "C_ENDRATIOSPIC",
            "C_ENDGAME1APIC", "C_ENDGAME1BPIC", "C_ENDGAME2APIC", "C_ENDGAME2BPIC",
            "C_ENDGAME3APIC", "C_ENDGAME3BPIC", "C_ENDGAME4APIC", "C_ENDGAME4BPIC",
            "C_ENDGAME5APIC", "C_ENDGAME5BPIC", "C_ENDGAME6APIC", "C_ENDGAME6BPIC"
        ])
        japanese_chunks.extend([
            "L_GUYPIC", "L_COLONPIC", "L_NUM0PIC", "L_NUM1PIC", "L_NUM2PIC",
            "L_NUM3PIC", "L_NUM4PIC", "L_NUM5PIC", "L_NUM6PIC", "L_NUM7PIC",
            "L_NUM8PIC", "L_NUM9PIC", "L_PERCENTPIC", "L_APIC", "L_BPIC",
            "L_CPIC", "L_DPIC", "L_EPIC", "L_FPIC", "L_GPIC", "L_HPIC",
            "L_IPIC", "L_JPIC", "L_KPIC", "L_LPIC", "L_MPIC", "L_NPIC",
            "L_OPIC", "L_PPIC", "L_QPIC", "L_RPIC", "L_SPIC", "L_TPIC",
            "L_UPIC", "L_VPIC", "L_WPIC", "L_XPIC", "L_YPIC", "L_ZPIC",
            "L_EXPOINTPIC", "L_APOSTROPHEPIC", "L_GUY2PIC", "L_BJWINSPIC",
            "STATUSBARPIC", "TITLEPIC"
        ])
        japanese_chunks.extend([
            "S_MOUSESENSPIC", "S_OPTIONSPIC", "S_SOUNDPIC", "S_SKILLPIC",
            "S_EPISODEPIC", "S_CHANGEPIC", "S_CUSTOMPIC", "S_CONTROLPIC",
            "CREDITSPIC", "HIGHSCORESPIC"
        ])
        japanese_chunks.extend([
            "KNIFEPIC", "GUNPIC", "MACHINEGUNPIC", "GATLINGGUNPIC", "NOKEYPIC",
            "GOLDKEYPIC", "SILVERKEYPIC", "N_BLANKPIC", "N_0PIC", "N_1PIC",
            "N_2PIC", "N_3PIC", "N_4PIC", "N_5PIC", "N_6PIC", "N_7PIC",
            "N_8PIC", "N_9PIC", "FACE1APIC", "FACE1BPIC", "FACE1CPIC",
            "FACE2APIC", "FACE2BPIC", "FACE2CPIC", "FACE3APIC", "FACE3BPIC",
            "FACE3CPIC", "FACE4APIC", "FACE4BPIC", "FACE4CPIC", "FACE5APIC",
            "FACE5BPIC", "FACE5CPIC", "FACE6APIC", "FACE6BPIC", "FACE6CPIC",
            "FACE7APIC", "FACE7BPIC", "FACE7CPIC", "FACE8APIC", "GOTGATLINGPIC",
            "MUTANTBJPIC", "PAUSEDPIC", "GETPSYCHEDPIC", "TILE8"
        ])
        japanese_chunks.extend([
            "ERRORSCREEN", "T_DEMO0", "T_DEMO1", "T_DEMO2", "T_DEMO3"
        ])

    # SOD chunks
    sod_chunks = []
    if sod:
        sod_chunks.extend([
            "C_BACKDROPPIC", "C_MOUSELBACKPIC", "C_CURSOR1PIC", "C_CURSOR2PIC",
            "C_NOTSELECTEDPIC", "C_SELECTEDPIC", "C_CUSTOMIZEPIC", "C_JOY1PIC",
            "C_JOY2PIC", "C_MOUSEPIC", "C_JOYSTICKPIC", "C_KEYBOARDPIC", "C_CONTROLPIC",
            "C_OPTIONSPIC", "C_FXTITLEPIC", "C_DIGITITLEPIC", "C_MUSICTITLEPIC",
            "C_HOWTOUGHPIC", "C_BABYMODEPIC", "C_EASYPIC", "C_NORMALPIC", "C_HARDPIC",
            "C_DISKLOADING1PIC", "C_DISKLOADING2PIC", "C_LOADGAMEPIC", "C_SAVEGAMEPIC",
            "HIGHSCORESPIC", "C_WONSPEARPIC"
        ])
        # Skip SPEARDEMO defines
        sod_chunks.extend([
            "BJCOLLAPSE1PIC", "BJCOLLAPSE2PIC", "BJCOLLAPSE3PIC", "BJCOLLAPSE4PIC", "ENDPICPIC"
        ])
        sod_chunks.extend([
            "L_GUYPIC", "L_COLONPIC", "L_NUM0PIC", "L_NUM1PIC", "L_NUM2PIC",
            "L_NUM3PIC", "L_NUM4PIC", "L_NUM5PIC", "L_NUM6PIC", "L_NUM7PIC",
            "L_NUM8PIC", "L_NUM9PIC", "L_PERCENTPIC", "L_APIC", "L_BPIC",
            "L_CPIC", "L_DPIC", "L_EPIC", "L_FPIC", "L_GPIC", "L_HPIC",
            "L_IPIC", "L_JPIC", "L_KPIC", "L_LPIC", "L_MPIC", "L_NPIC",
            "L_OPIC", "L_PPIC", "L_QPIC", "L_RPIC", "L_SPIC", "L_TPIC",
            "L_UPIC", "L_VPIC", "L_WPIC", "L_XPIC", "L_YPIC", "L_ZPIC",
            "L_EXPOINTPIC", "L_APOSTROPHEPIC", "L_GUY2PIC", "L_BJWINSPIC",
            "TITLE1PIC", "TITLE2PIC"
        ])
        # Skip SPEARDEMO defines
        sod_chunks.extend([
            "ENDSCREEN11PIC", "ENDSCREEN12PIC", "ENDSCREEN3PIC", "ENDSCREEN4PIC",
            "ENDSCREEN5PIC", "ENDSCREEN6PIC", "ENDSCREEN7PIC", "ENDSCREEN8PIC", "ENDSCREEN9PIC"
        ])
        sod_chunks.extend([
            "STATUSBARPIC", "PG13PIC", "CREDITSPIC"
        ])
        # Skip SPEARDEMO defines
        sod_chunks.extend([
            "IDGUYS1PIC", "IDGUYS2PIC", "COPYPROTTOPPIC", "COPYPROTBOXPIC",
            "BOSSPIC1PIC", "BOSSPIC2PIC", "BOSSPIC3PIC", "BOSSPIC4PIC"
        ])
        sod_chunks.extend([
            "KNIFEPIC", "GUNPIC", "MACHINEGUNPIC", "GATLINGGUNPIC", "NOKEYPIC",
            "GOLDKEYPIC", "SILVERKEYPIC", "N_BLANKPIC", "N_0PIC", "N_1PIC",
            "N_2PIC", "N_3PIC", "N_4PIC", "N_5PIC", "N_6PIC", "N_7PIC",
            "N_8PIC", "N_9PIC", "FACE1APIC", "FACE1BPIC", "FACE1CPIC",
            "FACE2APIC", "FACE2BPIC", "FACE2CPIC", "FACE3APIC", "FACE3BPIC",
            "FACE3CPIC", "FACE4APIC", "FACE4BPIC", "FACE4CPIC", "FACE5APIC",
            "FACE5BPIC", "FACE5CPIC", "FACE6APIC", "FACE6BPIC", "FACE6CPIC",
            "FACE7APIC", "FACE7BPIC", "FACE7CPIC", "FACE8APIC", "GOTGATLINGPIC",
            "GODMODEFACE1PIC", "GODMODEFACE2PIC", "GODMODEFACE3PIC", "BJWAITING1PIC",
            "BJWAITING2PIC", "BJOUCHPIC", "PAUSEDPIC", "GETPSYCHEDPIC", "TILE8",
            "ORDERSCREEN", "ERRORSCREEN", "TITLEPALETTE"
        ])
        # Skip SPEARDEMO defines
        sod_chunks.extend([
            "END1PALETTE", "END2PALETTE", "END3PALETTE", "END4PALETTE",
            "END5PALETTE", "END6PALETTE", "END7PALETTE", "END8PALETTE",
            "END9PALETTE", "IDGUYSPALETTE"
        ])
        sod_chunks.extend(["T_DEMO0"])
        # Skip SPEARDEMO defines
        sod_chunks.extend([
            "T_DEMO1", "T_DEMO2", "T_DEMO3", "T_ENDART1"
        ])

    # DEFAULT chunks (when none of the other defines are active)
    default_chunks = []
    if not (wl6 or japanese or sod):
        default_chunks.extend([
            "H_BJPIC", "H_CASTLEPIC", "H_KEYBOARDPIC", "H_JOYPIC", "H_HEALPIC",
            "H_TREASUREPIC", "H_GUNPIC", "H_KEYPIC", "H_BLAZEPIC", "H_WEAPON1234PIC",
            "H_WOLFLOGOPIC", "H_VISAPIC", "H_MCPIC", "H_IDLOGOPIC", "H_TOPWINDOWPIC",
            "H_LEFTWINDOWPIC", "H_RIGHTWINDOWPIC", "H_BOTTOMINFOPIC"
        ])

        # Special case for APOGEE versions
        if not (apogee_1_0 or apogee_1_1 or apogee_1_2):
            default_chunks.append("H_SPEARADPIC")

        default_chunks.extend([
            "C_OPTIONSPIC", "C_CURSOR1PIC", "C_CURSOR2PIC", "C_NOTSELECTEDPIC",
            "C_SELECTEDPIC", "C_FXTITLEPIC", "C_DIGITITLEPIC", "C_MUSICTITLEPIC",
            "C_MOUSELBACKPIC", "C_BABYMODEPIC", "C_EASYPIC", "C_NORMALPIC",
            "C_HARDPIC", "C_LOADSAVEDISKPIC", "C_DISKLOADING1PIC", "C_DISKLOADING2PIC",
            "C_CONTROLPIC", "C_CUSTOMIZEPIC", "C_LOADGAMEPIC", "C_SAVEGAMEPIC",
            "C_EPISODE1PIC", "C_EPISODE2PIC", "C_EPISODE3PIC", "C_EPISODE4PIC",
            "C_EPISODE5PIC", "C_EPISODE6PIC", "C_CODEPIC"
        ])

        # Special handling for APOGEE_1_0
        if apogee_1_0:
            default_chunks.append("C_TIMECODEPIC")  # Same as C_CODEPIC
        else:
            default_chunks.extend(["C_TIMECODEPIC", "C_LEVELPIC", "C_NAMEPIC", "C_SCOREPIC"])
            # Special case for apogee 1.1 and 1.2
            if not (apogee_1_1 or apogee_1_2):
                default_chunks.extend(["C_JOY1PIC", "C_JOY2PIC"])

        default_chunks.extend([
            "L_GUYPIC", "L_COLONPIC", "L_NUM0PIC", "L_NUM1PIC", "L_NUM2PIC",
            "L_NUM3PIC", "L_NUM4PIC", "L_NUM5PIC", "L_NUM6PIC", "L_NUM7PIC",
            "L_NUM8PIC", "L_NUM9PIC", "L_PERCENTPIC", "L_APIC", "L_BPIC",
            "L_CPIC", "L_DPIC", "L_EPIC", "L_FPIC", "L_GPIC", "L_HPIC",
            "L_IPIC", "L_JPIC", "L_KPIC", "L_LPIC", "L_MPIC", "L_NPIC",
            "L_OPIC", "L_PPIC", "L_QPIC", "L_RPIC", "L_SPIC", "L_TPIC",
            "L_UPIC", "L_VPIC", "L_WPIC", "L_XPIC", "L_YPIC", "L_ZPIC",
            "L_EXPOINTPIC"
        ])

        # Special handling for APOGEE_1_0
        if not apogee_1_0:
            default_chunks.append("L_APOSTROPHEPIC")

        default_chunks.extend([
            "L_GUY2PIC", "L_BJWINSPIC", "STATUSBARPIC", "TITLEPIC", "PG13PIC",
            "CREDITSPIC", "HIGHSCORESPIC", "KNIFEPIC", "GUNPIC", "MACHINEGUNPIC",
            "GATLINGGUNPIC", "NOKEYPIC", "GOLDKEYPIC", "SILVERKEYPIC", "N_BLANKPIC",
            "N_0PIC", "N_1PIC", "N_2PIC", "N_3PIC", "N_4PIC", "N_5PIC", "N_6PIC",
            "N_7PIC", "N_8PIC", "N_9PIC", "FACE1APIC", "FACE1BPIC", "FACE1CPIC",
            "FACE2APIC", "FACE2BPIC", "FACE2CPIC", "FACE3APIC", "FACE3BPIC",
            "FACE3CPIC", "FACE4APIC", "FACE4BPIC", "FACE4CPIC", "FACE5APIC",
            "FACE5BPIC", "FACE5CPIC", "FACE6APIC", "FACE6BPIC", "FACE6CPIC",
            "FACE7APIC", "FACE7BPIC", "FACE7CPIC", "FACE8APIC", "GOTGATLINGPIC",
            "MUTANTBJPIC", "PAUSEDPIC", "GETPSYCHEDPIC", "TILE8", "ORDERSCREEN",
            "ERRORSCREEN", "T_HELPART"
        ])

        # Special handling for APOGEE_1_0
        if apogee_1_0:
            default_chunks.append("T_ENDART1")

        default_chunks.extend(["T_DEMO0", "T_DEMO1", "T_DEMO2", "T_DEMO3"])

        # Special handling for APOGEE and UPLOAD
        if not apogee_1_0:
            default_chunks.append("T_ENDART1")
            if not upload:
                default_chunks.extend(["T_ENDART2", "T_ENDART3", "T_ENDART4", "T_ENDART5", "T_ENDART6"])

    # Use the appropriate chunk list based on the configuration
    chunks = []
    if wl6:
        chunks = wl6_chunks
    elif japanese:
        chunks = japanese_chunks
    elif sod:
        chunks = sod_chunks
    else:
        chunks = default_chunks

    # Adjust for base value (enums start at index 3)
    if 3 <= value < len(chunks) + 3:
        return chunks[value - 3]
    elif value == len(chunks) + 3:
        return "ENUMEND"
    else:
        return None