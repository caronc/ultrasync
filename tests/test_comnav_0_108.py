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
    join(dirname(__file__), 'var', NX595EVendor.COMNAV, '0.108')


@mock.patch('requests.Session.post')
def test_comnav_0_108_communication(mock_post):
    """
    Test ComNav v0.108 Hub Communication

    """

    # A area response object
    arobj = mock.Mock()

    # Simulate a valid login return
    with open(join(ULTRASYNC_TEST_VAR_DIR, 'area.htm'), 'rb') as f:
        arobj.content = f.read()
    arobj.status_code = requests.codes.ok

    # A zone response object
    zrobj = mock.Mock()

    # Simulate initial zone configuration
    with open(join(ULTRASYNC_TEST_VAR_DIR, 'zones.htm'), 'rb') as f:
        zrobj.content = f.read()
    zrobj.status_code = requests.codes.ok

    # A sequence response object
    seq_obj = mock.Mock()

    # Simulate initial sequence configuration
    with open(join(ULTRASYNC_TEST_VAR_DIR, 'seq.xml'), 'rb') as f:
        seq_obj.content = f.read()
    seq_obj.status_code = requests.codes.ok

    # A zone state response object
    zst_obj = mock.Mock()

    # Simulate initial zone fetch configuration
    with open(join(ULTRASYNC_TEST_VAR_DIR, 'zstate.xml'), 'rb') as f:
        zst_obj.content = f.read()
    zst_obj.status_code = requests.codes.ok

    # An area state response object
    ast_obj = mock.Mock()

    # Simulate initial area status fetch configuration
    with open(join(ULTRASYNC_TEST_VAR_DIR, 'status.xml'), 'rb') as f:
        ast_obj.content = f.read()
    ast_obj.status_code = requests.codes.ok

    # Assign our response object to our mocked instance of requests
    mock_post.side_effect = (arobj, zrobj)

    uobj = UltraSync()

    # Perform a login which under the hood queries both area.htm and zones.htm
    # (in that order)
    assert uobj.login()
    assert uobj.vendor is NX595EVendor.COMNAV
    assert uobj.version == '0.108'
    assert uobj.release == 'm'

    assert isinstance(uobj.areas, dict)
    # we only have 1 area defined in our test file
    assert len(uobj.areas) == 1
    assert uobj.areas[0]['name'] == 'Home'
    assert uobj.areas[0]['bank'] == 0
    assert uobj.areas[0]['sequence'] == 1
    assert uobj.areas[0]['status'] == 'Ready'

    assert isinstance(uobj.zones, dict)
    # our total zones defined
    assert len(uobj.zones) == 17
    zone_map = [
        {
            'bank': 0,
            'name': 'MasterBed Motion',
        }, {
            'bank': 1,
            'name': 'Living Room Motion',
        }, {
            'bank': 2,
            'name': 'Kitchen/DiningMotion',
        }, {
            'bank': 3,
            'name': 'Theater Motion',
        }, {
            'bank': 4,
            'name': 'Hallway Motion',
        }
    ]
    for entry in zone_map:
        assert entry['bank'] in uobj.zones
        assert uobj.zones[entry['bank']]['bank'] == entry['bank']
        assert uobj.zones[entry['bank']]['name'] == entry['name']
        assert uobj.zones[entry['bank']]['sequence'] == 1
        assert uobj.zones[entry['bank']]['status'] == \
            entry.get('status', 'Ready')
        assert uobj.zones[entry['bank']]['can_bypass'] is None

    # A call to login.cgi (which fetches area.html) and then zones.htm
    assert mock_post.call_count == 2
    assert mock_post.call_args_list[0][0][0] == \
        'http://zerowire/login.cgi'
    assert mock_post.call_args_list[1][0][0] == \
        'http://zerowire/user/zones.htm'

    # Reset our mock object
    mock_post.reset_mock()

    # Update our side effects
    mock_post.side_effect = (seq_obj, ast_obj, zst_obj)

    # Perform Updated Query
    uobj.update(max_age_sec=0)

    # Only 1 query made because seq.xml file unchanged
    assert mock_post.call_count == 1
    assert mock_post.call_args_list[0][0][0] == \
        'http://zerowire/user/seq.xml'
    assert uobj.areas[0]['sequence'] == 1

    # Update our sequence file so that it reflects a change
    with open(join(ULTRASYNC_TEST_VAR_DIR, 'seq.w.update.xml'), 'rb') as f:
        seq_obj.content = f.read()

    # Reset our mock object
    mock_post.reset_mock()

    # Update our side effects
    mock_post.side_effect = (seq_obj, ast_obj, zst_obj)

    # Perform Updated Query
    uobj.update(max_age_sec=0)

    assert mock_post.call_count == 3
    assert mock_post.call_args_list[0][0][0] == \
        'http://zerowire/user/seq.xml'
    assert mock_post.call_args_list[1][0][0] == \
        'http://zerowire/user/zstate.xml'
    assert mock_post.call_args_list[2][0][0] == \
        'http://zerowire/user/status.xml'

    assert isinstance(uobj.areas, dict)
    assert len(uobj.areas) == 1
    assert uobj.areas[0]['name'] == 'Home'
    assert uobj.areas[0]['bank'] == 0
    # Our sequence got bumped
    assert uobj.areas[0]['sequence'] == 1
    assert uobj.areas[0]['status'] == 'Ready'

    # Reset our mock object
    mock_post.reset_mock()

    # Update our side effects
    mock_post.side_effect = seq_obj

    uobj.details(max_age_sec=0)

    # Only 1 query made because seq.xml file unchanged
    assert mock_post.call_count == 1
    assert mock_post.call_args_list[0][0][0] == \
        'http://zerowire/user/seq.xml'
    assert uobj.areas[0]['sequence'] == 1
