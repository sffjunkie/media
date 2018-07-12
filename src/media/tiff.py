# Copyright (c) 2009-2014 Simon Kennedy <sffjunkie+code@gmail.com>

import os
import struct
from io import BytesIO
from datetime import datetime

from mogul.media import localize
_ = localize()

from mogul.media import MediaHandler
import mogul.media.xmp
import mogul.media.psd
from mogul.media.image import Image
from mogul.media import MediaContainer, MediaEntry, MediaStream, \
        ImageStreamInfo, Tag, TagTarget, TagGroup, MediaHandlerError
from mogul.media.element import Element

class TIFFError(Exception):
    pass


TIFF_Compression = {1: 'None', 2: 'CCITT Group 3', 32773: 'PackBits'}
TIFF_ResolutionUnits = {1: 'None', 2: 'Inch', 3: 'Inch'}
TIFF_FillOrder = {1: 'Lower Column First', 2: 'Lower Column Last'}
TIFF_GrayResponseUnit = {1: 'tenths', 2: 'hundredths', 3: 'thousandths',
                         4: 'ten-thousandths', 5: 'hundred-thousandths'}
TIFF_SubFileType = {0: 'Reduced Resolution', 1: 'Multipage', 2: 'Transparency Mask'}

class TIFFHandler(MediaHandler):
    """A handler for TIFF files"""
    
    def __init__(self, log_indent_level=0):
        super(TIFFHandler, self).__init__(log_indent_level)
        
        self.filename = ''
        self.endian = '>'
        
        self._media_entry = None
        
        self._elements = {
            254: Element(_('New Subfile Type'), key='subfile_type'),
            255: Element(_('Subfile Type'), key='subfile_type'),
            256: Element(_('Image Width'), key='image_width'),
            257: Element(_('Image Length'), key='image_height'),
            258: Element(_('Bits Per Sample'), key='bits_per_sample'),
            259: Element(_('Compression'), key='compression'),
            262: Element(_('Photometric Interpretation'), key='photometric_interpretation'),
            263: Element(_('Thresholding'), key='thresholding'),
            264: Element(_('Cell Width'), key='cell_width'),
            265: Element(_('Cell Length'), key='cell_length'),
            266: Element(_('Fill Order')),
            269: Element(_('Document Name'), key='name'),
            270: Element(_('Image Description'), key='description'),
            271: Element(_('Make'), key='make'),
            272: Element(_('Model'), key='model'),
            273: Element(_('Strip Offsets'), key='strip_offsets'),
            274: Element(_('Orientation'), key='orientation'),
            277: Element(_('Samples Per Pixel'), key='samples_per_pixel'),
            278: Element(_('Rows Per Strip'), key='rows_per_strip'),
            279: Element(_('Strip Byte Counts'), key='strip_byte_counts'),
            280: Element(_('Minimum Sample Value')),
            281: Element(_('Maximum Sample Value')),
            282: Element(_('X Resolution'), key='resolution_x'),
            283: Element(_('Y Resolution'), key='resolution_y'),
            284: Element(_('Planar Configuration')),
            285: Element(_('Page Name'), key='page_name'),
            286: Element(_('X Position'), key='position_x'),
            287: Element(_('Y Position'), key='position_y'),
            288: Element(_('Free Offsets')),
            289: Element(_('Free Bytes Count')),
            290: Element(_('Gray Response Unit')),
            291: Element(_('Gray Response Curve')),
            292: Element(_('T4 Options')),
            293: Element(_('T6 Options')),
            296: Element(_('Resolution Unit'), key='resolution_unit'),
            297: Element(_('Page Number')),
            301: Element(_('Transfer Function')),
            305: Element(_('Software'), key="software"),
            306: Element(_('Date/Time'), 'datetime', key='date_time'),
            315: Element(_('Artist'), key='artist'),
            316: Element(_('Host Computer'), key='host_computer'),
            317: Element(_('Predictor')),
            318: Element(_('White Point'), key='white_point'),
            319: Element(_('Primary Chromatics'), key='primary_chromatics'),
            320: Element(_('Colour Map'), key='colour_map'),
            321: Element(_('Halftone Units')),
            322: Element(_('Tile Width')),
            323: Element(_('Tile Length')),
            324: Element(_('Tile Offsets')),
            325: Element(_('Tile Byte Counts')),
            330: Element(_('Sub IFDs'), 'subifd'),
            332: Element(_('Ink Sets')),
            333: Element(_('Ink Names')),
            334: Element(_('Number Of Inks')),
            336: Element(_('Dot Range')),
            337: Element(_('Target Printer')),
            338: Element(_('Extra Samples')),
            339: Element(_('Sample Format')),
            340: Element(_('S Min Sample Value')),
            341: Element(_('S Max Sample Value')),
            342: Element(_('Transfer Range')),
            343: Element(_('Clip Path')),
            344: Element(_('X Clip Path Units')),
            345: Element(_('Y Clip Path Units')),
            346: Element(_('Indexed')),
            347: Element(_('JPEG Quantization or Huffman Tables')),
            351: Element(_('OPI')),
            400: Element(_('Global Parameters IFD')),
            401: Element(_('Profile Type')),
            402: Element(_('Fax Profile')),
            403: Element(_('Coding Methods')),
            404: Element(_('Version Year')),
            405: Element(_('Mode Number')),
            433: Element(_('Decode')),
            434: Element(_('Default Image Color')),
            512: Element(_('JPEG Processor')),
            513: Element(_('JPEG Interchange Format')),
            514: Element(_('JPEG Interchange Format Length')),
            515: Element(_('JPEG Restart Interval')),
            517: Element(_('JPEG Lossless Predictors')),
            518: Element(_('JPEG Point Transforms')),
            519: Element(_('JPEG Q Tables')),
            520: Element(_('JPEG DC Tables')),
            521: Element(_('JPEG AC Tables')),
            529: Element(_('YCbCr Coefficients')),
            530: Element(_('YCbCr Sub-Sampling')),
            531: Element(_('YCbCr Positioning')),
            532: Element(_('Reference Black/White')),
            559: Element(_('Strip Row Counts')),
            700: Element(_('XMP'), 'xmp'),
            # Tags over 32768 are private/not part of TIFF Baseline.
            32781: Element(_('OPI Related')),
            32932: Element(_('Wang Annotation')),
            33421: Element(_('CFA Repeat Pattern Dim')),
            33422: Element(_('CFA Pattern')),
            33423: Element(_('Battery Level'), key='battery_level'),
            33432: Element(_('Copyright'), key='copyright'),
            33434: Element(_('Exposure Time'), key='exposure_time'),
            33437: Element(_('F Number'), key='f_stop'),
            33445: Element(_('MD File Tag')),
            33446: Element(_('MD Scale Pixel')),
            33447: Element(_('MD Colour Table')),
            33448: Element(_('MD Lab Name')),
            33449: Element(_('MD Sample Info')),
            33450: Element(_('MD Preparation Date'), 'mddate'),
            33451: Element(_('MD Preparation Time'), 'mdtime'),
            33452: Element(_('MD File Units')),
            33550: Element(_('Model Pixel Scale Tag')),
            33723: Element(_('IPTC'), 'iptc'),
            33918: Element(_('INGR Packet Data Tag')),
            33919: Element(_('INGR Flag Registers')),
            33920: Element(_('IrasB Transformation Matrix')),
            33922: Element(_('Model Tiepoint Tag')),
            34264: Element(_('Model Transformation Tag')),
            34377: Element(_('Photoshop'), 'photoshop'),
            34665: Element(_('Exif IFD Offset'), 'exif_ifd'),
            34675: Element(_('ICC Profile')),
            34732: Element(_('Image Layer')),
            34735: Element(_('Geo Key Directory Tag')),
            34736: Element(_('Geo Double Params Tag')),
            34737: Element(_('Geo Ascii Params Tag')),
            34850: Element(_('Exposure Program')),
            34852: Element(_('Spectral Sensitivity')),
            34853: Element(_('GPS'), 'gps'),
            34855: Element(_('ISO Speed Ratings')),
            34856: Element(_('OECF')),
            34857: Element(_('Interlace')),
            34858: Element(_('Time Zone Offset')),
            34859: Element(_('Self Timer Mode')),
            34864: Element(_('Sensitivity Type')),
            34865: Element(_('Standard Output Sensitivity')),
            34866: Element(_('Recommended Exposure Index')),
            34867: Element(_('ISO Speed'), key='iso_speed'),
            34868: Element(_('ISO Speed Latitude yyy')),
            34869: Element(_('ISO Speed Latitude zzz')),
            34908: Element(_('Hylafax Fax Receive Parameters')),
            34909: Element(_('Hylafax Fax Sub Address')),
            34908: Element(_('Hylafax Fax Receive Time')),
            36864: Element(_('Exif Version')),
            36867: Element(_('Date Time Original')),
            36868: Element(_('Date Time Digitized')),
            37121: Element(_('Components Configuration')),
            37122: Element(_('Compressed Bits Per Pixel')),
            37377: Element(_('Shutter Speed')),
            37378: Element(_('Aperture Value')),
            37379: Element(_('Brightness')),
            37380: Element(_('Exposure Bias')),
            37381: Element(_('Max Aperture')),
            37382: Element(_('Subject Distance')),
            37383: Element(_('Metering Mode')),
            37384: Element(_('Light Source')),
            37385: Element(_('Flash')),
            37386: Element(_('Focal Length')),
            37387: Element(_('Flash Energy')),
            37388: Element(_('Spatial Frequency Response')),
            37389: Element(_('Noise')),
            37390: Element(_('Focal Plane X Resolution')),
            37391: Element(_('Focal Plane Y Resolution')),
            37392: Element(_('Focal Plane Resolution Unit')),
            37393: Element(_('Image Number')),
            37394: Element(_('Security Classification')),
            37395: Element(_('Image History')),
            37396: Element(_('Subject Area')),
            37397: Element(_('Exposure Index')),
            37398: Element(_('TIFF/EP Standard ID')),
            37399: Element(_('Sensing Method')),
            37500: Element(_('Maker Note')),
            37510: Element(_('User Comment')),
            37520: Element(_('Sub Second Time')),
            37521: Element(_('Sub Second Time Original')),
            37522: Element(_('Sub Second Time Digitized')),

            37677: Element('OCR Text', 'ocr_text'),
            37678: Element('OCR Data', 'ocr_data'),
            
            37679: Element(_('Page Content')),
            37680: Element(_('OLE Dump')),
            37681: Element(_('Content Position')),
            
            37724: Element(_('Image Source Data')),
            40091: Element(_('XP Title'), 'ucs2'),
            40092: Element(_('XP Comment'), 'ucs2'),
            40093: Element(_('XP Author'), 'ucs2'),
            40094: Element(_('XP Keywords'), 'ucs2'),
            40095: Element(_('XP Subject'), 'ucs2'),
            40960: Element(_('Flashpix Version')),
            40961: Element(_('Color Space')),
            40962: Element(_('Pixel X Dimension')),
            40963: Element(_('Pixel Y Dimension')),
            40964: Element(_('Related Sound File')),
            40965: Element(_('Interoperability'), 'i14y'),
            41483: Element(_('Flash Energy')),
            41484: Element(_('Spatial Frequency Response')),
            41486: Element(_('Focal Plane X Resolution')),
            41487: Element(_('Focal Plane Y Resolution')),
            41488: Element(_('Focal Plane Resolution Unit')),
            41492: Element(_('Subject Location')),
            41493: Element(_('Exposure Index')),
            41495: Element(_('Sensing Method')),
            41728: Element(_('File Source')),
            41729: Element(_('Scene Type')),
            41730: Element(_('CFA Pattern')),
            41985: Element(_('Custom Rendered')),
            41986: Element(_('Exposure Mode')),
            41987: Element(_('White Balance')),
            41988: Element(_('Digital Zoom Ratio')),
            41989: Element(_('Focal Length In 35mm')),
            41990: Element(_('Scene Capture Type')),
            41991: Element(_('Gain Control')),
            41992: Element(_('Contrast')),
            41993: Element(_('Saturation')),
            41994: Element(_('Sharpness')),
            41995: Element(_('Device Setting Description')),
            41996: Element(_('Subject Distance Range')),
            42016: Element(_('Image Unique ID')),
            42032: Element(_('Camera Owner Name')),
            42033: Element(_('Body Serial Number')),
            42034: Element(_('Lens Specification')),
            42035: Element(_('Lens Make')),
            42036: Element(_('Lens Model')),
            42037: Element(_('Lens Serial Number')),
            42112: Element(_('GDAL Metadata')),
            42113: Element(_('GDAL No Data')),
            50215: Element(_('Oce Scanjob Description')),
            50216: Element(_('Oce Application Selector')),
            50217: Element(_('Oce Identification Number')),
            50218: Element(_('Oce Imagelogic Characteristics')),
            50706: Element(_('DNG Version')),
            50707: Element(_('DNG Backward Version')),
            50708: Element(_('Unique Camera Model')),
            50709: Element(_('Localized Camera Model')),
            50710: Element(_('CFA Plane Color')),
            50711: Element(_('CFA Layout')),
            50712: Element(_('Linearization Table')),
            50713: Element(_('Black Level Repeat Dim')),
            50714: Element(_('Black Level')),
            50715: Element(_('Black Level Delta H')),
            50716: Element(_('Black Level Delta V')),
            50717: Element(_('White Level')),
            50718: Element(_('Default Scale')),
            50719: Element(_('Default Crop Origin')),
            50720: Element(_('Default Crop Size')),
            50721: Element(_('Color Matrix 1')),
            50722: Element(_('Color Matrix 2')),
            50723: Element(_('Camera Calibration 1')),
            50724: Element(_('Camera Calibration 2')),
            50725: Element(_('Reduction Matrix 1')),
            50726: Element(_('Reduction Matrix 2')),
            50727: Element(_('Analog Balance')),
            50728: Element(_('As Shot Neutral')),
            50729: Element(_('As Shot White XY')),
            50730: Element(_('Baseline Exposure')),
            50731: Element(_('Baseline Noise')),
            50732: Element(_('Baseline Sharpness')),
            50733: Element(_('Bayer Green Split')),
            50734: Element(_('Linear Response Limit')),
            50735: Element(_('Camera Serial Number')),
            50736: Element(_('Lens Info')),
            50737: Element(_('Chroma Blur Radius')),
            50738: Element(_('Anti Alias Strength')),
            50739: Element(_('Shadow Scale')),
            50740: Element(_('DNG Private Data')),
            50741: Element(_('Make Note Safety')),
            50778: Element(_('Calibration Illuminant 1')),
            50779: Element(_('Calibration Illuminant 2')),
            50780: Element(_('Best Quality Scale')),
            50784: Element(_('Alias Meta Data')),
            50827: Element(_('Original RAW File Name')),
            50828: Element(_('Original RAW File Data')),
            50829: Element(_('Active Area')),
            50830: Element(_('Masked Areas')),
            50831: Element(_('As Shot ICC Profile')),
            50832: Element(_('As Shot Profile Matrix')),
            50833: Element(_('Current ICC Profile')),
            50834: Element(_('Current Pre-Profile Matrix')),
            50879: Element(_('Colorimetric Reference')),
            50931: Element(_('Camera Calibration Signature')),
            50932: Element(_('Profile Calibration Signature')),
            50934: Element(_('As Shot Profile Name')),
            50935: Element(_('Noise Reduction Applied')),
            50936: Element(_('Profile Name')),
            50937: Element(_('Profile Hue Saturation Mapping Dimensions')),
            50938: Element(_('Profile Hue Saturation Mapping Data 1')),
            50939: Element(_('Profile Hue Saturation Mapping Data 2')),
            50940: Element(_('Profile Tone Curve')),
            50941: Element(_('Profile Embed Policy')),
            50942: Element(_('Profile Copyright')),
            50964: Element(_('Forward Matrix 1')),
            50965: Element(_('Forward Matrix 2')),
            50966: Element(_('Preview Application Name')),
            50967: Element(_('Preview Application Version')),
            50968: Element(_('Preview Settings Name')),
            50969: Element(_('Preview Settings Digest')),
            50970: Element(_('Preview Colour Space')),
            50971: Element(_('Preview Date Time')),
            50972: Element(_('Raw Image Digest')),
            50973: Element(_('Original Raw File Digest')),
            50974: Element(_('Sub-Tile Block Size')),
            50975: Element(_('Row Interleave Factor')),
            50981: Element(_('Profile Look Table Dimensions')),
            50982: Element(_('Profile Look Table Data')),
            51008: Element(_('Opcode List 1')),
            51009: Element(_('Opcode List 2')),
            51022: Element(_('Opcode List 3')),
            51041: Element(_('Noise Profile'), key='noise_profile'),
        }
        
        self.__gps_tags = {
            0: Element(_('GPS Tag Version')),
            1: Element(_('North or South Latitude')),
            2: Element(_('gpslatitude'), 'gpslatitude'),
            3: Element(_('East or West Longitude')),
            4: Element(_('Longitude'), 'longitude'),
            5: Element(_('Altitude Reference')),
            6: Element(_('Altitude'), 'altitude'),
            7: Element(_('GPS Time'), 'gpstime'),
            8: Element(_('GPS Satellites')),
            9: Element(_('GPS Receiver Status')),
            10: Element(_('GPS Measurement Mode')),
            11: Element(_('Measurement Precision')),
            12: Element(_('Speed Unit')),
            13: Element(_('Speed of GPS Receiver')),
            14: Element(_('Reference for Direction of Movement')),
            15: Element(_('Direction of Movement')),
            16: Element(_('Reference for Direction of Image')),
            17: Element(_('Direction of Image')),
            18: Element(_('Geodetic Survey Data Used')),
            19: Element(_('Reference for Latitude of Destination')),
            20: Element(_('Latitude of Destination')),
            21: Element(_('Reference for Longitude of Destination')),
            22: Element(_('Longitude of Destination')),
            23: Element(_('Reference for Bearing of Destination')),
            24: Element(_('Bearing of Destination')),
            25: Element(_('Reference for Distance to Destination')),
            26: Element(_('Distance to Destination')),
            27: Element(_('Name of GPS Processing Method')),
            28: Element(_('Name of GPS Area')),
            29: Element(_('GPS Date'), 'gpsdate'),
            30: Element(_('GPS Differential Correction')),
        }

        self.__i14y_tags = {
            1: Element(_('Interoperability Index')),
        }

        self._reads = None
        self._writes = None
        self._offset_size = -1
        self._ifd_offsets = []

    @staticmethod
    def can_handle(filename):
        with open(filename, 'rb') as fp:
            mimetype = None
            sig = fp.read(2)
            if sig == b'\x49\x49' or sig == b'\x4d\x4d':
                mimetype = 'image/tiff'

        return mimetype
    
    def read(self, filename, mimetype=None):
        if mimetype is None:
            mimetype = self.can_handle(filename)

        if mimetype is not None:
            self.filename = filename
            
            ds = None
            try:
                try:
                    length = os.path.getsize(filename)
                except:
                    length = -1
                    
                ds = open(filename, 'rb')
                self.read_stream(ds, length=length)
            except TIFFError as exc:
                self.logger.debug(exc.args[0])
                raise
            except:
                raise
            finally:
                if ds is not None:
                    ds.close()
                self.filename = ''
        else:
            self.logger.error('TIFFHandler: Unable to handle file %s' % filename)
            return None
        
    def read_stream(self, ds, length=-1):
        self.container = MediaContainer('image/tiff')

        self._reads = ds
        self._base = ds.tell()
        self._reads_length = length
        
        try:
            ifd_offset = self._read_header()
            
            while ifd_offset != 0:
                if self._reads_length == -1 or ifd_offset < self._reads_length:
                    self._media_entry = MediaEntry()
                    self.container.entries.append(self._media_entry)
                    
                    self.logger.debug('TIFF: Reading IFD')
                    try:
                        ifd_offset = self._read_ifd(self._media_entry.metadata, self._elements, ifd_offset)
                    except StopIteration:
                        break
                else:
                    self.logger.debug('TIFF: IFD offset past end of stream')
                    ifd_offset = 0
                    
            self._transform_metadata()
        except TIFFError as exc:
            if self.filename != '':
                raise TIFFError('%s reading file %s' % (exc.args[0], self.filename))
    
    def write(self, image, filename=''):
        if filename == '' and self.filename != '':
            filename = self.filename
            
        try:
            ds = open(filename, 'wb')
            self.write_stream(ds, image)
        except TIFFError as exc:
            self.logger.debug(exc.args[0])
            raise
        finally:
            ds.close()
            self.filename = ''
            
    def write_stream(self, ds, image):
        for entry in image.entries:
            self._write_ifd(entry)
    
    def _read_header(self):
        """Read the TIFF header to determine the endianness and offset to
        the first IFD"""
        
        bom = self._reads.read(2)
        if bom == b'\x49\x49':
            self.endian = '<'
        elif bom == b'\x4d\x4d':
            self.endian = '>'
        else:
            raise TIFFError('Unknown BOM %s' % bom)

        magic = struct.unpack('%sH' % self.endian, self._reads.read(2))[0]
        if magic == 42:
            self.big = False
            self._offset_size = 4
            self.logger.debug('TIFF: Format - Standard') 
        elif magic == 43:
            self.big = True
            self._offset_size, _resv = struct.unpack('%sHH' % self.endian,
                self._reads.read(4))
            
            if _resv != 0:
                raise TIFFError('Invalid TIFF file')
            self.logger.debug('TIFF: Format - Big') 
        else:
            raise TIFFError("Unknown TIFF Version number %d" % magic)

        if self._offset_size == 4:
            self._offset_format = 'L'
        elif self._offset_size == 8:
            self._offset_format = 'Q'
        else:
            raise TIFFError('Invalid TIFF offset size %d' % self._offset_size)

        return self._read_offset()
        
    def _read_ifd(self, target, valid_tags, offset=-1):
        """Read an IFD and any sub-IFDs"""

        self._reads.seek(self._base + offset, os.SEEK_SET)

        if not self.big:
            data = self._reads.read(2)
            if len(data) == 0:
                raise StopIteration
            count = struct.unpack('%sH' % self.endian, data)[0]
        else:
            data = self._reads.read(8)
            if len(data) == 0:
                raise StopIteration
            count = struct.unpack('%sQ' % self.endian, data)[0]
        
        for _x in range(count):
            self._read_ifd_entry(target, valid_tags)

        return self._read_offset()
    
    def _read_ifd_entry(self, target, valid_tags):
        """Read a single entry from an IFD"""
        
        tag, field_type = \
            struct.unpack('%sHH' % self.endian, self._reads.read(4))

        if not self.big:
            count = struct.unpack('%sL' % self.endian, self._reads.read(4))[0]
        else:
            count = struct.unpack('%sQ' % self.endian, self._reads.read(8))[0]
        
        value = self._read_value(field_type, count)
        if value is None:
            return

        if isinstance(value, (tuple, list)) and len(value) == 1:
            value = value[0]

        value = self._transform_value_after_read(value, tag, valid_tags)

        try:
            tag_name = valid_tags[tag].title
        except:
            tag_name = 'unknown'

        if value is not None:
            try:
                self.logger.debug('TIFF: 0x%04X - %s = %s' % (tag,
                    tag_name, str(value)[:255]))
            except:
                self.logger.debug('TIFF: 0x%04X - %s is not printable' % (tag,
                    tag_name))
        else:
            self.logger.debug('TIFF: 0x%04X - %s' % (tag, tag_name))
        
        try:
            key = valid_tags[tag].key
        except:
            key = None
            
        if key is None:
            key = tag
            
        if key in target: 
            self.logger.debug('TIFF: Repeated tag 0x%04X' % tag)
            
            if not isinstance(target[key], list):
                target[key] = [target[key], value]
        else:
            target[key] = value
    
    def _read_value(self, field_type, count):
        value = None
        
        # Byte
        if field_type == 1 or field_type == 6 or field_type == 7:
            if self._reads_length != -1 and count > self._reads_length:
                raise TIFFError(('Count too high. Data stream not long enough to '
                                 'hold %d items') % count)
            
            if field_type == 1 or field_type == 7:
                format_char = 'B'
            else:
                format_char = 'b'
                
            if (self.big and count <= 8) or count <= 4:
                value = struct.unpack('%d%s' % (count, format_char),
                    self._reads.read(count))
                
                if not self.big:
                    self._reads.seek(4 - count, os.SEEK_CUR)
                else:
                    self._reads.seek(8 - count, os.SEEK_CUR)
            else:
                offset = self._read_offset()
                pos = self._reads.tell()
                self._reads.seek(self._base + offset, os.SEEK_SET)
                value = struct.unpack('%s%d%s' % (self.endian, count,
                    format_char), self._reads.read(count))
                self._reads.seek(pos, os.SEEK_SET)
            
        # String
        elif field_type == 2:
            if self._reads_length != -1 and count > self._reads_length:
                raise TIFFError(('Count too high. Data stream not long enough to '
                                 'hold %d items') % count)
            
            if (self.big and count <= 8) or count <= 4:
                value = str(self._reads.read(count))[:-1]
                
                if not self.big:
                    self._reads.seek(4 - count, os.SEEK_CUR)
                else:
                    self._reads.seek(8 - count, os.SEEK_CUR)
            else:
                offset = self._read_offset()
                pos = self._reads.tell()
                self._reads.seek(self._base + offset, os.SEEK_SET)
                value = self._reads.read(count)[:-1]
                value = value.decode('UTF-8')
                self._reads.seek(pos, os.SEEK_SET)
               
        # Word 
        elif field_type == 3 or field_type == 8:
            if self._reads_length != -1 and count > (self._reads_length / 2):
                raise TIFFError(('Count too high. Data stream not long enough to '
                                 'hold %d items') % count)
            
            if field_type == 3:
                format_char = 'H'
            else:
                format_char = 'h'
                
            if (self.big and count <= 4) or count <= 2:
                value = struct.unpack('%s%d%s' % (self.endian, count,
                    format_char), self._reads.read(2*count))
                
                if not self.big:
                    self._reads.seek(4 - count*2, os.SEEK_CUR)
                else:
                    self._reads.seek(8 - count*2, os.SEEK_CUR)
                
            else:
                offset = self._read_offset()
                pos = self._reads.tell()
                self._reads.seek(self._base + offset, os.SEEK_SET)
                value = struct.unpack('%s%d%s' % (self.endian, count,
                    format_char), self._reads.read(2*count))
                self._reads.seek(pos, os.SEEK_SET)
        
        # Long
        elif field_type == 4 or field_type == 9:
            if self._reads_length != -1 and count > (self._reads_length / 4):
                raise TIFFError(('Count too high. Data stream not long enough to '
                                 'hold %d items') % count)
            
            if field_type == 4:
                format_char = 'L'
            else:
                format_char = 'l'
                
            if (self.big and count <= 2) or count == 1:
                value = struct.unpack('%s%d%s' % (self.endian, count,
                    format_char), self._reads.read(4*count))
                
                if self.big and count == 1:
                    self._reads.seek(4, os.SEEK_CUR)
            else:
                offset = self._read_offset()
                pos = self._reads.tell()
                self._reads.seek(self._base + offset, os.SEEK_SET)
                try:
                    value = struct.unpack('%s%d%s' % (self.endian, count,
                        format_char), self._reads.read(4*count))
                except OverflowError:
                    pass
                self._reads.seek(pos, os.SEEK_SET)
                
        # Numerator + denominator
        elif field_type == 5 or field_type == 10:
            if self._reads_length != -1 and count > (self._reads_length / 8):
                raise TIFFError(('Count too high. Data stream not long enough to '
                                 'hold %d items') % count)
            
            if field_type == 5:
                format_char = 'L'
            else:
                format_char = 'l'
                
            if self.big and count == 1:
                value = self._read_rational(format_char)
            else:
                offset = self._read_offset()
                pos = self._reads.tell()
                self._reads.seek(self._base + offset, os.SEEK_SET)
                if count == 1:
                    value = self._read_rational(format_char)
                else:
                    value = []
                    for _idx in range(count):
                        value.append(self._read_rational(format_char))
                    value = tuple(value)
                self._reads.seek(pos, os.SEEK_SET)
        
        # 4 byte float
        elif field_type == 11:
            if self._reads_length != -1 and count > (self._reads_length / 4):
                raise TIFFError(('Count too high. Data stream not long enough to '
                                 'hold %d items') % count)
            
            if (self.big and count <= 2) or count == 1:
                value = struct.unpack('%s%df' % (self.endian, count),
                    self._reads.read(4*count))
                
                if self.big and count == 1:
                    self._reads.seek(4, os.SEEK_CUR)
            else:
                offset = self._read_offset()
                pos = self._reads.tell()
                self._reads.seek(self._base + offset, os.SEEK_SET)
                value = struct.unpack('%s%df' % (self.endian, count),
                    self._reads.read(4*count))
                self._reads.seek(pos, os.SEEK_SET)
        
        # 8 byte double
        elif field_type == 12:
            if self._reads_length != -1 and count > (self._reads_length / 8):
                raise TIFFError(('Count too high. Data stream not long enough to '
                                 'hold %d items') % count)
            
            if (self.big and count == 1):
                value = struct.unpack('%sd' % self.endian, self._reads.read(8))
            else:
                offset = self._read_offset()
                pos = self._reads.tell()
                self._reads.seek(self._base + offset, os.SEEK_SET)
                value = struct.unpack('%s%dd' % (self.endian, count),
                    self._reads.read(8*count))
                self._reads.seek(pos, os.SEEK_SET)

        # 32 bit Sub IFD
        elif field_type == 13:
            value = struct.unpack('%s%dL' % (self.endian, count),
                self._reads.read(4*count))
        
        # Unicode
        elif field_type == 14:
            self.logger.debug("TIFF: Don't know how to handle Unicode field types") 
        
        # Complex
        elif field_type == 15:
            self.logger.debug("TIFF: Don't know how to handle Complex field types") 
        
        # Quad word
        elif field_type == 16 or field_type == 17:
            if self._reads_length != -1 and count > (self._reads_length / 16):
                raise TIFFError(('Count too high. Data stream not long enough to '
                                 'hold %d items') % count)
            
            if field_type == 16:
                format_char = 'Q'
            else:
                format_char = 'q'
                
            if (self.big and count == 1):
                value = struct.unpack('%s%s' % (self.endian, format_char),
                    self._reads.read(8))
            else:
                offset = self._read_offset()
                pos = self._reads.tell()
                self._reads.seek(self._base + offset, os.SEEK_SET)
                value = struct.unpack('%s%d%s' % (self.endian, count,
                    format_char), self._reads.read(8*count))
                self._reads.seek(pos, os.SEEK_SET)

        # 64 bit Sub IFD
        elif field_type == 18:
            value = struct.unpack('%s%dQ' % (self.endian, count),
                self._reads.read(8 * count))[0]
            
        else:
            self.logger.debug('TIFF: Unknown field type %d' % field_type)
                
        return value
    
    def _transform_value_after_read(self, value, tag, valid_tags):
        try:
            read_transform = valid_tags[tag].reader
        except KeyError:
            read_transform = None
        except AttributeError:
            pass

        if read_transform is None:
            return value
            
        if read_transform == 'ucs2':
            value = bytearray(value)
            value = value.decode('UTF-16')
        
        elif read_transform == 'datetime':
            try:
                value = datetime.strptime(str(value).strip(),
                                          '%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                try:
                    value = datetime.strptime(str(value).strip(),
                                              '%Y:%m:%d %H:%M:%S')
                except (ValueError, TypeError):
                    pass
        
        elif read_transform == 'mddate':
            value = datetime.strptime(str(value).strip(), '%y/%m/%d')
        
        elif read_transform == 'mdtime':
            value = datetime.strptime(str(value).strip(), '%H:%M')
        
        elif read_transform == 'i14y':
            info = {}
            pos = self._reads.tell()
            
            self._read_ifd(info, self.__i14y_tags, value)
            
            self._reads.seek(pos, os.SEEK_SET)
            value = info
        
        elif read_transform == 'gps':
            self.logger.debug('TIFF: Reading GPS Tags')

            info = {}
            pos = self._reads.tell()
            
            # The tag value is an offset to the GPS data
            self._read_ifd(info, self.__gps_tags, value)

            self._reads.seek(pos, os.SEEK_SET)
            value = info
        
        elif read_transform == 'gpsdate':
            try:
                value = datetime.strptime(str(value).strip(), '%Y:%m:%d')
            except:
                value = 'Invalid date: %s' % str(value)

        elif read_transform == 'gpslatitude':
            pass
        
        elif read_transform == 'exif_ifd':
            self.logger.debug('TIFF: Reading Exif IFD')

            pos = self._reads.tell()
            info = {}
            self._read_ifd(info, self._elements, offset=value)
            self._reads.seek(pos, os.SEEK_SET)
            value = info

        elif read_transform == 'subifd':
            self.logger.debug('TIFF: Reading Sub IFD')

            pos = self._reads.tell()                
            entry = MediaEntry()
            self._media_entry.subentries.append(entry)
            
            if isinstance(value, (list, tuple)):
                for offset in value:
                    self._read_ifd(entry.metadata, self._elements, offset)
            else:
                self._read_ifd(entry.metadata, self._elements, value)
                
            self._reads.seek(pos, os.SEEK_SET)
            value = None
                
        elif read_transform == 'xmp':
            self.logger.debug('TIFF:     Reading XMP')

            ds = BytesIO(bytearray(value))
            h = mogul.media.xmp.XMPHandler()
            h.read_stream(ds)
            value = h.metadata.copy()
                
        elif read_transform == 'iptc':
            self.logger.debug('TIFF:     Reading IPTC')

            pos = self._reads.tell()                

            if isinstance(value, (list, tuple)):
                for offset in value:
                    self._reads.seek(self._base + offset, os.SEEK_SET)

            self._reads.seek(pos, os.SEEK_SET)
                
        elif read_transform == 'photoshop':
            self.logger.debug('TIFF:     Reading Photoshop IRBs')

            ds = BytesIO(bytearray(value))
            h = mogul.media.psd.PSDHandler(self.logger.level + 1)
            h.read_irbs(ds)
            value = h.metadata.copy()
            pass
                
        elif read_transform == 'ocr_text':
            value = bytearray(value[6:]).decode('UTF-8')
                
        elif read_transform == 'ocr_data':
            value = bytearray(value[6:])
                
        elif read_transform == 'subfile_type':
            pass
                
        return value
    
    def _transform_metadata(self):
        for entry in self.container.entries:
            self._transform_entry_metadata(entry)
        
    def _transform_entry_metadata(self, entry):
        pass
    
    def _read_offset(self):
        format_string = '%s%s' % (self.endian, self._offset_format)
        return struct.unpack(format_string,
                             self._reads.read(self._offset_size))[0]

    def _read_rational(self, format_char):
        format_string = '%s%s%s' % (self.endian, format_char, format_char)
        numerator, denominator = struct.unpack(format_string,
            self._reads.read(8))
        if denominator == 0:
            return '0'
        else:
            return '%d/%d' % (numerator, denominator)
        
    def _build_image(self):
        image = Image('image/tiff')
        #for tag, value in self.metadata.items():
        #    pass
        return image

    def _write_header(self, endian='<'):
        pass

    def _write_ifd(self, entry):
        pass

    def _write_ifd_entry(self):
        pass

    def _transform_value_before_write(self):
        pass

    def _write_value(self, field_type, count, value):
        pass
    
    def _write_offset(self, offset):
        format_string = '%s%s' % (self.endian, self._offset_format)
        self._writes.write(struct.pack(format_string, offset))
    
    def _write_rational(self, format_char, numerator, denominator):
        format_string = '%s%s%s' % (self.endian, format_char, format_char)
        self._writes.write(struct.pack(format_string,
            int(numerator), int(denominator)))
