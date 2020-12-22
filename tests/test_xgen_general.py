# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Chris Caron <lead2gold@gmail.com>
# All rights reserved.
#
# This code is licensed under the MIT License.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files(the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and / or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions :
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import mock
import requests
from os.path import join
from os.path import dirname

from ultrasync import UltraSync
from ultrasync.common import NX595EVendor

# Disable logging for a cleaner testing output
import logging
logging.disable(logging.CRITICAL)

# Reference Directory
ULTRASYNC_TEST_VAR_DIR = \
    join(dirname(__file__), 'var', NX595EVendor.XGEN, 'general')


@mock.patch('requests.Session.post')
def test_xgen_general_communication(mock_post):
    """
    Test xGen ZeroWire Hub Communication

    """

    # A area response object
    arobj = mock.Mock()

    # Simulate a valid login return
    with open(join(ULTRASYNC_TEST_VAR_DIR, 'area.htm'), 'rb') as f:
        arobj.content = f.read()
    arobj.status_code = requests.codes.ok

    # A zone response object
    zrobj = mock.Mock()

    # Simulate a valid login return
    with open(join(ULTRASYNC_TEST_VAR_DIR, 'zones.htm'), 'rb') as f:
        zrobj.content = f.read()
    zrobj.status_code = requests.codes.ok

    # Assign our response object to our mocked instance of requests
    mock_post.side_effect = (arobj, zrobj)

    uobj = UltraSync()

    # Perform a login which under the hood queries both area.htm and zones.htm
    # (in that order)
    assert uobj.login()
    assert uobj.vendor is NX595EVendor.XGEN
    assert uobj.version == '4.01'
    assert uobj.release == 'B'

    assert isinstance(uobj.areas, dict)
    # we only have 1 area defined in our test file
    assert len(uobj.areas) == 2
    assert uobj.areas[0]['name'] == 'SENSOREN'
    assert uobj.areas[0]['bank'] == 0
    assert uobj.areas[0]['sequence'] == 241
    #TODOassert uobj.areas[0]['status'] == 'Ready'

    assert isinstance(uobj.zones, dict)
