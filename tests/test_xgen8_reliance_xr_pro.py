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

# Pages captured from a Reliance XR Pro (firmware 16.03) with an NXG-508N
# output expander.  Names and the session id were replaced; the panel's
# state data is as captured.  It sends 26 zone state banks of 4 hex
# characters each.
ULTRASYNC_TEST_VAR_DIR = \
    join(dirname(__file__), 'var', NX595EVendor.XGEN8, 'reliance-xr-pro')


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
def test_xgen8_reliance_xr_pro(mock_post):
    """A Reliance XR Pro logs in, reads its areas and zones, and polls."""
    mock_post.side_effect = (_resp(path='area.htm'), _resp(path='zones.htm'))

    uobj = UltraSync()
    assert uobj.login() is True
    assert uobj.vendor is NX595EVendor.XGEN8
    assert uobj.version == '8.000'

    # Three areas in use, all disarmed; the other 5 are named "!"
    assert [a['name'] for a in uobj.areas.values()] == \
        ['House', 'Workshop', 'Loft']
    assert all(a['status'] == 'Ready' for a in uobj.areas.values())
    assert all(a['arm_state'] == 'disarm' for a in uobj.areas.values())

    # Twelve named zones, all ready
    assert sorted(uobj.zones.keys()) == list(range(12))
    assert uobj.zones[0]['name'] == 'Lobby PIR'
    assert uobj.zones[11]['name'] == 'Key Switch'
    assert all(z['status'] == 'Ready' for z in uobj.zones.values())

    # The panel marks its smoke detectors (zones 6 to 8) as not bypassable
    assert [b for b, z in uobj.zones.items() if not z['can_bypass']] == \
        [5, 6, 7]

    # Nothing has changed since login, so only the sequence is checked
    mock_post.reset_mock()
    mock_post.side_effect = (_resp(path='seq.json'),)
    assert uobj.details(max_age_sec=0)
    assert mock_post.call_count == 1

    # Zone 1 opens: the first zone bank's sequence moves and is re-read
    seq = _resp(path='seq.json')
    seq.content = seq.content.replace(b'"zone":[5,', b'"zone":[6,')
    zstate = _resp(path='zstate.json')
    zstate.content = zstate.content.replace(
        b'"bankstates":"0000"', b'"bankstates":"0100"')

    mock_post.reset_mock()
    mock_post.side_effect = (seq, zstate)
    assert uobj.details(max_age_sec=0)
    assert mock_post.call_args_list[1][0][0] == \
        'http://zerowire/user/zstate.json'
    assert uobj.zones[0]['status'] == 'Not Ready'
    assert uobj.zones[0]['sequence'] == 2
    assert all(
        z['status'] == 'Ready' for bank, z in uobj.zones.items()
        if bank != 0)
