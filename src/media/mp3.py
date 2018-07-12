# Copyright (c) 2009-2014 Simon Kennedy <sffjunkie+code@gmail.com>

__all__ = ['MP3TagReader']

import os

from mogul.media import localize
_ = localize()

from mogul.media import MediaContainer, MediaEntry, MediaStream, \
        AudioStreamInfo, Tag, TagTarget, TagGroup, MediaHandlerError

from mogul.media.id3 import ID3v1TagHandler, ID3v2TagHandler

class MP3Handler(object):
    def __init__(self):
        self._fp = None
        self.metadata = {}
        self.streams = {}

    @staticmethod
    def can_handle(ds):
        pos = ds.tell()
        doctype = None
        if ds.read(3) == b'ID3':
            doctype = 'ID3v2'
        
        ds.seek(-10, os.SEEK_END)
        if ds.read(3) == b'3DI':
            doctype = 'ID3v1'
        
        ds.seek(-128, os.SEEK_END)
        if ds.read(3) == b'TAG':
            doctype = 'ID3v1'
            
        ds.seek(pos, os.SEEK_SET)
        return doctype

    def read(self, filename, doctype=None):
        with open(filename, 'rb') as ds:
            if doctype is None:
                doctype = self.can_handle(ds)
    
            if doctype is not None:
                try:
                    self.read_stream(ds, doctype)
                except EOFError:
                    pass
            else:
                raise MediaHandlerError("MP3Handler: Unable to handle file '%s'" % filename)

    def read_stream(self, ds, doctype=None):
        if doctype is None:
            doctype = self.can_handle(ds)

        if doctype is not None:
            self.container = MediaContainer('audio/mp3')
            self._media_entry = MediaEntry()
            self.container.entries.append(self._media_entry)
            
            if doctype == 'ID3v1':
                self.handler = ID3v1TagHandler()
            else:
                self.handler = ID3v2TagHandler()

            self.handler.read_stream(ds)
        else:
            raise MediaHandlerError("MP3Handler: Unable to handle stream")

    def __getattr__(self, attr):
        return self.handler.__getattr__(attr)
        