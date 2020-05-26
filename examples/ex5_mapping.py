#! /usr/bin/env python3

###########################################################
# The example shows how to get mapping  data              #
# The peak ratio at 1315 cm^-1 and 1380 cm^-1 are plotted #
# Details see Small 14, 1804006 (2018).                   #
###########################################################

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
    spectra_cut = spectra[:, :, cond]
    return getattr(np, method)(spectra_cut, axis=2, **params)


def main():
    filename = curdir / "spectra_files" / "mapping.wdf"
    reader = WDFReader(filename)
    assert reader.measurement_type == 3
    wn = reader.xdata
    spectra = reader.spectra
    print(wn.shape, spectra.shape)
    x = reader.xpos
    y = reader.ypos
    w, h = reader.map_shape
    print("The size of mapping is {0:d} * {1:d}".
          format(w, h))
    # w and h are the measure in xy coordinates
    # Level the spectra
    spectra = spectra - np.min(spectra, axis=2, keepdims=True)
    peaks_a = peak_in_range(spectra, wn, [1295, 1340])
    peaks_b = peak_in_range(spectra, wn, [1350, 1400])

    ratio = peaks_a / peaks_b
    ratio_fl = ratio.flatten()

    if plot is True:
        plt.figure(figsize=(10, 5))

        # Left plot histogram of Peak A/B ratio
        plt.subplot(121)
        plt.hist(ratio_fl, bins=50, range=(0.1, 2))
        plt.xlabel("Ratio peak A / peak B")
        plt.ylabel("Counts")

        # Right plot histogram of Peak A/B mapping
        plt.subplot(122)
        plt.imshow(ratio, interpolation="bicubic",
                   extent=[0, x.max() - x.min(),
                           y.max() - y.min(), 0],
                   vmin=0.5, vmax=1.5)
        plt.xlabel("Mapping x [μm]")
        plt.ylabel("Mapping y [μm]")
        cb = plt.colorbar()
        cb.ax.set_title("Ratio")
        plt.tight_layout()
        plt.show(block=False)
        plt.pause(3)
        plt.savefig(imgdir / "mapping.png", dpi=100)
        plt.close()
    else:
        pass
    return


if __name__ == "__main__":
    main()
