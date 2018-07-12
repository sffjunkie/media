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
import pytest

test_path = os.path.abspath(os.path.dirname(__file__))
data_path = os.path.join(test_path, 'data', 'itunes')
output_path = os.path.join(test_path, 'output', 'itunes')

p = os.path.abspath(os.path.join(test_path, '..'))
sys.path.insert(0, p)

logger = logging.getLogger('mogul.media')
del logger.handlers[:]
logger.addHandler(logging.StreamHandler())
logger.addHandler(logging.FileHandler(os.path.join(test_path, 'output', 'run.txt')))
logger.setLevel(logging.DEBUG)

from mogul.media.itunes import iTunesLibrary, iTunesArtworkDatabase

def dump_lib(doc):
    f = open(os.path.join(output_path, 'itunes_dump.txt'), 'w')
    try:
        from pprint import pprint
        for name, value in doc.iteritems():
            f.write('%s\n' % name)
            if name == 'Tracks':
                track = value['1527']
                pprint(track, stream=f)
#                for name1, value1 in track.iteritems():
#                    f.write('Key: %s, Value: %s\n' % (name1, value1))
            else:
                f.write(str(value))
            f.write('\n')
    except:
        pass
    finally:
        f.close()
        
#    print(doc['Tracks'].keys())
    pass

def read_library():
    library_path = os.path.join(data_path, 'iTunes Music Library.xml')    
    library = iTunesLibrary()
    return library.read(library_path)

@pytest.mark.slow
def test_iTunesLibrary():
    root = read_library()
    dump_lib(root)

@pytest.mark.slow
def test_iTunesCoverArt():
    dirname = os.path.join(data_path, 'Album Artwork')
    db = iTunesArtworkDatabase(dirname)
    
    root = read_library()
    library_id = root['Library Persistent ID']
    
    for track in root['Tracks'].itervalues():
        persistent_id = track['Persistent ID']
        
        if db.exists(library_id, persistent_id):
            try:
                image = db.get_image(library_id, persistent_id, 300)
                image.write(os.path.join(output_path, '%s-%s' % (library_id, persistent_id)))
            except:
                pass

