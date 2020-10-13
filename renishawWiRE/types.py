################################################################################################
# Declaration of DATA types            #                                                       #
# Credits for the Gwyddion project for #                                                       #
# deciphering the constants            #                                                       #
# See https://sourceforge.net/p/gwyddion/code/HEAD/tree/trunk/gwyddion/modules/file/renishaw.c #
################################################################################################

from enum import IntEnum, Enum


class LenType(Enum):
    l_int16 = 2
    l_int32 = 4
    l_int64 = 8
    s_int16 = "<H"              # unsigned short int
    s_int32 = "<I"              # unsigned int32
    s_int64 = "<Q"              # unsigned int64
    l_float = 4
    s_float = "<f"
    l_double = 8
    s_double = "<d"


class MeasurementType(IntEnum):
    Unspecified = 0
    Single = 1
    Series = 2
    Mapping = 3

    def __str__(self):
        return self._name_


class ScanType(IntEnum):
    Unspecified = 0
    Static = 1
    Continuous = 2
    StepRepeat = 3
    FilterScan = 4
    FilterImage = 5
    StreamLine = 6
    StreamLineHR = 7
    PointDetector = 8

    def __str__(self):
        return self._name_


class UnitType(IntEnum):
    Arbitrary = 0
    RamanShift = 1              # cm^-1 by default
    Wavenumber = 2              # nm
    Nanometre = 3
    ElectronVolt = 4
    Micron = 5                  # same for EXIF units
    Counts = 6
    Electrons = 7
    Millimetres = 8
    Metres = 9
    Kelvin = 10
    Pascal = 11
    Seconds = 12
    Milliseconds = 13
    Hours = 14
    Days = 15
    Pixels = 16
    Intensity = 17
    RelativeIntensity = 18
    Degrees = 19
    Radians = 20
    Celsius = 21
    Fahrenheit = 22
    KelvinPerMinute = 23
    FileTime = 24

    def __str__(self):
        """Rewrite the unit name output"""
        unit_str = dict(Arbitrary="",
                        RamanShift="1/cm",              # cm^-1 by default
                        Wavenumber="nm",            # nm
                        Nanometre="nm",
                        ElectronVolt="eV",
                        Micron="um",  # same for EXIF units
                        Counts="counts",
                        Electrons="electrons",
                        Millimetres="mm",
                        Metres="m",
                        Kelvin="K",
                        Pascal="Pa",
                        Seconds="s",
                        Milliseconds="ms",
                        Hours="h",
                        Days="d",
                        Pixels="px",
                        Intensity="",
                        RelativeIntensity="",
                        Degrees="°",
                        Radians="rad",
                        Celsius="°C",
                        Fahrenheit="°F",
                        KelvinPerMinute="K/min",
                        FileTime="",)
        return unit_str[self._name_]


class DataType(IntEnum):
    Arbitrary = 0
    Frequency = 1
    Intensity = 2
    Spatial_X = 3
    Spatial_Y = 4
    Spatial_Z = 5
    Spatial_R = 6
    Spatial_Theta = 7
    Spatial_Phi = 8
    Temperature = 9
    Pressure = 10
    Time = 11
    Derived = 12
    Polarization = 13
    FocusTrack = 14
    RampRate = 15
    Checksum = 16
    Flags = 17
    ElapsedTime = 18

    def __str__(self):
        return self._name_


class Offsets(IntEnum):
    """Offsets to the start of block
    """
    # General offsets
    block_name = 0x0
    block_id = 0x4
    block_data = 0x10
    # offsets in WDF1 block
    measurement_info = 0x3c                  #
    spectral_info = 0x98
    file_info = 0xd0
    usr_name = 0xf0
    data_block = 0x200
    # offsets in ORGN block
    origin_info = 0x14
    origin_increment = 0x18
    # offsets in WMAP block
    wmap_origin = 0x18
    wmap_wh = 0x30
    # offsets in WHTL block
    jpeg_header = 0x10


class ExifTags(IntEnum):
    """Customized EXIF TAGS
    """
    # Standard EXIF TAGS
    FocalPlaneXResolution = 0xa20e
    FocalPlaneYResolution = 0xa20f
    FocalPlaneResolutionUnit = 0xa210
    # Customized EXIF TAGS from Renishaw
    FocalPlaneXYOrigins = 0xfea0
    FieldOfViewXY = 0xfea1
