from enum import Enum

class VGAChunkType(Enum):
    STRUCTPIC = 0
    FONT = 1
    PICTURE = 2
    TILE8 = 3
    ENDSCREEN = 4
    ENDART = 5
    DEMO = 6
    PALETTE = 7

# reference: WDC
wl6_vga_type_range_map = {
    VGAChunkType.STRUCTPIC: [0],
    VGAChunkType.FONT: [1, 2],
    VGAChunkType.PICTURE: [(3, 134)],
    VGAChunkType.TILE8: [135],
    VGAChunkType.ENDSCREEN: [136, 137],
    VGAChunkType.ENDART: [138, (143, 148)],
    VGAChunkType.DEMO: [(139, 148)]
}

# reference: WDC
sod_vga_type_range_map = {
    VGAChunkType.STRUCTPIC: [0],
    VGAChunkType.FONT: [1, 2],
    VGAChunkType.PICTURE: [(3, 149)],
    VGAChunkType.TILE8: [150],
    VGAChunkType.ENDSCREEN: [151, 152],
    VGAChunkType.PALETTE: [(153, 163)],
    VGAChunkType.DEMO: [(164, 167)],
    VGAChunkType.ENDART: [168],
}


def get_chunk_type_and_index(chunk, range_map):
    for t, ra in range_map.items():
        off = 0
        for r in ra:
            if isinstance(r, int):
                if chunk == r:
                    return t, off
                else:
                    off += 1
            elif isinstance(r, tuple):
                if r[0] <= chunk <= r[1]:
                    return t, chunk - r[0] + off
                if chunk > r[1]:
                    off += r[1] - r[0]

    return None, 0


def range_to_array(chunk_type: VGAChunkType, range_map):
    arr = []

    ra = range_map.get(chunk_type)
    if ra is None:
        return arr

    for r in ra:
        if isinstance(r, int):
            arr.append(r)
        elif isinstance(r, tuple):
            arr.extend(range(r[0], r[1] + 1))

    return arr

# We could map name->name instead of idx->idx but meh
# Yes, id DID waste disk space! unbelievable!
sod_pic_palette_map = {
    76: 0,   # TITLE1PIC       -> TITLEPALETTE
    77: 0,   # TITLE2PIC       -> TITLEPALETTE
    78: 1,   # ENDSCREEN11PIC  -> END1PALETTE    seems identical to sodpal, but didnt check
    79: 2,   # ENDSCREEN12PIC  -> END2PALETTE    same as END2PALETTE
    80: 3,   # ENDSCREEN3PIC   -> END3PALETTE
    81: 4,   # ENDSCREEN4PIC   -> END4PALETTE
    82: 5,   # ENDSCREEN5PIC   -> END5PALETTE
    83: 6,   # ENDSCREEN6PIC   -> END6PALETTE
    84: 7,   # ENDSCREEN7PIC   -> END7PALETTE    same as END5PALETTE
    85: 8,   # ENDSCREEN8PIC   -> END8PALETTE    same as END5PALETTE
    86: 9,   # ENDSCREEN9PIC   -> END9PALETTE
    90: 10,  # IDGUYS1PIC      -> IDGUYSPALETTE
    91: 10,  # IDGUYS2PIC      -> IDGUYSPALETTE
}

sod_half_pics = [
    76, # + 77 = TITLEPIC
    90  # + 91 = IDGUYSPIC
]

# reference: `wl_def.h` / anonymous enum (SPR_*)
def gen_vswap_name_lookup_table(apogee_1_0=False,
                                apogee_1_1=False,
                                spear=False,
                                upload=False):

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

    return sprite_names


# reference: `gfxv_*.h` / enum graphicnums
def gen_vgagraph_name_lookup_table(apogee_1_0=False,
                                   apogee_1_1=False,
                                   apogee_1_2=False,
                                   upload=False,
                                   japanese=False,
                                   sod=False,
                                   wl6=True):

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
            "MUTANTBJPIC", "PAUSEDPIC", "GETPSYCHEDPIC",
            "TILE8",
            "ORDERSCREEN", "ERRORSCREEN",
            "T_HELPART",
            "T_DEMO0", "T_DEMO1", "T_DEMO2", "T_DEMO3",
            "T_ENDART1", "T_ENDART2", "T_ENDART3", "T_ENDART4", "T_ENDART5", "T_ENDART6"
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

    # Special chunk names (always the same)
    chunks[:0] = ["PICDEF", "FONT1", "FONT2"]

    return chunks
