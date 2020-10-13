#! /usr/bin/env python3

#####################################################
# The example shows how to extract a line scan data #
# from a StreamLine HR measurement                  #
#####################################################

import numpy as np
from renishawWiRE import WDFReader
from _path import curdir, imgdir
try:
    import matplotlib.pyplot as plt
    plot = True
except ImportError:
    plot = False


def main():
    filename = curdir / "spectra_files" / "line.wdf"
    reader = WDFReader(filename)
    assert reader.measurement_type == 3

    # For mapping, xdata is still wavenumber
    wn = reader.xdata
    spectra = reader.spectra
    assert wn.shape[0] == spectra.shape[1]
    # Now spectra.shape becomes (i, j, spectrum)
    print(wn.shape, spectra.shape)
    if plot is True:
        # Level the spectra with baseline intensity
        spectra = spectra - spectra.min(axis=1, keepdims=True)
        # Need to revert matrix for plotting
        spectra = spectra.T
        plt.figure(figsize=(6, 4))
        # plot the first 5 spectra
        for i in range(5):
            plt.plot(wn, spectra[:, i], label="{0:d}".format(i))
        plt.legend()
        plt.xlabel("Wavenumber (1/cm)")
        plt.ylabel("Intensity (ccd counts)")
        plt.title("Spectra from line.wdf")
        plt.show(block=False)
        plt.pause(3)
        plt.tight_layout()
        plt.savefig(imgdir / "linscan.png", dpi=100)
        plt.close()
    else:
        print("Wavenumber is like:", wn)
        print("Spectra matrix is like: \n", spectra)

    return


if __name__ == "__main__":
    main()
