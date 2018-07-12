# Copyright (c) 2009-2014 Simon Kennedy <sffjunkie+code@gmail.com>

import os
import struct
from io import StringIO

from mogul.media import localize
_ = localize()

from mogul.media import MediaHandler
import mogul.media.xmp
import mogul.media.exif
import mogul.media.iptc_naa
from mogul.media import MediaContainer, MediaEntry, MediaStream, \
        ImageStreamInfo, Tag, TagTarget, TagGroup, MediaHandlerError
from mogul.media.element import Element

class PSDHandler(MediaHandler):
    def __init__(self, log_indent_level=0):
        super(PSDHandler, self).__init__(log_indent_level)
        
        self.metadata = {}
        
        self._ds = None
        self._resources_len = -1
        
        self._elements = {
            0x03E8: Element(_('Obsolete: Photoshop 2.0 only'), None),
            0x03E9: Element(_('Macintosh print manager print metadata record'), None),
            0x03EB: Element(_('Obsolete: Photoshop 2.0 only'), None),
            0x03ED: Element(_('Resolution Info Structure'), None),
            0x03EE: Element(_('Alpha Channel Names'), None),
            0x03EF: Element(_('Obsolete: Display Info Structure'), None),
            0x03F0: Element(_('Caption'), None),
            0x03F1: Element(_('Border Information'), None),
            0x03F2: Element(_('Background Colour'), None),
            0x03F3: Element(_('Print Flags'), None),
            0x03F4: Element(_('Grayscale And Multichannel Halftoning Information'), None),
            0x03F5: Element(_('Colour Halftoning'), None),
            0x03F6: Element(_('Duotone Halftoning'), None),
            0x03F7: Element(_('Grayscale And Multichannel Transfer Function'), None),
            0x03F8: Element(_('Colour Transfer Functions'), None),
            0x03F9: Element(_('Duotone Transfer Functions'), None),
            0x03FA: Element(_('Duotone Image Information'), None),
            0x03FB: Element(_('Effective Black/White'), None),
            0x03FC: Element(_('Obsolete'), None),
            0x03FD: Element(_('EPS Options'), None),
            0x03FE: Element(_('Quick Mask'), None),
            0x03FF: Element(_('Obsolete'), None),
            0x0400: Element(_('Layer State Information'), None),
            0x0401: Element(_('Working Path'), None),
            0x0402: Element(_('Layers Group Information'), None),
            0x0403: Element(_('Obsolete'), None),
            0x0404: Element(_('IPTC-NAA Record'), self._read_iptc_naa),
            0x0405: Element(_('Raw Format Image Mode'), None),
            0x0406: Element(_('JPEG Quality'), None),
            0x0408: Element(_('Grid And Guides'), None),
            0x0409: Element(_('Thumbnail Resource'), None),
            0x040A: Element(_('Copyright Flag'), None),
            0x040B: Element(_('URL'), None),
            0x040C: Element(_('Thumbnail Resource'), None),
            0x040D: Element(_('Obsolete: Global Angle'), None),
            0x040E: Element(_('Obsolete: Colour Samplers Resource'), None),
            0x040F: Element(_('ICC Profile'), None),
            0x0410: Element(_('Watermark'), None),
            0x0411: Element(_('ICC Untagged Profile'), None),
            0x0412: Element(_('Effects Visible'), None),
            0x0413: Element(_('Spot Halftone'), None),
            0x0414: Element(_('Document ID Seed Number'), None),
            0x0415: Element(_('Unicode Alpha Names'), None),
            0x0416: Element(_('Indexed Colour Table Count'), None),
            0x0417: Element(_('Transparency Index'), None),
            0x0419: Element(_('Global Altitude'), None),
            0x041A: Element(_('Slices'), None),
            0x041B: Element(_('Workflow URL'), None),
            0x041C: Element(_('Jump To XPEP'), None),
            0x041D: Element(_('Alpha Identifiers'), None),
            0x041E: Element(_('URL List'), None),
            0x0421: Element(_('Version Info'), None),
            0x0422: Element(_('Exif Data 1'), self._read_exif_data1),
            0x0423: Element(_('Exif Data 3'), self._read_exif_data3),
            0x0424: Element(_('XMP Metadata'), self._read_xmp),
            0x0425: Element(_('Caption Digest'), None),
            0x0426: Element(_('Print Scale'), None),
            0x0428: Element(_('Pixel Aspect Ratio'), None),
            0x0429: Element(_('Layer Comps'), None),
            0x042A: Element(_('Alternate Duotone Colours'), None),
            0x042B: Element(_('Alternate Spot Colours'), None),
            0x042D: Element(_('Layer Selection IDs'), None),
            0x042E: Element(_('HDR Toning Information'), None),
            0x042F: Element(_('Print Information'), None),
            0x0430: Element(_('Layer Groups Enabled ID'), None),
            0x0431: Element(_('Colour Samplers Resource'), None),
            0x0432: Element(_('Measurement Scale'), None),
            0x0433: Element(_('Timeline Information'), None),
            0x0434: Element(_('Sheet Disclosure'), None),
            0x0435: Element(_('DisplayInfo Structure'), None),
            0x0436: Element(_('Onion Skins'), None),
            0x0438: Element(_('Count Information'), None),
            0x043A: Element(_('Print Information'), None),
            0x043B: Element(_('Print Style'), None),
            0x043C: Element(_('Macintosh NSPrintInfo'), None),
            0x043D: Element(_('Windows DEVMODE'), None),
            0x0BB7: Element(_('Name Of Clipping Path'), None),
            0x1B58: Element(_('Image Ready Variables'), None),
            0x1B59: Element(_('Image Ready Data Sets'), None),
            0x1F40: Element(_('Lightroom Workflow'), None),
            0x2710: Element(_('Print Flags Information'), None),
        }
        
        self.metadata = {}

    @staticmethod
    def can_handle(ds):
        """Determine if ASFHandler can read_stream the stream."""
        
        data = ds.read(4)
        ds.seek(-4, os.SEEK_CUR)
        
        if data == '8BPS':
            return 'PSD'
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
                raise MediaHandlerError("PSDHandler: Unable to handle file '%s'" % filename)

    def read_stream(self, ds, doctype=None):
        if doctype is None:
            doctype = self.can_handle(ds)

        if doctype is not None:
            self._ds = ds
            self.container = MediaContainer()
            self._media_entry = MediaEntry()
            self._media_entry.container = self.container
            self.container.entries.append(self._media_entry)
            
            self._ds.seek(4, os.SEEK_CUR)
            self.read_header()
        else:
            raise MediaHandlerError("PSDHandler: Unable to handle stream")
            
    def read_header(self):
        version, _resv, channels, height, width, bits_per_channel, \
            color_mode, color_size = struct.unpack('>H6sHLLHHL', self._ds.read(26))

        if color_size > 0:
            self._ds.seek(color_size, os.SEEK_CUR)
            
        self._resources_len = struct.unpack('>L', self._ds.read(4))[0]
        
        self.read_irbs(self._ds)
 
    def read_irbs(self, ds):
        self._ds = ds
        try:
            while True:
                data = self._ds.read(6)
                sig, resource_id = struct.unpack('>4sH', data)
                if sig == '8BIM':
                    name_len = ord(ds.read(1))
                    name_len + (name_len % 2)
                    if name_len > 0:
                        name = self._ds.read(name_len)
                        name = name[:-1]
                    else:
                        name= ''
                        # Empty names always take up 2 bytes
                        ds.seek(1, os.SEEK_CUR)
    
                    resource_len = struct.unpack('>L', self._ds.read(4))[0]
                    padding = resource_len % 2
    
                    try:
                        elem = self._elements[resource_id]
                        title = elem.title
                        handler = elem.reader
                        self.logger.debug('PSD:  %s' % title)
                    except:
                        handler = None
                    
                    if handler is not None: 
                        handler(resource_id, resource_len)
                    else:
                        self._ds.seek(resource_len, os.SEEK_CUR)
                        
                    if padding != 0:
                        self._ds.seek(padding, os.SEEK_CUR)
        except (EOFError, struct.error):
            pass

    def _read_iptc_naa(self, irb_id, length):
        handler = mogul.media.iptc_naa.IPTCNAAHandler(self.logger.level + 1)
        handler.read_stream(self._ds, length)
        self.metadata['iptc-naa'] = handler.metadata.copy()
        
    def _read_exif_data1(self, irb_id, length):
        handler = mogul.media.exif.ExifHandler(self.logger.level + 1)
        handler.read_stream(self._ds, length)
        pass
        
    def _read_exif_data3(self, irb_id, length):
        pass

    def _read_xmp(self, irb_id, length):
        handler = mogul.media.xmp.XMPHandler(self.logger.level + 1)
        handler.read_stream(self._ds, length)

    def parse_resource(self, data, len):
        data = StringIO(data)
        id = struct.unpack('>H', data.read(4))[0]
        if id == 1028:
            pass
                
