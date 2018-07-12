# Copyright (c) 2015 Simon Kennedy <sffjunkie+code@gmail.com>
#
# Licensed under the Apache License, Version 2.0

import sys
import glob
import os.path
import logging

test_path = os.path.abspath(os.path.dirname(__file__))

try:
    base_path = os.environ['DEV_HOME']
except:
    base_path = test_path
    
data_path = os.path.join(base_path, 'data', 'media', 'mkv')

p = os.path.abspath(os.path.join(test_path, '..'))
sys.path.insert(0, p)

logger = logging.getLogger('mogul.media')
del logger.handlers[:]
logger.addHandler(logging.StreamHandler())
logger.addHandler(logging.FileHandler(os.path.join(base_path, 'data', 'output', 'mogul', 'run.txt')))
logger.setLevel(logging.DEBUG)

from mogul.media.mkv import MKVHandler


def filename(name):
    return os.path.join(data_path, name)


def read_MKV(filename):
    logger.debug('test_MKVHandler: Reading file %s' % filename)
    with open(filename, 'rb') as ds:
        doctype = MKVHandler.can_handle(ds)
        
        if doctype is not None:
            h = MKVHandler()
            h.read_stream(ds, doctype)
            pass

    
def test_All_MKV(all_files=True):
    if not all_files:
        print('*** Only processing first file')

    for filename in glob.glob(os.path.join(data_path, '*.mkv')):
        read_MKV(filename)
        
        if not all_files:
            break
    
    
if __name__ == '__main__':
    test_All_MKV(False)
    #read_MKV(filename('test4.mkv'))
    