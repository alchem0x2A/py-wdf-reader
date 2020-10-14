#! /usr/bin/env python3

###########################################################
# The example shows how to get mapping  data              #
# The peak ratio at 1315 cm^-1 and 1380 cm^-1 are plotted #
# Details see Small 14, 1804006 (2018).                   #
###########################################################
import subprocess
import os
from pathlib import Path

import numpy as np
from renishawWiRE import WDFReader
from _path import curdir, imgdir
try:
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    plot = True
except ImportError:
    plot = False


def call_exe(name, extras="", output=None):
    filename = curdir / "spectra_files" / "{0}.wdf".format(name)
    root = filename.parent
    # clean up all
    reader = WDFReader(filename)
    assert reader is not None
    for ext in (".csv", ".txt"):
        for f in root.glob("*" + ext):
            print(f)
            os.remove(f)
    # Initial name
    cmd = "wdf-export {0} {1}".format(filename.as_posix(),
                                      extras)
    if output is not None:
        cmd += "-o {0}".format(output)

    run = subprocess.run(cmd, shell=True)
    assert run.returncode == 0

    # Manually set output
    if output is not None:
        output = Path(output)
    else:
        if ".txt" not in extras:
            output = filename.with_suffix(".csv")
        else:
            output = filename.with_suffix(".txt")

    assert output.is_file() is True
    # Read the data
    if output.suffix == ".csv":
        delimiter = ","
    else:
        delimiter = " "

    data = np.genfromtxt(output, delimiter=delimiter, skip_header=1)
    wn_data = data[:, 0]
    spectra_data = data[:, 1:]
    assert reader.xdata.shape[0] == wn_data.shape[0]
    assert reader.count == spectra_data.shape[1]
    spectra_reader = reader.spectra.reshape(reader.count,
                                            reader.xdata.shape[0]).T
    # Only do this for decreasing sequence
    if reader.xdata[0] >  reader.xdata[1]:
        spectra_reader = spectra_reader[::-1, :]
    print(spectra_reader)
    print(spectra_data)
    assert np.all(np.isclose(spectra_reader, spectra_data, 1e-3))

    
    


def main():
    
    for name in ("sp", "line", "depth",
                 "mapping", "undefined", "streamline"):
        # Normal exe
        call_exe(name)
        call_exe(name, extras="-f .txt")
        call_exe(name,
                 output="test.txt")
        call_exe(name,
                 output="test.csv")

        
    
    


if __name__ == "__main__":
    main()
