# Copyright (c) 2009-2014 Simon Kennedy <sffjunkie+code@gmail.com>

import os
import struct
from io import BytesIO

from mogul.media import localize
_ = localize()

from mogul.media import (MediaContainer, MediaEntry, MediaStream,
        AudioStreamInfo, VideoStreamInfo, ImageStreamInfo, SubtitleStreamInfo,
        Tag, TagTarget, TagGroup, MediaHandlerError)

from mogul.media import MediaHandler
from mogul.media.exif import ExifHandler
from mogul.media.psd import PSDHandler
from mogul.media.xmp import XMPHandler
from mogul.media.element import Element


class JPEGError(Exception):
    pass


class JPEGHandler(MediaHandler):
    def __init__(self, log_indent_level=0):
        super(JPEGHandler, self).__init__(log_indent_level)
        
        self.filename = ''
        
        self._elements = {
            0xC0: Element(_('Baseline DCT'), self._read_sof),
            0xC1: Element(_('Extended Sequential DCT'), self._read_sof),
            0xC2: Element(_('Progressive DCT'), self._read_sof),
            0xC3: Element(_('Lossless (Sequential)'), self._read_sof),
            0xC4: Element(_('Define Huffman Tables')),
            0xC5: Element(_('Differential Sequential DCT'), self._read_sof),
            0xC6: Element(_('Differential Progressive DCT'), self._read_sof),
            0xC7: Element(_('Differential Lossless (Sequential)'), self._read_sof),
            0xC8: Element(_('Reserved')),
            0xC9: Element(_('Extended Sequential DCT'), self._read_sof),
            0xCA: Element(_('Progressive DCT'), self._read_sof),
            0xCB: Element(_('Lossless (Sequential)'), self._read_sof),
            0xCC: Element(_('Define Arithmetic Coding Conditioning')),
            0xCD: Element(_('Differential Sequential DCT'), self._read_sof),
            0xCE: Element(_('Differential Progressive DCT'), self._read_sof),
            0xCF: Element(_('Differential Lossless (Sequential)'), self._read_sof),
            0xD8: Element(_('Start Of Image'), self._read_soi),
            0xD9: Element(_('End Of Image')),
            0xDA: Element(_('Start Of Scan'), self._read_sos),
            0xDB: Element(_('Define Quantisation Table')),
            0xDC: Element(_('Define Number Of Lines')),
            0xDD: Element(_('Define Restart Interval'), self._read_dri),
            0xDE: Element(_('Define Hierarchical Progression')),
            0xDF: Element(_('Expand Reference Component')),
            0xE0: Element(_('APP0'), self._read_APP0),
            0xE1: Element(_('APP1'), self._read_APP1),
            0xE2: Element(_('APP2')),
            0xE3: Element(_('APP3')),
            0xE4: Element(_('APP4')),
            0xE5: Element(_('APP5')),
            0xE6: Element(_('APP6')),
            0xE7: Element(_('APP7')),
            0xE8: Element(_('APP8')),
            0xE9: Element(_('APP9')),
            0xEA: Element(_('APP10')),
            0xEB: Element(_('APP11')),
            0xEC: Element(_('APP12')),
            0xED: Element(_('APP13'), self._read_APP13),
            0xEE: Element(_('APP14')),
            0xEF: Element(_('APP15')),
            0xFE: Element(_('Comment'), self._read_comment),
        }

        self._ds = None
        self.thumbnail = None
        self.thumbnail_format = 0

    @staticmethod
    def can_handle(ds):
        """Determine if JPEGHandler can parse the stream."""
        
        if ds.read(2) == b'\xFF\xD8':
            return 'image/jpeg'
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
                raise MediaHandlerError("JPEGHandler: Unable to handle file '%s'" % filename)

    def read_stream(self, ds, doctype=None):
        if doctype is None:
            doctype = self.can_handle(ds)

        if doctype is not None:
            self._ds = ds
            self.container = MediaContainer()
            self._media_entry = MediaEntry()
            self._media_entry.container = self.container
            self.container.entries.append(self._media_entry)
            
            # skip the file magic as we've checked this in can_handle
            self._ds.seek(2, os.SEEK_SET)

            try:
                while True:
                    self._read_box('root')
            except StopIteration:
                pass
            except JPEGError as exc:
                if self.filename != '':
                    raise JPEGError('%s in file %s' % (exc.args[0], self.filename))
        else:
            raise MediaHandlerError("JPEGHandler: Unable to handle stream")

    def _read_box(self, parent):
        preamble_length = -1
        box_id = 0xFF
        while box_id == 0xFF:
            preamble_length += 1
            box_id = self._ds.read(1)
            if len(box_id) == 0:
                raise StopIteration
            box_id = ord(box_id)
        
        if box_id != 0:        
            try:
                elem = self._elements[box_id]
                title = elem.title
                handler = elem.reader 
                self.logger.debug('JPEG: 0x%02X - %s' % (box_id, title))
            except:
                handler = None
                self.logger.debug('JPEG: Unknown box id 0x%02X' % box_id)
                
            box_size = struct.unpack('>H', self._ds.read(2))[0]

            if box_size >= 2:
                box_size -= 2
                if handler is not None:
                    handler(parent, box_size, box_id)
                else:
                    self._ds.seek(box_size, os.SEEK_CUR)
            else:
                raise JPEGError('Box size must be at least 2.')
        
    def _read_APP0(self, parent, size, box_id):
        """Read an APP0 structure"""
        
        self.identifier = self._ds.read(5)[:4]
        if self.identifier == b'JFIF':
            major, minor, density_units, self.density_x, self.density_y, \
            self.thumbnail_width, self.thumbnail_height = \
            struct.unpack('>BBBHHBB', self._ds.read(9))
            
            self.version = '%d.%d' % (major, minor)
            
            if density_units == 0:
                self.density_units = _('No units')
            elif density_units == 1:
                self.density_units = _('Pixels Per Inch')
            elif density_units == 2:
                self.density_units = _('Pixels Per Centimetre')
                
            if self.thumbnail_width != 0 and self.thumbnail_height != 0:
                self.thumbnail_format = 0x13
                self.thumbnail = self._ds.read(3 * self.thumbnail_width * self.thumbnail_height)
        elif self.identifier == b'JFXX':
            self.thumbnail_format = self._ds.read(1)
            
            if self.thumbnail_format == 0x10:
                handler = JPEGHandler(self.logger.level)
                
                # TODO: complete this
                del handler
            else:
                self.thumbnail_width, self.thumbnail_height = \
                struct.unpack('BB', self._ds.read(2))
                
                if self.thumbnail_format == 0x11:
                    self.palette = self._ds.read(768)
                    self.thumbnail = self._ds.read(self.thumbnail_width * self.thumbnail_height)
                if self.thumbnail_format == 0x13:
                    self.thumbnail = self._ds.read(3 * self.thumbnail_width * self.thumbnail_height)
                else:
                    raise JPEGError('Invalid thumbnail format') 
            
    def _read_APP1(self, parent, size, box_id):
        """Read an APP1 structure"""
        
        base = self._ds.tell()
        format = self._read_string()
        
        if format == b'Exif':
            self.logger.debug('JPEG: Reading Exif Data')
            self._ds.seek(1, os.SEEK_CUR)
            
            self.exif = ExifHandler(self.logger.level + 1)
            self.exif.filename = self.filename
            self.exif.read_stream(self._ds)
            
        elif format == b'http://ns.adobe.com/xap/1.0/':
            self.logger.debug('JPEG: Reading XMP Data')
            data = self._ds.read(size-29)
            ds = BytesIO(data)
            
            self.xmp = XMPHandler(self.logger.level + 1)
            self.xmp.read_stream(ds)
            
        elif format == b'http://ns.adobe.com/xmp/extension/':
            pass
            
        else:
            raise JPEGError('Unknown APP1 format %s' % format)

        self._ds.seek(base + size, os.SEEK_SET)
        
    def _read_APP13(self, parent, size, box_id):
        """Read an APP13 structure"""
        
        format = self._read_string()
        if format == 'Photoshop 3.0':
            self.logger.debug('JPEG: Reading PSD Data')
            data = self._ds.read(size-14)
            ds = BytesIO(data)
            self.psd = PSDHandler(self.logger.level + 1)
            self.psd.read_irbs(ds)
            
        elif format == 'Adobe_CM':
            self.logger.debug('JPEG: Reading Adobe CM Data')
            # size - 2 size bytes + len(format)
            data_len = size - 10
            _data = self._ds.read(data_len)

        else:
            raise JPEGError('Unknown APP13 format %s' % format)
            
    def _read_dri(self, parent, size, box_id):
        """Define Restart Interval"""
        
        if size > 0:
            self._dri = struct.unpack('>H', self._ds.read(2))[0]
            self._ds.seek(size - 2, os.SEEK_CUR)
            print('dri = %d' % self._dri)

    def _read_sof(self, parent, size, box_id):
        """Start of Frame"""
        
        precision, self.height, self.width, \
            components_in_frame = struct.unpack('>BHHB', self._ds.read(6))
            
        self._ds.seek(3 * components_in_frame, os.SEEK_CUR)
        
    def _read_soi(self, parent, size, box_id):
        """Start of Image"""
        
        total_read = 0
        while total_read < size:
            total_read += self._read_box('soi')
            
        return total_read

    def _read_sos(self, parent, size, box_id):
        """Start of Scan.
        
        There should only be image data and an EOI frame at the end.
        We're not yet bothered about the image data so we'll just terminate."""

        _image_component_count = ord(self._ds.read(1))
        _scan_header = self._ds.read(size)
        _start_of_spectral, _end_of_spectral, _successive_approx = \
            struct.unpack('>BBB', self._ds.read(3)) 
        raise StopIteration()
    
    def _read_comment(self, parent, size, box_id):
        data = self._ds.read(size)
        pass
    
    def _read_string(self):
        c = b'\xFF'
        s = b''
        while c != b'\x00':
            c = self._ds.read(1)
            s += c
        
        return s[:-1]
    