#!/usr/bin/env python3
"""Export the renishaw file as plain text files
   usage:
   renishaw-export  
"""

from renishawWiRE.wdfReader import WDFReader
from renishawWiRE.types import MeasurementType
from argparse import ArgumentParser
from pathlib import Path
import os
import sys
import numpy as np


def main():
    parser = ArgumentParser(description=("Simple script to convert Renishaw wdf spectroscopy"
                                         " files into plain text files"))
    parser.add_argument("wdf_file",
                        help="Renishaw wdf for input")
    parser.add_argument("-o",
                        "--output",
                        default=None,
                        help=("base name for the exported files."
                              " Do not need to add extension"))
    parser.add_argument("-f",
                        "--format",
                        default=".csv",
                        help=("format of exported, valid values\n"
                              ".csv (comma-separated) "
                              ".txt (space-separated)"))
    parser.add_argument("-p",
                        "--precision",
                        default="%.4f",
                        help=("precision of exported data."
                              " Use printf-compatible format such as %2.4f."))

    args = parser.parse_args()
    wdf_file = Path(args.wdf_file).expanduser().resolve()
    if not wdf_file.is_file():
        print("The file {0} does not exist. Abort!".format(wdf_file.as_posix()),
              file=sys.stderr)
        return 1

    reader = WDFReader(wdf_file)
    # Output test information
    print("Your Renishaw file looks like:")
    reader.print_info()
    # handle the spectra data
    X, header = handle_spectra(reader)

    if args.format not in (".csv", ".txt"):
        print("Only csv and txt formats are allowed! Abort.", file=sys.stderr)
        return 1
    if args.format == ".csv":
        delimiter = ","
    else:
        delimiter = " "

    root = wdf_file.parent
    # print(root, name)
    if args.output is not None:
        name = Path(args.output).with_suffix(args.format)
    else:
        name = wdf_file.with_suffix(args.format)

    filename = root / name
    if not filename.parent.is_dir():
        os.makedirs(filename.parent, exist_ok=True)

    np.savetxt(filename, X, fmt=args.precision,
               delimiter=delimiter, header=header)

    return 0


def handle_spectra(reader):
    """Function to treat single point spectrum
       return the X matrix using numpy, and header
    """
    # Wavenumber is alwa
    wn = reader.xdata
    spectra = reader.spectra
    try:
        if len(spectra.shape) == 1:
            # single point
            l_w, = spectra.shape
            assert l_w == len(wn)
            X = np.vstack([wn, spectra]).T
            header = "Wavenumber,point 1"
            print(1, X)
        elif len(spectra.shape) == 2:
            # line or depth scan
            n_p, l_w = spectra.shape
            X = np.vstack([wn, spectra]).T
            header = "Wavenumber," + ",".join(["point {:d}".format(i + 1)
                                               for i in range(n_p)])
            print(2, X)
        elif len(spectra.shape) == 3:
            # mapping
            c, r, l_w = spectra.shape
            assert l_w == len(wn)
            X = np.vstack([wn, spectra.reshape(c * r, l_w)]).T
            header = "Wavenumber," + ",".join(["row {:d} column {:d}"
                                               .format(i + 1,
                                                       j + 1)
                                               for i in range(c)
                                               for j in range(r)])
            print(3, X)
        else:
            print(("There seems to be something wrong "
                   "with the spectral file. Abort!"),
                  file=sys.stderr)
            return 1
    except AssertionError:
        print(("The length of wavenumber points do not "
               "match that in the spectral data. Abort!"), file=sys.stderr)

    # Sort the ndarray according to 0st
    X = X[X[:, 0].argsort()]
    return X, header


if __name__ == '__main__':
    main()
