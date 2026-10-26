# -*- coding: utf-8 -*-

# Copyright (C) 2026 Chris Caron <lead2gold@gmail.com>
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
from os.path import join
from os.path import dirname
from unittest import mock

import requests

from ultrasync import UltraSync
from ultrasync.common import NX595EVendor

# Disable logging for a cleaner testing output
import logging
logging.disable(logging.CRITICAL)

# Pages captured from a 128 zone ComNav panel (web v0.106-j) with only 6
# zones in use.  Used zones have blank names and unused ones are named "!".
ULTRASYNC_TEST_VAR_DIR = \
    join(dirname(__file__), 'var', NX595EVendor.COMNAV, '0.106-unused-zones')


def _resp(content=b'', path=None, status_code=requests.codes.ok):
    """Return a mocked panel response built from bytes or a fixture file."""
    # Fixture files hold a real page captured from a panel
    if path:
        with open(join(ULTRASYNC_TEST_VAR_DIR, path), 'rb') as f:
            content = f.read()

    obj = mock.Mock()
    obj.content = content
    obj.status_code = status_code
    return obj


@mock.patch('requests.Session.post')
def test_comnav_0_106_unused_zones(mock_post):
    """A ComNav v0.106 panel skips zones named "!" and keeps blank ones."""
    # Login reads the area page, zones, outputs and history (in that order)
    mock_post.side_effect = (
        _resp(path='area.htm'), _resp(path='zones.htm'), _resp(), _resp())

    uobj = UltraSync()
    assert uobj.login() is True
    assert uobj.vendor is NX595EVendor.COMNAV
    assert uobj.version == '0.106'
    assert uobj.release == 'j'

    # Only the first area is in use; the other 7 are named "!"
    assert len(uobj.areas) == 1
    assert uobj.areas[0]['name'] == 'Area 1'

    # The panel lists 128 zones, but only the first 6 are in use.  They
    # have no names, so each gets a generic one.
    assert sorted(uobj.zones.keys()) == [0, 1, 2, 3, 4, 5]
    assert [z['name'] for z in uobj.zones.values()] == \
        ['Sensor {}'.format(n) for n in range(1, 7)]

    # Zone 3 is open; every other zone is ready
    assert uobj.zones[2]['status'] == 'Not Ready'
    assert all(
        z['status'] == 'Ready' for bank, z in uobj.zones.items()
        if bank != 2)

    # Nothing has changed since login, so only the sequence is checked
    mock_post.reset_mock()
    mock_post.side_effect = (_resp(path='seq.xml'),)
    assert uobj.details(max_age_sec=0)
    assert mock_post.call_count == 1

    # Zone 3 closes: the first zone bank's sequence moves and is re-read
    seq = _resp(path='seq.xml')
    seq.content = seq.content.replace(b'<zones>184,', b'<zones>185,')
    zstate = _resp(path='zstate.xml')
    zstate.content = zstate.content.replace(
        b'<zdat>4,', b'<zdat>0,')

    mock_post.reset_mock()
    mock_post.side_effect = (seq, zstate)
    assert uobj.details(max_age_sec=0)
    assert mock_post.call_args_list[1][0][0] == \
        'http://zerowire/user/zstate.xml'
    assert uobj.zones[2]['status'] == 'Ready'
    assert uobj.zones[2]['sequence'] == 2

    # Still only the 6 zones in use
    assert len(uobj.zones) == 6
