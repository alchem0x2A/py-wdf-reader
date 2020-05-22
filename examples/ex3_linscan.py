#! /usr/bin/env python3

#####################################################
# The example shows how to extract a line scan data #
# from a StreamLine HR measurement                  #
#####################################################

import numpy as np
from renishawWiRE import WDFReader
from pathlib import Path
try:
    import matplotlib.pyplot as plt
    plot = True
except ImportError:
    plot = False


def main():
    curdir = Path(__file__).parent.resolve()
    filename = curdir / "spectra_files" / "line.wdf"
    reader = WDFReader(filename)
    assert reader.measurement_type == 3

    # For mapping, xdata is still wavenumber
    wn = reader.xdata
    spectra = reader.spectra
    # Now spectra.shape becomes (i, j, spectrum)
    print(wn.shape, spectra.shape)
    if plot is True:
        # Level the spectra with baseline intensity
        spectra_tr = spectra[:, 0, :]
        spectra_tr = spectra_tr - spectra_tr.min(axis=1, keepdims=True)
        spectra_tr = spectra_tr.T
        plt.figure()
        # plot the first 10 spectra
        for i in range(10):
            plt.plot(wn, spectra_tr[:, i], label="{0:d}".format(i))
        plt.legend()
        plt.xlabel("Wavenumber (1/cm)")
        plt.ylabel("Intensity (ccd counts)")
        plt.title("Spectra from ex2.wdf")
        plt.show(block=False)
        plt.pause(3)
        plt.close()
    else:
        print("Wavenumber is like:", wn)
        print("Spectra matrix is like: \n", spectra[:, 0, :])

    return


if __name__ == "__main__":
    main()
