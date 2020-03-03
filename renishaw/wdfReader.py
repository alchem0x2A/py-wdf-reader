# Renishaw wdf Raman spectroscopy file reader
# Code inspired by Henderson, Alex DOI:10.5281/zenodo.495477
from __future__ import print_function
import struct
import numpy
from .types import LenType, DataType, MeasurementType
from .types import ScanType, UnitType, DataType
from .types import Positions
from .utils import convert_wl

class wdfReader(object):
    """Reader for Renishaw(TM) WiRE Raman spectroscopy files (.wdf format)
    Args:
    file_name (file) : File object for the wdf file

    Attributes:
    title (str) : Title of measurement
    username (str) : Username
    application_name (str) : Default WiRE
    application_version (int,) * 4 : Version number, e.g. [4, 4, 0, 6602]
    measurement_type (int) : Type of measurement
                             0=unknown, 1=single, 2=multi, 3=mapping 
    scan_type (int) : Scan of type, see values in scan_types
    laser_wavenumber (float32) : Wavenumber in cm^-1
    count (int) : Numbers of experiments (same type)
    spectral_units (int) : Unit of spectra, see unit_types
    xlist_type (int) : See unit_types
    xlist_units (int) : See unit_types
    ylist_type : #TODO
    ylist_units : #TODO
    point_per_spectrum : None
    data_origin_count : None
    capacity : None
    xlist_length : None
    ylist_length : None
    accumulation_count : None
    block_info (dict) : Info block at least with following keys
                        DATA, XLST, YLST, ORGN
                        # TODO types?
    """

    def __init__(self, file_name, quiet=False):
        try:
            self.file_obj = open(file_name, "rb")
        except IOError:
            raise IOError("File {0} does noe exist!".format(file_name))
        # Initialize the properties for the wdfReader class
        # self.file_obj = file_obj
        self.title = ""
        self.username = ""
        self.measurement_type = ""
        self.scan_type = ""
        self.laser_length = None
        self.count = None
        self.spectral_units = ""
        self.xlist_type = None
        self.xlist_units = ""
        self.ylist_type = None
        self.ylist_units = ""
        self.point_per_spectrum = None
        self.data_origin_count = None
        self.capacity = None
        self.application_name = ""
        self.application_version = [None]*4
        self.xlist_length = None
        self.ylist_length = None
        self.accumulation_count = None
        self.block_info = {}    # each key has value (offset, size)
        self.quiet = quiet      # if need to output infomation
        # Parse the header section in the wdf file
        try:
            self.parse_header()
        except:
            print("Failed to parse the header of file")
        # Location the data, xlist, ylist and
        try:
            self.block_info["DATA"] = self.locate_block("DATA")
            self.block_info["XLST"] = self.locate_block("XLST")
            self.block_info["YLST"] = self.locate_block("YLST")
        except:
            print("Failed to get the block information")
        # set xlist and ylist unit and type
        self.xlist_type, self.xlist_units = self.get_xlist_info()
        self.ylist_type, self.ylist_units = self.get_ylist_info()
        # set the data origin, if count is not 0 (for mapping applications)
        if (self.data_origin_count != None) and (self.data_origin_count != 0):
            try:
                self.block_info["ORGN"] = self.locate_block("ORGN")
            except:
                print("Failed to get the block information")  # TODO correct Block
        # self.print_info()
        # TODO
        # self.origin_list_info = self.get_origin_list_info()

    def print_info(self):
        """Print information of the wdf file
        """
        if not self.quiet:
            s = []
            s.append("{0} version:\t{1}.{2}.{3}.{4}".format(self.application_name,
                                                            *self.application_version))
            s.append("Title:\t{0:s}".format(self.title))
            s.append("Wavelength:\t{0:.1f}".format(self.laser_length))
            print("\n".join(s))



    def _read_type(self, type, size=0):
        """ Unpack struct data for certain type
        """
        if type in ["int16", "int32", "int64", "float", "double"]:
            # unpack in unsigned values
            fmt_out = LenType["s_" + type].value
            fmt_in = LenType["l_" + type].value
            return struct.unpack(fmt_out, self.file_obj.read(fmt_in))[0]
        elif type == "utf8":
            # Read utf8 string with determined size block
            self.file_obj.read(size).decode("utf8")
        else:
            # TODO: strip the blanks
            raise ValueError("Unknown data length format!")

    # The method for reading the info in the file header
    def parse_header(self):
        self.file_obj.seek(0)   # return to the head
        # Must make the conversion under python3
        block_ID = self.file_obj.read(Positions.blockid).decode("ascii")
        block_UID = self._read_type("int32")
        block_len = self._read_type("int64")
        if (block_ID != "WDF1") or (block_UID != 0 and block_UID != 1) \
           or (block_len != 512):
            raise ValueError("The wdf file format is incorrect!")
        # TODO what are the digits in between?

        # The keys from the header
        self.file_obj.seek(Positions.ppl)  # space
        self.point_per_spectrum = self._read_type("int32")
        self.capacity = self._read_type("int64")
        self.count = self._read_type("int64")
        self.accumulation_count = self._read_type("int32")
        self.ylist_length = self._read_type("int32")
        self.xlist_length = self._read_type("int32")
        self.data_origin_count = self._read_type("int32")
        self.application_name = self._read_type("utf8", 24)
        for i in range(4):
            self.application_version[i] = self._read_type("int16")
        self.scan_type = self._read_type("int32")
        self.measurement_type = self._read_type("int32")
        # For the units
        self.file_obj.seek(152)
        self.spectral_units = self._read_type("int32")
        self.laser_length = convert_wl(self._read_type("float"))
        # Username and title
        self.file_obj.seek(0xd0)
        self.username = self._read_type("utf8", 0x20)
        self.title = self._read_type("utf8", 0x200 - 0xf0)

    # locate the data block offset with the corresponding block name
    def locate_block(self, block_name):
        if (block_name in self.block_info) and \
           (self.block_info[block_name] is not None):
            return self.block_info[block_name]
        else:
            # find the block by increment in block size
            # exhaustive but no need to worry
            curr_name = None
            curr_pos = 0
            next_pos = curr_pos
            self.file_obj.seek(curr_pos)
            while (curr_name != block_name) and (curr_name != ""):
                curr_pos = next_pos
                curr_name = self.file_obj.read(4).decode(
                    "ascii")  # Always a 4-str block name
                uid = self._read_type("int32")
                size = self._read_type("int64")
                next_pos += size
                self.file_obj.seek(next_pos)
                # print(curr_name, curr_pos, uid, size)
            # found the id
            if curr_name == block_name:
                return (curr_pos, size)
            else:
                raise ValueError(
                    "The block with name {} is not found!".format(block_name))

    # get the xlist info

    def get_xlist_info(self):
        pos, size = self.locate_block("XLST")
        offset = 16
        self.file_obj.seek(pos + offset)
        # TODO: strings
        data_type = self._read_type("int32")
        data_unit = self._read_type("int32")
        return (data_type, data_unit)

    # get the ylist info
    def get_ylist_info(self):
        pos, size = self.locate_block("YLST")
        offset = 16
        self.file_obj.seek(pos + offset)
        # TODO: strings
        data_type = self._read_type("int32")
        data_unit = self._read_type("int32")
        return (data_type, data_unit)

    # TODO: get the origin list info
    # def get_origin_list_info(self):
    #     return (None, None)

    """
    Important parts for data retrieval
    """

    def get_xdata(self):
        pos = self.locate_block("XLST")[0]
        offset = 24
        self.file_obj.seek(pos + offset)
        size = self.xlist_length
        self.file_obj.seek(pos + offset)
        x_data = numpy.fromfile(self.file_obj, dtype="float32", count=size)
        return x_data

    def get_ydata(self):
        pos = self.locate_block("YLST")[0]
        offset = 24
        self.file_obj.seek(pos + offset)
        size = self.ylist_length
        self.file_obj.seek(pos + offset)
        y_data = numpy.fromfile(self.file_obj, dtype="float32", count=size)
        return y_data

    def get_spectra(self, start=0, end=-1):
        if end == -1:           # take all spectra
            end = self.count-1
        if (start not in range(self.count)) or (end not in range(self.count)):
            raise ValueError("Wrong start and end indices of spectra!")
        if start > end:
            raise ValueError("Start cannot be larger than end!")

        # Determine start position
        pos_start = self.locate_block("DATA")[0] \
                    + 16 + LenType["l_float"].value * \
                    start * self.point_per_spectrum
        n_row = end - start + 1
        self.file_obj.seek(pos_start)
        spectra_data = numpy.fromfile(
            self.file_obj, dtype="float32",
            count=n_row*self.point_per_spectrum)
        if len(spectra_data.shape) == 1:
            # The spectra is only 1D array
            return spectra_data
        else:
            # Make 2D array
            spectra_data = spectra_data.reshape(
                n_row, spectra_data.size // n_row)
            return spectra_data

if __name__ == '__main__':
    import sys
    try:
        fn = sys.argv[1]
        print(fn)
        wdf = wdfReader(fn)
        for s in dir(wdf):
            if "__" not in s:
                print(s, getattr(wdf, s))
        wdf.print_info()
    except IndexError:
        raise
