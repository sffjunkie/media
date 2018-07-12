# Copyright (c) 2009-2014 Simon Kennedy <sffjunkie+code@gmail.com>

import os

from plistlib import PlistParser

from mogul.media.itc import ITCHandler

class iTunesLibrary(object):
    def __init__(self):
        self.tracks = {}
        
    def read(self, filename):
        self.filename = filename
        self._fp = open(filename)
        
        self._parser = PlistParser()
        root = self._parser.parse(self._fp)
        
        return root
                
class iTunesArtworkDatabase(object):
    def __init__(self, itunes_dir=''):
        self.itunes_dir = itunes_dir
            
    def exists(self, library_id, persistent_id):
        paths = self.itc_paths(library_id, persistent_id)
        if os.path.exists(paths[0]) or os.path.exists(paths[1]):
            return True
        else:
            return False
    
    def get_image(self, library_id, persistent_id, size=128):
        itc_file = ITCHandler()
        paths = self.itc_paths(library_id, persistent_id)
        try:
            itc_file.read(paths[0])
        except:
            itc_file.read(paths[1])
        
        found = None
        for image in itc_file.images:
            # If within 5%
            if size < (image.width + (image.width/20)) or size > (image.width - (image.width/20)) \
                    or size < (image.height + (image.height/20)) or size > (image.height - (image.height/20)):
                found = image
                break

        if found is not None:
            return found
        else:
            raise IndexError('Image with width %d not found in ITC file')
    
    def itc_paths(self, library_id, persistent_id):
        path = ''
        for ch in persistent_id[::-1][:3]:
            path = os.path.join(path, '%02d' % int(ch, 16))
        
        paths = [
            os.path.join(self.itunes_dir, 'Cache', library_id, path, '%s-%s.itc' % (library_id, persistent_id)),
            os.path.join(self.itunes_dir, 'Download', library_id, path, '%s-%s.itc' % (library_id, persistent_id))
        ]
        return paths 
