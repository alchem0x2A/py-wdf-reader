#! /usr/bin/env python3

################################################################
# The example shows how to retrieve metadata from wdf file     #
# spectra_files/sp.wdf contains 1 single-point Raman spectrum #
################################################################

from renishawWiRE import WDFReader
from _path import curdir
#import pytest


def main():
    for name in ("sp", "line", "depth",
                 "mapping", "undefined", "streamline"):
        filename = curdir / "spectra_files" / "{0}.wdf".format(name)
        print("Testing: ", filename.as_posix())
        # if debug=True, debug information will show in stderr
        reader = WDFReader(filename, debug=True)
        assert reader is not None
        # Explicitly print into stdout
        reader.print_info()
        reader.close()
    return


if __name__ == "__main__":
    main()
