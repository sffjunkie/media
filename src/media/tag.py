class Tag(object):
    """A name, value tag with optional sub tags
    
    Note: In EBML this is SimpleTag
    """
    
    def __init__(self, name='', value=None):
        self.name = name
        self.value = value
        self.application = ''
        self.default = True
        self.locale = None
        self.metadata = []
        
    def set_to(self, tag):
        self.name = tag.name
        self.value = tag.value
        self.application = tag.application
        self.default = tag.default
        self.locale = tag.locale
        
        del self.metadata[:]
        for subtag in tag.metadata:
            t = Tag()
            t.set_to(subtag)
            self.metadata.append(t)
            
    def __str__(self):
        return '%s=%s' % (self.name, self.value)


#+============================================================================+
#|TargetType | Audio strings                   | Video strings                |
#|Value      |                                 |                              |
#+============================================================================+
#| 70        | COLLECTION                      | COLLECTION                   |
#| 60        | EDITION / ISSUE / VOLUME / OPUS | SEASON / SEQUEL / VOLUME     |
#| 50        | ALBUM / OPERA / CONCERT         | MOVIE / EPISODE / CONCERT    |
#| 40        | PART / SESSION                  | PART / SESSION               |
#| 30        | TRACK / SONG                    | CHAPTER                      |
#| 20        | SUBTRACK / PART / MOVEMENT      | SCENE                        |
#| 10        | -                               | SHOT                         |
#+============================================================================+

class TagTarget(object):
    def __init__(self, uid=0, target_type=50):
        self.uid = uid
        self.target_type_value = target_type

    def __str__(self):
        return 'Type %d = UID %d' % (self.target_type_value, self.uid)


class TagGroup(object):
    """A group of tags and a list of targets to which they apply.
    
    Note: In EBML this is a Tag
    """
    
    def __init__(self, name=''):
        self.name = name
        self.tags = []
        self.targets = []
