# Copyright (c) 2009-2014 Simon Kennedy <sffjunkie+code@gmail.com>

import os
import zlib
import struct
import logging
import datetime
from array import array
from io import StringIO

from mogul.media import localize
_ = localize()

from mogul.media import (MediaContainer, MediaEntry, MediaStream,
    Tag, TagTarget, TagGroup, MediaHandlerError)

from mogul.media.image import Image
from mogul.media.xmp import XMPHandler

__spec_version__ = '2'

def enum(**enums):
    return type('Enum', (), enums)
        
PNG_COLOR_TYPE = enum(unknown=-1, greyscale=0, truecolor=2, indexed=3,
                       greyscale_alpha=4, truecolor_alpha=6)


class PNGError(Exception):
    pass


class PNGImage(Image):
    def __init__(self):
        Image.__init__(self, 'image/png')
        
        self._color_type = PNG_COLOR_TYPE.unknown
        self._palette = None
        self._image_data = None
        self._transparency = None
        self._gamma = -1
        self._primary_chromaticies = None
        self._icc_profile = None
        self._srgb_intent = -1
        self._text = []
        self._background_color = None
        self._physical_dimensions = None
        self._significant_bits = None
        self._suggested_palette = None
        self._histogram = None
        self._last_modification = None

    def bytes_per_row():
        def fget(self):            
            if self.color_type == PNG_COLOR_TYPE.indexed:
                bpr = self.width
            elif self.color_type == PNG_COLOR_TYPE.truecolor:
                bpr = self.width * (self.bits_per_sample/8) * 3
            elif self.color_type == PNG_COLOR_TYPE.truecolor_alpha:
                bpr = self.width * (self.bits_per_sample/8) * 4
            elif self.color_type == PNG_COLOR_TYPE.greyscale:
                bpr = self.width * (self.bits_per_sample/8)
            elif self.color_type == PNG_COLOR_TYPE.greyscale_alpha:
                bpr = self.width * ((self.bits_per_sample/8) + 1)
                
            return bpr
        
        return locals()
    
    bytes_per_row = property(**bytes_per_row())


