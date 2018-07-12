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
from os.path import join, abspath
import logging

def setup_module(m):
    p = abspath(join(test_path, '..'))
    sys.path.insert(0, p)
    
    logger = logging.getLogger('mogul.media')
    if len(logger.handlers) == 0:
        logger.addHandler(logging.StreamHandler())
        #logger.addHandler(logging.FileHandler(join(m.test_path, 'output', 'run.txt')))
    logger.setLevel(logging.DEBUG)

