# Some tiny functions for converting things


def convert_wl(wn):
    """Convert wavenumber (cm^-1) to nm
    """
    wl = 1 / (wn * 1e2) / 1e-9
    return wl
