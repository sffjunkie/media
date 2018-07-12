# Copyright (c) 2015 Simon Kennedy <sffjunkie+code@gmail.com>

import os
import uuid
import struct
import datetime
from io import BytesIO

from mogul.locale import localize
_ = localize.get_translator('mogul.media')

from mogul.locale.locale import LocaleIdentifier
from mogul.media import (MediaHandler, MediaHandlerError,
                         MediaContainer, MediaEntry, MediaStream,
                         AudioStreamInfo, VideoStreamInfo, SubtitleStreamInfo)
from mogul.media.element import Element
from mogul.media.tag import Tag, TagTarget, TagGroup
    
__all__ = ['EBMLHandler']

DATA_SIZE = [8, 7, 6, 6, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4,
             3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
             2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
             2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
             1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
             1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
             1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
             1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

VSINT_SUBTR = [0x3F, 0x1FFF, 0x0FFFFF, 0x07FFFFFF,
               0x03FFFFFFFF, 0x01FFFFFFFFFF,
               0x00FFFFFFFFFFFF, 0x007FFFFFFFFFFFFF]


"""
Segment+
    Meta Seek
    Segment Information
    Tracks
        Track Entry
    Chapters
    Clusters
    Cues
    Attachments
    Tags
        Tag
            Targets
                Target Type Value - uint
                Target Type - string
                Track UID - uint
                Edition UID - uint
                Chapter UID - uint
                Attachment UID - uint
            SimpleTag+
                Tag Name - UTF-8
                Tag Language
                Tag Default - bool
                Tag String^ - UTF-8
                Tag Binary^
                SimpleTag*
"""

class EBMLContainer(MediaContainer):
    pass



class EBMLHandler(MediaHandler):    
    def __init__(self):
        super(EBMLHandler, self).__init__()
        
        self.container = None
        
        self._ds = None
        self._media_entry = None
        self._media_stream = None
        self._tag_target = None
        self._attachment = None

        self._elements = {
            b'\x1a\x45\xdf\xa3': Element(_('Header'), self._read_header),
            b'\xec':             Element(_('Void')),
            b'\xbf':             Element(_('CRC-32')),
            b'\x42\x82':         Element(_('Doctype'), self._read_doctype),
            b'\x42\x86':         Element(_('Version'), self._read_uint, key='version'),
            b'\x42\xf7':         Element(_('Read Version'), self._read_uint, key='read_version'),
            b'\x42\xf2':         Element(_('Max ID Length'), self._read_uint, key='max_id_len'),
            b'\x42\xf3':         Element(_('Max Size Length'), self._read_uint, key='max_size_len'),
            b'\x42\x87':         Element(_('Doctype Version'), self._read_uint, key='doctype_version'),
            b'\x42\x85':         Element(_('Doctype Read Version'), self._read_uint, key='doctype_read_version'),
            b'\x18\x53\x80\x67': Element(_('Segment'), self._read_segment),
            b'\x2a\xd7\xb1':     Element(_('Timecode Scale'), self._read_uint, key='timecode_scale'),
            b'\x4d\x80':         Element(_('Muxing Application'), self._read_utf8, key='app_mux'),
            b'\x57\x41':         Element(_('Writing Application'), self._read_utf8, key='app_write'),
            b'\x44\x89':         Element(_('Duration'), self._read_rational, key='duration'),
            b'\x44\x61':         Element(_('Date UTC'), self._read_date, key='date_utc'),
            b'\x73\xa4':         Element(_('Segment UID'), self._read_segment_uid),
            b'\x11\x4d\x9b\x74': Element(_('Seek Head'), self._read_seek_head),
            b'\x4d\xbb':         Element(_('Seek'), self._read_seek),
            b'\x53\xab':         Element(_('Seek ID'), self._read_seek_id),
            b'\x53\xac':         Element(_('Seek Position'), self._read_seek_pos),
            b'\x15\x49\xa9\x66': Element(_('Info'), self._read_info),
            b'\x1f\x43\xb6\x75': Element(_('Cluster'), self._read_cluster),
            b'\xe7':             Element(_('Timecode')),
            b'\x58\x54':         Element(_('Silent Tracks')),
            b'\xa7':             Element(_('Position')),
            b'\xab':             Element(_('Previous Size')),
            b'\xa3':             Element(_('Simple Block'), log=False),
            b'\xa0':             Element(_('Block Group')),
            b'\xa1':             Element(_('Block')),
            b'\xa2':             Element(_('Block Virtual')),
            b'\x75\xa1':         Element(_('Block Additions')),
            b'\xa6':             Element(_('Block More')),
            b'\xee':             Element(_('Block Add ID')),
            b'\xa5':             Element(_('Block Additional')),
            b'\x9b':             Element(_('Block Duration')),
            b'\xfa':             Element(_('Reference Priority')),
            b'\xfb':             Element(_('Reference Block')),
            b'\xfd':             Element(_('Reference Virtual')),
            b'\xa4':             Element(_('Codec State')),
            b'\x8e':             Element(_('Slices')),
            b'\xe8':             Element(_('Time Slice')),
            b'\xcc':             Element(_('Lace Number')),
            b'\xcd':             Element(_('Frame Number')),
            b'\xcb':             Element(_('Block Addition ID')),
            b'\xce':             Element(_('Delay')),
            b'\xcf':             Element(_('Slice Duration')),
            b'\xc8':             Element(_('Reference Frame')),
            b'\xc9':             Element(_('Reference Offset')),
            b'\xca':             Element(_('Reference Timecode')),
            b'\xaf':             Element(_('Encrypted Block')),
            b'\x16\x54\xae\x6b': Element(_('Tracks'), self._read_tracks),
            b'\xae':             Element(_('Track Entry'), self._read_track_entry),
            b'\xd7':             Element(_('Track Number'), self._read_track_number),
            b'\x73\xc5':         Element(_('Track UID'), self._read_track_uid),
            b'\x83':             Element(_('Track Type'), self._read_track_type),
            b'\xb9':             Element(_('Flag Enabled')),
            b'\x88':             Element(_('Flag Default')),
            b'\x55\xaa':         Element(_('Flag Forced')),
            b'\x9c':             Element(_('Flag Lacing')),
            b'\x6d\xe7':         Element(_('Min Cache')),
            b'\x6d\xf8':         Element(_('Max Cache')),
            b'\x23\xe3\x83':     Element(_('Default Duration')),
            b'\x23\x31\x4f':     Element(_('Track Timecode Scale')),
            b'\x55\xee':         Element(_('Max Block Addition ID')),
            b'\x53\x6e':         Element(_('Track Name'), self._read_track_name),
            b'\x22\xb5\x9c':     Element(_('Track Language'), self._read_track_language),
            b'\x86':             Element(_('Codec ID'), self._read_track_codec_id),
            b'\x63\xa2':         Element(_('Codec Private')),
            b'\x25\x86\x88':     Element(_('Codec Name')),
            b'\x74\x46':         Element(_('Attachment Link')),
            b'\xaa':             Element(_('Codec Decode All')),
            b'\x6f\xab':         Element(_('Track Overlay')),
            b'\x66\x24':         Element(_('Track Translate')),
            b'\x66\xfc':         Element(_('Track Translate Edition UID')),
            b'\x66\xbf':         Element(_('Track Translate Codec')),
            b'\x66\xa5':         Element(_('Track Translate Track ID')),
            b'\xe0':             Element(_('Video'), self._read_video),
            b'\x9a':             Element(_('Flag Interlace'), self._read_video_entry),
            b'\x53\xb8':         Element(_('Stereo Mode')),
            b'\xb0':             Element(_('Pixel Width'), self._read_video_entry),
            b'\xba':             Element(_('Pixel Height'), self._read_video_entry),
            b'\x54\xaa':         Element(_('Pixel Crop Bottom')),
            b'\x54\xbb':         Element(_('Pixel Crop Top')),
            b'\x54\xcc':         Element(_('Pixel Crop Left')),
            b'\x54\xdd':         Element(_('Pixel Crop Right')),
            b'\x54\xb0':         Element(_('Display Width')),
            b'\x54\xba':         Element(_('Display Height')),
            b'\x54\xb2':         Element(_('Display Unit')),
            b'\x54\xb3':         Element(_('Aspect Ratio')),
            b'\x2e\xb5\x25':     Element(_('Colour Space'), self._read_color_space),
            b'\x2f\xb5\x23':     Element(_('Gamma')),
            b'\x23\x83\xe3':     Element(_('Frame Rate')),
            b'\xe1':             Element(_('Audio')),
            b'\xb5':             Element(_('Sampling Frequency')),
            b'\x78\xb5':         Element(_('Output Sampling Frequency')),
            b'\x9f':             Element(_('Channels')),
            b'\x7d\x7b':         Element(_('Channel Positions')),
            b'\x62\x64':         Element(_('Bit Depth')),
            b'\xe2':             Element(_('Track Operation')),
            b'\xe3':             Element(_('Track Combine Planes')),
            b'\xe4':             Element(_('Track Plane')),
            b'\xe5':             Element(_('Track Plane UID')),
            b'\xe6':             Element(_('Track Plane Type')),
            b'\xe9':             Element(_('Track Join Blocks')),
            b'\xed':             Element(_('Track Join UID')),
            b'\x6d\x80':         Element(_('Content Encodings')),
            b'\x62\x40':         Element(_('Content Encoding')),
            b'\x50\x31':         Element(_('Content Encoding Order')),
            b'\x50\x32':         Element(_('Content Encoding Scope')),
            b'\x50\x33':         Element(_('Content Encoding Type')),
            b'\x50\x34':         Element(_('Content Compression')),
            b'\x42\x54':         Element(_('Content Compression Algorithm')),
            b'\x42\x55':         Element(_('Content Compression Settings')),
            b'\x50\x35':         Element(_('Content Encryption')),
            b'\x47\xe1':         Element(_('Content Encryption Algorithm')),
            b'\x47\xe2':         Element(_('Content Encryption Key ID')),
            b'\x47\xe3':         Element(_('Content Signature')),
            b'\x47\xe4':         Element(_('Content Signature Key ID')),
            b'\x47\xe5':         Element(_('Content Signature Algorithm')),
            b'\x47\xe6':         Element(_('Content Signature Hash Algorithm')),
            b'\x1c\x53\xbb\x6b': Element(_('Cues'), self._read_cues),
            b'\xbb':             Element(_('Cue Point')),
            b'\xb3':             Element(_('Cue Time')),
            b'\xb7':             Element(_('Cue Track Positions')),
            b'\xf7':             Element(_('Cue Track')),
            b'\xf1':             Element(_('Cue Cluster Position')),
            b'\x53\x78':         Element(_('Cue Block Number')),
            b'\xea':             Element(_('Cue Codec State')),
            b'\xdb':             Element(_('Cue Reference')),
            b'\x96':             Element(_('Cue Reference Time')),
            b'\x97':             Element(_('Cue Reference Cluster')),
            b'\x53\x5f':         Element(_('Cue Reference Number')),
            b'\xeb':             Element(_('Cue Reference Codec State')),
            b'\x19\x41\xa4\x69': Element(_('Attachments'), self._read_attachments),
            b'\x61\xa7':         Element(_('Attached File'), self._read_attached_file),
            b'\x46\x7e':         Element(_('File Description'), self._read_file_description),
            b'\x46\x6e':         Element(_('File Name'), self._read_file_name),
            b'\x46\x60':         Element(_('File Mime Type'), self._read_file_mimetype),
            b'\x46\x5c':         Element(_('File Data'), self._read_file_data),
            b'\x46\xae':         Element(_('File UID'), self._read_file_uid),
            b'\x46\x75':         Element(_('File Referral')),
            b'\x46\x61':         Element(_('File Used Start Time')),
            b'\x46\x62':         Element(_('File Used End Time')),
            b'\x10\x43\xa7\x70': Element(_('Chapters'), self._read_chapters),
            b'\x45\xb9':         Element(_('Edition Entry')),
            b'\x45\xbc':         Element(_('Edition UID')),
            b'\x45\xbd':         Element(_('Edition Flag Hidden')),
            b'\x45\xdb':         Element(_('Edition Flag Default')),
            b'\x45\xdd':         Element(_('Edition Flag Ordered')),
            b'\xb6':             Element(_('Chapter')),
            b'\x73\xc4':         Element(_('Chapter UID')),
            b'\x91':             Element(_('Chapter Time Start')),
            b'\x92':             Element(_('Chapter Time End')),
            b'\x98':             Element(_('Chapter Flag Hidden')),
            b'\x45\x98':         Element(_('Chapter Flag Enabled')),
            b'\x6e\x67':         Element(_('Chapter Segment UID')),
            b'\x6e\xbc':         Element(_('Chapter Segment Edition UID')),
            b'\x63\xc3':         Element(_('Chapter Physical Equivalent')),
            b'\x8f':             Element(_('Chapter Track')),
            b'\x89':             Element(_('Chapter Track Number')),
            b'\x80':             Element(_('Chapter Display')),
            b'\x85':             Element(_('Chapter String')),
            b'\x43\x7c':         Element(_('Chapter Language')),
            b'\x43\x7e':         Element(_('Chapter Country')),
            b'\x69\x44':         Element(_('Chapter Process')),
            b'\x69\x55':         Element(_('Chapter Process Codec ID')),
            b'\x45\x0d':         Element(_('Chapter Process Private')),
            b'\x69\x11':         Element(_('Chapter Process Command')),
            b'\x69\x22':         Element(_('Chapter Process Time')),
            b'\x69\x33':         Element(_('Chapter Process Data')),
            b'\x12\x54\xc3\x67': Element(_('Tags'), self._read_tags),
            b'\x73\x73':         Element(_('Tag'), self._read_tag),
            b'\x63\xc0':         Element(_('Targets'), self._read_targets),
            b'\x68\xca':         Element(_('Target Type Value'), self._read_tag_target_type_value),
            b'\x63\xca':         Element(_('Target Type'), self._read_tag_target_type),
            b'\x63\xc5':         Element(_('Tag Track UID'), self._read_tag_track_uid),
            b'\x63\xc9':         Element(_('Tag Edition UID'), self._read_tag_edition_uid),
            b'\x63\xc4':         Element(_('Tag Chapter UID'), self._read_tag_chapter_uid),
            b'\x63\xc6':         Element(_('Tag Attachment UID'), self._read_tag_attachment_uid),
            b'\x67\xc8':         Element(_('Simple Tag'), self._read_simple_tag),
            b'\x45\xa3':         Element(_('Tag Name'), self._read_tag_name),
            b'\x44\x7a':         Element(_('Tag Language'), self._read_tag_language),
            b'\x44\x84':         Element(_('Tag Default'), self._read_tag_default),
            b'\x44\x87':         Element(_('Tag String'), self._read_tag_string),
            b'\x44\x85':         Element(_('Tag Binary'), self._read_tag_binary),
        }
        
        self.__attribute_accessors = {
            'doctype': ('header', '\x42\x82'),
            'title': ('tag', 'TITLE', 30),
            'artist': ('tag', 'ARTIST', 30),
            'album_artist': ('tag', 'ARTIST', 50),
            'album': ('tag', 'TITLE', 50),
            'track': ('tag', 'PART_NUMBER', 30),
            'release_date': ('tag', 'DATE_RELEASE'),
            'writer': ('tag', 'LYRICIST'),
            'comment': ('tag', 'COMMENT'),
            'lead_performer': ('tag', 'LEAD_PERFORMER'),
            'cover': ('attachment', 'cover'),
            'thumbnail': ('attachment', 'small_cover'),
        }

    def __getattr__(self, attr):
        accessor = self.__attribute_accessors.get(attr, None)
        
        if accessor is not None:
            if callable(accessor):
                return accessor()
            else:
                target_type = -1
                if len(accessor) == 2:
                    location, name = accessor
                elif len(accessor) == 3:
                    location, name, target_type = accessor

                if location == 'header':
                    return self.container.metadata[name]
                elif location == 'tag':
                    entry = self._find_tag(name, target_type)                        
                    
                    if entry is not None:
                        return entry.value
                elif location == 'attachment':
                    return self.attachments[name]

                raise AttributeError("Attribute '%s' not found in file." % attr)
        else:
            raise AttributeError("Unknown attribute '%s'." % attr)

    @staticmethod
    def can_handle(ds):
        """Determine if EBMLHandler can parse the stream."""
        
        sig = ds.read(4)
        ds.seek(-4, os.SEEK_CUR)
        
        if sig == b'\x1a\x45\xdf\xa3':
            return ebml_read_doctype(ds)
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
                raise MediaHandlerError("EBMLHandler: Unable to handle file '%s'" % filename)

    def read_stream(self, ds, doctype=None):
        if doctype is None:
            doctype = self.can_handle(ds)

        if doctype is not None:
            self._ds = ds
            self.container = MediaContainer('application/x-ebml')
            self._read_element('root')
            self.container.metadata['stream_size'] = self._ds.tell()
        else:
            raise MediaHandlerError("EBMLHandler: Unable to handle stream")

    def _read_element(self, parent, end=None):
        element_id, element_id_len = ebml_read_id(self._ds)
            
        if end is not None and element_id in end:
            self._ds.seek(-element_id_len, os.SEEK_CUR)
            return -1
        
        element_size, element_size_len = ebml_read_size(self._ds)
        
        if element_size != 0:
            try:
                info = self._elements[element_id]
                
                reader = info.reader
                key = info.key
                log = info.log
                if key is None:
                    key = element_id
            except:
                reader = None
                key = None
                log = False
        
            if log:
                id_str = ''.join([ "%02X " % x for x in element_id ]).strip()
                try:
                    self.logger.debug('EBML: ID = %s, Name = %s' % (id_str, self._elements[element_id].title))
                except:
                    self.logger.debug('EBML: Unknown ID = %s' % id_str)
                
            if reader is not None:
                size_read = reader(parent, element_size, key)
            else:
                size_read = element_size
                self._ds.seek(element_size, os.SEEK_CUR)
        else:
            size_read = 0
                
        return element_id_len + element_size_len + size_read

    def _read_header(self, parent, size, element_id):
        total_read = 0
        
        while total_read < size:
            total_read += self._read_element('header')
            
        return total_read

    def _read_doctype(self, parent, size, element_id):
        self.container.metadata['doctype'] = ebml_read_doctype(self._ds)
        return size

    def _read_segment(self, parent, size, element_id):
        self._media_entry = MediaEntry()
        self._media_entry.container = self.container
        self._media_entry.tick_period = 1000000
        self.container.entries.append(self._media_entry)

        total_read = 0
        if size == -1:                    
            end = [b'\x18\x53\xB0\x67', b'\x1F\x43\xB6\x75', 
                   b'\x11\x4d\x9b\x74', b'\x15\x49\xA9\x66',
                   b'\x16\x54\xAE\x6B', b'\x1C\x53\xBB\x6B',
                   b'\x19\x41\xA4\x69', b'\x10\x43\xA7\x70',
                   b'\x12\x54\xC3\x67']

            total_read = self._skip_junk(end)
                
        while (total_read < size):
            total_read += self._read_element('segment')

        try:
            t = self._media_entry.metadata.pop('duration')
            self._media_entry.ticks = t
        except KeyError:
            pass

        try:
            ts = self._media_entry.metadata.pop('timecode_scale')    
            self._media_entry.tick_period = ts
        except KeyError:
            pass
            
        return total_read
        
    def _read_seek_head(self, parent, size, element_id):
        total_read = 0
        
        while total_read < size:
            total_read += self._read_element('seek_head')

        return total_read
            
    def _read_seek(self, parent, size, element_id):
        total_read = 0
        while total_read < size:
            total_read += self._read_element('seek')
            
        return total_read

    def _read_seek_id(self, parent, size, element_id):
        seek_id = self._ds.read(size)
        if seek_id == b'\x15\x49\xa9\x66':
            self._seek_id = 'metadata'
        elif seek_id == b'\x16\x54\xae\x6b':
            self._seek_id = 'tracks'
        elif seek_id == b'\x10\x43\xa7\x70':
            self._seek_id = 'chapters'
        elif seek_id == b'\x1c\x53\xbb\x6b':
            self._seek_id = 'cues'
        elif seek_id == b'\x19\x41\xa4\x69':
            self._seek_id = 'attachments'
        elif seek_id == b'\x12\x54\xc3\x67':
            self._seek_id = 'metadata'
            
        return size

    def _read_seek_pos(self, parent, size, element_id):
        self._media_entry.seek[self._seek_id] = ebml_read_uint(self._ds, size)
        return size

    def _read_info(self, parent, size, element_id):
        total_read = 0
        
        while total_read < size:
            total_read += self._read_element('metadata')

        return total_read

    def _read_cluster(self, parent, size, element_id):
        total_read = 0
        if size == -1:                    
            end = [b'\x18\x53\xB0\x67', b'\x1F\x43\xB6\x75', 
                   b'\x11\x4d\x9b\x74', b'\x15\x49\xA9\x66',
                   b'\x16\x54\xAE\x6B', b'\x1C\x53\xBB\x6B',
                   b'\x19\x41\xA4\x69', b'\x10\x43\xA7\x70',
                   b'\x12\x54\xC3\x67']
    
            size_read = 0
            while size_read != -1:
                size_read = self._read_element('cluster', end)
                if size_read != -1:
                    total_read += size_read

        else:                    
            while total_read < size:
                total_read += self._read_element('cluster')
            
        return total_read

    def _read_block_group(self, parent, size, element_id):
        total_read = 0
        while (total_read < size):
            total_read += self._read_element('block_group')
            
        return total_read

    def _read_tracks(self, parent, size, element_id):
        total_read = 0
        
        while total_read < size:
            total_read += self._read_element('tracks')
            
        return total_read

    def _read_track_entry(self, parent, size, element_id):
        self._media_stream = MediaStream()
        self._media_entry.streams.append(self._media_stream)
        
        total_read = 0
        
        while total_read < size:
            total_read += self._read_element('track_entry')
            
        return total_read

    def _read_track_number(self, parent, size, element_id):
        self._media_stream.number = ebml_read_uint(self._ds, size)
        return size

    def _read_track_uid(self, parent, size, element_id):
        self._media_stream.uid = ebml_read_uint(self._ds, size)
        return size

    def _read_track_type(self, parent, size, element_id):
        track_type = ebml_read_uint(self._ds, size)
        
        if track_type == 1:
            self._media_stream.stream_type_info = VideoStreamInfo()
        elif track_type == 2:
            self._media_stream.stream_type_info = AudioStreamInfo()
        elif track_type == 17:
            self._media_stream.stream_type_info = SubtitleStreamInfo()
            
        return size

    def _read_video(self, parent, size, element_id):
        total_read = 0
        
        while total_read < size:
            total_read += self._read_element('video')
            
        return total_read

    def _read_video_entry(self, parent, size, element_id):
        if element_id == b'\xb0':
            self._media_stream.stream_type_info.width = ebml_read_uint(self._ds, size)
        elif element_id == b'\xba':
            self._media_stream.stream_type_info.height = ebml_read_uint(self._ds, size)
        else:
            _u = ebml_read_uint(self._ds, size)
            
        return size

    def _read_color_space(self, parent, size, element_id):
        self._media_stream.stream_type_info.fourcc = self._ds.read(size)
        return size

    def _read_track_language(self, parent, size, element_id):
        self._media_stream.language = self._ds.read(size)
        return size

    def _read_track_codec_id(self, parent, size, element_id):
        self._media_stream.codec = self._ds.read(size)
        return size

    def _read_track_name(self, parent, size, element_id):
        self._media_stream.name = self._ds.read(size).decode('UTF-8')
        return size

    def _read_cues(self, parent, size, element_id):
        self._ds.seek(size, os.SEEK_CUR)
        return size

    def _read_attachments(self, parent, size, element_id):
        total_read = 0
        while total_read < size:
            total_read += self._read_element('attachments')

        return total_read

    def _read_attached_file(self, parent, size, element_id):
        self._attachment = {}
        self._media_entry.attachments.append(self._attachment)
        
        total_read = 0
        while total_read < size:
            total_read += self._read_element('attachment')

        return total_read

    def _read_file_description(self, parent, size, element_id):
        self._attachment['description'] = self._ds.read(size).decode('UTF-8')
        return size

    def _read_file_name(self, parent, size, element_id):
        self._attachment['name'] = self._ds.read(size).decode('UTF-8')
        return size

    def _read_file_mimetype(self, parent, size, element_id):
        self._attachment['mimetype'] = self._ds.read(size).decode('ASCII')
        return size

    def _read_file_data(self, parent, size, element_id):
        self._attachment['data'] = (self._ds.tell(), size)
        self._ds.seek(size, os.SEEK_CUR)
        return size

    def _read_file_uid(self, parent, size, element_id):
        self._attachment['uid'] = ebml_read_uint(self._ds, size)
        return size

    def _read_chapters(self, parent, size, element_id):
        self._ds.seek(size, os.SEEK_CUR)
        return size

    def _read_tags(self, parent, size, element_id):
        total_read = 0
        while total_read < size:
            total_read += self._read_element('metadata')

        return size

    def _read_tag(self, parent, size, element_id):
        self._tag_group = TagGroup()

        total_read = 0
        while total_read < size:
            total_read += self._read_element('tag_group')
            
        self._media_entry.tag_groups.append(self._tag_group)
        self._tag = None

        return size
    
    def _read_targets(self, parent, size, element_id):
        self._tag_target = TagTarget()
        
        total_read = 0
        while total_read < size:
            total_read += self._read_element('targets')

        self._tag_group.targets.append(self._tag_target)

        return size

    def _read_tag_target_type(self, parent, size, element_id):
        self._tag_target.target_type = str(self._ds.read(size))
        return size

    def _read_tag_target_type_value(self, parent, size, element_id):
        self._tag_target.target_type_value = ebml_read_uint(self._ds, size)
        return size

    def _read_tag_track_uid(self, parent, size, element_id):
        self._tag_target.track_uid = ebml_read_uint(self._ds, size)
        return size

    def _read_tag_edition_uid(self, parent, size, element_id):
        self._tag_target.edition_uid = ebml_read_uint(self._ds, size)
        return size

    def _read_tag_chapter_uid(self, parent, size, element_id):
        self._tag_target.chapter_uid = ebml_read_uint(self._ds, size)
        return size

    def _read_tag_attachment_uid(self, parent, size, element_id):
        self._tag_target.attachment_uid = ebml_read_uint(self._ds, size)
        return size

    def _read_simple_tag(self, parent, size, element_id):
        tag = Tag()
        if parent == 'tag_group':
            self._tag_group.tags.append(tag)
        elif self._tag is not None:
            self._tag.metadata.append(tag)
            
        self._tag = tag
        
        total_read = 0
        while total_read < size:
            total_read += self._read_element('simple_tag')

        return size
    
    def _read_tag_name(self, parent, size, element_id):
        self._tag.name = str(self._ds.read(size))
        return size

    def _read_tag_string(self, parent, size, element_id):
        self._tag.value = ebml_read_utf8(self._ds, size)
        return size

    def _read_tag_binary(self, parent, size, element_id):
        self._tag.value = (ord(self._ds.read(1)) == 1)
        return size

    def _read_tag_language(self, parent, size, element_id):
        language = ebml_read_utf8(self._ds, size)
        if language.find('-') != -1:
            language, country = language.split('-')
        else:
            country = u'UND'
        self._tag.locale = LocaleIdentifier(language, country)
        return size

    def _read_tag_default(self, parent, size, element_id):
        self._tag.default = (ord(self._ds.read(1)) == 1)
        return size
        
    def _read_bytes(self, parent, size, element_id):
        data = self._ds.read(size)
        if parent == 'header':
            self.container.metadata[element_id] = data
        elif parent == 'metadata':
            self._media_entry.metadata[element_id] = data
        return size

    def _read_string(self, parent, size, element_id):
        data = self._ds.read(size).decode('latin-1')
        if parent == 'header':
            self.container.metadata[element_id] = data
        elif parent == 'metadata':
            self._media_entry.metadata[element_id] = data
        return size

    def _read_uint(self, parent, size, element_id):
        data = ebml_read_uint(self._ds, size)
        if parent == 'header':
            self.container.metadata[element_id] = data
        elif parent == 'metadata':
            self._media_entry.metadata[element_id] = data
        return size

    def _read_utf8(self, parent, size, element_id):
        data = ebml_read_utf8(self._ds, size)
        if parent == 'header':
            self.container.metadata[element_id] = data
        elif parent == 'metadata':
            self._media_entry.metadata[element_id] = data
        return size

    def _read_rational(self, parent, size, element_id):
        data = ebml_read_float(self._ds, size)
        if parent == 'header':
            self.container.metadata[element_id] = data
        elif parent == 'metadata':
            self._media_entry.metadata[element_id] = data
        return size
    
    def _read_date(self, parent, size, element_id):
        data = ebml_read_int(self._ds, size)
        delta = datetime.timedelta(microseconds=data/1000)
        base = datetime.datetime(2001, 1, 1, 0, 0, 0)
        
        if parent == 'metadata':
            self._media_entry.metadata[element_id] = base + delta
            
        return size
    
    def _read_segment_uid(self, parent, size, element_id):
        data = self._ds.read(size)
        self._media_entry.uid = uuid.UUID(bytes=data)
        return size
    
    def element_title(self, element_id):
        return self._elements[element_id][0]
    
    def _find_tag(self, name, target_type):
        for group in self._candidate_groups(target_type):
            for tag in group.metadata:
                if tag.name == name:
                    return tag
        
        for entry in self.container.entries:
            for group in entry.tag_groups:
                for tag in group.metadata:
                    if tag.name == name:
                        return tag
        
        return None 

    def _candidate_groups(self, target_type):
        for entry in self.container.entries:
            for group in entry.tag_groups:
                for target in group.targets:
                    if target.target_type_value == target_type:
                        yield group
                        
    def _skip_junk(self, end):
        # Skip any junk at the start of the Cluster
        total_read = 0
        buf = b'\x00\x00\x00\x00'
        while 1:
            buf += self._ds.read(1)
            buf = buf[1:]
            total_read += 1
            if buf in end:
                total_read -= 4
                self._ds.seek(-4, os.SEEK_CUR)
                break
            
        return total_read

def ebml_read(ds, size):
    data = ds.read(size)
    total_read = len(data)
    if total_read < size:
        raise EOFError()
    
    return data

def ebml_read_id(ds):
    _id = ebml_read(ds, 1)
    length = DATA_SIZE[ord(_id)]

    _id += ebml_read(ds, length)
    return (_id, length+1)

def ebml_read_size(ds):
    start = ord(ds.read(1))
    
    if start == 0xFF:
        return (-1, 1)
    
    length = DATA_SIZE[start]
    
    if length != 0:
        mask = int(pow(2, (7-length))-1)
        val = (start & mask)

        rest = ds.read(length)
                
        for x in range(length):
            val = val << 8
            val = val | rest[x]
    else:
        val = start ^ 0x80

    return (val, length+1)

def ebml_read_utf8(fp, size):
    data = fp.read(size)
    return data.decode('UTF-8')

def ebml_read_uint(ds, size):
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

def ebml_read_int(ds, size):
    if size == 1:
        return struct.unpack('>b', ds.read(1))[0]
    elif size == 2:
        return struct.unpack('>h', ds.read(2))[0]
    elif size == 3:
        return struct.unpack('>l', b'\0' + ds.read(3))[0]
    elif size == 4:
        return struct.unpack('>l', ds.read(4))[0]
    elif size == 5:
        return struct.unpack('>q', b'\0\0\0' + ds.read(5))[0]
    elif size == 6:
        return struct.unpack('>q', b'\0\0' + ds.read(6))[0]
    elif size == 7:
        return struct.unpack('>q', b'\0' + ds.read(7))[0]
    elif size == 8:
        return struct.unpack('>q', ds.read(8))[0]

def ebml_read_float(ds, size):
    if size == 4:
        return struct.unpack('>f', ds.read(4))[0]
    elif size == 8:
        return struct.unpack('>d', ds.read(8))[0]

def ebml_read_bytes(ds, size):
    return ds.read(size)

def ebml_skip_int(ds, count=1):
    for _x in range(count):
        start = ord(ds.read(1))
        length = DATA_SIZE[start]
        ds.seek(length, os.SEEK_CUR)   

def ebml_read_doctype(ds):
    ds.seek(0, os.SEEK_SET)
    _id = ebml_read_id(ds)[0]
    size = ebml_read_size(ds)[0]
    
    ds = BytesIO(ds.read(size))
    
    found = False
    while not found:
        _id = ebml_read_id(ds)[0]
        size = ebml_read_size(ds)[0]
        
        if _id == b'\x42\x82':
            data = ebml_read_utf8(ds, size)
            found = True
        else:
            ds.seek(size, os.SEEK_CUR)
    
    if found:
        return data
    else:
        return None