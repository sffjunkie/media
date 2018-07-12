from mogul.media import MediaContainer, MediaEntry, MediaStream, ImageStreamInfo
from mogul.media import TagGroup, TagTarget

class Video(MediaContainer):
    def __init__(self, mime):
        MediaContainer.__init__(self, mime)
