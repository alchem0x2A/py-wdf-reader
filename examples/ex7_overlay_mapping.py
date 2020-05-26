#! /usr/bin/env python3


########################################################
# The example shows on top of example 6 how to overlay #
# the cropped image with mapping                       #
########################################################

import numpy as np
from renishawWiRE import WDFReader
from _path import curdir, imgdir
try:
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    import PIL
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
    map_x = reader.xpos
    map_y = reader.ypos
    map_w = reader.map_info["x_span"]
    map_h = reader.map_info["y_span"]

    # w and h are the measure in xy coordinates
    # Level the spectra
    spectra = spectra - np.min(spectra, axis=2, keepdims=True)
    peaks_a = peak_in_range(spectra, wn, [1295, 1340])
    peaks_b = peak_in_range(spectra, wn, [1350, 1400])

    ratio = peaks_a / peaks_b
    extent = [0, map_w,
              map_h, 0]

    if plot is True:
        # Must provide the format to read the optical image
        # img = mpimg.imread(reader.img, format="jpg")
        img = PIL.Image.open(reader.img)
        print(reader.img_cropbox)
        # Desaturate the whitelight image
        img1 = img.crop(box=reader.img_cropbox).convert("L")

        plt.figure(figsize=(6, 6))

        # Left, plot the white light image and rectangle area
        # Show the image with upper origin extent See
        # https://matplotlib.org/3.1.1/gallery/text_labels_and_annotations/text_alignment.html
        plt.imshow(img1,
                   alpha=0.5,
                   cmap="hot",
                   extent=extent)

        # Right plot histogram of Peak A/B mapping
        cm = plt.imshow(ratio, interpolation="bicubic",
                        alpha=0.5,
                        cmap="viridis_r",
                        extent=extent,
                        vmin=0.5, vmax=1.5)
        plt.xlabel("Mapping x [μm]")
        plt.ylabel("Mapping y [μm]")
        cb = plt.colorbar(cm)
        cb.ax.set_title("Ratio")
        plt.title("50% Optical + 50% Raman")
        plt.tight_layout()
        plt.show(block=False)
        plt.pause(3)
        plt.savefig(imgdir / "map-overlay.png", dpi=100)
        plt.close()
    else:
        pass
    return


if __name__ == "__main__":
    main()
