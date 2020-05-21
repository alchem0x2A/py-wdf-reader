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

```bash
git clone https://github.com/alchem0x2A/py-wdf-reader.git
cd py-wdf-reader
pip install .
```

# Basic Usage

Check the sample codes in `samples/` folder for more details about
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
reader = WDFReader(filename)
wavenumber = reader.xdata
spectra = reader.spectra
plt.plot(wavenumber, spectra)
```

## Get line scan from StreamLine™ / StreamHR Line™ measurements

## Get grid mapping from StreamLine™ / StreamHR Line™ measurements



# TODOs

There are still several functionalities not implemented:

- [ ] Verify image coordinate
- [ ] Z-scan data retrieval
- [ ] Testing on various version of Renishaw instruments
- [ ] Binary utilities

# Bug reports

The codes are only tested on the Raman spectra files that generated
from my personal measurements. If you encounter any peculiar behavior
of the package please kindly open an issue with your report /
suggestions. Thx!

