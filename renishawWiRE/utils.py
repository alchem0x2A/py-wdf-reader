# Some tiny functions for converting things
from numpy import nan


def convert_wl(wn):
    """Convert wavenumber (cm^-1) to nm
    """
    try:
        wl = 1 / (wn * 1e2) / 1e-9
    except ZeroDivisionError:
        wl = nan
    return wl


def convert_attr_name(s):
    """Convert all underline in string name to space and capitalize
    """
    return " ".join(map(str.capitalize, s.strip().split("_")))
