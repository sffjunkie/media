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
import os.path
import logging

test_path = os.path.abspath(os.path.dirname(__file__))

try:
    base_path = os.environ['DEV_HOME']
except:
    base_path = test_path
    
data_path = os.path.join(base_path, 'data', 'media', 'xmp')

p = os.path.abspath(os.path.join(test_path, '..'))
sys.path.insert(0, p)

logger = logging.getLogger('mogul.media')
del logger.handlers[:]
logger.addHandler(logging.StreamHandler())
logger.addHandler(logging.FileHandler(os.path.join(base_path, 'data', 'output', 'mogul', 'run.txt')))
logger.setLevel(logging.DEBUG)

from mogul.media.xmp import XMPHandler

def filename(name):
    return os.path.join(data_path, name)

def test_XMP():
    fname = filename('test1.xmp')    

    ds = open(fname, 'rb')
    h = XMPHandler()
    h.read_stream(ds)
    pass

if __name__ == '__main__':
    test_XMP()
