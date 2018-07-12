# Copyright (c) 2009-2014 Simon Kennedy <sffjunkie+code@gmail.com>

import os
import struct
import uuid
import logging
from collections import namedtuple
from datetime import timedelta, datetime

from mogul.media import localize
_ = localize()

from mogul.media import MediaHandler
from mogul.media.element import Element
from mogul.media.id3 import ID3v1TagHandler, ID3v2TagHandler

from mogul.media import (MediaContainer, MediaEntry, MediaStream,
    AudioStreamInfo, VideoStreamInfo, ImageStreamInfo, MediaHandlerError)

ASF_GUID = b'\x30\x26\xb2\x75\x8e\x66\xcf\x11\xa6\xd9\x00\xaa\x00\x62\xce\x6c'

ASF_EXT_MIMETYPE = {
    '.asx': 'video/x-ms-asf',
    '.wma': 'audio/x-ms-wma',
    '.wax': 'audio/x-ms-wax',
    '.wmv': 'video/x-ms-wmv',
    '.wvx': 'video/x-ms-wvx',
    '.wm':  'video/x-ms-wm',
    '.wmx': 'video/x-ms-wmx',
    '.wmz': 'application/x-ms-wmz',
    '.wmd': 'application/x-ms-wmd',
}

MetadataInfo = namedtuple('MetadataInfo', 'stream name value lang')

class ASFError(Exception):
    pass


