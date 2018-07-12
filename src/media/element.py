# Copyright (c) 2015 Simon Kennedy <sffjunkie+code@gmail.com>

from collections import namedtuple

__all__ = ['Element']

_Element = namedtuple('Element', "title reader writer key log")

def Element(title, reader=None, writer=None, key=None, log=True):
    return _Element(title, reader, writer, key, log)
