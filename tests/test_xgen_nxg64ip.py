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

# Pages captured from a Caddx xGen NXG64IP (firmware A56P002003-15).  This
# panel sends 17 zone state banks of 4 hex characters each, where older
# xGen panels send 18 banks of 6.
ULTRASYNC_TEST_VAR_DIR = \
    join(dirname(__file__), 'var', NX595EVendor.XGEN, 'nxg64ip')


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
def test_xgen_nxg64ip_communication(mock_post):
    """An xGen NXG64IP logs in, reads its zones and follows changes."""
    mock_post.side_effect = (_resp(path='area.htm'), _resp(path='zones.htm'))

    uobj = UltraSync()
    assert uobj.login() is True
    assert uobj.vendor is NX595EVendor.XGEN
    assert uobj.version == '3.01'
    assert uobj.release == 'A'

    # One area, which is not ready because a zone is open
    assert len(uobj.areas) == 1
    assert uobj.areas[0]['name'] == 'HOME'
    assert uobj.areas[0]['status'] == 'Not Ready'
    assert uobj.areas[0]['states']['chime'] is True

    # Blank and "!" names mark unused zones, which are skipped
    assert sorted(uobj.zones.keys()) == \
        [0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 12, 13]
    assert uobj.zones[0]['name'] == 'ENTRY'
    assert uobj.zones[12]['name'] == 'BEAM BALKONY'

    # Only zone 14 is open; everything else is ready
    assert uobj.zones[13]['name'] == 'OROFOS'
    assert uobj.zones[13]['status'] == 'Not Ready'
    assert uobj.zones[13]['sequence'] == 1
    assert all(
        z['status'] == 'Ready' for bank, z in uobj.zones.items()
        if bank != 13)

    # Nothing has changed since login, so only the sequence is checked
    mock_post.reset_mock()
    mock_post.side_effect = (_resp(path='seq.json'),)
    assert uobj.details(max_age_sec=0)
    assert mock_post.call_count == 1

    # The open zone closes: its sequence moves and its bank is re-read
    seq = _resp(path='seq.json')
    seq.content = seq.content.replace(b'"zone":[224,', b'"zone":[225,')
    zstate = _resp(path='zstate.json')
    zstate.content = zstate.content.replace(
        b'"bankstates":"0020"', b'"bankstates":"0000"')

    mock_post.reset_mock()
    mock_post.side_effect = (seq, zstate)
    assert uobj.details(max_age_sec=0)
    assert mock_post.call_args_list[1][0][0] == \
        'http://zerowire/user/zstate.json'
    assert uobj.zones[13]['status'] == 'Ready'
    assert uobj.zones[13]['sequence'] == 2

    # The area changes next, using the panel's real area status reply
    seq = _resp(path='seq.json')
    seq.content = seq.content.replace(
        b'"zone":[224,', b'"zone":[225,').replace(
        b'"area":[120]', b'"area":[121]')

    mock_post.reset_mock()
    mock_post.side_effect = (seq, _resp(path='status.json'))
    assert uobj.details(max_age_sec=0)
    assert mock_post.call_args_list[1][0][0] == \
        'http://zerowire/user/status.json'
    assert uobj.areas[0]['states']['chime'] is True