class ASFHandler(MediaHandler):
    def __init__(self):
        self.container = None
        
        self._ds = None
        self._media_entry = None
        self._media_stream = None
        self._tag_target = None
        self._attachment = None
        self.logger = logging.getLogger('mogul.media')
        
        # Name and Handler Function for each ASF GUID type.
        self._elements = {
            '75b22630-668e-11cf-a6d9-00aa0062ce6c':
                Element('ASF_Header', self._read_header),
            '75b22636-668e-11cf-a6d9-00aa0062ce6c':
                Element('ASF_Data'),
            '33000890-e5b1-11cf-89f4-00a0c90349cb':
                Element('ASF_Simple_Index'),
            'd6e229d3-35da-11d1-9034-00a0c90349be':
                Element('ASF_Index'),
            'feb103f8-12ad-4c64-840f-2a1d2f7ad48c':
                Element('ASF_Media_Object_Index'),
            '3cb73fd0-0c4a-4803-953d-edf7b6228f0c':
                Element('ASF_Timecode_Index'),
             
            '8cabdca1-a947-11cf-8ee4-00c00c205365':
                Element('ASF_File_Properties', self._read_file_properties),
            'b7dc0791-a9b7-11cf-8ee6-00c00c205365':
                Element('ASF_Stream_Properties', self._read_stream_properties),
            '5fbf03b5-a92e-11cf-8ee3-00c00c205365':
                Element('ASF_Header_Extension', self._read_header_extension),
            '86d15240-311d-11d0-a3a4-00a0c90348f6':
                Element('ASF_Codec_List', self._read_codec_list),
            '1efb1a30-0b62-11d0-a39b-00a0c90348f6':
                Element('ASF_Script_Command'),
            'f487cd01-a951-11cf-8ee6-00c00c205365':
                Element('ASF_Marker'),
            'd6e229dc-35da-11d1-9034-00a0c90349be':
                Element('ASF_Bitrate_Mutual_Exclusion'),
            '75b22635-668e-11cf-a6d9-00aa0062ce6c':
                Element('ASF_Error_Correction'),
            '75b22633-668e-11cf-a6d9-00aa0062ce6c':
                Element('ASF_Content_Description', self._read_content_description),
            'd2d0a440-e307-11d2-97f0-00a0c95ea850':
                Element('ASF_Extended_Content_Description', self._read_extended_content_description),
            '2211b3fa-bd23-11d2-b4b7-00a0c955fc6e':
                Element('ASF_Content_Branding'),
            '7bf875ce-468d-11d1-8d82-006097c9a2b2':
                Element('ASF_Stream_Bitrate_Properties', self._read_stream_bitrate_properties),
            '2211b3fb-bd23-11d2-b4b7-00a0c955fc6e':
                Element('ASF_Content_Encryption'),
            '298ae614-2622-4c17-b935-dae07ee9289c':
                Element('ASF_Extended_Content_Encryption'),
            '2211b3fc-bd23-11d2-b4b7-00a0c955fc6e':
                Element('ASF_Digital_Signature'),
            '1806d474-cadf-4509-a4ba-9aabcb96aae8':
                Element('ASF_Padding'),             
             
            'f8699e40-5b4d-11cf-a8fd-00805f5c442b':
                Element('ASF_Audio_Media'),
            'bc19efc0-5b4d-11cf-a8fd-00805f5c442b':
                Element('ASF_Video_Media'),
            '59dacfc0-59e6-11d0-a3ac-00a0c90348f6':
                Element('ASF_Command_Media'),
            'b61be100-5b4e-11cf-a8fd-00805f5c442b':
                Element('ASF_JFIF_Media'),
            '35907de0-e415-11cf-a917-00805f5c442b':
                Element('ASF_Degradable_JPEG_Media'),
            '91bd222c-f21c-497a-8b6d-5aa86bfc0185':
                Element('ASF_File_Transfer_Media'),
            '3afb65e2-47ef-40f2-ac2c-70a90d71d343':
                Element('ASF_Binary_Media'),
             
            '776257d4-c627-41cb-8f81-7ac7ff1c40cc':
                Element('ASF_Web_Stream_Media_Subtype'),
            'da1e6b13-8359-4050-b398-388e965bf00c':
                Element('ASF_Web_Stream_Format'),
             
            '20fb5700-5b55-11cf-a8fd-00805f5c442b':
                Element('ASF_No_Error_Correction'),
            'bfc3cd50-618f-11cf-8bb2-00aa00b4e220':
                Element('ASF_Audio_Spread'),
             
            'abd3d211-a9ba-11cf-8ee6-00c00c205365':
                Element('ASF_Reserved_1'),
            '7a079bb6-daa4-4e12-a5ca-91d38dc11a8d':
                Element('ASF_Content_Encryption_System_Windows_Media_DRM_Network_Devices'),
            '86d15241-311d-11d0-a3a4-00a0c90348f6':
                Element('ASF_Reserved_2'),
            '4b1acbe3-100b-11d0-a39b-00a0c90348f6':
                Element('ASF_Reserved_3'),
            '4cfedb20-75f6-11cf-9c0f-00a0c90349cb':
                Element('ASF_Reserved_4'),
             
            'd6e22a00-35da-11d1-9034-00a0c90349be':
                Element('ASF_Mutex_Language'),
            'd6e22a01-35da-11d1-9034-00a0c90349be':
                Element('ASF_Mutex_Bitrate'),
            'd6e22a02-35da-11d1-9034-00a0c90349be':
                Element('ASF_Mutex_Unknown'),
             
            'af6060aa-5197-11d2-b6af-00c04fd908e9':
                Element('ASF_Bandwidth_Sharing_Exclusive'),
            'af6060ab-5197-11d2-b6af-00c04fd908e9':
                Element('ASF_Bandwidth_Sharing_Partial'),
             
            '399595ec-8667-4e2d-8fdb-98814ce76c1e':
                Element('ASF_Payload_Extension_System_Timecode'),
            'e165ec0e-19ed-45d7-b4a7-25cbd1e28e9b':
                Element('ASF_Payload_Extension_System_File_Name'),
            'd590dc20-07bc-436c-9cf7-f3bbfbf1a4dc':
                Element('ASF_Payload_Extension_System_Content_Type'),
            '1b1ee554-f9ea-4bc8-821a-376b74e4c4b8':
                Element('ASF_Payload_Extension_System_Pixel_Aspect_Ratio'),
            'c6bd9450-867f-4907-83a3-c77921b733ad':
                Element('ASF_Payload_Extension_System_Sample_Duration'),
            '6698b84e-0afa-4330-aeb2-1c0a98d7a44d':
                Element('ASF_Payload_Extension_System_Encryption_Sample_ID'),

            '14e6a5cb-c672-4332-8399-a96952065b5a':
                Element('ASF_Extended_Stream_Properties'),
            'a08649cf-4775-4670-8a16-6e35357566cd':
                Element('ASF_Advanced_Mutual_Exclusion'),
            'd1465a40-5a79-4338-b71b-e36b8fd6c249':
                Element('ASF_Group_Mutual_Exclusion'),
            'd4fed15b-88d3-454f-81f0-ed5c45999e24':
                Element('ASF_Stream_Prioritization'),
            'a69609e6-517b-11d2-b6af-00c04fd908e9':
                Element('ASF_Bandwidth_Sharing'),
            '7c4346a9-efe0-4bfc-b229-393ede415c85':
                Element('ASF_Language_List', self._read_language_list),
            'c5f8cbea-5baf-4877-8467-aa8c44fa4cca':
                Element('ASF_Metadata', self._read_metadata),
            '44231c94-9498-49d1-a141-1d134e457054':
                Element('ASF_Metadata_Library', self._read_metadata_library),
            'd6e229df-35da-11d1-9034-00a0c90349be':
                Element('ASF_Index_Parameters'),
            '6b203bad-3f11-48e4-aca8-d7613de2cfa7':
                Element('ASF_Media_Object_Index_Parameters'),
            'f55e496d-9797-4b5d-8c8b-604dfe9bfb24':
                Element('ASF_Timecode_Index_Parameters'),
            '43058533-6981-49e6-9b74-ad12cb86d58c':
                Element('ASF_Advanced_Content_Encryption'),
        }

        #   '75b22630-668e-11cf-a6d9-00aa0062ce6c': Element('ASF_Compatibility', None),
        
        self.DESCRIPTOR = {
            'ID3': self._parse_id3v2_descriptor,
            'TAG': self._parse_id3v1_descriptor,
        }
        
        self.__attribute_accessors = {
            'artist': 'WM/AlbumArtist',
            'album': 'WM/AlbumTitle',
            'track': 'WM/TrackNumber',
            'release_date': 'WM/Year',
            'composer': 'WM/Composer',
            'genre': 'WM/Genre',
            'copyright': 'copyright',
            'lyrics': 'WM/Lyrics',
            'rating': 'rating',
        }
            
    def __getattr__(self, attr):
        accessor = self.__attribute_accessors.get(attr, None)
        
        if accessor is not None:
            if callable(accessor):
                return accessor()
            else:
                tag = self._media_entry.metadata.get(accessor, None)
                if tag is not None:
                    return tag

                raise AttributeError("Attribute '%s' not found in file." % attr)
        else:
            raise AttributeError("Unknown attribute '%s'." % attr)

    @staticmethod
    def can_handle(ds):
        """Determine if ASFHandler can parse the stream."""
        
        data = ds.read(16)
        ds.seek(-16, os.SEEK_CUR)
        
        if data == ASF_GUID:
            return 'asf'
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
                raise MediaHandlerError("ASFHandler: Unable to handle file '%s'" % filename)

    def read_stream(self, ds, doctype=None):
        if doctype is None:
            doctype = self.can_handle(ds)

        if doctype is not None:
            self._ds = ds
            self.container = MediaContainer()
            self._media_entry = MediaEntry()
            self._media_entry.container = self.container
            self.container.entries.append(self._media_entry)
            
            self._read_element('root')
        else:
            raise MediaHandlerError("ASFHandler: Unable to handle stream")
            
    def _read_element(self, parent):
        box_id = self._read_guid()
        size_read = 16

        title = 'Unknown'
        try:
            elem = self._elements[box_id]
            title = elem.title
            handler = elem.reader
        except:
            handler = None

        self.logger.debug('ASF:  %s - %s' % (box_id, title))
            
        element_size = struct.unpack('<Q', self._ds.read(8))[0]
        size_read += 8
        
        if element_size > 24:
            element_size -= 24
            if handler is not None:
                size_read += handler(parent, element_size)
            else:
                self._ds.seek(element_size, os.SEEK_CUR)
                size_read += element_size
                
        return size_read
    
    def _read_guid(self):
        return str(uuid.UUID(bytes_le=self._ds.read(16)))
    
    def _read_header(self, parent, size):
        count, res1, res2 = struct.unpack('<LBB', self._ds.read(6))
        
        if res1 != 1 or res2 != 2:
            raise ASFError(_('File is not a valid ASF file.'))
        
        for _x in range(count):
            self._read_element('header')
            
        return size

    def _read_header_extension(self, parent, size):
        _res1 = self._read_guid()
        if _res1 != 'abd3d211-a9ba-11cf-8ee6-00c00c205365':
            self.logger.debug('Expected ASF_Reserved_1 guid (abd3d211-a9ba-11cf-8ee6-00c00c205365)')
        
        _res2, extension_size = struct.unpack('<HL', self._ds.read(6))

        pos = 0
        while pos < extension_size:
            pos += self._read_element('header_ext')
            
        return size

    def _read_language_list(self, parent, size):
        count = struct.unpack('<H', self._ds.read(2))[0]
        
        for _x in range(count):
            length = struct.unpack('B', self._ds.read(1))[0]
            _lang = self._read_utf16le(length)
            
        return size

    def _read_content_description(self, parent, size):
        content_info = struct.unpack('<HHHHH', self._ds.read(10))

        self._media_entry.metadata['title'] = self._read_utf16le(content_info[0])
        self._media_entry.metadata['author'] = self._read_utf16le(content_info[1])
        self._media_entry.metadata['copyright'] = self._read_utf16le(content_info[2])
        self._media_entry.metadata['description'] = self._read_utf16le(content_info[3])
        self._media_entry.metadata['rating'] = self._read_utf16le(content_info[4])
        
        return size

    def _read_extended_content_description(self, parent, size):
        count = struct.unpack('<H', self._ds.read(2))[0]
        
        for _x in range(count):
            d = self._read_descriptor()
            self.logger.debug('   ECD: %s' % str(d))
            
        return size

    def _read_file_properties(self, parent, size):
        self._media_entry.metadata['file_id'] = self._read_guid()
        
        self._media_entry.metadata['file_size'], \
        file_creation, \
        self._media_entry.metadata['data_packet_count'], \
        duration, send_duration, preroll, flags, \
        min_packet_size, max_packet_size, max_bitrate = \
            struct.unpack('<QQQQQQLLLL', self._ds.read(64))
        
        ns100 = 10000000.0
        delta = timedelta(seconds=file_creation/ns100)
        self._media_entry.metadata['file_creation'] = datetime(year=1601, month=1, day=1) + delta
            
        self._media_entry.metadata['duration'] = duration / ns100
        self._media_entry.metadata['send_duration'] = send_duration / ns100
        self._media_entry.metadata['preroll'] = preroll / 1000
        self._media_entry.metadata['broadcast'] = bool(flags & 1)
        self._media_entry.metadata['seekable'] = bool((flags & 2) >> 1)

        return size

    def _read_metadata(self, parent, size):
        count = struct.unpack('<H', self._ds.read(2))[0]
        
        for _x in range(count):
            d = self._read_metadata_descriptor()
            self.logger.debug('   M: %s' % str(d))
            
        return size

    def _read_metadata_library(self, parent, size):
        count = struct.unpack('<H', self._ds.read(2))[0]
        
        for _x in range(count):
            d = self._read_metadata_descriptor()
            self.logger.debug('   ML: %s' % str(d))
            
        return size

    def _read_stream_properties(self, parent, size):
        try:
            stream_type_id = self._read_guid()
            stream_type = self._elements[str(stream_type_id)].title
        except:
            raise ValueError(_('Unknown stream type %s found') % stream_type_id)
            
        _correction_type_id = self._read_guid()
        
        info = struct.unpack('<QLLH0004x', self._ds.read(22))
        _time_offset = info[0]
        type_data_len = info[1]
        
        _flags = info[3]
        number = (info[3] & 0x7F)
        self._extend_stream_array(number)
        
        encrypted = bool(info[3] >> 15)

        if stream_type == 'ASF_Video_Media':
            self.container.metadata['mimetype'] = 'video/x-ms-wmv'
            
            if self._media_entry.streams[number - 1].stream_type_info is None:
                stream_info = VideoStreamInfo()
                self._media_entry.streams[number - 1].stream_type_info = stream_info
            else:
                stream_info = self._media_entry.streams[number - 1].stream_type_info

            self._parse_video_stream_info(type_data_len, stream_info)

        elif stream_type == 'ASF_Audio_Media':
            self.container.metadata['mimetype'] = 'audio/x-ms-wma'
            
            if self._media_entry.streams[number - 1].stream_type_info is None:
                stream_info = AudioStreamInfo()
                self._media_entry.streams[number - 1].stream_type_info = stream_info
            else:
                stream_info = self._media_entry.streams[number - 1].stream_type_info

            self._parse_audio_stream_info(type_data_len, stream_info)

        elif stream_type == 'ASF_JFIF_Media' or \
        stream_type == 'ASF_Degradable_JPEG_Media':
            self.container.metadata['mimetype'] = 'video/x-ms-asf'
            
            if self._media_entry.streams[number - 1].stream_type_info is None:
                stream_info = ImageStreamInfo()
                self._media_entry.streams[number - 1].stream_type_info = stream_info
            else:
                stream_info = self._media_entry.streams[number - 1].stream_type_info

            self._parse_image_stream_info(type_data_len, stream_info)
        else:
            self.container.metadata['mimetype'] = 'video/x-ms-asf'
            stream_type = 'Unknown'
            self._ds.seek(type_data_len, os.SEEK_CUR)

        stream_info.type = stream_type
        
        correction_data_len = info[2]
        #correction_data = self._ds.read(correction_data_len)
        self._ds.seek(correction_data_len, os.SEEK_CUR)
            
        return size

    def _read_stream_bitrate_properties(self, parent, size):
        count = struct.unpack('<H', self._ds.read(2))[0]
        
        for _x in range(count):
            flags, bitrate = struct.unpack('<HL', self._ds.read(6))
            
            number = flags & 0x7F
            self._extend_stream_array(number)
            
            self._media_entry.streams[number - 1].average_bitrate = bitrate
            
        return size

    def _read_codec_list(self, parent, size):
        _reserved = self._read_guid()
        count = struct.unpack('<L', self._ds.read(4))[0]
        
        for _x in range(count):
            self._read_codec_info()
            
        return size

    def _read_codec_info(self):
        _codec_type, length = struct.unpack('<HH', self._ds.read(4))
        name = self._read_utf16le(length * 2)
        
        length = struct.unpack('<H', self._ds.read(2))[0]
        description = self._read_utf16le(length * 2)
        
        length = struct.unpack('<H', self._ds.read(2))[0]
        data = self._ds.read(length)
        
        self._media_entry.codecs.append({'name': name,
                             'description': description,
                             'data': data})

    def _read_descriptor(self):
        length = struct.unpack('<H', self._ds.read(2))[0]
        name = self._read_utf16le(length)
        
        data_type, length = struct.unpack('<HH', self._ds.read(4))
        data = self._ds.read(length)
        value = self._data_value(data_type, data)

        return (name, value)

    def _read_metadata_descriptor(self):
        lang, stream, name_len, data_type, data_len = \
            struct.unpack('<HHHHL', self._ds.read(12))
            
        name = self._read_utf16le(name_len)
        data = self._ds.read(data_len)
        value = self._data_value(data_type, data)

        return MetadataInfo(stream, name, value, lang)

    def _data_value(self, data_type, data):
        if data_type == 0x0000:
            value = data.decode('UTF-16-LE')
            if value[-1] == '\0':
                value = value[:-1]
        elif data_type == 0x0001:
            value = data
        elif data_type == 0x0002:
            value = bool(data)
        elif data_type == 0x0003:
            value = struct.unpack('<L', data)[0]
        elif data_type == 0x0004:
            value = struct.unpack('<Q', data)[0]
        elif data_type == 0x0005:
            value = struct.unpack('<H', data)[0]
        elif data_type == 6:
            value = str(uuid.UUID(bytes_le=data))
            
        return value

    def _parse_audio_stream_info(self, data_len, stream_info):
        data = self._ds.read(data_len)
        info = struct.unpack('<HHLLHHH', data[:18])
        
        stream_info.codec = info[0]
        stream_info.channels = info[1]
        stream_info.samples_per_second = info[2]
        stream_info.bytes_per_second = info[3]
        stream_info.alignment = info[4]
        stream_info.bits_per_sample = info[5]
        stream_info.codec_data_size = info[6]

    def _parse_video_stream_info(self, data_len, stream_info):
        data = self._ds.read(data_len)
        info = struct.unpack('<LL0001xH', data[:11])

        stream_info.width = info[0]
        stream_info.height = info[1]
        _info_len = info[2]
        
        info = struct.unpack('<LllHHLLllLL', data[11:51])
        stream_info.bits_per_pixel = info[4]
        stream_info.compression_id = info[5]
        stream_info.image_size = info[6]
        stream_info.pixels_per_meter_horiz = info[7]
        stream_info.pixels_per_meter_vert = info[8]
        stream_info.colours_used = info[9]
        stream_info.important_colours = info[10]

    def _parse_image_stream_info(self, data_len, stream_info):
        self._ds.seek(data_len, os.SEEK_CUR)

    def _parse_id3v1_descriptor(self, data):
        self.id3_info = ID3v1TagHandler(data)

    def _parse_id3v2_descriptor(self, data):
        self.id3_info = ID3v2TagHandler(data)

    def _read_utf16le(self, length):
        if length != 0:
            data = self._ds.read(length)
            data = data.decode('UTF-16-LE')
            if data[-1] == '\0':
                data = data[:-1]
            return data
        else:
            return ''

    def media_format():
        def fget(self):
            for stream in self._streams:
                if isinstance(stream, VideoStreamInfo):
                    return 'video'
                
            return 'audio'
        
        return locals()
    
    media_format = property(**media_format()) 

    def _extend_stream_array(self, number):        
        extra = number - len(self._media_entry.streams)
        if extra > 0:
            self._media_entry.streams.extend([None] * extra)
            self._media_entry.streams[number - 1] = MediaStream()
    
