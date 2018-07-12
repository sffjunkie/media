# Copyright (c) 2009-2014 Simon Kennedy <sffjunkie+code@gmail.com>

import logging

__all__ = ['MediaContainer', 'MediaEntry', 'MediaStream', 'MediaHandlerError',
           'AudioStreamInfo', 'VideoStreamInfo', 'ImageStreamInfo',
           'SubtitleStreamInfo', 'Image', 'TagTarget', 'Tag', 'TagGroup']


class MediaHandlerError(Exception):
    pass


"""
MediaContainer
    metadata: {} - mimetype
    entries: MediaEntry[]
        metadata
        streams: MediaStream[]
            metadata
            media_type_info = AudioStreamInfo | VideoStreamInfo
    MediaEntry
"""

class MediaHandler(object):
    def __init__(self, log_indent_level=0):
        self.logger = self.Logger(log_indent_level)
    
    class Logger(object):
        def __init__(self, log_indent_level):
            self.level = log_indent_level
            self._logger = logging.getLogger('mogul.media')
            
        def debug(self, msg):
            self._logger.debug('%s%s', (' ' * self.level * 4, msg))
        
        def error(self, msg):
            self._logger.error('%s%s', (' ' * self.level * 4, msg))


class MediaStream(object):
    def __init__(self):
        self.uid = 0
        self.metadata = {}
        
        self.codec = None
        self.time_offset = 0
        self.average_bitrate = 0

        self.enabled = True
        self.default = True
        self.locale = None

        self.stream_info = None
        """Instance of AudioStreamInfo, VideoStreamInfo,
        SubtitleStreamInfo, ImageStreamInfo"""
        
        self.data = None
        """Encoded stream data"""

    @property
    def isaudio(self):
        return isinstance(self.stream_info, AudioStreamInfo)

    @property
    def isvideo(self):
        return isinstance(self.stream_info, VideoStreamInfo)

    @property
    def issubtitle(self):
        return isinstance(self.stream_info, SubtitleStreamInfo)

    @property
    def isimage(self):
        return isinstance(self.stream_info, ImageStreamInfo)


class MediaEntry(object):
    def __init__(self):
        self.uid = None
        self.metadata = {}
        self.seek = {}
        self.subentries = []
        self.streams = []
        self.tag_groups = []
        self.attachments = []
        self.codecs = []

        self.ticks = -1
        # duration in ticks
        self.tick_period = -1
        # period of one tick in nanoseconds
        
        def duration():
            def fget(self):
                if self.ticks != -1 and self.tick_period != -1:
                    return self.ticks * self.tick_period / 1000000000
                else:
                    return -1
                
            return locals()
        
        duration = property(**duration())
    

class MediaContainer(object):
    def __init__(self, mime=''):
        self.metadata = {}
        if mime:
            self.metadata['mimetype'] = mime
            
        self.entries = []
        self.attachments = []
                


class AudioStreamInfo(object):
    def __init__(self):
        self.metadata = {}
        self.sample_rate = 0
        self.sample_count = 0
        self.channels = 0
        self.bits_per_sample = 0
        self.flags = 0
        self.volume = 100.0
        self.balance = 0.0
        self.bytes_per_second = 0
        self.block_alignment = 0
        self.locale = None

        
class VideoStreamInfo(object):
    def __init__(self):
        self.metadata = {}
        self.flags = 0

        self.width = 0
        self.height = 0
        self.color = True
        self.bit_depth = 0
        self.horiz_dpi = 0
        self.vert_dpi = 0
        self.fourcc = ''


class ImageStreamInfo(object):
    def __init__(self):
        self.metadata = {}
        self.flags = 0

        self.width = 0
        self.height = 0
        self.bit_depth = 0
        self.interlaced = False
        self.horiz_dpi = 0
        self.vert_dpi = 0
        self.fourcc = ''


class SubtitleStreamInfo(object):
    def __init__(self):
        self.metadata = {}
        self.locale = None    
