# Copyright (c) 2009-2014 Simon Kennedy <sffjunkie+code@gmail.com>

from mogul.locale import localize
_ = localize.get_translator('mogul.media')

__all__ = ['Image']

ID3_IMAGE_TYPE = {
    0x00: _('Other'),
    0x01: _('32x32 pixels \'file icon\' (PNG only)'),
    0x02: _('Other file icon'),
    0x03: _('Cover (front)'),
    0x04: _('Cover (back)'),
    0x05: _('Leaflet page'),
    0x06: _('Media (e.g. label side of CD)'),
    0x07: _('Lead artist/lead performer/soloist'),
    0x08: _('Artist/performer'),
    0x09: _('Conductor'),
    0x0A: _('Band/Orchestra'),
    0x0B: _('Composer'),
    0x0C: _('Lyricist/text writer'),
    0x0D: _('Recording Location'),
    0x0E: _('During recording'),
    0x0F: _('During performance'),
    0x10: _('Movie/video screen capture'),
    0x11: _('A bright coloured fish'),
    0x12: _('Illustration'),
    0x13: _('Band/artist logotype'),
    0x14: _('Publisher/Studio logotype'),
}


class Attachment(object):
    def __init__(self, mime_type, data):
        self.mime_type = mime_type
        self.data = data
        
        self.item_id = ''
        self.library_id = ''
        self.description = ''


class Image(Attachment):
    """Image Attachment
    
    mkv - file name, mime type, description, data, uid
    mp4 - data type, element name, locale (language, country)
    id3v2 - mime type, picture type (byte), description
    
    image type, mime type, data, description, uid
    """
    
    def __init__(self, image_type=0x03, mime_type=None, data=None):
        self.image_type = image_type
        self.width = 0
        self.height = 0

        # Normalise image/jpg to image/jpeg
        if mime_type is not None:
            try:
                main, sub = mime_type.split('/')
            except ValueError:
                main = 'image'
                sub = mime_type
    
            if sub == 'jpg':
                sub = 'jpeg'
                
            mime_type = '%s/%s' % (main, sub)
        
        Attachment.__init__(self, mime_type, data)

    def write(self, filename='', with_extension=True):
        if filename == '' and self.image_type == 0x03:
            filename = 'cover'
        
        if with_extension:
            if self.mime_type == 'image/png':
                filename += '.png'
            elif self.mime_type == 'image/jpeg':
                filename += '.jpg'
            elif self.mime_type == 'image/bmp':
                filename += '.bmp'
            
        fp = open(filename, 'wb')
        fp.write(self.data)
        fp.close()
