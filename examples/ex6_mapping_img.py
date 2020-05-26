#! /usr/bin/env python3

########################################################
# The example shows on top of example 5 how to extract #
# the white-light image                                #
########################################################

import numpy as np
from renishawWiRE import WDFReader
from _path import curdir, imgdir
try:
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
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
    # Test newer API
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

    if plot is True:
        # Must provide the format to read the optical image
        img = mpimg.imread(reader.img, format="jpg")
        img_x0, img_y0 = reader.img_origins
        img_w, img_h = reader.img_dimensions
        print(reader.img_dimensions)
        plt.figure(figsize=(10, 5))

        # Left, plot the white light image and rectangle area
        plt.subplot(121)
        # Show the image with upper origin extent See
        # https://matplotlib.org/3.1.1/gallery/text_labels_and_annotations/text_alignment.html
        plt.imshow(img, extent=(img_x0, img_x0 + img_w,
                                img_y0 + img_h, img_y0))
        # Add rectangle for marking
        r = plt.Rectangle(xy=(map_x.min(), map_y.min()),
                          width=map_w,
                          height=map_h,
                          fill=False)
        plt.gca().add_patch(r)
        plt.xlabel("Stage X [μm]")
        plt.ylabel("Stage Y [μm]")

        # Right plot histogram of Peak A/B mapping
        plt.subplot(122)
        plt.imshow(ratio, interpolation="bicubic",
                   extent=[0, map_w,
                           map_h, 0],
                   vmin=0.5, vmax=1.5)
        plt.xlabel("Mapping x [μm]")
        plt.ylabel("Mapping y [μm]")
        cb = plt.colorbar()
        cb.ax.set_title("Ratio")
        plt.tight_layout()
        plt.show(block=False)
        plt.pause(3)
        plt.savefig(imgdir / "map-optical.png", dpi=100)
        plt.close()
    else:
        pass
    return


if __name__ == "__main__":
    main()
