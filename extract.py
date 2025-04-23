import argparse
import json
import numpy as np
import os
import struct
import sys
from dataclasses import dataclass, field
from typing import List
from PIL import Image
from pathlib import Path

MAX_OSPATH = 256
PROJECT_DOOR_COUNT = 8

def RGB(r, g, b):
    return {
        'r': r * 255 // 63,
        'g': g * 255 // 63,
        'b': b * 255 // 63,
        'a': 0
    }

# wolfpal.inc
WolfPal = [
    RGB(  0,  0,  0),RGB(  0,  0, 42),RGB(  0, 42,  0),RGB(  0, 42, 42),RGB( 42,  0,  0),
    RGB( 42,  0, 42),RGB( 42, 21,  0),RGB( 42, 42, 42),RGB( 21, 21, 21),RGB( 21, 21, 63),
    RGB( 21, 63, 21),RGB( 21, 63, 63),RGB( 63, 21, 21),RGB( 63, 21, 63),RGB( 63, 63, 21),
    RGB( 63, 63, 63),RGB( 59, 59, 59),RGB( 55, 55, 55),RGB( 52, 52, 52),RGB( 48, 48, 48),
    RGB( 45, 45, 45),RGB( 42, 42, 42),RGB( 38, 38, 38),RGB( 35, 35, 35),RGB( 31, 31, 31),
    RGB( 28, 28, 28),RGB( 25, 25, 25),RGB( 21, 21, 21),RGB( 18, 18, 18),RGB( 14, 14, 14),
    RGB( 11, 11, 11),RGB(  8,  8,  8),RGB( 63,  0,  0),RGB( 59,  0,  0),RGB( 56,  0,  0),
    RGB( 53,  0,  0),RGB( 50,  0,  0),RGB( 47,  0,  0),RGB( 44,  0,  0),RGB( 41,  0,  0),
    RGB( 38,  0,  0),RGB( 34,  0,  0),RGB( 31,  0,  0),RGB( 28,  0,  0),RGB( 25,  0,  0),
    RGB( 22,  0,  0),RGB( 19,  0,  0),RGB( 16,  0,  0),RGB( 63, 54, 54),RGB( 63, 46, 46),
    RGB( 63, 39, 39),RGB( 63, 31, 31),RGB( 63, 23, 23),RGB( 63, 16, 16),RGB( 63,  8,  8),
    RGB( 63,  0,  0),RGB( 63, 42, 23),RGB( 63, 38, 16),RGB( 63, 34,  8),RGB( 63, 30,  0),
    RGB( 57, 27,  0),RGB( 51, 24,  0),RGB( 45, 21,  0),RGB( 39, 19,  0),RGB( 63, 63, 54),
    RGB( 63, 63, 46),RGB( 63, 63, 39),RGB( 63, 63, 31),RGB( 63, 62, 23),RGB( 63, 61, 16),
    RGB( 63, 61,  8),RGB( 63, 61,  0),RGB( 57, 54,  0),RGB( 51, 49,  0),RGB( 45, 43,  0),
    RGB( 39, 39,  0),RGB( 33, 33,  0),RGB( 28, 27,  0),RGB( 22, 21,  0),RGB( 16, 16,  0),
    RGB( 52, 63, 23),RGB( 49, 63, 16),RGB( 45, 63,  8),RGB( 40, 63,  0),RGB( 36, 57,  0),
    RGB( 32, 51,  0),RGB( 29, 45,  0),RGB( 24, 39,  0),RGB( 54, 63, 54),RGB( 47, 63, 46),
    RGB( 39, 63, 39),RGB( 32, 63, 31),RGB( 24, 63, 23),RGB( 16, 63, 16),RGB(  8, 63,  8),
    RGB(  0, 63,  0),RGB(  0, 63,  0),RGB(  0, 59,  0),RGB(  0, 56,  0),RGB(  0, 53,  0),
    RGB(  1, 50,  0),RGB(  1, 47,  0),RGB(  1, 44,  0),RGB(  1, 41,  0),RGB(  1, 38,  0),
    RGB(  1, 34,  0),RGB(  1, 31,  0),RGB(  1, 28,  0),RGB(  1, 25,  0),RGB(  1, 22,  0),
    RGB(  1, 19,  0),RGB(  1, 16,  0),RGB( 54, 63, 63),RGB( 46, 63, 63),RGB( 39, 63, 63),
    RGB( 31, 63, 62),RGB( 23, 63, 63),RGB( 16, 63, 63),RGB(  8, 63, 63),RGB(  0, 63, 63),
    RGB(  0, 57, 57),RGB(  0, 51, 51),RGB(  0, 45, 45),RGB(  0, 39, 39),RGB(  0, 33, 33),
    RGB(  0, 28, 28),RGB(  0, 22, 22),RGB(  0, 16, 16),RGB( 23, 47, 63),RGB( 16, 44, 63),
    RGB(  8, 42, 63),RGB(  0, 39, 63),RGB(  0, 35, 57),RGB(  0, 31, 51),RGB(  0, 27, 45),
    RGB(  0, 23, 39),RGB( 54, 54, 63),RGB( 46, 47, 63),RGB( 39, 39, 63),RGB( 31, 32, 63),
    RGB( 23, 24, 63),RGB( 16, 16, 63),RGB(  8,  9, 63),RGB(  0,  1, 63),RGB(  0,  0, 63),
    RGB(  0,  0, 59),RGB(  0,  0, 56),RGB(  0,  0, 53),RGB(  0,  0, 50),RGB(  0,  0, 47),
    RGB(  0,  0, 44),RGB(  0,  0, 41),RGB(  0,  0, 38),RGB(  0,  0, 34),RGB(  0,  0, 31),
    RGB(  0,  0, 28),RGB(  0,  0, 25),RGB(  0,  0, 22),RGB(  0,  0, 19),RGB(  0,  0, 16),
    RGB( 10, 10, 10),RGB( 63, 56, 13),RGB( 63, 53,  9),RGB( 63, 51,  6),RGB( 63, 48,  2),
    RGB( 63, 45,  0),RGB( 45,  8, 63),RGB( 42,  0, 63),RGB( 38,  0, 57),RGB( 32,  0, 51),
    RGB( 29,  0, 45),RGB( 24,  0, 39),RGB( 20,  0, 33),RGB( 17,  0, 28),RGB( 13,  0, 22),
    RGB( 10,  0, 16),RGB( 63, 54, 63),RGB( 63, 46, 63),RGB( 63, 39, 63),RGB( 63, 31, 63),
    RGB( 63, 23, 63),RGB( 63, 16, 63),RGB( 63,  8, 63),RGB( 63,  0, 63),RGB( 56,  0, 57),
    RGB( 50,  0, 51),RGB( 45,  0, 45),RGB( 39,  0, 39),RGB( 33,  0, 33),RGB( 27,  0, 28),
    RGB( 22,  0, 22),RGB( 16,  0, 16),RGB( 63, 58, 55),RGB( 63, 56, 52),RGB( 63, 54, 49),
    RGB( 63, 53, 47),RGB( 63, 51, 44),RGB( 63, 49, 41),RGB( 63, 47, 39),RGB( 63, 46, 36),
    RGB( 63, 44, 32),RGB( 63, 41, 28),RGB( 63, 39, 24),RGB( 60, 37, 23),RGB( 58, 35, 22),
    RGB( 55, 34, 21),RGB( 52, 32, 20),RGB( 50, 31, 19),RGB( 47, 30, 18),RGB( 45, 28, 17),
    RGB( 42, 26, 16),RGB( 40, 25, 15),RGB( 39, 24, 14),RGB( 36, 23, 13),RGB( 34, 22, 12),
    RGB( 32, 20, 11),RGB( 29, 19, 10),RGB( 27, 18,  9),RGB( 23, 16,  8),RGB( 21, 15,  7),
    RGB( 18, 14,  6),RGB( 16, 12,  6),RGB( 14, 11,  5),RGB( 10,  8,  3),RGB( 24,  0, 25),
    RGB(  0, 25, 25),RGB(  0, 24, 24),RGB(  0,  0,  7),RGB(  0,  0, 11),RGB( 12,  9,  4),
    RGB( 18,  0, 18),RGB( 20,  0, 20),RGB(  0,  0, 13),RGB(  7,  7,  7),RGB( 19, 19, 19),
    RGB( 23, 23, 23),RGB( 16, 16, 16),RGB( 12, 12, 12),RGB( 13, 13, 13),RGB( 54, 61, 61),
    RGB( 46, 58, 58),RGB( 39, 55, 55),RGB( 29, 50, 50),RGB( 18, 48, 48),RGB(  8, 45, 45),
    RGB(  8, 44, 44),RGB(  0, 41, 41),RGB(  0, 38, 38),RGB(  0, 35, 35),RGB(  0, 33, 33),
    RGB(  0, 31, 31),RGB(  0, 30, 30),RGB(  0, 29, 29),RGB(  0, 28, 28),RGB(  0, 27, 27),
    RGB( 38,  0, 34)
]

