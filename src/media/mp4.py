# Copyright (c) 2009-2014 Simon Kennedy <sffjunkie+code@gmail.com>

__all__ = ['MP4Handler']

import os
import uuid
import struct
import datetime
import logging

from mogul.media import localize
_ = localize()

from mogul.media.id3_info import ID3_GENRE
from mogul.media.image import Image
from mogul.media import MediaContainer, MediaEntry, MediaStream, \
        AudioStreamInfo, VideoStreamInfo, Tag, TagTarget, TagGroup, \
        MediaHandlerError
from mogul.media.element import Element
from mogul.media.xmp import XMPHandler

class MP4Warning(UserWarning):
    pass


class MP4Exception(Exception):
    pass

"""
moov
    mvhd - Global Header
    prfl*
    trak+ - Track
        tkhd
        edts
            elst
        mdia
            mdhd - Media Header
            hdlr*
            minf
                vmhd? - Video Header
                smhd? - Sound Header
                hdlr*
                dinf
                stbl
                    stsd
                    stco
                    co64
                    stts
                    stss
                    stsc
                    stsz
        meta* - Track Metadata
    trak
    trak
    udta
        meta* - Global Metadata
            hdlr*
            mhdr
            keys
            ilst
            _elements
            ctry
            lang
..
mdat
    [data]
"""


