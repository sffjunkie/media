# Copyright (c) 2009-2014 Simon Kennedy <sffjunkie+code@gmail.com>

import os.path

from mogul.media.asf import ASFHandler
from mogul.media.mp3 import MP3Handler
from mogul.media.mp4 import MP4Handler
from mogul.media.mkv import MKVHandler

HANDLERS = {
    'asf': ASFHandler,
}

class MediaFile(object):
    def __init__(self, filename):
        self._filename = filename
    
    def read(self):
        self.container = self._get_container()
            
        if self.container is not None:
            self.container.read(self._filename)
    
    def artist():
        def fget(self):
            return self.container.artist
            
        def fset(self, value):
            self.container.artist = value
            
        return locals()
    
    artist = property(**artist())
    
    def album():
        def fget(self):
            return self.container.album
            
        def fset(self, value):
            self.container.album = value
            
        return locals()
    
    album = property(**album())
        
    def _get_container(self):
        extension = os.path.splitext(self._filename)[1]
        if extension == '.wmv' or extension == '.wma':
            if ASFHandler.can_handle(self._filename) is not None:
                return ASFHandler()
        elif extension == '.mp3':
            if MP3Handler.can_handle(self._filename) is not None:
                return MP3Handler()
        elif extension == '.mp4' or extension == '.m4a' or \
                extension == '.m4p' or extension.startswith('.ala'):
            if MP4Handler.can_handle(self._filename) is not None:
                return MP4Handler()
        elif extension == '.mkv':
            if MKVHandler.can_handle(self._filename) is not None:
                return MKVHandler()
            
        return None
        

if __name__ == "__main__":
    filename = os.path.join(os.path.dirname(__file__), 'data', 'music.wma')
    
    f = MediaFile(filename)
    f.read()
    print f.container
    print f.artist
    print f.album