# sodpal.inc
SodPal = [
    RGB(  0,  0,  0),RGB(  0,  0, 42),RGB(  0, 42,  0),RGB(  0, 42, 42),RGB( 42,  0,  0),
    RGB( 42,  0, 42),RGB( 42, 21,  0),RGB( 42, 42, 42),RGB( 21, 21, 21),RGB( 21, 21, 63),
    RGB( 21, 63, 21),RGB( 21, 63, 63),RGB( 63, 21, 21),RGB( 63, 21, 63),RGB( 63, 63, 21),
    RGB( 63, 63, 63),RGB( 59, 59, 59),RGB( 55, 55, 55),RGB( 52, 52, 52),RGB( 48, 48, 48),
    RGB( 45, 45, 45),RGB( 42, 42, 42),RGB( 38, 38, 38),RGB( 35, 35, 35),RGB( 31, 31, 31),
    RGB( 28, 28, 28),RGB( 25, 25, 25),RGB( 21, 21, 21),RGB( 18, 18, 18),RGB( 14, 14, 14),
    RGB( 11, 11, 11),RGB(  8,  8,  8),RGB( 63,  0,  0),RGB( 59,  0,  0),RGB( 56,  0,  0),
    RGB( 53,  0,  0),RGB( 50,  0,  0),RGB( 47,  0,  0),RGB( 44,  0,  0),RGB( 41,  0,  0),
    RGB( 38,  0,  0),RGB( 34,  0,  0),RGB( 31,  0,  0),RGB( 28,  0,  0),RGB( 25,  0,  0),
    RGB( 22,  0,  0),RGB( 19,  0,  0),RGB( 16,  0,  0),RGB( 63, 54, 54),RGB( 63, 46, 46),
    RGB( 63, 39, 39),RGB( 63, 31, 31),RGB( 63, 23, 23),RGB( 63, 16, 16),RGB( 63,  8,  8),
    RGB( 63,  0,  0),RGB( 63, 42, 23),RGB( 63, 38, 16),RGB( 63, 34,  8),RGB( 63, 30,  0),
    RGB( 57, 27,  0),RGB( 51, 24,  0),RGB( 45, 21,  0),RGB( 39, 19,  0),RGB( 63, 63, 54),
    RGB( 63, 63, 46),RGB( 63, 63, 39),RGB( 63, 63, 31),RGB( 63, 62, 23),RGB( 63, 61, 16),
    RGB( 63, 61,  8),RGB( 63, 61,  0),RGB( 57, 54,  0),RGB( 51, 49,  0),RGB( 45, 43,  0),
    RGB( 39, 39,  0),RGB( 33, 33,  0),RGB( 28, 27,  0),RGB( 22, 21,  0),RGB( 16, 16,  0),
    RGB( 52, 63, 23),RGB( 49, 63, 16),RGB( 45, 63,  8),RGB( 40, 63,  0),RGB( 36, 57,  0),
    RGB( 32, 51,  0),RGB( 29, 45,  0),RGB( 24, 39,  0),RGB( 54, 63, 54),RGB( 47, 63, 46),
    RGB( 39, 63, 39),RGB( 32, 63, 31),RGB( 24, 63, 23),RGB( 16, 63, 16),RGB(  8, 63,  8),
    RGB(  0, 63,  0),RGB(  0, 63,  0),RGB(  0, 59,  0),RGB(  0, 56,  0),RGB(  0, 53,  0),
    RGB(  1, 50,  0),RGB(  1, 47,  0),RGB(  1, 44,  0),RGB(  1, 41,  0),RGB(  1, 38,  0),
    RGB(  1, 34,  0),RGB(  1, 31,  0),RGB(  1, 28,  0),RGB(  1, 25,  0),RGB(  1, 22,  0),
    RGB(  1, 19,  0),RGB(  1, 16,  0),RGB( 54, 63, 63),RGB( 46, 63, 63),RGB( 39, 63, 63),
    RGB( 31, 63, 62),RGB( 23, 63, 63),RGB( 16, 63, 63),RGB(  8, 63, 63),RGB(  0, 63, 63),
    RGB(  0, 57, 57),RGB(  0, 51, 51),RGB(  0, 45, 45),RGB(  0, 39, 39),RGB(  0, 33, 33),
    RGB(  0, 28, 28),RGB(  0, 22, 22),RGB(  0, 16, 16),RGB( 23, 47, 63),RGB( 16, 44, 63),
    RGB(  8, 42, 63),RGB(  0, 39, 63),RGB(  0, 35, 57),RGB(  0, 31, 51),RGB(  0, 27, 45),
    RGB(  0, 23, 39),RGB( 54, 54, 63),RGB( 46, 47, 63),RGB( 39, 39, 63),RGB( 31, 32, 63),
    RGB( 23, 24, 63),RGB( 16, 16, 63),RGB(  8,  9, 63),RGB(  0,  1, 63),RGB(  0,  0, 63),
    RGB(  0,  0, 59),RGB(  0,  0, 56),RGB(  0,  0, 53),RGB(  0,  0, 50),RGB(  0,  0, 47),
    RGB(  0,  0, 44),RGB(  0,  0, 41),RGB(  0,  0, 38),RGB(  0,  0, 34),RGB(  0,  0, 31),
    RGB(  0,  0, 28),RGB(  0,  0, 25),RGB(  0,  0, 22),RGB(  0,  0, 19),RGB(  0,  0, 16),
    RGB( 10, 10, 10),RGB( 63, 56, 13),RGB( 63, 53,  9),RGB( 63, 51,  6),RGB( 63, 48,  2),
    RGB( 63, 45,  0),RGB(  0, 14,  0),RGB(  0, 10,  0),RGB( 38,  0, 57),RGB( 32,  0, 51),
    RGB( 29,  0, 45),RGB( 24,  0, 39),RGB( 20,  0, 33),RGB( 17,  0, 28),RGB( 13,  0, 22),
    RGB( 10,  0, 16),RGB( 63, 54, 63),RGB( 63, 46, 63),RGB( 63, 39, 63),RGB( 63, 31, 63),
    RGB( 63, 23, 63),RGB( 63, 16, 63),RGB( 63,  8, 63),RGB( 63,  0, 63),RGB( 56,  0, 57),
    RGB( 50,  0, 51),RGB( 45,  0, 45),RGB( 39,  0, 39),RGB( 33,  0, 33),RGB( 27,  0, 28),
    RGB( 22,  0, 22),RGB( 16,  0, 16),RGB( 63, 58, 55),RGB( 63, 56, 52),RGB( 63, 54, 49),
    RGB( 63, 53, 47),RGB( 63, 51, 44),RGB( 63, 49, 41),RGB( 63, 47, 39),RGB( 63, 46, 36),
    RGB( 63, 44, 32),RGB( 63, 41, 28),RGB( 63, 39, 24),RGB( 60, 37, 23),RGB( 58, 35, 22),
    RGB( 55, 34, 21),RGB( 52, 32, 20),RGB( 50, 31, 19),RGB( 47, 30, 18),RGB( 45, 28, 17),
    RGB( 42, 26, 16),RGB( 40, 25, 15),RGB( 39, 24, 14),RGB( 36, 23, 13),RGB( 34, 22, 12),
    RGB( 32, 20, 11),RGB( 29, 19, 10),RGB( 27, 18,  9),RGB( 23, 16,  8),RGB( 21, 15,  7),
    RGB( 18, 14,  6),RGB( 16, 12,  6),RGB( 14, 11,  5),RGB( 10,  8,  3),RGB( 24,  0, 25),
    RGB(  0, 25, 25),RGB(  0, 24, 24),RGB(  0,  0,  7),RGB(  0,  0, 11),RGB( 12,  9,  4),
    RGB( 18,  0, 18),RGB( 20,  0, 20),RGB(  0,  0, 13),RGB(  7,  7,  7),RGB( 19, 19, 19),
    RGB( 23, 23, 23),RGB( 16, 16, 16),RGB( 12, 12, 12),RGB( 13, 13, 13),RGB( 54, 61, 61),
    RGB( 46, 58, 58),RGB( 39, 55, 55),RGB( 29, 50, 50),RGB( 18, 48, 48),RGB(  8, 45, 45),
    RGB(  8, 44, 44),RGB(  0, 41, 41),RGB(  0, 38, 38),RGB(  0, 35, 35),RGB(  0, 33, 33),
    RGB(  0, 31, 31),RGB(  0, 30, 30),RGB(  0, 29, 29),RGB(  0, 28, 28),RGB(  0, 27, 27),
    RGB( 38,  0, 34)
]

