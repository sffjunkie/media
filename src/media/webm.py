# Copyright (c) 2009-2014 Simon Kennedy <sffjunkie+code@gmail.com>

from mogul.media import localize
_ = localize()
from mogul.media import localize
_ = localize()

from mogul.media.ebml import EBMLHandler

class WebMHandler(EBMLHandler):
    def __init__(self):
        EBMLHandler.__init__(self)

    @staticmethod
    def can_handle(filename):
        if EBMLHandler.can_handle(filename) == 'webm':
            return 'webm'
        else:
            return None
    