#! /usr/bin/env python3

################################################################
# The example shows how to get single spectrum from wdf file   #
# spectra_files/sp.wdf contains 1 single-point Raman spectrum #
################################################################

from renishawWiRE import WDFReader
from _path import curdir, imgdir
try:
    import matplotlib.pyplot as plt
    plot = True
except ImportError:
    plot = False


def main():
    filename = curdir / "spectra_files" / "sp.wdf"
    reader = WDFReader(filename)
    print("Measurement type is ", reader.measurement_type)
    print("{0} Spectra obtained with {1} accumulations each".
          format(reader.count, reader.accumulation_count))
    # For ex1.wdf there is only 1 spectrum
    assert reader.count == 1

    wn = reader.xdata           # wavenumber
    sp = reader.spectra         # spectrum / spectra in ccd counts
    # For single spectrum the spectra has shape (point_per_spectrum, )
    print(wn.shape, sp.shape)
    assert wn.shape == sp.shape
    if plot:
        print("Use matplotlib to plot spectrum")
        plt.figure(figsize=(6, 4))
        plt.plot(wn, sp, label="Spectrum 1")
        plt.xlabel("Wavenumber (1/cm)")
        plt.ylabel("Intensity (ccd counts)")
        plt.title("Spectrum from sp.wdf")
        plt.show(block=False)
        plt.tight_layout()
        plt.pause(3)
        plt.savefig(imgdir / "sp_spectra.png", dpi=100)
        plt.close()
    else:
        print("No matplotlib, simply print the values")
        print("Wavenumbers (1/cm): ", wn)
        print("Intensities (ccd counts): ", sp)
    return


if __name__ == "__main__":
    main()
