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

import re
from datetime import datetime
from os.path import join
from os.path import dirname
from unittest import mock

import pytest
import requests

from ultrasync import UltraSync
from ultrasync.common import NX595EVendor

# Disable logging for a cleaner testing output
import logging
logging.disable(logging.CRITICAL)

# Reference Directories
ZEROWIRE_VAR_DIR = \
    join(dirname(__file__), 'var', NX595EVendor.ZEROWIRE, 'general')
COMNAV_VAR_DIR = \
    join(dirname(__file__), 'var', NX595EVendor.COMNAV, '0.108')

# Every panel type the library supports
VENDORS = (
    NX595EVendor.ZEROWIRE,
    NX595EVendor.XGEN,
    NX595EVendor.XGEN8,
    NX595EVendor.COMNAV,
)


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


def _drop(page, variable):
    """Return a panel page with one JavaScript variable removed."""
    # Rename the variable so the parser can no longer find it
    return re.sub(
        r'var {}\b'.format(variable).encode(),
        b'var removed', page)


@pytest.mark.parametrize('variable', (
    'zoneSequence', 'zoneStatus', 'zoneNames', 'ismaster', 'isinstaller'))
@mock.patch('requests.Session.post')
def test_zerowire_bad_zones_page(mock_post, variable):
    """Login fails when the ZeroWire zones page is missing a value."""
    area = _resp(path=join(ZEROWIRE_VAR_DIR, 'area.htm'))
    zones = _resp(path=join(ZEROWIRE_VAR_DIR, 'zones.htm'))
    zones.content = _drop(zones.content, variable)

    mock_post.side_effect = (area, zones)
    assert UltraSync().login() is False


@mock.patch('requests.Session.post')
def test_comnav_bad_zones_page(mock_post):
    """Login fails when the ComNav zones page has no zone states."""
    area = _resp(path=join(COMNAV_VAR_DIR, 'area.htm'))
    zones = _resp(path=join(COMNAV_VAR_DIR, 'zones.htm'))
    zones.content = _drop(zones.content, 'zoneStatus')

    mock_post.side_effect = (area, zones)
    assert UltraSync().login() is False


@pytest.mark.parametrize('variable', ('areaStatus', 'areaNames'))
@mock.patch('requests.Session.post')
def test_bad_area_page(mock_post, variable):
    """Login fails when the area page is missing a value."""
    area = _resp(path=join(ZEROWIRE_VAR_DIR, 'area.htm'))
    area.content = _drop(area.content, variable)

    mock_post.side_effect = (area,)
    assert UltraSync().login() is False


@mock.patch('requests.Session.post')
def test_zones_page_unreachable(mock_post):
    """Login fails when the zones page can not be fetched."""
    mock_post.side_effect = (
        _resp(path=join(ZEROWIRE_VAR_DIR, 'area.htm')),
        _resp(status_code=500),
    )
    assert UltraSync().login() is False


@mock.patch('requests.Session.post')
def test_area_page_refresh(mock_post):
    """Areas can be re-read from the panel after login."""
    mock_post.side_effect = (
        _resp(path=join(ZEROWIRE_VAR_DIR, 'area.htm')),
        _resp(path=join(ZEROWIRE_VAR_DIR, 'zones.htm')),
    )
    uobj = UltraSync()
    assert uobj.login() is True

    # The area page is fetched on its own this time
    mock_post.side_effect = (
        _resp(path=join(ZEROWIRE_VAR_DIR, 'area.htm')),)
    assert uobj._areas() is True
    assert mock_post.call_args_list[-1][0][0] == \
        'http://zerowire/user/area.htm'

    # The area page can not be fetched
    mock_post.side_effect = (_resp(status_code=500),)
    assert uobj._areas() is False


@pytest.mark.parametrize('vendor', VENDORS)
@mock.patch('requests.Session.post')
def test_panel_unreachable(mock_post, vendor):
    """Every panel read gives up quietly when the panel stops answering."""
    mock_post.return_value = _resp(status_code=500)

    # Without a session, each read first tries (and fails) to log in
    uobj = UltraSync()
    uobj.vendor = vendor
    assert uobj._zones() is False
    assert uobj._areas() is False
    assert uobj._sequence() is None
    assert uobj._zone_status_update(bank=0) is None
    assert uobj._area_status_update(bank=0) is None

    # With a session, each read gets an error reply instead
    uobj.session_id = 'ABCD'
    assert uobj._sequence() is None
    assert uobj._zone_status_update(bank=0) is None
    assert uobj._area_status_update(bank=0) is None


