# Copyright (c) 2009-2014 Simon Kennedy <sffjunkie+code@gmail.com>

__all__ = ['FlacHandler']

import os
import struct

from mogul.locale import localize
_ = localize.get_translator('mogul.media')

from mogul.media import (MediaHandler,
        MediaContainer, MediaEntry, MediaStream,
        AudioStreamInfo, MediaHandlerError)

from mogul.media.tag import Tag, TagTarget, TagGroup
from mogul.media.element import Element
from mogul.media.attachment import Image


FLAC_SIG = b'\x66\x4c\x61\x43'
FLAC_MIMETYPE = 'audio/flac'

# See https://xiph.org/flac/id.html for IDs
FLAC_APPLICATIONS = {
    b'ATCH': 'FlacFile',
    b'BSOL': 'beSolo',
    b'BUGS': 'Bugs Player',
    b'Cues': 'GoldWave cue points',
    b'Fica': 'CUE Splitter',
    b'Ftol': 'flac-tools',
    b'MOTB': 'MOTB MetaCzar',
    b'MPSE': 'MP3 Stream Editor',
    b'MuML': 'MusicML: Music Metadata Language',
    b'RIFF': 'Sound Devices RIFF chunk storage',
    b'SFFL': 'Sound Font FLAC',
    b'SONY': 'Sony Creative Software',
    b'SQEZ': 'flacsqueeze',
    b'TtWv': 'TwistedWave',
    b'UITS': 'UITS Embedding tools',
    b'aiff': 'FLAC AIFF chunk storage',
    b'imag': 'flac-image application for storing arbitrary files in APPLICATION metadata blocks',
    b'peem': 'Parseable Embedded Extensible Metadata',
    b'qfst': 'QFLAC Studio',
    b'riff': 'FLAC RIFF chunk storage',
    b'tune': 'TagTuner',
    b'xbat': 'XBAT',
    b'xmcd': 'xmcd',
}


class FlacWarning(UserWarning):
    pass


class FlacError(Exception):
    pass


