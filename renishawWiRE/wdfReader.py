# Renishaw wdf Raman spectroscopy file reader
# Code inspired by Henderson, Alex DOI:10.5281/zenodo.495477
from __future__ import print_function
import struct
import numpy
import io
from .types import LenType, DataType, MeasurementType
from .types import ScanType, UnitType, DataType
from .types import Offsets, ExifTags
from .utils import convert_wl, convert_attr_name
from sys import stderr
try:
    import PIL
except ImportError:
    PIL = None


class WDFReader(object):
    """Reader for Renishaw(TM) WiRE Raman spectroscopy files (.wdf format)

    The wdf file format is separated into several DataBlocks, with starting 4-char 
    strings such as (incomplete list):
    `WDF1`: File header for information
    `DATA`: Spectra data
    `XLST`: Data for X-axis of data, usually the Raman shift or wavelength
    `YLST`: Data for Y-axis of data, possibly not important
    `WMAP`: Information for mapping, e.g. StreamLine or StreamLineHR mapping
    `MAP `: Mapping information(?)
    `ORGN`: Data for stage origin
    `TEXT`: Annotation text etc
    `WXDA`: ? TODO
    `WXDM`: ? TODO
    `ZLDC`: ? TODO
    `BKXL`: ? TODO
    `WXCS`: ? TODO
    `WXIS`: ? TODO
    `WHTL`: An embeded image (?)

    Following the block name, there are two indicators:
    Block uid: int32
    Block size: int64

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
    count (int) : Numbers of experiments (same type), can be smaller than capacity
    spectral_units (int) : Unit of spectra, see unit_types
    xlist_type (int) : See unit_types
    xlist_units (int) : See unit_types
    xlist_length (int): Size for the xlist
    xdata (numpy.array): x-axis data
    ylist_type (int): Same as xlist_type
    ylist_units (int): Same as xlist_units
    ylist_length (int): Same as xlist_length
    ydata (numpy.array): y-data, possibly not used
    point_per_spectrum (int): Should be identical to xlist_length
    data_origin_count (int) : Number of rows in data origin list
    capacity (int) : Max number of spectra
    accumulation_count (int) : Single or multiple measurements
    block_info (dict) : Info block at least with following keys
                        DATA, XLST, YLST, ORGN
                        # TODO types?
    """

    def __init__(self, file_name, quiet=False):
        try:
            self.file_obj = open(str(file_name), "rb")
        except IOError:
            raise IOError("File {0} does noe exist!".format(file_name))
        # Initialize the properties for the wdfReader class
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
        self.xlist_length = 0
        self.ylist_length = 0
        self.accumulation_count = None
        self.block_info = {}    # each key has value (uid, offset, size)
        self.quiet = quiet      # if need to output infomation
        self.is_completed = False
        # Parse the header section in the wdf file
        self._locate_all_blocks()
        self._treat_block_data("WDF1")
        self._treat_block_data("DATA")
        self._treat_block_data("XLST")
        self._treat_block_data("YLST")
        self._treat_block_data("ORGN")
        self._treat_block_data("WMAP")
        self._treat_block_data("WHTL")

        # Reshape spectra after reading mapping information
        self._reshape_spectra()
        # self._parse_wmap()

        # Finally print the information
        if not self.quiet:
            self.print_info()

    def close(self):
        self.file_obj.close()

    def _get_type_string(self, attr, data_type):
        """Get the enumerated-data_type as string
        """
        val = getattr(self, attr)  # No error checking
        # print(attr, data_type, val)
        if data_type is None:
            return val
        else:
            return data_type(val).name

    def _read_type(self, type, size=1):
        """ Unpack struct data for certain type
        """
        if type in ["int16", "int32", "int64", "float", "double"]:
            if size > 1:
                raise NotImplementedError(
                    "Does not support read number type with size >1")
            # unpack into unsigned values
            fmt_out = LenType["s_" + type].value
            fmt_in = LenType["l_" + type].value
            return struct.unpack(fmt_out, self.file_obj.read(fmt_in * size))[0]
        elif type == "utf8":
            # Read utf8 string with determined size block
            return self.file_obj.read(size).decode("utf8").replace("\x00", "")
        else:
            raise ValueError("Unknown data length format!")

    def _locate_single_block(self, pos):
        """Get block information starting at pos
        """
        self.file_obj.seek(pos)
        block_name = self.file_obj.read(0x4).decode("ascii")
        if len(block_name) < 4:
            raise EOFError
        block_uid = self._read_type("int32")
        block_size = self._read_type("int64")
        return block_name, block_uid, block_size

    def _locate_all_blocks(self):
        """Get information for all data blocks and store them inside self.block_info
        """
        curpos = 0
        finished = False
        while not finished:
            try:
                block_name, block_uid, block_size = self._locate_single_block(
                    curpos)
                # print(block_name, block_uid, block_size)
                self.block_info[block_name] = (block_uid, curpos, block_size)
                curpos += block_size
            except (EOFError, UnicodeDecodeError):
                finished = True

    def _treat_block_data(self, block_name):
        """Get data according to specific block name
        """
        if block_name not in self.block_info.keys():
            print("Block name {0} not present in current measurement".
                  format(block_name), file=stderr)
            return
        actions = {
            "WDF1": ("_parse_header", ()),
            "DATA": ("_parse_spectra", ()),
            "XLST": ("_parse_xylist", ("X")),
            "YLST": ("_parse_xylist", ("Y")),
            "ORGN": ("_parse_orgin_list", ()),
            "WMAP": ("_parse_wmap", ()),
            "WHTL": ("_parse_img", ()),
        }
        func_name, val = actions[block_name]
        getattr(self, func_name)(*val)

    # The method for reading the info in the file header

    def _parse_header(self):
        """Solve block WDF1
        """
        self.file_obj.seek(0)   # return to the head
        # Must make the conversion under python3
        block_ID = self.file_obj.read(Offsets.block_id).decode("ascii")
        block_UID = self._read_type("int32")
        block_len = self._read_type("int64")
        # First block must be "WDF1"
        if (block_ID != "WDF1") or (block_UID != 0 and block_UID != 1) \
           or (block_len != 512):
            raise ValueError("The wdf file format is incorrect!")
        # TODO what are the digits in between?

        # The keys from the header
        self.file_obj.seek(Offsets.measurement_info)  # space
        self.point_per_spectrum = self._read_type("int32")
        self.capacity = self._read_type("int64")
        self.count = self._read_type("int64")
        # If count < capacity, this measurement is not completed
        self.is_completed = (self.count == self.capacity)
        self.accumulation_count = self._read_type("int32")
        self.ylist_length = self._read_type("int32")
        self.xlist_length = self._read_type("int32")
        self.data_origin_count = self._read_type("int32")
        self.application_name = self._read_type("utf8", 24)  # Must be "WiRE"
        for i in range(4):
            self.application_version[i] = self._read_type("int16")
        self.scan_type = self._read_type("int32")
        self.measurement_type = self._read_type("int32")
        # For the units
        self.file_obj.seek(Offsets.spectral_info)
        self.spectral_units = self._read_type("int32")
        self.laser_length = convert_wl(self._read_type("float"))
        # Username and title
        self.file_obj.seek(Offsets.file_info)
        self.username = self._read_type("utf8",
                                        Offsets.usr_name -
                                        Offsets.file_info)
        self.title = self._read_type("utf8",
                                     Offsets.data_block -
                                     Offsets.usr_name)

    def _parse_xylist(self, dir):
        """Get information from XLST or YLST blocks
        """
        if not dir.upper() in ["X", "Y"]:
            raise ValueError("Direction argument `dir` must be X or Y!")
        name = dir.upper() + "LST"
        uid, pos, size = self.block_info[name]
        offset = Offsets.block_data
        self.file_obj.seek(pos + offset)
        setattr(self, "{0}list_type".format(dir.lower()),
                self._read_type("int32"))
        setattr(self, "{0}list_units".format(dir.lower()),
                self._read_type("int32"))
        size = getattr(self, "{0}list_length".format(dir.lower()))
        if size == 0:           # Possibly not started
            raise ValueError("{0}-List possibly not initialized!".
                             format(dir.upper()))

        # self.file_obj.seek(pos + offset)
        data = numpy.fromfile(self.file_obj, dtype="float32", count=size)
        setattr(self, "{0}data".format(dir.lower()), data)
        return

    def _parse_spectra(self, start=0, end=-1):
        """Get information from DATA block
        """
        if end == -1:           # take all spectra
            end = self.count-1
        if (start not in range(self.count)) or (end not in range(self.count)):
            raise ValueError("Wrong start and end indices of spectra!")
        if start > end:
            raise ValueError("Start cannot be larger than end!")

        # Determine start position
        uid, pos, size = self.block_info["DATA"]
        pos_start = pos + Offsets.block_data + LenType["l_float"].value * \
            start * self.point_per_spectrum
        n_row = end - start + 1
        self.file_obj.seek(pos_start)
        spectra_data = numpy.fromfile(
            self.file_obj, dtype="float32",
            count=n_row * self.point_per_spectrum)
        # if len(spectra_data.shape) > 1:
        # The spectra is only 1D array
        # spectra_data = spectra_data.reshape(
        # n_row, spectra_data.size // n_row)
        self.spectra = spectra_data
        return

    def _parse_orgin_list(self):
        """Get information from OriginList
        Set the following attributes:
        `self.origin_list_header`: 2D-array
        `self.origin_list`: origin list
        """
        # First confirm origin list type
        uid, pos, size = self.block_info["ORGN"]
        self.origin_list_header = [[None, ] * 5
                                   for i in range(self.data_origin_count)]
        self.xpos = numpy.zeros(self.count)
        self.ypos = numpy.zeros(self.count)
        list_increment = Offsets.origin_increment + \
            LenType.l_double.value * self.capacity
        curpos = pos + Offsets.origin_info

        for i in range(self.data_origin_count):
            self.file_obj.seek(curpos)
            p1 = self._read_type("int32")
            p2 = self._read_type("int32")
            s = self._read_type("utf8", 0x10)
            # First index: is the list x, or y pos?
            self.origin_list_header[i][0] = (p1 >> 31 & 0b1) == 1
            # Second: Data type of the row
            self.origin_list_header[i][1] = DataType(p1 & ~(0b1 << 31))
            # Third: Unit
            self.origin_list_header[i][2] = UnitType(p2)
            # Fourth: annotation
            self.origin_list_header[i][3] = s
            # Last: the actual data
            # array = numpy.empty(self.count)
            array = numpy.array([self._read_type("double")
                                 for i in range(self.count)])
            self.origin_list_header[i][4] = array
            # Set self.xpos or self.ypos
            if self.origin_list_header[i][1] == DataType.X:
                self.xpos = array
            elif self.origin_list_header[i][1] == DataType.Y:
                self.ypos = array
            else:
                pass
            curpos += list_increment

    def _parse_wmap(self):
        """Get information about mapping in StreamLine and StreamLineHR
        """
        try:
            uid, pos, size = self.block_info["WMAP"]
        except KeyError:
            print("Current measurement does not contain mapping information!",
                  file=stderr)
            return

        self.file_obj.seek(pos + Offsets.wmap_origin)
        x_start = self._read_type("float")
        if not numpy.isclose(x_start, self.xpos[0], rtol=1e-4):
            raise ValueError("WMAP Xpos is not same as in ORGN!")
        y_start = self._read_type("float")
        if not numpy.isclose(y_start, self.ypos[0], rtol=1e-4):
            raise ValueError("WMAP Ypos is not same as in ORGN!")
        unknown1 = self._read_type("float")
        x_pad = self._read_type("float")
        y_pad = self._read_type("float")
        unknown2 = self._read_type("float")
        # for i in range(9):
        #     print(i, self._read_type("int32"))
        #     self.file_obj.seek(pos + Offsets.wmap_origin + i * 4)
        #     print(i, self._read_type("float"))
        # self.file_obj.seek(pos + Offsets.wmap_wh)
        self.spectra_w = self._read_type("int32")
        self.spectra_h = self._read_type("int32")
        # print(self.spectra_w, self.spectra_h)
        # print(len(self.xpos), len(self.ypos))
        if len(self.xpos) > 1:
            if not numpy.isclose(x_pad, self.xpos[1] - self.xpos[0],
                                 rtol=1e-4):
                raise ValueError("WMAP Xpad is not same as in ORGN!")
        # If ypos smaller than spectra_w,
        # posssibly not even finished single line scan
        if len(self.ypos) >= self.spectra_w:
            if self.spectra_h > 1:
                loc = self.spectra_w
            else:
                loc = 1
            if not numpy.isclose(y_pad, self.ypos[loc] - self.ypos[0],
                                 rtol=1e-4):
                raise ValueError("WMAP Ypad is not same as in ORGN!")

        self.map_info = (x_start, y_start, x_pad, y_pad)

    def _parse_img(self):
        """Extract the white-light JPEG image
           The size of while-light image is coded in its EXIF
           Use PIL to parse the EXIF information
        """
        try:
            uid, pos, size = self.block_info["WHTL"]
        except KeyError:
            print("The wdf file does not contain an image",
                  file=stderr)
            return

        # Read the bytes. `self.img` is a wrapped IO object mimicking a file
        self.file_obj.seek(pos + Offsets.jpeg_header)
        img_bytes = self.file_obj.read(size - Offsets.jpeg_header)
        self.img = io.BytesIO(img_bytes)
        # Handle image dimension if PIL is present
        if PIL is not None:
            pil_img = PIL.Image.open(self.img)
            exif_header = dict(pil_img.getexif())
            try:
                # Get the width and height of image
                w_ = exif_header[ExifTags.FocalPlaneXResolution]
                h_ = exif_header[ExifTags.FocalPlaneYResolution]
                x_org_, y_org_ = exif_header[ExifTags.FocalPlaneXYOrigins]
                # The dimensions (width, height)
                # with unit `img_dimension_unit`
                self.img_dimensions = numpy.array([w_[0] / w_[1],
                                                   h_[0] / h_[1]])
                # Origin of image is at upper right corner
                self.img_origins = numpy.array([x_org_[0] / x_org_[1],
                                                y_org_[0] / y_org_[1]])
                # Default is microns (5)
                self.img_dimension_unit = UnitType(
                    exif_header[ExifTags.FocalPlaneResolutionUnit])
                # Give the box for cropping
                # Following the PIL manual
                # (left, upper, right, lower)
                self.img_cropbox = self._calc_crop_box()

            except KeyError:
                print("Some keys in white light image header cannot be read!",
                      file=stderr)
        return

    def _calc_crop_box(self):
        """Helper function to calculate crop box
        """
        def _proportion(x, minmax, pixels):
            """Get proportional pixels"""
            min, max = minmax
            return int(pixels * (x - min) / (max - min))

        pil_img = PIL.Image.open(self.img)
        w_, h_ = self.img_dimensions
        x0_, y0_ = self.img_origins
        pw = pil_img.width
        ph = pil_img.height
        map_xl = self.xpos.min()
        map_xr = self.xpos.max()
        map_yt = self.ypos.min()
        map_yb = self.ypos.max()
        left = _proportion(map_xl, (x0_, x0_ + w_), pw)
        right = _proportion(map_xr, (x0_, x0_ + w_), pw)
        top = _proportion(map_yt, (y0_, y0_ + h_), ph)
        bottom = _proportion(map_yb, (y0_, y0_ + h_), ph)
        return (left, top, right, bottom)

    def _reshape_spectra(self):
        """Reshape spectra into w * h * self.point_per_spectrum
        """
        if not self.is_completed:
            print("The measurement is not completed, " +
                  "will try to reshape spectra into count * pps.", file=stderr)
            try:
                self.spectra = numpy.reshape(self.spectra,
                                             (self.count,
                                              self.point_per_spectrum))
            except ValueError:
                print("Reshaping spectra array failed. Please check.",
                      file=stderr)
            return
        elif all(hasattr(self, "spectra_" + n) for n in ("w", "h")):
            # Is a mapping
            if self.spectra_w * self.spectra_h != self.count:
                print("Mapping information from WMAP not corresponding to ORGN! " +
                      "Will not reshape the spectra", file=stderr)
                return
            elif self.spectra_w * self.spectra_h * self.point_per_spectrum \
                    != len(self.spectra):
                print("Mapping information from WMAP not corresponding to DATA! " +
                      "Will not reshape the spectra", file=stderr)
                return
            else:
                # Should be h rows * w columns. numpy.ndarray is row first
                # Reshape to 3D matrix when doing 2D mapping
                if (self.spectra_h > 1) and (self.spectra_w > 1):
                    self.spectra = numpy.reshape(self.spectra,
                                                 (self.spectra_h, self.spectra_w,
                                                  self.point_per_spectrum))
                # otherwise it is a line scan or series
                else:
                    self.spectra = numpy.reshape(self.spectra,
                                                 (self.count,
                                                  self.point_per_spectrum))
        else:
            return

    def print_info(self):
        """Print information of the wdf file
        """
        if not self.quiet:
            s = []
            s.append("{0:>24s}:\t{1}".format("Title", self.title))
            s.append("{0:>17s} version:\t{1}.{2}.{3}.{4}".
                     format(self.application_name,
                            *self.application_version))

            s.append("{0:>24s}:\t{1} nm".format("Laser Wavelength",
                                                self.laser_length))
            for a, t in zip(["count", "capacity", "point_per_spectrum",
                             "scan_type", "measurement_type",
                             "spectral_units",
                             "xlist_units", "xlist_length",
                             "ylist_units", "ylist_length",
                             "data_origin_count"],

                            [None, None, None,
                             ScanType, MeasurementType,
                             UnitType,
                             UnitType, None,
                             UnitType, None, None, ]):
                sname = convert_attr_name(a)
                val = self._get_type_string(a, t)
                s.append("{0:>24s}:\t{1}".format(sname, val))
            print("\n".join(s))


if __name__ == '__main__':
    import sys
    try:
        fn = sys.argv[1]
        # print(fn)
        wdf = WDFReader(fn)
        # for s in dir(wdf):
        # if "__" not in s:
        # print(s, getattr(wdf, s))
        wdf.print_info()
        print(wdf.spectra.shape)
        # print(wdf.spectra_w, wdf.spectra_h)
        # xdata = wdf.get_xdata()
        # ydata = wdf.get_ydata()
        # spectra = wdf.get_spectra()
        # print(wdf.xdata)
        # print(wdf.ydata)
        # print(wdf.spectra)
    except IndexError:
        raise
    # plt.plot(xdata, spectra)
    # plt.show()
