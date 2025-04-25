from pathlib import Path

import numpy as np
from PIL import Image

from palette import WolfPal, SodPal

def extract_signon(sod: bool):
    print("FileIO: SIGNON screen")

    hw = 320 * 200

    parent = Path(__file__).resolve().parent
    input_path = parent / ("signon_sod.bin" if sod else "signon_wl.bin")
    palette = SodPal if sod else WolfPal

    with open(input_path, 'rb') as fp:
        src = fp.read(hw)

    block = bytearray(hw * 3)
    for n in range(hw):
        color_idx = src[n]
        block[n * 3 + 0] = palette[color_idx][0]
        block[n * 3 + 1] = palette[color_idx][1]
        block[n * 3 + 2] = palette[color_idx][2]

    output_path = Path("signon")
    output_path.mkdir(parents=True, exist_ok=True)

    im = Image.frombytes('RGB', (320, 200), bytes(block), 'raw')
    im.save(output_path / "signon.png")