class MP4Handler(object):
    def __init__(self):
        self.container = MediaContainer()

        self._ds = None
        self._stream = None
        self._media_entry = None
        self._tag_group = None
        self._tag_target = None
        self._languages = None
        self._countries = None
        self.logger = logging.getLogger('mogul.media')

        self._elements = {
            b'clip': Element(_('Clipping')),
            b'cmov': Element(_('Compressed Movie')),
            b'crgn': Element(_('Clipping Region')),
            b'cslg': Element(_('Composition Shift Least Greatest')),
            b'ctab': Element(_('Colour Table'), self._read_ctab),
            b'ctry': Element(_('Country'), self._read_ctry),
            b'dinf': Element(_('Data Information'), self._read_dinf),
            b'dref': Element(_('Data Reference'), self._read_dref),
            b'edts': Element(_('Edit')),
            b'elst': Element(_('Edit List')),
            b'free': Element(_('Free')),
            b'ftyp': Element(_('File type'), self._read_ftyp),
            b'gmhd': Element(_('Base Media Information Header')),
            b'hdlr': Element(_('Handler'), self._read_hdlr),
            b'ilst': Element(_('Item List'), self._read_ilst),
            b'kmat': Element(_('Compressed Matte')),
            b'lang': Element(_('Language'), self._read_lang),
            b'matt': Element(_('Track Matte')),
            b'mdat': Element(_('Media data'), self._read_mdat),
            b'mdhd': Element(_('Media Header'), self._read_mdhd),
            b'mdia': Element(_('Media box'), self._read_mdia),
            b'meta': Element(_('Metadata'), self._read_meta),
            b'minf': Element(_('Media Info'), self._read_minf),
            b'moov': Element(_('Movie'), self._read_moov),
            b'mvhd': Element(_('Movie Header'), self._read_mvhd),
            b'name': Element(_('Name'), self._read_name),
            b'rmra': Element(_('Reference Movie')),
            b'prfl': Element(_('Profile')),
            b'sbgp': Element(_('Sample-to-Group')),
            b'sdtp': Element(_('Sample Dependency Flags')),
            b'sgpd': Element(_('Sample Group Description')),
            b'skip': Element(_('Skip')),
            b'smhd': Element(_('Sound Media Information Header'), self._read_smhd),
            b'stbl': Element(_('Sample Table'), self._read_stbl),
            b'stco': Element(_('Chunk Offset')),
            b'stps': Element(_('Partial Sync Sample')),
            b'stsc': Element(_('Sample-to-Chunk')),
            b'stsd': Element(_('Sample Description'), self._read_stsd),
            b'stss': Element(_('Sync Sample')),
            b'stsz': Element(_('Sample Size')),
            b'stts': Element(_('Time To Sample')),
            b'stsh': Element(_('Shadow Sync')),
            b'tkhd': Element(_('Track Header'), self._read_tkhd),
            b'trak': Element(_('Track'), self._read_trak),
            b'udta': Element(_('User Data'), self._read_udta),
            b'vmhd': Element(_('Video Media Information Header'), self._read_vmhd),
            b'wide': Element(_('64 Bit Expansion')),
            b'XMP_': Element(_('XMP MetaData'), self._read_xmp),
        }
        
        self._tagname_mapping = {
            '@alb': 'TITLE'
        }
        
        self.__attribute_accessors = {
            'doctype': lambda: b'mp4',
            'title': b'\xA9nam',
            'artist': b'\xA9ART',
            'album_artist': b'\aART',
            'album': b'\xA9alb',
            'track': b'trkn',
            'release_date': b'\xA9day',
            'writer': b'\xA9wrt',
            'comment': b'',
            'genre': self._get_id3_genre,
            'compilation': b'cpil',
            'gapless': b'pgap',
            'encoder': b'\xA9too',
            'lyrics': b'\xA9lyr',
        }
        
        self.__audio_formats = [b'NONE', b'raw ', b'twos', b'sowt', b'MAC3',
                              b'MAC6', b'ima4', b'fl32', b'fl64', b'in24',
                              b'in32', b'ulaw', b'alaw',
                              b'\x6d\x73\x00\x02', b'\x6d\x73\x00\x11',
                              b'dvca', b'QDMC', b'QDM2', b'Qclp',
                              b'\x6d\x73\x00\x55',
                              b'.mp3', b'mp4a', b'alac']
        
        self.__visual_formats = [b'cvid', b'jpeg', b'smc ', b'rle ', b'rpza',
                              b'kpcd', b'png ', b'mjpa', b'mjpb', b'SVQ1',
                              b'mp4v', b'dvc ', b'dvcp', b'gif ', b'h263',
                              b'tiff', b'raw ', b'2vuY', b'yuv2', b'v308',
                              b'v408', b'v216', b'v410', b'v210',
                              b'avc1']

        self.__metadata_formats = [b'mp4s']
        
        self.__text_formats = [b'text']
            
    def __getattr__(self, attr):
        accessor = self.__attribute_accessors.get(attr, None)
        
        if accessor is not None:
            if callable(accessor):
                return accessor()
            else:
                for entry in self.container.entries:
                    tag = entry.tags.find(accessor)
                    if tag is not None:
                        return tag.value

                raise AttributeError("Attribute '%s' not found in file." % attr)
        else:
            raise AttributeError("Unknown attribute '%s'." % attr)

    @staticmethod
    def can_handle(ds):
        doctype = None
        data = ds.read(8)
        ds.seek(-8, os.SEEK_CUR)
        
        if data[4:8] == b'ftyp':
            doctype = 'application/mp4'

        return doctype

    def read(self, filename, doctype=None):
        with open(filename, 'rb') as ds:
            self.filename = filename
            if doctype is None:
                doctype = self.can_handle(ds)
    
            if doctype is not None:
                size = os.stat(filename).st_size
                self.read_stream(ds, size)
            else:
                raise Exception("MP4Handler: Unable to handle file '%s'" % filename)

    def read_stream(self, ds, doctype=None):
        if doctype is None:
            doctype = self.can_handle(ds)

        if doctype is not None:
            self._ds = ds

            size_read = 0
            try:
                while True:
                    size_read += self._read_box('root')
            except StopIteration:
                pass
            
            return size_read
        else:
            raise MediaHandlerError("MP4Handler: Unable to handle stream")

    def _read_box(self, parent):
        size_left = element_size = self._read_long()
        if element_size == 0:
            return 4
        
        if element_size == 1:
            element_size = self._read_quad()
        
        element_type = self._ds.read(4)
        size_read = 8
        size_left -= 8

        if size_left == 1:
            element_size = self._read_quad()
            size_read += 8
            element_size -= 8

        if element_type == b'uuid':
            data = self._ds.read(16)
            element_type = uuid.UUID(bytes=data)
            size_read += 16
            size_left -= 16

        offset = self._ds.tell() - size_read
        self.logger.debug('MP4:  Reading box %s at offset %d, size %d' % (element_type, offset, element_size))

        if element_size > 0:
            try:
                elem = self._elements[element_type]
                handler = elem.reader
            except:
                self.logger.debug('MP4:  No handler for box %s available' % element_type)
                handler = None
    
            if handler is not None:
                handler(parent, size_left)
            else:
                self._ds.seek(size_left, os.SEEK_CUR)

            size_read += size_left

        return size_read
        
    def _read_ftyp(self, parent, element_size):
        """File Type"""
        
        data = self._ds.read(8)
        self.brand, self.version = struct.unpack('>4sL', data)
        
        data_len = element_size - 8
        data = self._ds.read(data_len)
        fmt_str = '>%s' % ('4s' * int(data_len / 4))
        self.compatible_brands = []
        for cb in struct.unpack(fmt_str, data):
            if cb != '\x00\x00\x00\x00':
                self.compatible_brands.append(cb)
            
        return element_size
    
    def _read_mdat(self, parent, element_size):
        self._ds.seek(element_size, os.SEEK_CUR)
            
        return element_size

    def _read_moov(self, parent, element_size):
        """Movie"""
        
        self._media_entry = MediaEntry()
        self.container.entries.append(self._media_entry)
        
        size_read = 0
        while size_read < element_size:
            size_read += self._read_box('moov')
            
        return size_read
    
    def _read_mvhd(self, parent, element_size):
        """Movie Header"""

        data = self._ds.read(1)
        version = ord(data)
        _flags = mp4_read_uint(self._ds, 3)
        size_read = 4
        
        if version == 0:
            mvhd_format = '>LLLLLH2x8x36s24xL'
        else:
            mvhd_format = '>QQLQLH2x8x36s24xL'

        # preview time, preview duration, poster time,
        # selection time, selection duration & current time
        # are Quicktime specific and not used in MP4 files
        data = self._ds.read(element_size-size_read)
        ctime, mtime, \
            self._media_entry.time_scale, self._media_entry.duration, \
            self._media_entry.rate, self._media_entry.volume, \
            self._media_entry.matrix, \
            self._media_entry.next_track = \
            struct.unpack(mvhd_format, data)
        
        self._media_entry.duration_secs = round(float(self._media_entry.duration) / self._media_entry.time_scale)
        
        base = datetime.datetime(1904, 1, 1, 0, 0, 0)
        delta = datetime.timedelta(seconds=ctime)
        self._media_entry.ctime = base + delta
        delta = datetime.timedelta(seconds=mtime)
        self._media_entry.mtime = base + delta
        
        return element_size
    
    def _read_trak(self, parent, element_size):
        """Track"""
        
        self._stream = MediaStream()
        self._media_entry.streams.append(self._stream)
        
        size_read = 0
        while size_read < element_size:
            size_read += self._read_box('trak')
    
        assert(size_read == element_size)
        return size_read
    
    def _read_tkhd(self, parent, element_size):
        """Track Header"""
        
        version = ord(self._ds.read(1))
        flags = mp4_read_uint(self._ds, 3)
        
        self._stream.enabled = (flags & 0x01) == 0x01 
        
        if version == 0:
            tkhd_format = '>LLL8xL4xH2xH2x36sLL'
        else:
            tkhd_format = '>QQL8xQ4xH2xH2x36sLL'
            
        ctime, mtime, \
            self._stream.id, duration,  \
            self._stream.layer, self._stream.volume, self._stream.matrix, \
            self._stream.width, self._stream.height = \
            struct.unpack(tkhd_format, self._ds.read(element_size-4))

        if duration == 0:
            self._stream.duration = self._media_entry.duration
            self._stream.duration_secs = self._media_entry.duration_secs
        else:
            self._stream.duration_secs = round(float(duration) / self._media_entry.time_scale)
        
        base = datetime.datetime(1904, 1, 1, 0, 0, 0)
        if ctime != 0:
            delta = datetime.timedelta(seconds=ctime)
            self._stream.ctime = base + delta
        else:
            self._stream.ctime = self._media_entry.ctime
        
        if mtime != 0:    
            delta = datetime.timedelta(seconds=mtime)
            self._stream.mtime = base + delta
        else:
            self._stream.mtime = self._media_entry.mtime
        
        #self._ds.seek(element_size, os.SEEK_CUR)
        return element_size
    
    def _read_mdia(self, parent, element_size):
        """Media box"""
        
        size_read = 0
        while size_read < element_size:
            size_read += self._read_box('mdia')
    
        assert(size_read == element_size)
        return size_read
    
    def _read_mdhd(self, parent, element_size):
        """Media Header"""
        
        version = ord(self._ds.read(1))
        _flags = mp4_read_uint(self._ds, 3)
        
        if version == 0:
            unpack_fmt = '>LLLLHH'
        elif version == 1:
            unpack_fmt = '>QQLQHH'
        else:
            self.logger.debug("Unknown Media Header box 'mdhd' version %d" % version)

        stream = self._stream
        ctime, mtime, \
            stream.time_scale, self._stream.duration, \
            lang, \
            stream.quality = struct.unpack(unpack_fmt, self._ds.read(element_size-4))
        
        base = datetime.datetime(1904, 1, 1, 0, 0, 0)
        delta = datetime.timedelta(seconds=ctime)
        stream.ctime = base + delta
        delta = datetime.timedelta(seconds=mtime)
        stream.mtime = base + delta
            
        stream.duration_secs = round(float(stream.duration) / stream.time_scale)
        
        if lang != 0:
            stream.language = self._get_language(lang)
        else:
            stream.language = 'und'
        
        return element_size

    def _read_hdlr(self, parent, element_size):
        """Handler"""
        
        version = ord(self._ds.read(1))
        flags = mp4_read_uint(self._ds, 3)
        if flags != 0:
            self.logger.debug("Non zero 'flags' in 'hdlr' box")

        if version == 0:
            component_type, component_subtype, \
                _component_manufacturer, \
                _component_flags, _component_flags_mask = \
                struct.unpack('>4s4s4sLL', self._ds.read(20))
    
            if self.brand.startswith(b'qt'):
                length, name = self._read_pascal_string()
            else:
                length, name = self._read_utf8_string()

            size_read = 24 + length + 1
            if element_size > size_read:
                #TODO: Determine what this extra data is for
                self.logger.debug('MP4:  ** Extra data found, previous assumption is correct')
                _unknown = self._ds.read(element_size-size_read)
                
            if parent == 'mdia' or (parent == 'minf' and self._stream is None):
                if component_subtype == b'vide':
                    self._stream.media_type_info = VideoStreamInfo()
                elif component_subtype == b'soun':
                    self._stream.media_type_info = AudioStreamInfo()
        else:
            self.logger.debug('MP4:  Unknown hdlr box version %d' % version)
        
        return element_size
    
    def _read_minf(self, parent, element_size):
        """Media Info"""
        
        size_read = 0
        while size_read < element_size:
            size_read += self._read_box('minf')
            
        return size_read
    
    def _read_smhd(self, parent, element_size):
        """Sound Media Header"""
        
        version = ord(self._ds.read(1))
        _flags = mp4_read_uint(self._ds, 3)
        
        if version != 0:
            self.logger.debug("Unknown Sound Media Header box 'smhd' version %d" % version)

        self._stream.media_type_info.balance = struct.unpack('>H2x', self._ds.read(4))[0]
        
        return element_size
    
    def _read_vmhd(self, parent, element_size):
        """Video Media Header"""
        
        _version = ord(self._ds.read(1))
        _flags = mp4_read_uint(self._ds, 3)
        
        _mode, _opcolor1, _opcolor2, _opcolor3 = struct.unpack('>HHHH', self._ds.read(8))
        
        return element_size

    def _read_dinf(self, parent, element_size):
        """Data Information"""
        
        size_read = 0
        while size_read < element_size:
            size_read += self._read_box('dinf')
            
        return size_read
    
    #TODO: We don't actually do anything with dref information. Should we?
    def _read_dref(self, parent, element_size):
        """Data Reference"""
        
        _version = ord(self._ds.read(1))
        _flags = mp4_read_uint(self._ds, 3)

        entry_count = struct.unpack('>L', self._ds.read(4))[0]

        if entry_count > 0:
            #if self._stream.media_data_info is None:            
            #    self._stream.media_data_info = []
                
            for _x in range(entry_count):
                dref = {}
                
                ref_size, ref_type, _ref_ver = \
                    struct.unpack('>L4sB', self._ds.read(9))

                flags = mp4_read_uint(self._ds, 3)
                dref['external'] = flags & 0x01
                
                data = ''    
                if ref_size > 12:
                    data = self._ds.read(ref_size - 12)

                dref[ref_type] = data
                #self._stream.media_data_info.append(dref)
                
        return element_size

    def _read_stbl(self, parent, element_size):
        """Sample Table"""
        
        size_read = 0
        while size_read < element_size:
            size_read += self._read_box('stbl')
    
        assert(size_read == element_size)
        return size_read

    def _read_stsd(self, parent, element_size):
        """Sample Description"""
        
        _version = ord(self._ds.read(1))
        _flags = mp4_read_uint(self._ds, 3)

        entry_count = struct.unpack('>L', self._ds.read(4))[0]
        size_read = 8
        
        for _x in range(entry_count):
            data_size, sample_format, _dref_index = \
                struct.unpack('>L4s6xH', self._ds.read(16))

            self._stream.codec = sample_format
                
            if data_size > 16:
                if sample_format in self.__audio_formats:
                    self._read_audio_sample_entry(data_size - 16)
                elif sample_format in self.__visual_formats:
                    self._read_visual_sample_entry(data_size - 16)
                elif sample_format in self.__metadata_formats:
                    self._read_metadata_sample_entry(data_size - 16)
                elif sample_format in self.__text_formats:
                    self._read_text_sample_entry(data_size - 16)
                else:
                    self._ds.seek(data_size - 16, os.SEEK_CUR)
                    self.logger.debug("Unknown sample data format '%s'" % str(sample_format))
                    
            size_read += data_size

        assert size_read == element_size                    
        return size_read
    
    def _read_visual_sample_entry(self, element_size):
        type_info = self._stream.media_type_info
                
        _version, _revision, _vendor, \
            _temporal_quality, _spatial_quality, \
            _width, _height, _hdpi_int, _hdpi_frac, _vdpi_int, _vdpi_frac, \
            _resv, _frame_count, compressor_len = \
            struct.unpack('>HHLLLHHHHHHLHB', self._ds.read(35))
            
        size_read = 35
        
        _compressor = self._ds.read(31)[:compressor_len]
        size_read += 31
            
        depth, color_table_id = struct.unpack('>Hh', self._ds.read(4))
        size_read += 4
                
        if depth == 1:
            type_info.color = False
            type_info.bits_per_pixel = 1
        elif depth > 1 and depth <= 32:
            type_info.color = True
            type_info.bits_per_pixel = depth
        elif depth > 32:
            type_info.color = False
            type_info.bits_per_pixel = depth - 32                        
        
        if color_table_id == 0:
            size_read += self._read_color_table()

        size_left = element_size - size_read
        if size_left > 0:
            size_read = 0
            while size_read < size_left:
                data_length = struct.unpack('>L', self._ds.read(4))[0]
                size_read += 4
                
                if data_length > 4:
                    data_format = self._ds.read(4)
                    size_read += 4
                    
                    if data_format == b'esds':
                        self._read_esds(data_length - 8)
                    elif data_format == b'avcC':
                        self._read_avcC(data_length - 8)
                    else:
                        self._ds.seek(data_length-8, os.SEEK_CUR)
                        
                    size_read += data_length-8
    
    def _read_audio_sample_entry(self, element_size):
        type_info = self._stream.media_type_info
                
        version, _revision, _vendor, \
        channels, sample_size, \
        _compression_id, _packet_size, \
        sample_rate_int, sample_rate_frac = \
        struct.unpack('>HHLHHHHHH', self._ds.read(20))
        
        size_read = 20
        
        type_info.channels = channels
        type_info.sample_size = sample_size
        type_info.sample_rate = \
            float("%d.%d" % (sample_rate_int, sample_rate_frac))

        if version == 1:
            _samples_per_packet, _bytes_per_packet, \
                _bytes_per_frame, _bytes_per_sample = \
                struct.unpack('>LLLL', self._ds.read(16))
            
            size_read += 16
        
        while size_read < element_size:
            data_length, data_format = struct.unpack('>L4s', self._ds.read(8))
            
            if data_format == b'esds':
                self._read_esds(data_length - 8)
            elif data_format == b'alac':
                self._ds.seek(data_length-8, os.SEEK_CUR)
            else:
                type_info.codec_data = self._ds.read(data_length - 8)

            size_read += data_length
    
    def _read_metadata_sample_entry(self, element_size):
        data_length, data_format = struct.unpack('>L4s', self._ds.read(8))
        
        if data_format == b'esds':
            self._read_esds(data_length - 8)

    def _read_text_sample_entry(self, element_size):
        self._ds.seek(element_size, os.SEEK_CUR)
    
    def _read_color_table(self):
        return 0
    
    def _read_stsz(self, parent, element_size):
        """Sample Size"""
        
        _version = ord(self._ds.read(1))
        _flags = mp4_read_uint(self._ds, 3)

        sample_size, count = struct.unpack('>LL', self._ds.read(8))
        if sample_size == 0 and count > 0:
            _data = self._ds.read(count*4)
        else:
            pass

        return element_size

    def _read_stts(self, parent, element_size):
        """Time to Sample"""
        
        _version = ord(self._ds.read(1))
        _flags = mp4_read_uint(self._ds, 3)

        count = struct.unpack('>L', self._ds.read(4))[0]
        for _x in range(count):
            _sample_count, _sample_duration = struct.unpack('>LL', self._ds.read(8))
        
        return element_size

    def _read_esds(self, element_size):
        """Elementary Stream Descriptor"""
        
        version = ord(self._ds.read(1))
        _flags = mp4_read_uint(self._ds, 3)
        size_read = 4
        
        if version == 0:
            while size_read < element_size:
                tag_type = ord(self._ds.read(1))
                size_read += 1
                
                if tag_type == 0x03:
                    length, byte_count = self._read_descriptor_length()
                    size_read += byte_count
                    _stream_id, _stream_priority = struct.unpack('>HB', self._ds.read(3))
                    size_read += 3
    
                    #self._stream.codec['stream_id'] = stream_id
                    #self._stream.codec['stream_priority'] = stream_priority
                    
                    if ord(self._ds.read(1)) == 0x04:
                        length, byte_count = self._read_descriptor_length()
                        size_read += (1 + byte_count)
    
                        _object_type, _stream_type, _buffer_size, \
                        _bitrate_max, _bitrate_avg = struct.unpack('>BB3sLL', self._ds.read(13))
                        size_read += 13
    
                        #self._stream.codec['buffer_size'] = buffer_size
                        #self._stream.codec['bitrate_max'] = bitrate_max
                        #self._stream.codec['bitrate_avg'] = bitrate_avg

                        if ord(self._ds.read(1)) == 0x05:
                            length, byte_count = self._read_descriptor_length()
                            self._ds.seek(length, os.SEEK_CUR)
                            size_read += (1 + byte_count + length)
                            
                    
                elif tag_type == 0x06:
                    length, byte_count = self._read_descriptor_length()
                    self._ds.seek(length, os.SEEK_CUR)
                    size_read += (byte_count + length)
        
        return element_size

    def _read_alac(self, element_size):
        """Apple Lossless Stream Descriptor"""
        
        _version = ord(self._ds.read(1))
        _flags = mp4_read_uint(self._ds, 3)
        
        _max_samples_per_frame, _sample_size, _history_mult, _initial_history, \
        _modifier, _channels, _max_coded_frame_size, _bitrate, _sample_rate = \
        struct.unpack('>LxBBBBB2xLLL', self._ds.read(element_size-4))

        return element_size

    def _read_avcC(self, element_size):
        self._ds.seek(element_size, os.SEEK_CUR)
        return element_size
    
    def _read_ctab(self, parent, element_size):
        """Color Table"""
        
        seed, flags, table_size = struct.unpack('>LHH', self._ds.read(8))
        if seed == 0 and flags == 0x8000:
            for _x in range(table_size+1):
                _red, _green, _blue = struct.unpack('>2xHHH', self._ds.read(8))
        else:
            self._ds.seek((table_size+1)*8)
        
        return element_size
            
    def _read_udta(self, parent, element_size):
        """User Data"""
        
        size_read = 0
        while size_read < element_size:
            size_read += self._read_box('udta')
    
        assert(size_read == element_size)
        return size_read

    def _read_name(self, parent, element_size):
        _s = self._ds.read(element_size)
    
    def _read_meta(self, parent, element_size):
        """Metadata"""
        
        _version = ord(self._ds.read(1))
        _flags = mp4_read_uint(self._ds, 3)
        
        size_read = 4
        while size_read < element_size:
            size_read += self._read_box('meta')
    
        assert(size_read == element_size)
        return size_read

    def _read_lang(self, parent, element_size):
        """Language"""
        
        version = ord(self._ds.read(1))
        flags = mp4_read_uint(self._ds, 3)

        if version == 0:            
            entry_count = struct.unpack('>L', self._ds.read(4))[0]

            if flags != 0:
                self.logger.debug("Non zero 'flags' in 'lang' box")

            self._languages = []
            for _x in range(entry_count):
                count = struct.unpack('>H', self._ds.read(2))
                
                items = struct.unpack('>%04dH' % count, self._ds.read(2 * count))
                
                for item in items:
                    self._languages.append(self._get_language(item))
        else:
            self.logger.debug("Unknown Language box 'lang' version %d" % version)
            self._ds.seek(element_size-4, os.SEEK_CUR)

        return element_size

    def _read_ctry(self, parent, element_size):
        """Country"""
        
        version = ord(self._ds.read(1))
        flags = mp4_read_uint(self._ds, 3)
        if flags != 0:
            self.logger.debug("Non zero 'flags' in 'ctry' box")

        if version == 0:            
            entry_count = struct.unpack('>L', self._ds.read(4))[0]

            self._countries = []
            for _x in range(entry_count):
                count = struct.unpack('>H', self._ds.read(2))
                
                items = struct.unpack('>%s' % ('2s' * count), self._ds.read(2 * count))
                
                for item in items:
                    self._countries.append(item)
        else:
            self._ds.seek(element_size-4, os.SEEK_CUR)
            self.logger.debug("Unknown Country box 'ctry' version %d" % version)

        return element_size

    def _read_keys(self, parent, element_size):
        """Keys"""
        
        version = ord(self._ds.read(1))
        flags = mp4_read_uint(self._ds, 3)
        if flags != 0:
            self.logger.debug("Non zero 'flags' in '_elements' box")

        if version == 0:
            if self._stream._elements is None:
                self._stream._elements = []
            
            count = struct.unpack('>L', self._ds.read(4))[0]

            for _x in range(count):
                key_size, key_namespace = \
                    struct.unpack('>LL', self._ds.read(8))
                    
                key = self._ds.read(key_size)
                
                self._stream._elements.append((key_namespace, key))
        else:
            self.logger.debug("Unknown box '_elements' version %d" % version)
            self._ds.seek(element_size-4, os.SEEK_CUR)

        return element_size

    def _read_xmp(self, parent, element_size):
        handler = XMPHandler()
        handler.read_stream(self._ds, element_size)
        pass
    
    def _read_ilst(self, parent, element_size):
        """Item List"""
        
        if parent == 'meta':
            self._tag_group = TagGroup()
            self._tag_target = TagTarget()
            self._tag_group.targets.append(self._tag_target)
            self._media_entry.tag_groups.append(self._tag_group)

        size_read = 0
        while size_read < element_size:
            size_read += self._read_ilst_entry('ilst')

        assert(size_read == element_size)
        return size_read
    
    def _read_ilst_entry(self, parent):
        """Item List Entry"""
        
        size = struct.unpack('>L', self._ds.read(4))[0]
        size_read = 4

        if size != 0:
            tag = Tag()
            if self._tag_group is not None:
                self._tag_group.tags.append(tag)
        
            name = struct.unpack('>4s', self._ds.read(4))[0]
            size_read += 4
            if name == b'----':
                msize, _mean, _ver_flags = struct.unpack('>LLL', self._ds.read(12))
                app = self._ds.read(msize - 12).decode('UTF-8')

                nsize, _name, _ver_flags = struct.unpack('>LLL', self._ds.read(12))
                name = self._ds.read(nsize - 12).decode('UTF-8')
                size_read += (msize + nsize)
            else:
                app = ''

            while size_read < size:                
                dsize, element_name, dtype, dlocale = struct.unpack('>L4sLL', self._ds.read(16))
                size_read += 16
        
                data_size = dsize - 16
                if data_size > 0 and element_name == b'data':
                    value = self._decode_meta_data(name, dtype, self._ds.read(data_size))
                
                    tag.name = name
                    tag.value = value
                    tag.locale = self._get_locale(dlocale)
                    tag.app = app
                else:
                    self._ds.seek(data_size, os.SEEK_CUR)
                    
                size_read += data_size
        
        return size_read

    def _decode_meta_data(self, name, dtype, data):
        if dtype == 0x00:
            value = data
        elif dtype == 0x01:
            value = data.decode('UTF-8')
        elif dtype == 0x02:
            value = data.decode('UTF-16BE')
        elif dtype == 0x15:
            length = len(data) 
            if length == 1:
                value = ord(data)
            elif length == 2:
                value = struct.unpack('>H', data)[0]
            elif length == 4:
                value = struct.unpack('>L', data)[0]
            elif length == 8:
                value = struct.unpack('>Q', data)[0]
        elif dtype in [0x0C, 0x0D, 0x0E, 0x11]:
            if name == 'covr':
                image_type = 0x03
            else:
                image_type = 0x00
                
            value = Image(image_type, self._dtype_to_mime(dtype), data)
        else:
            # Track Number
            if name == b'trkn':
                value = struct.unpack('>2xHH2x', data[:8])
            # Disc number
            elif name == b'disk':
                value = struct.unpack('>2xHH', data[:6])
            elif name == b'gnre':
                if dtype == 0:
                    value = ID3_GENRE[struct.unpack('>H', data)[0]]
                else:
                    value = str(data)

        return value

    def _dtype_to_mime(self, dtype):
        """MP4 Data Type to Mime Type"""
        
        if dtype == 0x0C:
            return 'image/gif'
        elif dtype == 0x0D:
            return 'image/jpeg'
        elif dtype == 0x0E:
            return 'image/png'
        elif dtype == 0x11:
            return 'image/bmp'
        else:
            raise ValueError('Unknown MP4 data type %d' % dtype)
    
    def _read_byte_string(self):
        """Read a null terminated byte string"""
         
        length = 0
        string = b''
        while 1:
            ch = self._ds.read(1)
            
            if ch == b'\0':
                break
            
            length += 1
            string += ch

        return (length, string)
    
    def _read_pascal_string(self):
        length = ord(self._ds.read(1))
        string = self._ds.read(length)
        return (length, string)
    
    def _read_utf8_string(self):
        """Read a null terminated UTF-8 string"""
        
        length, data = self._read_byte_string()
        return (length, data.decode('utf-8'))

    def _read_descriptor_length(self):
        count = 0
        length = 0
        while True:
            value = ord(self._ds.read(1))
            length = (length << 7) | (value & 0x7f)
            count = count + 1
            
            if ((value & 0x80) == 0 or count == 4):
                break
            
        return (length, count)

    def _get_language(self, code):
        """Convert a language code into its string representation"""
        
        language = ''
        for x in range(3):        
            language += chr(((code >> ((2-x)*5)) & 0x1f) + 0x60)
            
        return language 

    def _get_locale(self, locale_id):
        """Convert a locale code into its string representation"""
        
        value = (locale_id >> 16) & 65535
        if value == 0:
            country = 'und'
        elif value < 256:
            if self._countries is not None:
                country = self._countries[value]
            else:
                raise IndexError("Attempting to access country but no 'ctry' box present")
        else:
            country = struct.unpack('>2s', value)
        
        value = locale_id & 65535
        if value == 0:
            language = 'und'
        elif value < 256:
            if self._languages is not None:
                language = self._languages[value]
            else:
                raise IndexError("Attempting to access language but no 'lang' box present")
        else:
            language = self._get_language(value)
    
        return (language, country)

    def _get_id3_genre(self):
        g = self.meta.get('gnre', None)
        if g is not None:
            index = struct.unpack('>H', g[0])[0] - 1
            return ID3_GENRE[index]
        else:
            raise AttributeError("Attribute 'genre' not found in file.")
        
    def _read_long(self):
        data = self._ds.read(4)
        if len(data) == 0:
            raise StopIteration
            
        return struct.unpack('>L', data)[0]
        
    def _read_quad(self):
        data = self._ds.read(8)
        if len(data) == 0:
            raise StopIteration
            
        return struct.unpack('>Q', data)[0]

def mp4_read_uint(ds, size):
    if size == 1:
        return ord(ds.read(1))
    elif size == 2:
        return struct.unpack('>H', ds.read(2))[0]
    elif size == 3:
        return struct.unpack('>L', b'\0' + ds.read(3))[0]
    elif size == 4:
        return struct.unpack('>L', ds.read(4))[0]
    elif size == 5:
        return struct.unpack('>Q', b'\0\0\0' + ds.read(5))[0]
    elif size == 6:
        return struct.unpack('>Q', b'\0\0' + ds.read(6))[0]
    elif size == 7:
        return struct.unpack('>Q', b'\0' + ds.read(7))[0]
    elif size == 8:
        return struct.unpack('>Q', ds.read(8))[0]
