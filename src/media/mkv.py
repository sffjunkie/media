# Copyright (c) 2015 Simon Kennedy <sffjunkie+code@gmail.com>

from mogul.locale import localize
_ = localize.get_translator('mogul.media')

from mogul.media.ebml import EBMLHandler

class MKVHandler(EBMLHandler):
    def __init__(self):
        EBMLHandler.__init__(self)

    @staticmethod
    def can_handle(filename):
        if EBMLHandler.can_handle(filename) == 'matroska':
            return 'matroska'
        else:
            return None
    