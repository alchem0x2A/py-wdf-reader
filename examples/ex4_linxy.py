#! /usr/bin/env python3

###################################################
# The example shows how to correlate spectra data #
# with xy-coordinate from the line scane          #
###################################################

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
    x = reader.xpos
    y = reader.ypos
    print(x.shape, y.shape)
    assert x.shape[0] == y.shape[0] == spectra.shape[0]
    
    # Distance
    d = np.sqrt(x ** 2 + y ** 2)
    wn = reader.xdata
    spectra = reader.spectra
    spectra_tr = spectra[:, 0, :]
    spectra_tr = spectra_tr - spectra_tr.min(axis=1, keepdims=True)
    # Simply get accumulated counts between 1560 and 1620 cm^-1
    pos = np.where((wn >= 1560) & (wn <= 1620))[0]
    cut = spectra_tr[:, pos]
    sum_cnt = np.sum(cut, axis=1)
    
    if plot is True:
        # Level the spectra with baseline intensity
        plt.figure()
        plt.plot(d, sum_cnt, "-o")
        plt.xlabel("Distance (μm)")
        plt.ylabel("Sum. Intensity (ccd counts)")
        plt.title("Results from ex2.wdf")
        plt.show(block=False)
        plt.pause(3)
        plt.close()
    else:
        print("Wavenumber is like:", wn)
        print("Distance is like:", d)
        print("Spectra matrix is like: \n", spectra_tr[:, 0, :])

    return


if __name__ == "__main__":
    main()
