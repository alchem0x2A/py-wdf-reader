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
    from PIL import Image
    from PIL.TiffImagePlugin import IFDRational
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
    `WHTL`: Whilte light image

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
    xlist_unit (int) : See unit_types
    xlist_length (int): Size for the xlist
    xdata (numpy.array): x-axis data
    ylist_type (int): Same as xlist_type
    ylist_unit (int): Same as xlist_unit
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

    def __init__(self, file_name, debug=False):
        try:
            self.file_obj = open(str(file_name), "rb")
        except IOError:
            raise IOError("File {0} does noe exist!".format(file_name))
        # Initialize the properties for the wdfReader class
        self.title = ""
        self.username = ""
        self.measurement_type = None
        self.scan_type = None
        self.laser_length = None
        self.count = None
        self.spectral_unit = None
        self.xlist_type = None
        self.xlist_unit = None
        self.ylist_type = None
        self.ylist_unit = None
        self.point_per_spectrum = None
        self.data_origin_count = None
        self.capacity = None
        self.application_name = ""
        self.application_version = [None]*4
        self.xlist_length = 0
        self.ylist_length = 0
        self.accumulation_count = None
        self.block_info = {}    # each key has value (uid, offset, size)
        self.is_completed = False
        self.debug = debug
        # Parse the header section in the wdf file
        self.__locate_all_blocks()
        # Parse individual blocks
        self.__treat_block_data("WDF1")
        self.__treat_block_data("DATA")
        self.__treat_block_data("XLST")
        self.__treat_block_data("YLST")
        self.__treat_block_data("ORGN")
        self.__treat_block_data("WMAP")
        self.__treat_block_data("WHTL")

        # Reshape spectra after reading mapping information
        self.__reshape_spectra()
        # self._parse_wmap()

        # Finally print the information
        if self.debug:
            print(("File Metadata").center(80, "="),
                  file=stderr)
            self.print_info(file=stderr)
            print("=" * 80, file=stderr)

    def close(self):
        self.file_obj.close()
        if hasattr(self, "img"):
            self.img.close()

    def __get_type_string(self, attr, data_type):
        """Get the enumerated-data_type as string
        """
        val = getattr(self, attr)  # No error checking
        if data_type is None:
            return val
        else:
            return data_type(val).name

    def __read_type(self, type, size=1):
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

    def __locate_single_block(self, pos):
        """Get block information starting at pos
        """
        self.file_obj.seek(pos)
        block_name = self.file_obj.read(0x4).decode("ascii")
        if len(block_name) < 4:
            raise EOFError
        block_uid = self.__read_type("int32")
        block_size = self.__read_type("int64")
        return block_name, block_uid, block_size

    def __locate_all_blocks(self):
        """Get information for all data blocks and store them inside self.block_info
        """
        curpos = 0
        finished = False
        while not finished:
            try:
                block_name, block_uid, block_size = self.__locate_single_block(
                    curpos)
                self.block_info[block_name] = (block_uid, curpos, block_size)
                curpos += block_size
            except (EOFError, UnicodeDecodeError):
                finished = True

    def __treat_block_data(self, block_name):
        """Get data according to specific block name
        """
        if block_name not in self.block_info.keys():
            if self.debug:
                print("Block name {0} not present in current measurement".
                      format(block_name), file=stderr)
            return
        # parse individual blocks with names
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
        block_UID = self.__read_type("int32")
        block_len = self.__read_type("int64")
        # First block must be "WDF1"
        if (block_ID != "WDF1") \
           or (block_UID != 0 and block_UID != 1) \
           or (block_len != Offsets.data_block):
            raise ValueError("The wdf file format is incorrect!")
        # TODO what are the digits in between?

        # The keys from the header
        self.file_obj.seek(Offsets.measurement_info)  # space
        self.point_per_spectrum = self.__read_type("int32")
        self.capacity = self.__read_type("int64")
        self.count = self.__read_type("int64")
        # If count < capacity, this measurement is not completed
        self.is_completed = (self.count == self.capacity)
        self.accumulation_count = self.__read_type("int32")
        self.ylist_length = self.__read_type("int32")
        self.xlist_length = self.__read_type("int32")
        self.data_origin_count = self.__read_type("int32")
        self.application_name = self.__read_type("utf8", 24)  # Must be "WiRE"
        for i in range(4):
            self.application_version[i] = self.__read_type("int16")
        self.scan_type = ScanType(self.__read_type("int32"))
        self.measurement_type = MeasurementType(self.__read_type("int32"))
        # For the units
        self.file_obj.seek(Offsets.spectral_info)
        self.spectral_unit = UnitType(self.__read_type("int32"))
        self.laser_length = convert_wl(self.__read_type("float"))  # in nm
        # Username and title
        self.file_obj.seek(Offsets.file_info)
        self.username = self.__read_type("utf8",
                                         Offsets.usr_name -
                                         Offsets.file_info)
        self.title = self.__read_type("utf8",
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
                DataType(self.__read_type("int32")))
        setattr(self, "{0}list_unit".format(dir.lower()),
                UnitType(self.__read_type("int32")))
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
            end = self.count - 1
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
        # All possible to have x y and z positions!
        self.xpos = numpy.zeros(self.count)
        self.ypos = numpy.zeros(self.count)
        self.zpos = numpy.zeros(self.count)
        list_increment = Offsets.origin_increment + \
            LenType.l_double.value * self.capacity
        curpos = pos + Offsets.origin_info

        for i in range(self.data_origin_count):
            self.file_obj.seek(curpos)
            p1 = self.__read_type("int32")
            p2 = self.__read_type("int32")
            s = self.__read_type("utf8", 0x10)
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
            array = numpy.array([self.__read_type("double")
                                 for i in range(self.count)])
            self.origin_list_header[i][4] = array
            # Set self.xpos or self.ypos
            if self.origin_list_header[i][1] == DataType.Spatial_X:
                self.xpos = array
                self.xpos_unit = self.origin_list_header[i][2]
            elif self.origin_list_header[i][1] == DataType.Spatial_Y:
                self.ypos = array
                self.ypos_unit = self.origin_list_header[i][2]
            elif self.origin_list_header[i][1] == DataType.Spatial_Z:
                self.zpos = array
                self.zpos_unit = self.origin_list_header[i][2]
            else:
                pass
            curpos += list_increment

    def _parse_wmap(self):
        """Get information about mapping in StreamLine and StreamLineHR
        """
        try:
            uid, pos, size = self.block_info["WMAP"]
        except KeyError:
            if self.debug:
                print(("Current measurement does not"
                       " contain mapping information!"),
                      file=stderr)
            return

        self.file_obj.seek(pos + Offsets.wmap_origin)
        x_start = self.__read_type("float")
        if not numpy.isclose(x_start, self.xpos[0], rtol=1e-4):
            raise ValueError("WMAP Xpos is not same as in ORGN!")
        y_start = self.__read_type("float")
        if not numpy.isclose(y_start, self.ypos[0], rtol=1e-4):
            raise ValueError("WMAP Ypos is not same as in ORGN!")
        unknown1 = self.__read_type("float")
        x_pad = self.__read_type("float")
        y_pad = self.__read_type("float")
        unknown2 = self.__read_type("float")
        spectra_w = self.__read_type("int32")
        spectra_h = self.__read_type("int32")

        # Determine if the xy-grid spacing is same as in x_pad and y_pad
        if (len(self.xpos) > 1) and (len(self.ypos) > 1):
            xdist = numpy.abs(self.xpos - self.xpos[0])
            ydist = numpy.abs(self.ypos - self.ypos[0])
            xdist = xdist[numpy.nonzero(xdist)]
            ydist = ydist[numpy.nonzero(ydist)]
            # Get minimal non-zero padding in the grid
            try:
                x_pad_grid = numpy.min(xdist)
            except ValueError:
                x_pad_grid = 0

            try:
                y_pad_grid = numpy.min(ydist)
            except ValueError:
                y_pad_grid = 0

        self.map_shape = (spectra_w, spectra_h)
        self.map_info = dict(x_start=x_start,
                             y_start=y_start,
                             x_pad=x_pad,
                             y_pad=y_pad,
                             x_span=spectra_w * x_pad,
                             y_span=spectra_h * y_pad,
                             x_unit=self.xpos_unit,
                             y_unit=self.ypos_unit)

    def _parse_img(self):
        """Extract the white-light JPEG image
           The size of while-light image is coded in its EXIF
           Use PIL to parse the EXIF information
        """
        try:
            uid, pos, size = self.block_info["WHTL"]
        except KeyError:
            if self.debug:
                print("The wdf file does not contain an image",
                      file=stderr)
            return

        # Read the bytes. `self.img` is a wrapped IO object mimicking a file
        self.file_obj.seek(pos + Offsets.jpeg_header)
        img_bytes = self.file_obj.read(size - Offsets.jpeg_header)
        self.img = io.BytesIO(img_bytes)
        # Handle image dimension if PIL is present
        if PIL is not None:
            pil_img = Image.open(self.img)
            exif_header = dict(pil_img.getexif())
            try:
                # Get the width and height of image
                w_ = exif_header[ExifTags.FocalPlaneXResolution]
                h_ = exif_header[ExifTags.FocalPlaneYResolution]
                x_org_, y_org_ = exif_header[ExifTags.FocalPlaneXYOrigins]

                def rational2float(v):
                    """ Pillow<7.2.0 returns tuple, Pillow>=7.2.0 returns IFDRational """
                    if not isinstance(v, IFDRational):
                        return v[0] / v[1]
                    return float(v)

                w_, h_ = rational2float(w_), rational2float(h_)
                x_org_, y_org_ = rational2float(x_org_), rational2float(y_org_)

                # The dimensions (width, height)
                # with unit `img_dimension_unit`
                self.img_dimensions = numpy.array([w_,
                                                   h_])
                # Origin of image is at upper right corner
                self.img_origins = numpy.array([x_org_,
                                                y_org_])
                # Default is microns (5)
                self.img_dimension_unit = UnitType(
                    exif_header[ExifTags.FocalPlaneResolutionUnit])
                # Give the box for cropping
                # Following the PIL manual
                # (left, upper, right, lower)
                self.img_cropbox = self.__calc_crop_box()

            except KeyError:
                if self.debug:
                    print(("Some keys in white light image header"
                           " cannot be read!"),
                          file=stderr)
        return

    def __calc_crop_box(self):
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

    def __reshape_spectra(self):
        """Reshape spectra into w * h * self.point_per_spectrum
        """
        if not self.is_completed:
            if self.debug:
                print(("The measurement is not completed, "
                       "will try to reshape spectra into count * pps."),
                      file=stderr)
            try:
                self.spectra = numpy.reshape(self.spectra,
                                             (self.count,
                                              self.point_per_spectrum))
            except ValueError:
                if self.debug:
                    print("Reshaping spectra array failed. Please check.",
                          file=stderr)
            return
        elif hasattr(self, "map_shape"):
            # Is a mapping
            spectra_w, spectra_h = self.map_shape
            if spectra_w * spectra_h != self.count:
                if self.debug:
                    print(("Mapping information from WMAP not"
                           " corresponding to ORGN! "
                           "Will not reshape the spectra"),
                          file=stderr)
                return
            elif spectra_w * spectra_h * self.point_per_spectrum \
                    != len(self.spectra):
                if self.debug:
                    print(("Mapping information from WMAP"
                           " not corresponding to DATA! "
                           "Will not reshape the spectra"),
                          file=stderr)
                return
            else:
                # Should be h rows * w columns. numpy.ndarray is row first
                # Reshape to 3D matrix when doing 2D mapping
                if (spectra_h > 1) and (spectra_w > 1):
                    self.spectra = numpy.reshape(self.spectra,
                                                 (spectra_h, spectra_w,
                                                  self.point_per_spectrum))
                # otherwise it is a line scan
                else:
                    self.spectra = numpy.reshape(self.spectra,
                                                 (self.count,
                                                  self.point_per_spectrum))
        # For any other type of measurement, reshape into (counts, point_per_spectrum)
        # example: series scan
        elif self.count > 1:
            self.spectra = numpy.reshape(self.spectra,
                                         (self.count,
                                          self.point_per_spectrum))
        else:
            return

    def print_info(self, **params):
        """Print information of the wdf file
        """
        s = []
        s.append(u"{0:>24s}:\t{1}".format("Title", self.title))
        s.append(u"{0:>17s} version:\t{1}.{2}.{3}.{4}".
                 format(self.application_name,
                        *self.application_version))

        s.append(u"{0:>24s}:\t{1} nm".format("Laser Wavelength",
                                            self.laser_length))
        for a in ("count", "capacity", "point_per_spectrum",
                  "scan_type", "measurement_type",
                  "spectral_unit",
                  "xlist_unit", "xlist_length",
                  "ylist_unit", "ylist_length",
                  "xpos_unit", "ypos_unit"):
            sname = convert_attr_name(a)
            # Use explicit string conversion to replace
            try:
                val = str(getattr(self, a))
            except AttributeError:
                continue
            s.append("{0:>24s}:\t{1}".format(sname, val))
        text = u"\n".join(s)
        print(text, **params)


if __name__ == '__main__':
    raise NotImplementedError("Please dont run this module as a script!")
