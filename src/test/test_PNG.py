# Copyright (c) 2009-2014 Simon Kennedy <sffjunkie+code@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import glob
import os.path
import logging

test_path = os.path.abspath(os.path.dirname(__file__))

try:
    base_path = os.environ['DEV_HOME']
except:
    base_path = test_path
    
data_path = os.path.join(base_path, 'data', 'media', 'png')

p = os.path.abspath(os.path.join(test_path, '..'))
sys.path.insert(0, p)

logger = logging.getLogger('mogul.media')
del logger.handlers[:]
logger.addHandler(logging.StreamHandler())
logger.addHandler(logging.FileHandler(os.path.join(base_path, 'data', 'output', 'mogul', 'run.txt')))
logger.setLevel(logging.DEBUG)

from mogul.media.png import PNGHandler

def filename(name):
    return os.path.join(data_path, name)

def read_PNG(filename):
    logger.debug('read_PNG: Reading file %s' % filename)
    with open(filename, 'rb') as ds:
        doctype = PNGHandler.can_handle(ds)
    
        if doctype is not None:
            h = PNGHandler()
            h.read(ds, doctype)
            pass
    
def test_All_PNG():
    for filename in glob.glob(os.path.join(data_path, '*.png')):
        read_PNG(filename)

if __name__ == '__main__':
    read_PNG(filename('xcrn0g04.png'))
    #test_All_PNG()
    