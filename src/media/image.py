# Copyright (c) 2009-2014 Simon Kennedy <sffjunkie+code@gmail.com>

from mogul.media import MediaContainer, MediaEntry, MediaStream, ImageStreamInfo
from mogul.media import TagGroup, TagTarget

class Image(MediaContainer):
    def __init__(self, mime):
        MediaContainer.__init__(self, mime)
        self.media_entry = MediaEntry()
        self.entries.append(self.media_entry)
        
        self.stream = MediaStream()
        self.stream_type_info = ImageStreamInfo()
        self.stream.stream_type_info = self.stream_type_info
        
        self.media_entry.streams.append(self.stream)

        self.tag_group = TagGroup()
        self.tag_group.targets.append(TagTarget())
        self.media_entry.tag_groups.append(self.tag_group)

    def width():
        def fget(self):
            return self.stream.stream_type_info.width
        
        def fset(self, value):
            self.stream.stream_type_info.width = value
        
        return locals()
        
    width = property(**width())

    def height():
        def fget(self):
            return self.stream.stream_type_info.height
        
        def fset(self, value):
            self.stream.stream_type_info.height = value
        
        return locals()
        
    height = property(**height())

    def interlaced():
        def fget(self):
            return self.stream.stream_type_info.interlaced
        
        def fset(self, value):
            self.stream.stream_type_info.interlaced = value
        
        return locals()
        
    interlaced = property(**interlaced())

    def bytes_per_row():
        def fget(self):
            return self.stream.stream_type_info.bytes_per_row
        
        def fset(self, value):
            self.stream.stream_type_info.bytes_per_row = value
        
        return locals()
        
    bytes_per_row = property(**bytes_per_row())

    def thumbnail():
        def fget(self):
            if self._thumbnail is None:
                self._generate_thumbnail()

            return self._thumbnail

        def fset(self, value):
            self._thumbnail = value
        
        return locals()
        
    thumbnail = property(**thumbnail())


