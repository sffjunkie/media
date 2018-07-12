# Copyright (c) 2009-2014 Simon Kennedy <sffjunkie+code@gmail.com>

from mogul.media import localize
_ = localize()

from mogul.media import MediaHandler
import mogul.media.tiff

class ExifError(Exception):
    pass


class ExifHandler(MediaHandler):
    def __init__(self, log_indent_level=0):
        super(ExifHandler, self).__init__(log_indent_level)
        
        self.filename = ''    
        self.metadata = {}
        
        self._tiff_tag_map = {
        }
    
    def read_stream(self, ds, length=-1):
        self.logger.debug('EXIF: Reading TIFF Data')

        tiff = mogul.media.tiff.TIFFHandler(self.logger.level + 1)
        tiff.filename = self.filename
        tiff.read_stream(ds, length)
        
        self._handle_container(tiff.container)
    
    def _handle_container(self, container):
        for entry in container.entries:
            self._handle_entry(entry)
    
    def _handle_entry(self, entry):
        flash = entry.metadata.get(37385, None)
        if flash is not None:
            self.metadata['exif']['Flash']['Fired'] = False
            