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

# Real two-area captures
COMNAV_VAR_DIR = join(
    dirname(__file__), 'var', NX595EVendor.COMNAV, '0.108-zone-test')
XGEN_VAR_DIR = join(dirname(__file__), 'var', NX595EVendor.XGEN, 'general')

# A ComNav sequence reply where only the area counter has moved
COMNAV_AREA_SEQ = b'<response><areas>71</areas>' \
    b'<zones>201,0,0,225,2,16,0,0,1,0,0,8,0,0</zones></response>'


def _resp(content=b'', path=None, status_code=requests.codes.ok):
    """Return a mocked panel response built from bytes or a fixture file."""
    # Fixture files hold a real page captured from a panel
    if path:
        with open(path, 'rb') as f:
            content = f.read()

    obj = mock.Mock()
    obj.content = content
    obj.status_code = status_code
    return obj


def _comnav(mock_post):
    """Return a logged in two-area ComNav panel."""
    mock_post.side_effect = (
        _resp(path=join(COMNAV_VAR_DIR, 'area.htm')),
        _resp(path=join(COMNAV_VAR_DIR, 'zones.htm')),
        _resp(),
        _resp(path=join(COMNAV_VAR_DIR, 'history.htm')),
    )
    uobj = UltraSync()
    assert uobj.login() is True
    assert uobj.areas[0]['status'] == 'Ready'
    assert uobj.areas[1]['status'] == 'Ready'
    return uobj


def _comnav_status(old, new):
    """Return the captured ComNav area status with one value replaced."""
    status = _resp(path=join(COMNAV_VAR_DIR, 'status.xml'))
    status.content = status.content.replace(old, new)
    return status


@mock.patch('requests.Session.post')
def test_comnav_second_area_updates(mock_post):
    """Changes reported for a ComNav panel's second area are applied."""
    uobj = _comnav(mock_post)

    # Area 2 opens a zone: "Ready" goes from both areas (3) to Area 1 (1)
    mock_post.side_effect = (
        _resp(COMNAV_AREA_SEQ),
        _comnav_status(b'<stat2>3</stat2>', b'<stat2>1</stat2>'))
    assert uobj.details(max_age_sec=0)
    assert uobj.areas[0]['status'] == 'Ready'
    assert uobj.areas[1]['status'] == 'Not Ready'


@mock.patch('requests.Session.post')
def test_comnav_second_area_armed(mock_post):
    """A ComNav panel's second area reports being armed away."""
    uobj = _comnav(mock_post)

    # Area 2 is armed away: the "Armed Away" value gains Area 2's bit (2)
    mock_post.side_effect = (
        _resp(COMNAV_AREA_SEQ),
        _comnav_status(b'<stat0>0</stat0>', b'<stat0>2</stat0>'))
    assert uobj.details(max_age_sec=0)
    assert uobj.areas[0]['status'] == 'Ready'
    assert uobj.areas[0]['arm_state'] == 'disarm'
    assert uobj.areas[1]['status'] == 'Armed Away'
    assert uobj.areas[1]['arm_state'] == 'away'


@mock.patch('requests.Session.post')
def test_xgen_second_area_updates(mock_post):
    """Changes reported for an xGen panel's second area are applied."""
    mock_post.side_effect = (
        _resp(path=join(XGEN_VAR_DIR, 'area.htm')),
        _resp(path=join(XGEN_VAR_DIR, 'zones.htm')),
    )
    uobj = UltraSync()
    assert uobj.login() is True
    assert uobj.areas[1]['status'] == 'Ready'

    # The captured sequence moves a zone counter and the area counter.
    # In the area reply, Area 2 opens a zone (Ready byte 03 -> 01).
    status = _resp(path=join(XGEN_VAR_DIR, 'status.json'))
    status.content = status.content.replace(
        b'"bankstates":"03', b'"bankstates":"01')
    mock_post.side_effect = (
        _resp(path=join(XGEN_VAR_DIR, 'seq.json')),
        _resp(path=join(XGEN_VAR_DIR, 'zstate.json')),
        status)
    assert uobj.details(max_age_sec=0)
    assert uobj.areas[0]['status'] == 'Ready'
    assert uobj.areas[1]['status'] == 'Not Ready'


@mock.patch('requests.Session.post')
def test_area_bank_groups(mock_post):
    """An area bank update only touches the 8 areas in that bank."""
    uobj = _comnav(mock_post)
    area2_state = uobj.areas[1]['bank_state']

    # Bank 1 covers areas 9 to 16, which this panel doesn't have
    uobj._store_area_bank_state(1, [255] * 17)
    assert uobj.areas[1]['bank_state'] == area2_state

    # Area 1 unused on the panel: an update for bank 0 still works
    del uobj.areas[0]
    uobj._store_area_bank_state(0, [0] * 17)
    assert uobj.areas[1]['bank_state'] == [0] * 17