@mock.patch('requests.Session.post')
def test_comnav_extras_unreachable(mock_post):
    """ComNav history and outputs give up when the panel stops answering."""
    mock_post.return_value = _resp(status_code=500)

    # Without a session the login attempt fails first
    uobj = UltraSync()
    uobj.vendor = NX595EVendor.COMNAV
    assert uobj.history() is False
    assert uobj.output_control() is False

    # With a session the page request itself fails
    uobj.session_id = 'ABCD'
    assert uobj.history() is False
    assert uobj.output_control() is False


@mock.patch('requests.Session.post')
def test_comnav_history_formats(mock_post):
    """ComNav history copes with missing or unexpected event text."""
    uobj = UltraSync()
    uobj.vendor = NX595EVendor.COMNAV
    uobj.session_id = 'ABCD'

    def _history(text):
        # Wrap event text the way the panel's history page does
        return _resp(
            '<textarea id="event" readonly>{}</textarea>'.format(text)
            .encode())

    # No event box on the page at all
    mock_post.side_effect = (_resp(b'<html></html>'),)
    assert uobj.history() is True
    assert uobj.history_data == {}

    # Too few lines to be an event
    mock_post.side_effect = (_history('Turn Off*\nAlarm'),)
    assert uobj.history() is True
    assert uobj.history_data == {}

    # An event whose date can not be read keeps its other details
    mock_post.side_effect = (
        _history('Turn Off*\nAlarm\nTest\nTime: 18:00\nDate: 99 Foo'),)
    assert uobj.history() is True
    assert uobj.history_data[1]['action'] == 'Turn Off'
    assert uobj.history_data[1]['user'] == 'Test'
    assert uobj.history_data[1]['timestamp'] is None

    # A date well ahead of today must be from last year
    class _June(datetime):
        """A datetime whose today is always the first of June 2026."""
        @classmethod
        def now(cls, tz=None):
            # Fixed so the test gives the same answer on any day it runs
            return cls(2026, 6, 1, 12, 0)

    mock_post.side_effect = (
        _history('Turn On*\nAlarm\nTest\nTime: 08:30\nDate: 15 Dec'),)
    with mock.patch('ultrasync.main.datetime', _June):
        assert uobj.history() is True

    assert uobj.history_data[1]['timestamp'] == '2025-12-15T08:30:00'


def _login(vendor_dir, area=None):
    """Return a logged in panel, optionally with its area page replaced."""
    # Each panel type is read from its own captured pages
    var_dir = join(dirname(__file__), 'var', *vendor_dir.split('/'))
    area_resp = _resp(path=join(var_dir, 'area.htm'))
    if area:
        area_resp.content = area(area_resp.content)

    replies = (area_resp, _resp(path=join(var_dir, 'zones.htm')))
    if vendor_dir.startswith(NX595EVendor.COMNAV):
        # ComNav also reads its outputs and history during login
        replies += (_resp(), _resp())

    with mock.patch('requests.Session.post', side_effect=replies):
        uobj = UltraSync()
        assert uobj.login() is True

    return uobj


def test_area_arm_state():
    """Each area reports whether it is armed away, armed stay or disarmed."""
    # Disarmed panels, whatever their status text says
    assert _login('zerowire/general').areas[0]['arm_state'] == 'disarm'
    assert _login('xgen/nxg64ip').areas[0]['status'] == 'Not Ready'
    assert _login('xgen/nxg64ip').areas[0]['arm_state'] == 'disarm'

    # Still armed away while an alarm or exit delay owns the status text
    uobj = _login('comnav/0.108-burglar-alarm-on')
    assert uobj.areas[0]['status'] == 'Burglar Alarm'
    assert uobj.areas[0]['arm_state'] == 'away'

    uobj = _login('zerowire/armed')
    assert uobj.areas[0]['status'] == 'Exit Delay 1'
    assert uobj.areas[0]['arm_state'] == 'away'

    # Turn on the stay (partial) bit of a real ZeroWire area page
    uobj = _login('zerowire/general', area=lambda page: page.replace(
        b'["010000000000', b'["010001000000'))
    assert uobj.areas[0]['status'] == 'Armed Stay'
    assert uobj.areas[0]['arm_state'] == 'stay'

    # Turn on the stay (partial) bit of a real ComNav area page
    uobj = _login('comnav/0.108', area=lambda page: page.replace(
        b'new Array(0,0,1,', b'new Array(0,1,1,'))
    assert uobj.areas[0]['status'] == 'Armed Stay'
    assert uobj.areas[0]['arm_state'] == 'stay'