class FlacHandler(MediaHandler):
    def __init__(self):
        super(FlacHandler, self).__init__()
        
        self._ds = None
        self._media_entry = None
        self._stream = None
        self._tag_group = None

        self._elements = {
            0: Element(_('Stream Info'), self._read_stream_info),
            1: Element(_('Padding'), self._read_padding),
            2: Element(_('Application'), self._read_application),
            3: Element(_('Seek Table'), self._read_seek_table),
            4: Element(_('Vorbis Comment'), self._read_vorbis_comments),
            5: Element(_('Cue Sheet'), self._read_cue_sheet),
            6: Element(_('Picture'), self._read_picture),
        }

    @staticmethod
    def can_handle(ds):
        """Return the FLAC MIME type if the data stream is a FLAC data stream"""
        
        sig = ds.read(4)
        ds.seek(-4, os.SEEK_CUR)
        
        if sig == FLAC_SIG:
            return FLAC_MIMETYPE

        return None

    def read(self, filename, doctype=None, **kwargs):
        with open(filename, 'rb') as ds:
            self.filename = filename
            if doctype is None:
                doctype = self.can_handle(ds)
    
            if doctype is not None:
                self.read_ds(ds, doctype, **kwargs)
            else:
                raise FlacError("FlacHandler: Unable to handle file '%s'" % filename)

    def read_ds(self, ds, doctype=None, **kwargs):
        only_metadata = kwargs.get('only_metadata', True)
        foreign_metadata = kwargs.get('foreign_metadata', False)

        if doctype is None:
            doctype = self.can_handle(ds)

        if doctype is not None:
            self.container = MediaContainer(FLAC_MIMETYPE)
            self._media_entry = MediaEntry()
            self.container.entries.append(self._media_entry)
    
            ds.seek(4, os.SEEK_SET)
            self._ds = ds

            last_metadata = 0
            while not last_metadata:
                last_metadata = self._read_block(foreign_metadata)
            
            if only_metadata:
                return
            
            self._media_entry.streams[0].data = self._ds.read(-1)
        else:
            raise MediaHandlerError("FlacHandler: Unable to handle stream")

    def _read_block(self, foreign_metadata=False):
        block_info = ord(self._ds.read(1))
        block_size = _read_24bit_int(self._ds)
        
        last_block = (block_info & 128) >> 7
        block_type = block_info & 127
        
        handler = self._elements[block_type].reader
        handler(block_size)
        
        return last_block

    def _read_stream_info(self, block_size):
        stream = MediaStream()
        stream_info = AudioStreamInfo()
        
        _min_block_size, _max_block_size = struct.unpack('>HH', self._ds.read(4))
        _min_frame_size = _read_24bit_int(self._ds)
        _max_frame_size = _read_24bit_int(self._ds)
        
        data = self._ds.read(8)
        stream_info.sample_rate = (data[0] << 12) | (data[1] << 4) | ((data[2] & 0xF0) >> 4)
        stream_info.channels = ((data[2] & 0x0E) >> 1) + 1
        stream_info.bits_per_sample = ((data[2] & 0x01) | ((data[3] & 0xF0) >> 4)) + 1
        stream_info.sample_count = ((data[3] & 0x0F) << 32) | (data[4] << 24) | (data[5] << 16) | (data[6] << 8) | data[7]
        stream_info.md5 = self._ds.read(16)
        
        stream.stream_info = stream_info
        self._media_entry.streams.append(stream)
        
    def _read_padding(self, block_size):
        self._ds.seek(block_size, os.SEEK_CUR)
        
    def _read_application(self, block_size, root=False):
        if 'apps' not in self.container.metadata:
            self.container.metadata['apps'] = {}
            
        app_id = self._ds.read(4)
        application_data = self._ds.read(block_size - 4)
        
        self.container.metadata['apps'][app_id] = application_data
        
    def _read_seek_table(self, block_size):
        self._ds.seek(block_size, os.SEEK_CUR)
        
    def _read_vorbis_comments(self, block_size):
        vendor_len = struct.unpack('<L', self._ds.read(4))[0]
        vendor = self._ds.read(vendor_len)
        
        if 'vendor' not in self.container.metadata: 
            self.container.metadata['vendor'] = vendor
        
        comment_count = struct.unpack('<L', self._ds.read(4))[0]
        data = self._ds.read(block_size - vendor_len - 8)

        if self._tag_group is None:
            self._tag_group = TagGroup()
            
            tag_target = TagTarget(target_type=30)
            self._tag_group.targets.append(tag_target)
        
        start = 0
        for _idx in range(comment_count):
            comment_length = struct.unpack('<L', data[start:start + 4])[0]
            start += 4
            comment_data = data[start:start + comment_length]
            start += comment_length
            
            comment = comment_data.decode('UTF-8')
            name, value = comment.split('=')

            tag = Tag(name, value)
            self._tag_group.tags.append(tag)
        
    def _read_cue_sheet(self, block_size):
        self._ds.seek(block_size, os.SEEK_CUR)
        
    def _read_picture(self, block_size):
        picture_type, mime_type_length = struct.unpack('>LL', self._ds.read(8))
        mime_type = self._ds.read(mime_type_length)
        mime_type = mime_type.decode('ASCII')

        description_length = struct.unpack('>L', self._ds.read(4))[0]
        description = None
        if description_length:
            description = self._ds.read(description_length)
            description = description.decode('UTF-8')

        width, height, _color_depth, _color_count, data_length = \
            struct.unpack('>LLLLL', self._ds.read(20))
        picture_data = self._ds.read(data_length)
        
        image = Image(image_type=picture_type,
                      mime_type=mime_type,
                      data=picture_data)
        image.width = width
        image.height = height
        if description:
            image.description = description
        self.container.attachments.append(image)

    
def _read_24bit_int(ds):
    data = ds.read(3)
    return (data[0] << 16) + (data[1] << 8) + data[2]
