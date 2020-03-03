# Declaration of DATA types
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


class UnitType(IntEnum):
    Arbitrary = 0
    RamanShift = 1
    Wavenumber = 2
    Nanometre = 3
    ElectronVolt = 4
    Micron = 5
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


class DataType(IntEnum):
    Arbitrary = 0
    Frequency = 1
    Intensity = 2
    X = 3
    Y = 4
    Z = 5
    R = 6
    Theta = 7
    Phi = 8
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

class Positions(IntEnum):
    blockid = 0x4
    pps = 0x3c
