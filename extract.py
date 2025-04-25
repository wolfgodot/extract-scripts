#!/usr/bin/env python

import argparse
from pathlib import Path

from gamemaps import extract_maps
from vgagraph import extract_vga
from vswap import extract_vswap

def main():
    parser = argparse.ArgumentParser(description="Extract Wolfenstein3D assets")
    parser.add_argument('-i', '--input', type=str, required=True, help='Directory with game files')
    args = parser.parse_args()
    input_path = Path(args.input)

    extract_maps(input_path / "MAPHEAD.WL6", input_path / "GAMEMAPS.WL6")
    print()
    extract_vswap(input_path / "VSWAP.WL6")
    print()
    extract_vga(input_path / "VGADICT.WL6", input_path / "VGAHEAD.WL6", input_path / "VGAGRAPH.WL6")

            
if __name__ == "__main__":
    main()
