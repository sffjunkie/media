# Copyright (c) 2009-2014 Simon Kennedy <sffjunkie+code@gmail.com>

import os
import struct
import datetime
from io import StringIO

from mogul.media import localize
_ = localize()

from mogul.media.id3_info import ID3_GENRE
from mogul.media.attachment import Image

class ID3v1TagHandler(object):
    def __init__(self, data=None):
        if data is not None:
            self._parse(StringIO(data))

    def read_stream(self, ds):
        self.parse(ds)
        
    def write(self, ds):
        #TODO: Not implemented.
        pass

    def parse(self, ds):
        if ds.read(3) != '\x54\x41\x47':
            raise ValueError(_('Stream does not contain a valid ID3v1TagHandler tag'))
            
        self.title = self._parse_string(ds.read(30))
        self.artist = self._parse_string(ds.read(30))
        self.album = self._parse_string(ds.read(30))
        self.year = self._parse_string(ds.read(4))
        
        comment = ds.read(30)
        self.comment = self._parse_string(comment)
        if comment[-2] == '\0':
            self.track_id = ord(comment[-1])
        else:
            self.track_id = 0
        self.genre_id = ds.read(1)
        
    def genre():
        def fget(self):
            return ID3_GENRE[self.genre_id]
        
        return locals()
    
    genre = property(**genre())
        
    def _parse_string(self, data):
        str = ''
        for x in data:
            if x == '\0':
                break
            else:
                str += x
                
        return str