@mock.patch('requests.Session.post')
def test_xgen_more_than_8_areas(mock_post):
    """Areas 9 and up read and follow their own area bank."""
    # Areas 1, 2, 9 and 10 in use.  Bank 1 (areas 9-16) only has Area 10
    # ready (02), and its sequence counter starts at 5.
    area = _resp(path=join(XGEN_VAR_DIR, 'area.htm'))
    area.content = area.content.replace(
        b'["Area 1","Area 2"]',
        b'["Area 1","Area 2","!","!","!","!","!","!","Area 9","Area 10"]'
    ).replace(b'areaSequence = [126]', b'areaSequence = [126,5]').replace(
        b'areaStatus = ["03', b'areaStatus = ["03' + b'0' * 78 + b'","02')
    mock_post.side_effect = (
        area, _resp(path=join(XGEN_VAR_DIR, 'zones.htm')))

    uobj = UltraSync()
    assert uobj.login() is True
    assert uobj.areas[0]['status'] == 'Ready'
    assert uobj.areas[1]['status'] == 'Ready'
    assert uobj.areas[8]['status'] == 'Not Ready'
    assert uobj.areas[9]['status'] == 'Ready'

    # Only bank 1's counter moves; Area 9 is now ready too (03)
    seq = _resp(path=join(XGEN_VAR_DIR, 'seq.json'))
    seq.content = seq.content.replace(
        b'"area":[127]', b'"area":[126,6]').replace(
        b'"zone":[57,', b'"zone":[56,')
    status = _resp(path=join(XGEN_VAR_DIR, 'status.json'))
    status.content = status.content.replace(b'"abank":0', b'"abank":1')
    mock_post.side_effect = (seq, status)
    assert uobj.details(max_age_sec=0)
    assert mock_post.call_args_list[-1][1]['data']['arsel'] == 1

    # Areas 1 and 2 keep their own bank's state
    assert uobj.areas[0]['status'] == 'Ready'
    assert uobj.areas[1]['status'] == 'Ready'
    assert uobj.areas[8]['status'] == 'Ready'
    assert uobj.areas[9]['status'] == 'Ready'


@mock.patch('requests.Session.post')
def test_comnav_more_than_8_areas(mock_post):
    """ComNav areas 9 and up read the second group of 17 values."""
    # Areas 1, 2, 9 and 10 in use.  In the second group only Area 10 is
    # ready (value 2 in the "Ready" position).
    second_group = b',0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0'
    area = _resp(path=join(COMNAV_VAR_DIR, 'area.htm'))
    area.content = area.content.replace(
        b'"%21","%21","%21","%21","%21");',
        b'"%21","%21","%21","%21","%21","%21","AREA%209","AREA%2010");'
    ).replace(
        b'new Array(0,0,3,0,0,0,0,0,0,0,0,0,0,0,0,2,0);',
        b'new Array(0,0,3,0,0,0,0,0,0,0,0,0,0,0,0,2,0' + second_group + b');')
    mock_post.side_effect = (
        area,
        _resp(path=join(COMNAV_VAR_DIR, 'zones.htm')),
        _resp(),
        _resp(path=join(COMNAV_VAR_DIR, 'history.htm')),
    )

    uobj = UltraSync()
    assert uobj.login() is True
    assert uobj.areas[0]['status'] == 'Ready'
    assert uobj.areas[1]['status'] == 'Ready'
    assert uobj.areas[8]['status'] == 'Not Ready'
    assert uobj.areas[9]['status'] == 'Ready'


@mock.patch('requests.Session.post')
def test_comnav_missing_area_values(mock_post):
    """Areas the panel names but sends no values for don't break login."""
    # Areas 9 and 10 are named, but only the first group's values exist
    area = _resp(path=join(COMNAV_VAR_DIR, 'area.htm'))
    area.content = area.content.replace(
        b'"%21","%21","%21","%21","%21");',
        b'"%21","%21","%21","%21","%21","%21","AREA%209","AREA%2010");')
    mock_post.side_effect = (
        area,
        _resp(path=join(COMNAV_VAR_DIR, 'zones.htm')),
        _resp(),
        _resp(path=join(COMNAV_VAR_DIR, 'history.htm')),
    )

    uobj = UltraSync()
    assert uobj.login() is True
    assert uobj.areas[0]['status'] == 'Ready'
    assert uobj.areas[1]['status'] == 'Ready'
    assert uobj.areas[8]['bank_state'] == [0] * 17