# VSWAP

class Chunk:
    def __init__(self, offset=0, length=0):
        self.offset = offset
        self.length = length

class PF_Struct:
    def __init__(self):
        self.ChunksInFile = 0
        self.SpriteStart = 0
        self.SoundStart = 0
        self.Pages = []
        self.FileName = ""

@dataclass
class Shape:
    leftpix: int
    rightpix: int
    dataofs: List[int]  # Array of 64 unsigned short offsets

PageFile = PF_Struct()

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
                                r += pal[i * 3 + 0]
                                g += pal[i * 3 + 1]
                                b += pal[i * 3 + 2]
                                c += 1
                c = max(c, 1)
                dst.extend([r // c, g // c, b // c, 0])
            else:
                dst.extend([pal[srcp * 3 + 0], pal[srcp * 3 + 1], pal[srcp * 3 + 2]])
                if transparent:
                    dst.append(255)

def File_PML_OpenPageFile(filename: Path):
    global PageFile
    try:
        with open(filename, 'rb') as fp:
            PageFile.FileName = filename

            header = fp.read(6)
            PageFile.ChunksInFile, PageFile.SpriteStart, PageFile.SoundStart = struct.unpack('<HHH', header)

            print(f"-> {filename}")
            print(f"-> Total Chunks : {PageFile.ChunksInFile}")
            print(f"-> Sprites start: {PageFile.SpriteStart}")
            print(f"-> Sounds start : {PageFile.SoundStart}")

            PageFile.Pages = [Chunk() for _ in range(PageFile.ChunksInFile)]

            for i in range(PageFile.ChunksInFile):
                PageFile.Pages[i].offset = struct.unpack('<L', fp.read(4))[0]

            for i in range(PageFile.ChunksInFile):
                tmp = struct.unpack('<H', fp.read(2))[0]
                PageFile.Pages[i].length = tmp

        return 1
    except FileNotFoundError:
        print(f"FileIO: Unable to open page file: {filename}")
        return 0

def File_PML_ReadPage(n, data):
    if not PageFile.FileName:
        print("FileIO: Page file not opened")
        return 0
    if n >= PageFile.ChunksInFile:
        print(f"FileIO: Wrong chunk num {n}")
        return 0
    if not PageFile.Pages[n].length or not PageFile.Pages[n].offset:
        print(f"FileIO: Page {n} wrong header data")
        return 0
    if data is None:
        print("FileIO: Bad Pointer!")
        return 0

    with open(PageFile.FileName, 'rb') as fp:
        fp.seek(PageFile.Pages[n].offset)
        chunk_data = fp.read(PageFile.Pages[n].length)
        data[:] = chunk_data
        if len(chunk_data) != PageFile.Pages[n].length:
            print(f"FileIO: Page {n} read error")
            return 0
    return 1

def File_PML_LoadWall(n, block, palette=WolfPal):
    if n >= PageFile.SpriteStart:
        print(f"FileIO: Wall index ({n}) out of bounds [0-{PageFile.SpriteStart}]")
        return 0

    data = bytearray(PageFile.Pages[n].length)
    if not File_PML_ReadPage(n, data):
        return 0

    for x in range(64):
        for y in range(64):
            val = data[(x << 6) + y]
            idx = ((y << 6) + x) * 3
            block[idx + 0] = palette[val]['r']
            block[idx + 1] = palette[val]['g']
            block[idx + 2] = palette[val]['b']
    return 1

def File_PML_LoadDoor(n, block, palette=WolfPal):
    return File_PML_LoadWall(n + (PageFile.SpriteStart - PROJECT_DOOR_COUNT), block)


def File_PML_LoadSprite(n, block, palette=WolfPal):
    if n < PageFile.SpriteStart or n >= PageFile.SoundStart:
        print(f"FileIO: Sprite index ({n}) out of bounds [{PageFile.SpriteStart}-{PageFile.SoundStart}]")
        return 0

    sprite = bytearray(PageFile.Pages[n].length)
    if not File_PML_ReadPage(n, sprite):
        return 0
    
    # Initialize all as transparent
    tmp = bytearray([255] * (64 * 64))
    
    shape = Shape(
        leftpix=int.from_bytes(sprite[0:2], byteorder='little', signed=False),
        rightpix=int.from_bytes(sprite[2:4], byteorder='little', signed=False),
        dataofs=[int.from_bytes(sprite[4+i*2:6+i*2], byteorder='little', signed=False) for i in range(64)]
    )
    
    # Process each column from leftpix to rightpix
    for x in range(shape.leftpix, shape.rightpix + 1):
        # Get command pointer offset
        cmd_offset = shape.dataofs[x - shape.leftpix]
        
        # Process line commands
        pos = cmd_offset
        while True:
            # Read command values (3 shorts)
            cmd0 = int.from_bytes(sprite[pos:pos+2], byteorder='little', signed=True)
            if cmd0 == 0:  # End of commands for this column
                break
                
            cmd1 = int.from_bytes(sprite[pos+2:pos+4], byteorder='little', signed=True)
            cmd2 = int.from_bytes(sprite[pos+4:pos+6], byteorder='little', signed=True)
            pos += 6  # Move to next command
            
            i = cmd2 // 2 + cmd1
            for y in range(cmd2 // 2, cmd0 // 2):
                tmp[y * 64 + x] = sprite[i]
                i += 1
    
    # Clear block before expanding palette
    block.clear()
    
    # Convert palette to flat RGB list
    flat_pal = []
    for color in WolfPal:
        flat_pal.append(color['r'])
        flat_pal.append(color['g'])
        flat_pal.append(color['b'])
    
    # Now expand the palette
    Img_ExpandPalette(block, tmp, 64, 64, flat_pal, True)
    
    return 1


def extract_vswap(vswap_path):
    spear = True if vswap_path.suffix.lower() == ".sod" else False
    palette = SodPal if spear else WolfPal

    Path("vswap/walls").mkdir(parents=True, exist_ok=True)
    Path("vswap/sprites").mkdir(parents=True, exist_ok=True)
    Path("vswap/digisounds").mkdir(parents=True, exist_ok=True)

    if not os.path.isfile(vswap_path):
        print(f"Error: Input file not found: {vswap_path}")
        sys.exit(1)

    if not File_PML_OpenPageFile(vswap_path):
        print("Failed to open page file.")
        sys.exit(1)

    for i in range(PageFile.SpriteStart):
        block = bytearray(64 * 64 * 3)
        if File_PML_LoadWall(i, block, palette):
            im = Image.frombytes('RGB', (64, 64), block, 'raw')
            im.save(f"vswap/walls/{i}.png")
        else:
            print(f"Failed to load wall {i}.")

    for i in range(PageFile.SpriteStart, PageFile.SoundStart):
        block = bytearray(64 * 64 * 4)
        if File_PML_LoadSprite(i, block, palette):
            im = Image.frombytes('RGBA', (64, 64), block, 'raw')
            shapenum = i - PageFile.SpriteStart
            im.save(f"vswap/sprites/{shapenum}_{GetSpriteName(shapenum, spear=spear)}.png")
        else:
            print(f"Failed to load sprite {i}.")

    digimap_n = PageFile.ChunksInFile - 1
    digimap = bytearray(PageFile.Pages[digimap_n].length)
    if not File_PML_ReadPage(digimap_n, digimap):
        print("Failed to load digimap page.")
        sys.exit(1)

    with open("vswap/digisounds/digimap.bin", "wb") as digimap_file:
        digimap_file.write(digimap)

    for i in range(PageFile.SoundStart, digimap_n):
        block = bytearray(PageFile.Pages[i].length)
        soundnum = i - PageFile.SoundStart
        if not File_PML_ReadPage(i, block):
            print(f"Failed to load sound {soundnum}.")
        with open(f"vswap/digisounds/{soundnum}.bin", "wb") as sound_file:
            sound_file.write(block)

# VGAGRAPH

@dataclass
class VF_Struct:
    TotalChunks: int = 0
    HeadName: str = ""
    DictName: str = ""
    FileName: str = ""
    offset: List[int] = field(default_factory=list)
    pictable: List[dict] = field(default_factory=list)  # List of dicts with width/height
    grhuffman32: List[dict] = field(default_factory=list)  # List of dicts with bit0/bit1

VgaFiles = VF_Struct()

def File_HuffExpand(source, dest, length, c_len, hufftable):
    headptr = hufftable[254]  # Head node is always node 254
    end = length

    node = headptr
    if not source:
        return

    ch = source[0]
    source = source[1:]
    c_len -= 1
    cl = 1

    dest_pos = 0

    while dest_pos < end:
        if ch & cl:
            next_node = node['bit1']
        else:
            next_node = node['bit0']

        if isinstance(next_node, int) and next_node < 256:
            # Leaf node - output the value
            if dest_pos < len(dest):
                dest[dest_pos] = next_node
            dest_pos += 1
            node = headptr
        else:
            # Internal node - continue traversing
            node = hufftable[next_node]

        cl <<= 1
        if cl == 0:
            # Need next byte
            if c_len <= 0:
                break
            ch = source[0]
            source = source[1:]
            c_len -= 1
            cl = 1


def File_OptimizeNodes(hufftmp, hufftable32):
    for i in range(255):
        if hufftmp[i]['bit0'] >= 256:
            hufftable32[i]['bit0'] = hufftmp[i]['bit0'] - 256  # Will be treated as index
        else:
            hufftable32[i]['bit0'] = hufftmp[i]['bit0']

        if hufftmp[i]['bit1'] >= 256:
            hufftable32[i]['bit1'] = hufftmp[i]['bit1'] - 256  # Will be treated as index
        else:
            hufftable32[i]['bit1'] = hufftmp[i]['bit1']

def File_VGA_GetChunkSize(n):
    global VgaFiles
    
    if n < 0 or n >= VgaFiles.TotalChunks:
        print(f"FileIO: VGA chunk index out of bounds [0, {VgaFiles.TotalChunks}]: {n}")
        return 0

    with open(VgaFiles.FileName, 'rb') as fp:
        fp.seek(VgaFiles.offset[n])
        size_bytes = fp.read(4)

        if len(size_bytes) != 4:
            return 0

        size = struct.unpack('<L', size_bytes)[0]
        return size


def File_VGA_ReadChunk(n, target):
    global VgaFiles

    if n < 0 or n >= VgaFiles.TotalChunks:
        print(f"FileIO: VGA chunk index out of bounds [0, {VgaFiles.TotalChunks}]: {n}")
        return 0

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
        return 0

    # The first 4 bytes are the expanded length (except for chunk 0)
    if n == 0:
        expanded = VgaFiles.TotalChunks * 4
    else:
        expanded = struct.unpack('<L', src[:4])[0]

    if expanded == 0:
        return 0

    source = src[4:]  # Skip length bytes

    # Huffman expand the data
    File_HuffExpand(source, target, expanded, compressed_size, VgaFiles.grhuffman32)
    return 1


def File_VGA_ReadPic(chunk, pic):
    picnum = chunk - 3  # STARTPICS (0..2 are special chunks)
    if picnum < 0:
        return 0

    size = File_VGA_GetChunkSize(chunk)
    if size <= 0:
        return 0

    width = VgaFiles.pictable[picnum]['width']
    height = VgaFiles.pictable[picnum]['height']
    if width < 1 or width > 320 or height < 1 or height > 200:
        return 0  # Not a picture

    buf = bytearray(size)
    if not File_VGA_ReadChunk(chunk, buf):
        return 0

    buf1 = bytearray(size)

    width = VgaFiles.pictable[picnum]['width']
    height = VgaFiles.pictable[picnum]['height']
    hw = width * height
    quarter = hw // 4

    # Reorganize the planar data
    for n in range(hw):
        buf1[n] = buf[(n % 4) * quarter + n // 4]

    # Convert to RGB data
    pic['width'] = width
    pic['height'] = height
    pic['data'] = bytearray(hw * 3)

    for n in range(hw):
        color_idx = buf1[n]
        pic['data'][n * 3 + 0] = WolfPal[color_idx]['r']
        pic['data'][n * 3 + 1] = WolfPal[color_idx]['g']
        pic['data'][n * 3 + 2] = WolfPal[color_idx]['b']

    return 1


def File_VGA_OpenVgaFiles(dict_path: Path, header_path: Path, vga_path: Path):
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
    VgaFiles.grhuffman32 = [{'bit0': 0, 'bit1': 0} for _ in range(256)]

    # Read dictionary file (huffman nodes)
    with open(dict_path, 'rb') as fp:
        hufftmp = []
        for _ in range(256):
            bit0, bit1 = struct.unpack('<HH', fp.read(4))
            hufftmp.append({'bit0': bit0, 'bit1': bit1})

    # Optimize huffman nodes
    File_OptimizeNodes(hufftmp, VgaFiles.grhuffman32)

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
    picdef = bytearray(VgaFiles.TotalChunks * 4)
    if not File_VGA_ReadChunk(0, picdef):
        print("Failed to read picture definitions chunk")
        return 0

    # Convert to picture table
    VgaFiles.pictable = []
    for i in range(VgaFiles.TotalChunks):
        # TODO: this is borked...
        # 64764x65021
        # 65020x65021
        # 64764x64764
        width = struct.unpack('<H', picdef[i * 4:i * 4 + 2])[0]
        height = struct.unpack('<H', picdef[i * 4 + 2:i * 4 + 4])[0]
        print(f"{width}x{height}")
        VgaFiles.pictable.append({'width': width, 'height': height})

    print("FileIO: VGA graphics files:")
    print(f"-> dict: {dict_path}")
    print(f"-> head: {header_path}")
    print(f"-> main: {vga_path}")
    print(f"-> Total Chunks: {VgaFiles.TotalChunks}")
    return 1


def extract_vga(dict_path: Path, header_path: Path, vga_path: Path):
    if not File_VGA_OpenVgaFiles(dict_path, header_path, vga_path):
        print("Failed to open VGA files")
        sys.exit(1)

    # Create output directories
    Path("vga/pics").mkdir(parents=True, exist_ok=True)
    Path("vga/chunks").mkdir(parents=True, exist_ok=True)

    # Extract all pictures
    for chunk in range(3, VgaFiles.TotalChunks):  # First 3 chunks are special
        pic = {}
        if File_VGA_ReadPic(chunk, pic): # TODO: always returns 0
            if pic.get('width', 0) > 0 and pic.get('height', 0) > 0:
                im = Image.frombytes('RGB', (pic['width'], pic['height']), bytes(pic['data']), 'raw')
                im.save(f"vga/pics/{chunk - 3}.png")

    # Extract raw chunks
    # TODO: infinite loop after 134th chunk
    for chunk in range(VgaFiles.TotalChunks):
        size = File_VGA_GetChunkSize(chunk)
        if size > 0:
            data = bytearray(size)
            if File_VGA_ReadChunk(chunk, data):
                with open(f"vga/chunks/{chunk}.bin", "wb") as f:
                    f.write(data)


# GAMEMAPS/MAPHEAD

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


def tile_to_color(tile):
    if tile == 0:
        return (255, 255, 255)
    elif 1 <= tile <= 63:
        return (64, 64, 64)
    elif 90 <= tile <= 101:
        return (0, 128, 255)
    elif 106 <= tile <= 111:
        return (255, 0, 0)
    else:
        return (128, 128, 128)


def extract_maps(maphead_path: Path, gamemaps_path: Path):
    level = 1

    print("FileIO: Map Files")

    # Create output directories
    Path("maps/thumbs").mkdir(parents=True, exist_ok=True)
    Path("maps/json").mkdir(parents=True, exist_ok=True)

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

            Image.fromarray(combined, "RGB").save(f"maps/thumbs/{level}_{name}.png")

            grid = [layer1[y * 64:(y + 1) * 64] for y in range(64)]

            with open(f"maps/json/{level}_{name}.json", "w") as f:
                json.dump(grid, f)

    return 1

def main():
    parser = argparse.ArgumentParser(description="Extract Wolfenstein3D assets")
    parser.add_argument('-i', '--input', type=str, required=True, help='Directory with game files')
    args = parser.parse_args()
    input_path = Path(args.input)

    extract_maps(input_path / "MAPHEAD.WL6", input_path / "GAMEMAPS.WL6")
    extract_vswap(input_path / "VSWAP.WL6")
    # TODO: borked
    extract_vga(input_path / "VGADICT.WL6", input_path / "VGAHEAD.WL6", input_path / "VGAGRAPH.WL6")

            
if __name__ == "__main__":
    main()
