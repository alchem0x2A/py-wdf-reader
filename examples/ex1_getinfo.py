#! /usr/bin/env python3
from renishawWiRE import WDFReader
from pathlib import Path


def main():
    curdir = Path(__file__).parent.resolve()
    filename = curdir / "spectra_files" / "ex1.wdf"
    reader = WDFReader(filename)
    reader.print_info()
    return

if __name__ == "__main__":
    main()
