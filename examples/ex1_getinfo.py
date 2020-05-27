#! /usr/bin/env python3

################################################################
# The example shows how to retrieve metadata from wdf file     #
# spectra_files/sp.wdf contains 1 single-point Raman spectrum #
################################################################

from renishawWiRE import WDFReader
from _path import curdir


def main():
    for name in ("sp", "line", "depth", "mapping"):
        filename = curdir / "spectra_files" / "{0}.wdf".format(name)
        print("Testing: ", filename.as_posix())
        # if debug=True, debug information will show in stderr
        reader = WDFReader(filename, debug=True)
        # Explicitly print into stdout
        reader.print_info()
    return


if __name__ == "__main__":
    main()
