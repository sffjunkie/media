# Copyright (c) 2009-2014 Simon Kennedy <sffjunkie+code@gmail.com>

import os
import struct

from mogul.media import localize
_ = localize()

from mogul.media import MediaHandler
from mogul.media.element import Element

class IPTCNAAHandler(MediaHandler):
    def __init__(self, log_indent_level=0):
        super(IPTCNAAHandler, self).__init__(log_indent_level)
        
        self.metadata = {}

        self._encoding = 'ISO-8859-1'
        
        self._elements = {
            (1, 0):   Element(_('Model Version')),
            (1, 5):   Element(_('Destination')),
            (1, 90):  Element(_('Coded Character Set'), self._parse_character_set),
            (2, 0):   Element(_('Record Version'), self._parse_number, key='version'),
            (2, 5):   Element(_('Name'), self._parse_string, key='object'),
            (2, 7):   Element(_('Edit Status'), self._parse_string, key='edit_status'),
            (2, 8):   Element(_('Editorial Update'), self._parse_string, key='editorial_update'),
            (2, 10):  Element(_('Urgency'), self._parse_string, key='urgency'),
            (2, 12):  Element(_('Subject'), self._parse_string, key='reference'),
            (2, 15):  Element(_('Category'), self._parse_string, key='category'),
            (2, 20):  Element(_('Supplemental Category'), self._parse_string, key='supplemental_category'),
            (2, 22):  Element(_('Fixture Identifier'), self._parse_string, key='fixture_identifier'),
            (2, 25):  Element(_('Keywords'), self._parse_string, key='keywords'),
            (2, 26):  Element(_('Content Location Code'), self._parse_string, key='content_location_code'),
            (2, 27):  Element(_('Content Location Name'), self._parse_string, key='content_location_name'),
            (2, 30):  Element(_('Release Date'), self._parse_date, key='release_date'),
            (2, 35):  Element(_('Release Time'), self._parse_time, key='release_time'),
            (2, 37):  Element(_('Expiration Date'), self._parse_date, key='expiration_date'),
            (2, 38):  Element(_('Expiration Time'), self._parse_time, key='expiration_time'),
            (2, 40):  Element(_('Special Instructions'), self._parse_string, key='special_instructions'),
            (2, 42):  Element(_('Action Advised'), self._parse_string, key='action_advised'),
            (2, 45):  Element(_('Reference Service'), self._parse_string, key='reference_service'),
            (2, 47):  Element(_('Reference Date'), self._parse_date, key='reference_date'),
            (2, 50):  Element(_('Reference Number'), self._parse_string, key='reference_number'),
            (2, 55):  Element(_('Date Created'), self._parse_date, key='creation_date'),
            (2, 60):  Element(_('Time Created'), self._parse_time, key='creation_time'),
            (2, 62):  Element(_('Digital Creation Date'), self._parse_date, key='digital_creation_date'),
            (2, 63):  Element(_('Digital Creation Time'), self._parse_time, key='digital_creation_time'),
            (2, 65):  Element(_('Originating Program'), self._parse_string, key='originating_program'),
            (2, 70):  Element(_('Program Version'), self._parse_string, key='program_version'),
            (2, 75):  Element(_('Object Cycle'), self._parse_string, key='object_cycle'),
            (2, 80):  Element(_('Byline'), self._parse_string, key='byline'),
            (2, 85):  Element(_('Byline Title'), self._parse_string, key='byline_title'),
            (2, 90):  Element(_('City'), self._parse_string, key='city'),
            (2, 92):  Element(_('Sub-location'), self._parse_string, key='sublocation'),
            (2, 95):  Element(_('Province/State'), self._parse_string, key='province'),
            (2, 100): Element(_('Country/Primary Location Code'), self._parse_string, key='country_code'),
            (2, 101): Element(_('Country/Primary Location Name'), self._parse_string, key='country_name'),
            (2, 103): Element(_('Original Transmission Reference'), self._parse_string, key='original_reference'),
            (2, 105): Element(_('Headline'), self._parse_string, key='headline'),
            (2, 110): Element(_('Credit'), self._parse_string, key='credit'),
            (2, 115): Element(_('Source'), self._parse_string, key='source'),
            (2, 116): Element(_('Copyright Notice'), self._parse_string, key='copyright'),
            (2, 118): Element(_('Contact'), self._parse_string, key='contact'),
            (2, 120): Element(_('Caption'), self._parse_string, key='caption'),
            (2, 122): Element(_('Write/Editor'), self._parse_string, key='writer_editor'),
            (2, 125): Element(_('Rasterized Caption'), self._parse_bitmap, key='caption_rasterized'),
            (2, 130): Element(_('Image Type'), self._parse_string, key='image_type'),
            (2, 131): Element(_('Image Orientation'), self._parse_string, key='image_orientation'),
            (2, 135): Element(_('Language Identifier'), self._parse_string, key='language'),
            (2, 150): Element(_('Audio Type')),
            (2, 151): Element(_('Audio Sampling Rate')),
            (2, 152): Element(_('Audio Sampling Resolution')),
            (2, 153): Element(_('Audio Duration')),
            (2, 154): Element(_('Audio Outcue')),
            (2, 200): Element(_('ObjectData Preview File Format')),
            (2, 201): Element(_('ObjectData Preview File Format Version')),
            (2, 202): Element(_('ObjectData Preview Data')),
            (3, 0):   Element(_('Record Version')),
            (3, 10):  Element(_('Picture Number')),
            (3, 20):  Element(_('Pixels Per Line')),
            (3, 30):  Element(_('Number of Lines')),
            (3, 40):  Element(_('Pixel Size In Scanning Direction')),
            (3, 50):  Element(_('Pixel Size Perpendicular To Scanning Direction')),
            (3, 55):  Element(_('Supplement Type')),
            (3, 60):  Element(_('Colour Representation')),
            (3, 64):  Element(_('Interchange Colour Space')),
            (3, 65):  Element(_('Colour Sequence')),
            (3, 66):  Element(_('ICC Input Colour Profile')),
            (3, 70):  Element(_('Colour Calibration Matrix Table')),
            (3, 80):  Element(_('Lookup Table')),
            (3, 84):  Element(_('Number Of Index Entries')),
            (3, 85):  Element(_('Colour Palette')),
            (3, 86):  Element(_('Number Of Bits Per Sample')),
            (3, 90):  Element(_('Sampling Structure')),
            (3, 100): Element(_('Scanning Direction')),
            (3, 102): Element(_('Image Rotation')),
            (3, 110): Element(_('Data Compression Method')),
            (3, 120): Element(_('Quantisation Method')),
            (3, 125): Element(_('End Points')),
            (3, 130): Element(_('Excursion Tolerance')),
            (3, 135): Element(_('Bits Per Component')),
            (3, 140): Element(_('Maximum Density Range')),
            (3, 145): Element(_('Gamma Compensated Value')),
            (7, 10):  Element(_('Size Mode'), self._parse_bool, key='fixed_size'),
            (7, 20):  Element(_('Max Subfile Size'), self._parse_number, key='max_subfile_size'),
            (7, 90):  Element(_('ObjectData Size'), self._parse_number, key='objectdata_size'),
            (7, 95):  Element(_('Max ObjectData Size'), self._parse_number, key='objectdata_size_max'),
            (8, 10):  Element(_('Subfile')),
            (9, 10):  Element(_('Confirmed ObjectData Size'), self._parse_number, key='objectdata_size_confirmed'),
        }
    
    def read_stream(self, ds, length):
        total_read = 0
        
        while total_read < length:
            tag, record, dataset, count = struct.unpack('>BBBH', ds.read(5))
            total_read += 5
            
            if count & 0x8000:
                count_len = count & 0x7FFF
                if count_len == 4:
                    unpack_format = 'L'
                elif count_len == 8:
                    unpack_format = 'Q'
                
                count = struct.unpack('>%s' % unpack_format, self._ds.read(count_len))
                total_read += count_len
            
            key = (record, dataset)
            try:
                element = self._elements[key]
                self.logger.debug('IPTC-NAA:  %s' % element.title)
                
                try:
                    handler = element.reader
                except:
                    handler = None
                    
                if handler is not None:
                    data = ds.read(count)
                    handler(key, data, count)
                else:
                    ds.seek(count, os.SEEK_CUR)
            except:
                ds.seek(count, os.SEEK_CUR)
                    
            total_read += count
            
        self._handle_references()
    
    def _parse_number(self, key, data, count):
        key = self._elements[key].key
        if key is None:
            return
        
        if count == 1:
            struct_format = 'B'
        elif count == 2:
            struct_format = 'H'
        elif count == 4:
            struct_format = 'L'
        if count == 8:
            struct_format = 'Q'
        
        value = struct.unpack('>%s' % struct_format, data)[0]
        self.metadata[key] = value 
    
    def _parse_string(self, key, data, count):
        key = self._elements[key].key
        if key is None:
            return
        
        value = data.decode(self._encoding)
        
        if key in self.metadata:
            if not isinstance(self.metadata[key], list):
                self.metadata[key] = [self.metadata[key]]
            self.metadata[key].append(value)
        else:
            self.metadata[key] = value 

    def _parse_bool(self, key, data, count):
        key = self._elements[key].key
        if key is None:
            return
        
        self.metadata[key] = bool(data)

    def _parse_date(self, key, data, count):
        pass

    def _parse_time(self, key, data, count):
        pass

    def _parse_bitmap(self, key, data, count):
        pass

    def _parse_character_set(self, key, data, count):
        pass
    
    def _parse_subfile(self, key, data, count):
        pass
    
    def _handle_references(self):
        pass
    