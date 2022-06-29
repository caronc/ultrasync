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
    join(dirname(__file__), 'var', NX595EVendor.XGEN8, 'bypass')


@mock.patch('requests.Session.post')
def test_xgen8_bypass(mock_post):
    """
    Test xGen 8 Zone Bypass
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

    # A zonefunction response object
    zfun_obj = mock.Mock()

    with open(join(ULTRASYNC_TEST_VAR_DIR, 'zonefunction.json'), 'rb') as f:
        zfun_obj.content = f.read()
    zfun_obj.status_code = requests.codes.ok

    # A sequence response object
    seq_obj = mock.Mock()

    # Simulate initial sequence configuration
    with open(join(ULTRASYNC_TEST_VAR_DIR, 'seq.json'), 'rb') as f:
        seq_obj.content = f.read()
    seq_obj.status_code = requests.codes.ok

    # A zone state response object
    zst_obj = mock.Mock()

    # Simulate initial zone fetch configuration
    with open(join(ULTRASYNC_TEST_VAR_DIR, 'zstate.json'), 'rb') as f:
        zst_obj.content = f.read()
    zst_obj.status_code = requests.codes.ok

    # Assign our response object to our mocked instance of requests
    mock_post.side_effect = (arobj, zrobj)

    uobj = UltraSync()
    # uobj.load('/home/vagabond/.config/ultrasync')

    # Test that we're a xGen v8
    assert uobj.login()
    assert uobj.vendor is NX595EVendor.XGEN8
    assert uobj.version == '8.000'
    assert uobj.release == '0'

    assert isinstance(uobj.areas, dict)
    # we only have 1 area defined in our test file
    assert len(uobj.areas) == 1
    assert uobj.areas[0]['name'] == 'Area 1'
    assert uobj.areas[0]['bank'] == 0
    assert uobj.areas[0]['sequence'] == 1
    assert uobj.areas[0]['status'] == 'Not Ready'

    assert isinstance(uobj.zones, dict)
    # we have 15 zones defined
    assert len(uobj.zones) == 15

    for bank in range(15):
        assert uobj.zones[bank]['name'] == 'Sensor ' + str(bank + 1)
        assert uobj.zones[bank]['bank'] == bank
        assert uobj.zones[bank]['sequence'] == 1
        assert uobj.zones[bank]['status'] == 'Ready' \
            if bank in (0, 1, 3, 4, 5, 7, 8, 12, 13, 14) else 'Not Ready'
        assert uobj.zones[bank]['can_bypass'] is True

    assert uobj.zones[0]['bank_state'] == '000000000000000000'

    # Call set_zone_bypass
    mock_post.reset_mock()
    mock_post.side_effect = (zfun_obj,)

    assert uobj.set_zone_bypass(1, True)

    assert mock_post.call_count == 1
    assert mock_post.call_args_list[0][0][0] == \
        'http://zerowire/user/zonefunction.cgi'

    # Perform Update and check that the zone is bypassed
    mock_post.reset_mock()
    mock_post.side_effect = (seq_obj, zst_obj)

    uobj.update(max_age_sec=0)

    assert uobj.zones[0]['bank_state'] == '000100000000000000'

    assert mock_post.call_count == 2
    assert mock_post.call_args_list[0][0][0] == \
        'http://zerowire/user/seq.json'
    assert mock_post.call_args_list[1][0][0] == \
        'http://zerowire/user/zstate.json'