class PNGHandler(object):
    def __init__(self):
        self.logger = logging.getLogger('mogul.media')
        
        self._chunks = {
            b'IHDR': (_('Header'), self._read_header, self._write_header),
            b'PLTE': (_('Palette'), None, None),
            b'IDAT': (_('Image Data'), self._read_image_data, None),
            b'IEND': (_('End Of File'), None, None),
            b'tRNS': (_('Transparency'), None, None),
            b'gAMA': (_('Image Gamma'), None, None),
            b'cHRM': (_('Primary Chromatacies'), None, None),
            b'sRGB': (_('Standard RGB Color Space'), None, None),
            b'iCCP': (_('Embedded ICC Profile'), None, None),
            b'tEXt': (_('Textual Data'), self._read_text, None),
            b'zTXt': (_('Compressed Textual Data'), self._read_text, None),
            b'iTXt': (_('International Textual Data'), self._read_itext, None),
            b'bKGD': (_('Background Color'), self._read_background_color, None),
            b'pHYs': (_('Physical Dimensions'), self._read_physical_dimensions, None),
            b'sBIT': (_('Significant Bits'), self._read_significant_bits, None),
            b'sPLT': (_('Suggested Palette'), self._read_suggested_palette, None),
            b'hIST': (_('Palette Histogram'), self._read_histogram, None),
            b'tIME': (_('Image Last Modification Time'), self._read_last_modification, None),
        }

        self.filename = ''
        """The filename to use for reading or writing."""

        self._ds = None
        
        self._idat = []
        """Collect the IDAT chunk data until all image data has been read as
        the chunks need to be decompressed together""" 
        
    @staticmethod                                                                                                                
    def can_handle(ds):
        """Determine if PNGHandler can parse the stream."""
        
        data = ds.read(8)
        ds.seek(-8, os.SEEK_CUR)
        
        if data == '\x89\x50\x4e\x47\x0d\x0a\x1a\x0a':
            return 'image/png'
        else:
            return None

    def read(self, filename, doctype=None):
        with open(filename, 'rb') as ds:
            if doctype is None:
                doctype = self.can_handle(ds)
    
            if doctype is not None:
                try:
                    self.read_stream(ds)
                except EOFError:
                    pass
            else:
                raise MediaHandlerError("PNGHandler: Unable to handle file '%s'" % filename)
        
    def write(self, image, filename=''):
        if filename != '':
            self.filename = filename

    def read_stream(self, ds, doctype=None):
        if doctype is None:
            doctype = self.can_handle(ds)

        if doctype is not None:
            self._ds = ds
            self.container = MediaContainer()
            self._media_entry = MediaEntry()
            self._media_entry.container = self.container
            self.container.entries.append(self._media_entry)
        
            try:
                while True:
                    self._read_box('root')
            except StopIteration:
                self._combine_idat()
        else:
            raise MediaHandlerError("PNGHandler: Unable to handle stream")

    def _read_box(self, parent):
        box_size, box_id = struct.unpack('>L4s', self._ds.read(8))
        
        name = 'Unknown'
        read_handler = None
        try:
            name, read_handler, _write_handler = self._chunks[box_id]
        except KeyError:
            pass

        self.logger.debug('PNG:  %s - %s' % (box_id, name))

        if box_size > 0:            
            if read_handler is not None:
                read_handler(parent, box_id, box_size)
            else:
                self._ds.seek(box_size, os.SEEK_CUR)

        _crc32 = struct.unpack('>L', self._ds.read(4))
        
        if box_size == 0:
            raise StopIteration
    
    def _read_header(self, parent, box_id, box_size):
        stream = self._image.stream
        
        stream.width, stream.height, self._image.bits_per_sample, \
            self._image.color_type, self._image.compression_method, \
            self._image.filter_method, self._image.interlace_method = \
            struct.unpack('>LLBBBBB', self._ds.read(13))

    def _read_image_data(self, parent, box_id, box_size):
        self._idat.append(self._ds.read(box_size))
    
    def _read_palette(self, parent, box_id, box_size):
        self._image._palette = self._ds(box_size)
    
    def _read_text(self, parent, box_id, box_size):
        length, keyword = self._read_string()
        keyword = keyword.decode('Latin_1')
        size_read = length+1
        
        if box_id == 'zTXt':
            compression_type = ord(self._ds.read(1))
            size_read += 1
        
        value = self._ds.read(box_size - size_read)
        
        if box_id == 'zTXt':
            if compression_type == 0:
                value = zlib.decompress(value)
            else:
                raise PNGError('Cannot handle compression type %d in text.' %
                               compression_type)
        
        value = value.decode('Latin_1')
        
        tag = Tag(keyword, value)
        self._image.tag_group.tags.append(tag)

    def _read_itext(self, parent, box_id, box_size):
        length, keyword = self._read_string()
        keyword = keyword.decode('Latin_1')
        size_read = length+1

        compression_flag = ord(self._ds.read(1))
        compression_method = ord(self._ds.read(1))
        size_read += 2
        
        length, language = self._read_string()
        size_read += length+1
        
        if length == 0:
            locale = ('und', 'und')
        elif language.startswith('x-'):
            locale = (language[2:], 'und')
        else:
            try:
                locale = language.split('-')
            except:
                locale = (language, 'und')
        
        length, tx_keyword = self._read_string()
        tx_keyword = tx_keyword.decode('UTF-8')
        size_read += length+1
        
        value = self._ds.read(box_size - size_read)
        
        if compression_flag == 1:
            if compression_method == 0:
                value = zlib.decompress(value)
            else:
                raise PNGError('Cannot handle compression type %d in text.' %
                               compression_method)
        
        value = value.decode('UTF-8')
        
        if keyword == 'XML:com.adobe.xmp':
            handler = XMPHandler()
            ds = StringIO(value)
            handler.read_stream(ds)

            group = TagGroup('XMP')
            for tag in handler.tags:
                t = Tag()
                t.set_to(tag)
                group.append(t)
                
            self._image.tag_group.append(group)
        else:
            tag = Tag(keyword, value)
            tag.locale = locale
            self._image.tag_group.tags.append(tag)
    
    def _read_background_color(self, parent, box_id, box_size):
        data = self._ds.read(box_size)
        if box_size == 1:
            self._image._background_color = ord(data[0])
        elif box_size == 2:
            self._image._background_color = struct.unpack('>H', data)
        elif box_size == 6:
            self._image._background_color = struct.unpack('>HHH', data)
    
    def _read_physical_dimensions(self, parent, box_id, box_size):
        ppu_x, ppu_y, specifier = struct.unpack('>LLB', self._ds.read(9))
        self._image._physical_dimensions = (ppu_x, ppu_y, specifier)
    
    def _read_significant_bits(self, parent, box_id, box_size):
        self._image._significant_bits = self._ds.read(box_size)
    
    def _read_suggested_palette(self, parent, box_id, box_size):
        bytes_left = box_size
        size, name = self._read_string()
        name = name.decode('latin-1')
        bytes_left -= (size + 1)
        
        sample_depth = ord(self._ds.read(1))
        bytes_left -= 1
        
        if sample_depth == 8:
            bytes_per_sample = 1
        else:
            bytes_per_sample = 2
            
        if self._image._suggested_palette is None:
            self._image._suggested_palette = {}
            
        palette = (bytes_per_sample, self._ds.read(bytes_left))
        self._image._suggested_palette[name] = palette

    def _read_histogram(self, parent, box_id, box_size):
        rest = box_size - 2
        frequency, data = struct.unpack('>H%ds' % rest, self._ds.read(box_size))
        
        self._image._histogram = (frequency, data)
    
    def _read_last_modification(self, parent, box_id, box_size):
        year, month, day, hour, minute, second = \
            struct.unpack('>HBBBBB', self._ds.read(box_size))
        
        self._image._last_modification = datetime.datetime(year, month, day,
                                                    hour, minute, second)
    
    def _write_box(self, name, data, length):
        if length > 0:
            crc = zlib.crc32(name)
            crc = zlib.crc32(data, crc)
            self._writes.write(struct.pack('>L4s%dsL' % length,
                length, name, data,
                crc))
        else:
            self._writes.write(struct.pack('>L4sL', 0, name, zlib.crc32(name)))
        
    def _write_header(self, width, height, depth, color_type, compression=0,
                      filter_=0, interlace=0):
        data = struct.pack('>LLbbbbb', width, height, depth, color_type,
                           compression, filter_, interlace)
        self._write_box(b'IHDR', data, 9)
    
    def _write_palette(self, data, length):
        self._write_box(b'PLTE', data, length)
    
    def _write_data(self, data, length):
        compress = zlib.compressobj(self.compression)
        compressed = compress.compress(data.tostring())
        compressed += compress.flush()
        length = len(compressed)
        
        self._write_box(b'IDAT', compressed, length)
    
    def _write_argb_data(self, width, height, argb_data, length):
        data = array('B')
        for y in range(height):
            data.append(0)
            for x in range(width):
                offset = ((y * width) + x) * 4
                data.append(ord(argb_data[offset+1]))
                data.append(ord(argb_data[offset+2]))
                data.append(ord(argb_data[offset+3]))
                data.append(ord(argb_data[offset]))
        
        self._write_data(data)
        
    def _write_end(self):
        self._write_box(b'IEND', '', 0)

    def _combine_idat(self):
        decompressor = zlib.decompressobj()
        for idat in self._idat:
            decompressed = decompressor.decompress(idat)
            self._image.stream.data.fromstring(decompressed)
            
        del self._idat[:]
    
    def _read_string(self):
        l = 0
        c = ''
        s = ''
        while c != '\x00':
            c = self._ds.read(1)
            s += c
            l += 1
        
        return (l-1, str(s[:-1]))
        