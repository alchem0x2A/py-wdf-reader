#! /usr/bin/env python3

#####################################################################
# This example shows how to handle series data such as z-depth scan #
#####################################################################

# TODO: automatic determination of scan type

import numpy as np
from renishawWiRE import WDFReader
from _path import curdir, imgdir
try:
    import matplotlib.pyplot as plt
    plot = True
except ImportError:
    plot = False


def peak_in_range(spectra, wn, range, method="max", **params):
    """Find the max intensity of peak within range
       method can be max, min, or mean
    """
    cond = np.where((wn >= range[0]) & (wn <= range[1]))[0]
    spectra_cut = spectra[:, cond]
    return getattr(np, method)(spectra_cut, axis=1, **params)


def main():
    filename = curdir / "spectra_files" / "depth.wdf"
    reader = WDFReader(filename)
    # A depth scan
    assert reader.measurement_type == 2

    # For depth scan, xdata is still wavenumber
    wn = reader.xdata
    spectra = reader.spectra
    x = reader.xpos
    y = reader.ypos
    z = reader.zpos
    # print(x, y, z)
    # In this example only z is non-zero
    assert all([np.all(x == 0), np.all(y == 0), ~np.all(z == 0)])
    assert reader.count == z.shape[0]
    print(spectra, spectra.shape)
    print(reader.count)

    # Distance
    wn = reader.xdata
    spectra = reader.spectra

    # Filter blank spectra
    cond = np.where(spectra.mean(axis=1) > 0)[0]
    z = z[cond]
    spectra = spectra[cond, :]

    # Data processing
    spectra = spectra - spectra.min(axis=1, keepdims=True)
    # Simply get accumulated counts between 1560 and 1620 cm^-1
    peak_1 = peak_in_range(spectra, wn, range=[1560, 1620])
    peak_2 = peak_in_range(spectra, wn, range=[2650, 2750])
    ratio = peak_2 / peak_1

    if plot is True:
        # Level the spectra with baseline intensity
        plt.figure(figsize=(6, 4))
        plt.plot(z, peak_1 / peak_1.max(), "-o", label="G Peak")
        # plt.plot(z, peak_2 / peak_2.max(), label="2D")
        # plt.plot(z, ratio, label="2D/G")
        plt.xlabel("Z [{0}]".format(str(reader.zpos_unit)))
        plt.legend(loc=0)
        plt.ylabel("Normed Intensity")
        plt.title("Results from depth.wdf")
        plt.show(block=False)
        plt.pause(3)
        plt.savefig(imgdir / "depth.png", dpi=100)
        plt.close()
    else:
        print("Wavenumber is like:", wn)
        print("Z-Distance is like:", z)
        print("2D/G ratio is like: \n", ratio)

    return


if __name__ == "__main__":
    main()
