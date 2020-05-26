#! /usr/bin/env python3

################################################################
# The example shows how to retrieve metadata from wdf file     #
# spectra_files/sp.wdf contains 1 single-point Raman spectrum #
################################################################

from renishawWiRE import WDFReader
from _path import curdir


def main():
    filename = curdir / "spectra_files" / "sp.wdf"
    reader = WDFReader(filename)
    reader.print_info()
    return


if __name__ == "__main__":
    main()