class ID3v2TagHandler(object):
    def __init__(self, data=None):
        self.FRAME_HANDLER = {
            'AENC': ( _('Audio encryption'), None, None),
            'APIC': ( _('Attached picture'), self._read_apic, None),
            'ASPI': ( _('Audio seek point index'), None, None),
            'COMM': ( _('Comments'), None, None),
            'COMR': ( _('Commercial frame'), None, None),
            'ENCR': ( _('Encryption method registration'), None, None),
            'EQU2': ( _('Equalisation (2)'), None, None),
            'ETCO': ( _('Event timing codes'), None, None),
            'GEOB': ( _('General encapsulated object'), None, None),
            'GRID': ( _('Group identification registration'), None, None),
            'LINK': ( _('Linked information'), None, None),
            'MCDI': ( _('Music CD identifier'), None, None),
            'MLLT': ( _('MPEG location lookup table'), None, None),
            'OWNE': ( _('Ownership frame'), None, None),
            'PRIV': ( _('Private frame'), None, None),
            'PCNT': ( _('Play counter'), None, None),
            'POPM': ( _('Popularimeter'), None, None),
            'POSS': ( _('Position synchronisation frame'), None, None),
            'RBUF': ( _('Recommended buffer size'), None, None),
            'RVA2': ( _('Relative volume adjustment (2)'), None, None),
            'RVRB': ( _('Reverb'), None, None),
            'SEEK': ( _('Seek frame'), None, None),
            'SIGN': ( _('Signature frame'), None, None),
            'SYLT': ( _('Synchronised lyric/text'), None, None),
            'SYTC': ( _('Synchronised tempo codes'), None, None),
            'TALB': ( _('Album/Movie/Show title'), self._read_text, None),
            'TBPM': ( _('BPM (beats per minute)'), self._read_text, None),
            'TCOM': ( _('Composer'), self._read_text, None),
            'TCON': ( _('Content type'), self._read_text, None),
            'TCOP': ( _('Copyright message'), self._read_text, None),
            'TDEN': ( _('Encoding time'), self._read_text, None),
            'TDLY': ( _('Playlist delay'), self._read_text, None),
            'TDOR': ( _('Original release time'), self._read_text, None),
            'TDRC': ( _('Recording time'), self._read_text, None),
            'TDRL': ( _('Release time'), self._read_text, None),
            'TDTG': ( _('Tagging time'), self._read_text, None),
            'TENC': ( _('Encoded by'), self._read_text, None),
            'TEXT': ( _('Lyricist/Text writer'), self._read_text, None),
            'TFLT': ( _('File type'), self._read_text, None),
            'TIPL': ( _('Involved people list'), self._read_text, None),
            'TIT1': ( _('Content group description'), self._read_text, None),
            'TIT2': ( _('Title/songname/content description'), self._read_text, None),
            'TIT3': ( _('Subtitle/Description refinement'), self._read_text, None),
            'TKEY': ( _('Initial key'), self._read_text, None),
            'TLAN': ( _('Language(s)'), self._read_text, None),
            'TLEN': ( _('Length'), self._read_text, None),
            'TMCL': ( _('Musician credits list'), self._read_text, None),
            'TMED': ( _('Media type'), self._read_text, None),
            'TMOO': ( _('Mood'), None, None),
            'TOAL': ( _('Original album/movie/show title'), self._read_text, None),
            'TOFN': ( _('Original filename'), self._read_text, None),
            'TOLY': ( _('Original lyricist(s)/text writer(s)'), self._read_text, None),
            'TOPE': ( _('Original artist(s)/performer(s)'), self._read_text, None),
            'TOWN': ( _('File owner/licensee'), self._read_text, None),
            'TPE1': ( _('Lead performer(s)/Soloist(s)'), self._read_text, None),
            'TPE2': ( _('Band/orchestra/accompaniment'), self._read_text, None),
            'TPE3': ( _('Conductor/performer refinement'), self._read_text, None),
            'TPE4': ( _('Interpreted, remixed, or otherwise modified by'), self._read_text, None),
            'TPOS': ( _('Part of a set'), self._read_text, None),
            'TPRO': ( _('Produced notice'), self._read_text, None),
            'TPUB': ( _('Publisher'), self._read_text, None),
            'TRCK': ( _('Track number/Position in set'), self._read_text, None),
            'TRSN': ( _('Internet radio station name'), self._read_text, None),
            'TRSO': ( _('Internet radio station owner'), self._read_text, None),
            'TSOA': ( _('Album sort order'), self._read_text, None),
            'TSOP': ( _('Performer sort order'), self._read_text, None),
            'TSOT': ( _('Title sort order'), self._read_text, None),
            'TSRC': ( _('ISRC (international standard recording code)'), self._read_text, None),
            'TSSE': ( _('Software/Hardware and settings used for encoding'), self._read_text, None),
            'TSST': ( _('Set subtitle'), self._read_text, None),
            'TXXX': ( _('User defined text information frame'), self._read_text, None),
            'TYER': ( _('Year of recording'), self._read_text, None),
            'UFID': ( _('Unique file identifier'), self._read_ufid, None),
            'USER': ( _('Terms of use'), None, None),
            'USLT': ( _('Unsynchronised lyric/text transcription'), None, None),
            'WCOM': ( _('Commercial information'), None, None),
            'WCOP': ( _('Copyright/Legal information'), None, None),
            'WOAF': ( _('Official audio file webpage'), None, None),
            'WOAR': ( _('Official artist/performer webpage'), None, None),
            'WOAS': ( _('Official audio source webpage'), None, None),
            'WORS': ( _('Official Internet radio station homepage'), None, None),
            'WPAY': ( _('Payment'), None, None),
            'WPUB': ( _('Publishers official webpage'), None, None),
            'WXXX': ( _('User defined URL link frame'), None, None),
        }
        
        self.__attribute_accessors = {
            'artist': 'TPE1',
            'album': 'TALB',
            'title': 'TIT2',
            'year': 'TYER',
            'genre': 'TCON',
            'track_id': 'TRCK',
            'set': 'TPOS',
            'text': 'TXXX',
            'image': 'APIC',
            'encoder': 'TENC',
            'bpm': 'TBPM',
            'ufid': 'UFID',
            'written': 'TOLY',
            'compilation': 'TCMP',
            'length': lambda: self._length
        }
        
        self.frames = {}
        
        if data is not None:
            self._parse(StringIO(data))

    def read_stream(self, ds):
        """Read an ID3v2TagHandler tag from a data stream."""
        
        self._parse(ds)
        
    def write(self, ds):
        """Write ID3v2TagHandler tag to a data stream."""
        
        #TODO: Not implemented.
        pass

    def __getattr__(self, attr):
        accessor = self.__attribute_accessors.get(attr, None)
        
        if accessor is not None:
            if callable(accessor):
                return accessor()
            else:
                value = self.frames.get(accessor, None)
                if value is not None:
                    if isinstance(value, list):
                        if len(value) == 1:
                            return value[0]
                        else:
                            return value
                    else:
                        return value

                raise AttributeError("Attribute '%s' not found in file." % attr)
        else:
            raise AttributeError("Unknown attribute '%s'." % attr)

    def _length(self):
        try:
            ms = int(self.frames['TLEN'])
            return datetime.timedelta(milliseconds = ms)
        except:
            return -1

    def _parse(self, ds, search=''):
        """Parse the ID3v2TagHandler data stream."""
        header = struct.unpack('0003sBBB0004B', ds.read(10))
        if header[0] != b'ID3':
            raise ValueError(_('Data stream \'ds\' does not represent an ID3 tag'))

        self.version = '2.%d.%d' % (header[1], header[2])
        flags = header[3]
        self.unsync = bool((flags & 0x80) >> 7);
        self.extended = bool((flags & 0x40) >> 6);
        self.experimental = bool((flags & 0x20) >> 5);
        self.footer = bool((flags & 0x10) >> 4);
        _size = self._safeunsync(header[4:8])
        
        if self.extended:
            _pos = self._read_extended_header(ds)
        else:
            self.any_text_encoding = True

        try:
            while 1:
                self._read_box(ds)
        except:
            pass

    def _read_extended_header(self, ds):
        # TODO: extended_header handling
        info = struct.unpack('0004BB', ds.read(5))
        size = info[4]
        _flags = struct.unpack('%04sB' % size, ds.read(size))
        self.any_text_encoding = True

    def _read_box(self, ds):
        info = struct.unpack('0004s0004B0002B', ds.read(10))
        frame = info[0]
        size = self._frame_size(info[1:5])
        _flag0 = info[5]
        _flag1 = info[6]

        try:
            frame_handler = self.FRAME_HANDLER[frame][1]
        except:
            frame_handler = None

        if frame_handler is not None:
            frame_handler(frame, ds, size)
        else:
            ds.seek(size, os.SEEK_CUR)

    def _read_ufid(self, frame, ds, size):
        owner_id = self._read_byte_string(ds)
        identifier = ds.read(size - len(owner_id) - 1)
        
        ufid = (owner_id, identifier)
        
        if 'UFID' not in self.frames:
            self.frames['UFID'] = []
            
        self.frames['UFID'].append(ufid)

    def _read_text(self, frame, ds, size):
        encoding = ord(ds.read(1))
        text = ds.read(size - 1)

        if encoding == 0x00:
            codec = 'UTF-8'
        elif encoding == 0x01:
            codec = 'UTF-16'
        elif encoding == 0x02:
            codec = 'UTF-16-BE'
        elif encoding == 0x03:
            codec = 'UTF-8'

        text = text.decode(codec)
        if frame not in self.frames:
            self.frames[frame] = []

        self.frames[frame].append(text)

    def _read_apic(self, frame, ds, size):
        encoding = struct.unpack('B', ds.read(1))[0]
        mime = self._read_byte_string(ds)
        image_type = struct.unpack('B', ds.read(1))[0]
        
        description = self._read_byte_string(ds)
        if encoding == 0x00:
            codec = 'UTF-8'
        elif encoding == 0x01:
            codec = 'UTF-16'
        elif encoding == 0x02:
            codec = 'UTF-16-BE'
        elif encoding == 0x03:
            codec = 'UTF-8'

        description = description.decode(codec)
        
        data = ds.read(size - (2 + len(mime) + len(description) + 2))
        
        image = Image(image_type, mime, data)
        image.description = description

        if 'APIC' not in self.frames:
            self.frames['APIC'] = []

        self.frames['APIC'].append(image)

    def _read_byte_string(self, ds):
        string = ''
        while 1:
            ch = ds.read(1)
            
            if ch == '\0':
                break
            
            string += ch

        return string

    def _frame_size(self, values):
        size = 0
        count = len(values)
        for x in range(count):
            size += values[x] << ((count-1 - x) * 8)
        
        return size
    
    def _safeunsync(self, values):
        size = 0
        count = len(values)
        for x in range(count):
            value = values[x]
            
            if ((value & 0x80) >> 7) == 1:
                raise ValueError(_('Invalid ID3 sync safe integer'))
            
            size += (value & 0x7F) << ((count-1 - x) * 7)
        
        return size
        
    def _safesync(self, value):
        pass
    