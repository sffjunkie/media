# Copyright (c) 2009-2014 Simon Kennedy <sffjunkie+code@gmail.com>

import os
import struct

from mogul.media.attachment import Image

class ITCException(Exception):
    pass

class ITCWarning(Warning):
    pass

ITUNES_9 = 208
ITUNES_OLD = 216

class ITCHandler(object):
    def __init__(self, mode=ITUNES_9):
        self._elements = {
            'itch': self._read_itch,
            'item': self._read_item,
        }
        
        self._ds = ''
        self._image_offset = mode

        self.track_id = ''
        self.library_id = ''
        self.images = []

    @staticmethod
    def can_handle(filename):
        fp = open(filename, 'rb')
        fp.seek(4)
        sig = fp.read(4)
        fp.close()
        if sig == 'itch':
            return 'itc'
        else:
            return None
    
    def read(self, filename, format_=None):
        if format_ is None:
            format_ = ITCHandler.can_handle(filename)
            
        if format_ == 'itc':
            self._ds = open(filename, 'rb')
            
            done = False
            while not done:
                done = self._read_box()
                
            self._ds.close()
                
    def _read_box(self):
        data = self._ds.read(8)
        if len(data) == 8:
            box_size, box_id = struct.unpack('>L0004s', data)
    
            try:
                handler = self._elements[box_id]
            except:
                handler = None
                
            if handler is not None:
                handler(box_id, box_size)
            else:
                self._ds.seek(box_size, os.SEEK_CUR)
                
            return False
        else:
            return True            

    def _read_itch(self, frame, size):
        self._ds.seek(16, os.SEEK_CUR)
        subframe = struct.unpack('0004s', self._ds.read(4))[0]
        if subframe == 'artw':
            # Assuming this is a hold-over from a previous ITC format and 
            # is where the artwork was stored at some point in time.
            self._ds.seek(256, os.SEEK_CUR)

    def _read_item(self, frame, size):
        start = self._ds.tell()
        self._image_offset = struct.unpack('>L', self._ds.read(4))[0]

        # 16 byte preamble for ITUNES_9 & 20 after ITUNES_OLD. 
        # The reason for this unclear.
        # ITUNES_OLD also has extra 4 bytes before image data to account for the
        # 8 bytes difference
        if self._image_offset == ITUNES_9:
            self.info_preamble = self._ds.read(16) # 1L, 2L, 1L, 0L
        elif self._image_offset == ITUNES_OLD:
            self.info_preamble = self._ds.read(20) # 1L, 1L, 1L, 2L, 0L
        
        library, track, imethod, iformat = struct.unpack('>QQ0004s0004s', self._ds.read(24))
        
        library = ('%16x' % library).upper()
        if self.library_id == '':
            self.library_id = library
        elif self.library_id == library:
            pass
        else:
            raise ITCWarning('Images with multiple library_id IDs found. Only the first found will be used (%s).' % self.library_id)
        
        track = ('%16x' % track).upper()
        if self.track_id == '':
            self.track_id = track
        elif self.track_id == track:
            pass
        else:
            raise ITCWarning('Images with multiple track_id IDs found. Only the first found will be used (%s).' % self.track_id)
        
        #method = ''
        #if imethod == 'locl':
        #    method = 'local'
        #elif imethod == 'down':
        #    method = 'download'
            
        # TODO: Confirm that downloaded and local images use the same
        # format identifiers
        format_ = ''
        if iformat == 'PNGf':
            format_ = 'image/png'
        elif iformat == '\x00\x00\x00\x0d':
            format_ = 'image/jpeg'
        
        self._ds.seek(4, os.SEEK_CUR)
        width, height = struct.unpack('>LL', self._ds.read(8))

        image_pos = start + self._image_offset - 8
        self._ds.seek(image_pos)
        
        data_size = size - self._image_offset
        
        data = self._ds.read(data_size)
        
        image = Image(mime_type=format_, data=data)
        image.width = width
        image.height = height
        image.item_id = self.track_id
        image.library_id = self.library_id
        self.images.append(image)
