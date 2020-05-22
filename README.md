[![PyPI version](https://badge.fury.io/py/renishawWiRE.svg)](https://badge.fury.io/py/renishawWiRE)

A python wrapper for read-only accessing the wdf Raman spectroscopy file format created
by the WiRE software of Ranishaw Inc.  Renishaw Inc owns copyright of
the wdf file format.

Ideas for reverse-engineering the WDF format is inspired by:

- [Renishaw File Reader](https://zenodo.org/record/495477#.XsZs3y17FBw) by Alex Henderson (DOI:10.5281/zenodo.495477))
- Renishaw IO module in [`Gwyddion`](http://gwyddion.net/module-list-nocss.en.php)

# Installation

Requirements:

- `python` version > 3.4
- `Numpy`
- `Matplotlib` (optional, if you want to plot the spectra in the examples)

## Versions hosted on PyPI: via `pip`

```bash
# Optionally on a virtualenv
pip install -U renishawWiRE
```

## `HEAD` version: via `git` + `pip`

**Caution!** cloning the repo (when you have `git-lfs` installed) will
also get all the example Raman spectra files which ends up to be
around 40 MiB.

```bash
git clone https://github.com/alchem0x2A/py-wdf-reader.git
cd py-wdf-reader
pip install .
```

# Basic Usage

Check the sample codes in `examples/` folder for more details about
what the package can do.

## Get file information

`renishawWiRE.WDFReader` is the main entry point to get information of a WDF file.

```python
# The following example shows how to get the info from a WDF file
# Check `examples/ex1_getinfo.py`
from renishawWiRE import WDFReader

#`filename` can be string, file obj or `pathlib.Path`
filename = "path/to/your/file.wdf"
reader = WDFReader(filename)
reader.print_info()
```

## Get single point spectrum / spectra

When the spectrum is single-point (`WDFReader.measurement_type == 1`),
`WDFReader.xdata` is the spectral points, and `WDFReader.spectra` is
the accumulated spectrum.

```python
# Example to read and plot single point spectrum
# Assume same file as in previous section
# Check `examples/ex2_sp_spectra.py`
import matplotlib.pyplot as plt
wavenumber = reader.xdata
spectra = reader.spectra
plt.plot(wavenumber, spectra)
```

## Get depth series spectra

A depth series measures contains single point spectra with varied
Z-depth. For this type `WDFReader.measurement_type == 2`. The code to
get the spectra are the same as the one in the single point spectra
measurement, instead that the `WDFReade.spectra` becomes a matrix with
size of `(count, point_per_spectrum)`:

*WIP*





## Get line scan from StreamLine™ / StreamHR Line™ measurements

For mapped measurements (line or grid scan),
`WDFReader.measurement_type == 3`.  The code to get the spectra are
the same as the one in the single point spectra measurement, instead
that the `WDFReade.spectra` becomes a matrix with size of `(count, point_per_spectrum)`:

```python
# Example to read line scane spectrum
# Check `examples/ex3_linscan.py`
filename = "path/to/line-scan.wdf"
reader = WDFReader(filename)
wn = reader.xdata
spectra = reader.spectra
print(wn.shape, spectra.shape)
```

It is also possible to correlate the xy-coordinates with the
spectra. For a mapping measurement, `WDFReader.xpos` and
`WDFReader.ypos` will contain the point-wise x and y coordinates.

```python
# Check examples/ex4_linxy.py for details
x = reader.xpos
y = reader.ypos
# Cartesian distance
d = (x ** 2 + y ** 2) ** (1 / 2)
```

## Get grid mapping from StreamLine™ / StreamHR Line™ measurements

Finally let's extract the grid-spaced Raman data. For mapping data
with `spectra_w` pixels in the x-direction and `spectra_h` in the
y-direction, the matrix of spectra is shaped into `(spectra_h,
spectra_w, points_per_spectrum)`.

Make sure your xy-coordinates starts from the top left corner.

```python
# For gridded data, x and y are on rectangle grids
# check examples/ex5_mapping.py for details
x = reader.xpos
y = reader.ypos
spectra = reader.spectra
# Use other packages to handle spectra
# write yourself the function or use a 3rd-party libray
mapped_data = some_treating_function(spectra, **params)
# plot mapped data using plt.imshow
plt.pcolor(mapped_data, extends=[0, x.max() - x.min(),
                                 y.max() - y.min(), 0])
```


# TODOs

There are still several functionalities not implemented:

- [ ] Extract image info
- [ ] Verify image coordinate superposition
- [ ] Improve series measurement retrieval
- [ ] Testing on various version of Renishaw instruments
- [ ] Binary utilities

# Bug reports

The codes are only tested on the Raman spectra files that generated
from my personal measurements. If you encounter any peculiar behavior
of the package please kindly open an issue with your report /
suggestions. Thx!

