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
from ultrasync.common import AlarmScene
from ultrasync.common import CNPanelFunction
from ultrasync.common import NX595EVendor
from ultrasync.common import XGZWPanelFunction

# Disable logging for a cleaner testing output
import logging
logging.disable(logging.CRITICAL)

# Reference Directories
ZEROWIRE_VAR_DIR = \
    join(dirname(__file__), 'var', NX595EVendor.ZEROWIRE, 'general')
COMNAV_VAR_DIR = \
    join(dirname(__file__), 'var', NX595EVendor.COMNAV, '0.108')

# A ComNav outputs.htm page with two outputs, the second one switched on
COMNAV_OUTPUTS = (
    b'var oname1 = decodeURIComponent(decode_utf8("Garage%20Door"));\n'
    b'var ostate1 = "0";\n'
    b'var oname2 = decodeURIComponent(decode_utf8("Gate"));\n'
    b'var ostate2 = "1";\n'
)

# Replies the panel sends when an action is accepted
JSON_OK = b'{"result": 1}'
XML_OK = b'<response><result>1</result></response>'


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


def _zerowire(mock_post):
    """Return a ZeroWire panel that is logged in."""
    mock_post.side_effect = (
        _resp(path=join(ZEROWIRE_VAR_DIR, 'area.htm')),
        _resp(path=join(ZEROWIRE_VAR_DIR, 'zones.htm')),
    )
    uobj = UltraSync()
    assert uobj.login() is True
    mock_post.reset_mock()
    return uobj


def _comnav(mock_post):
    """Return a ComNav panel with two outputs that is logged in."""
    mock_post.side_effect = (
        _resp(path=join(COMNAV_VAR_DIR, 'area.htm')),
        _resp(path=join(COMNAV_VAR_DIR, 'zones.htm')),
        _resp(COMNAV_OUTPUTS),
        _resp(path=join(COMNAV_VAR_DIR, 'history.htm')),
    )
    uobj = UltraSync()
    assert uobj.login() is True
    mock_post.reset_mock()
    return uobj


def _sent(mock_post):
    """Return the form data of the last request sent to the panel."""
    return mock_post.call_args_list[-1][1]['data']


@mock.patch('requests.Session.post')
def test_zerowire_set_alarm(mock_post):
    """ZeroWire arming sends the matching panel function code."""
    uobj = _zerowire(mock_post)

    for state, fnum in (
            (AlarmScene.STAY, XGZWPanelFunction.AREA_STAY),
            (AlarmScene.AWAY, XGZWPanelFunction.AREA_AWAY),
            (AlarmScene.DISARMED, XGZWPanelFunction.AREA_DISARM)):

        mock_post.side_effect = (_resp(JSON_OK),)
        assert uobj.set_alarm(areas=1, state=state) is True
        assert mock_post.call_args_list[-1][0][0] == \
            'http://zerowire/user/keyfunction.cgi'
        assert _sent(mock_post) == {
            'sess': uobj.session_id, 'start': 0, 'mask': 1, 'fnum': fnum}

    # No areas given means every area found on the panel
    mock_post.side_effect = (_resp(JSON_OK),)
    assert uobj.set_alarm(state=AlarmScene.AWAY) is True
    assert mock_post.call_count == 4


@mock.patch('requests.Session.post')
def test_comnav_set_alarm(mock_post):
    """ComNav arming sends the matching panel function code."""
    uobj = _comnav(mock_post)

    for state, data2 in (
            (AlarmScene.STAY, CNPanelFunction.AREA_STAY),
            (AlarmScene.AWAY, CNPanelFunction.AREA_AWAY),
            (AlarmScene.FIRE, CNPanelFunction.AREA_FIRE),
            (AlarmScene.MEDICAL, CNPanelFunction.AREA_MEDICAL),
            (AlarmScene.PANIC, CNPanelFunction.AREA_PANIC),
            (AlarmScene.DISARMED, CNPanelFunction.AREA_DISARM)):

        mock_post.side_effect = (_resp(XML_OK),)
        assert uobj.set_alarm(areas=[1], state=state) is True
        assert _sent(mock_post) == {
            'sess': uobj.session_id, 'comm': 80, 'data0': 2,
            'data1': 1, 'data2': data2}


@mock.patch('requests.Session.post')
def test_set_alarm_bad_input(mock_post):
    """Unknown scenes and areas are refused without contacting the panel."""
    uobj = _zerowire(mock_post)

    # Not a real scene
    assert uobj.set_alarm(areas=1, state='party') is False

    # Not a number, and an area that does not exist
    assert uobj.set_alarm(areas=['abc'], state=AlarmScene.AWAY) is False
    assert uobj.set_alarm(areas=5, state=AlarmScene.AWAY) is False
    assert mock_post.call_count == 0

    # An area number given as text is still understood
    mock_post.side_effect = (_resp(JSON_OK),)
    assert uobj.set_alarm(areas='1', state=AlarmScene.AWAY) is True

    # The panel rejects the request
    mock_post.side_effect = (_resp(status_code=500),)
    assert uobj.set_alarm(areas=1, state=AlarmScene.AWAY) is False


@mock.patch('requests.Session.post')
def test_set_alarm_no_login(mock_post):
    """Actions fail when the panel can not be logged into."""
    mock_post.return_value = _resp(status_code=500)
    uobj = UltraSync()
    assert uobj.set_alarm(state=AlarmScene.AWAY) is False
    assert uobj.set_zone_bypass(zone=1, state=True) is False
    assert uobj.set_output_control(output=1, state=1) is False


@mock.patch('requests.Session.post')
def test_set_deprecated(mock_post):
    """The old set() call still arms the panel."""
    uobj = _zerowire(mock_post)
    mock_post.side_effect = (_resp(JSON_OK),)
    assert uobj.set(area=1, state=AlarmScene.STAY) is True
    assert _sent(mock_post)['fnum'] == XGZWPanelFunction.AREA_STAY


@mock.patch('requests.Session.post')
def test_zerowire_zone_bypass(mock_post):
    """ZeroWire bypass sends the zone and the wanted state."""
    uobj = _zerowire(mock_post)

    mock_post.side_effect = (_resp(JSON_OK),)
    assert uobj.set_zone_bypass(zone=2, state=True) is True
    assert mock_post.call_args_list[-1][0][0] == \
        'http://zerowire/user/zonefunction.cgi'
    assert _sent(mock_post) == {
        'sess': uobj.session_id, 'cmd': 5, 'opt': 1, 'zone': 1}

    # Zones that do not exist, or are not numbers, are refused
    assert uobj.set_zone_bypass(zone=99, state=True) is False
    assert uobj.set_zone_bypass(zone='2', state=True) is False

    # The panel rejects the request
    mock_post.side_effect = (_resp(status_code=500),)
    assert uobj.set_zone_bypass(zone=2, state=False) is False


@mock.patch('requests.Session.post')
def test_comnav_zone_bypass(mock_post):
    """ComNav bypass toggles the zone through its own command."""
    uobj = _comnav(mock_post)

    # Zone 1 can be bypassed, so a bypass request toggles it
    mock_post.side_effect = (_resp(b'ok'),)
    assert uobj.set_zone_bypass(zone=1, state=True) is True
    assert _sent(mock_post) == {
        'sess': uobj.session_id, 'comm': 82, 'data0': 0}

    # Asking for the opposite state sends no toggle command
    mock_post.side_effect = (_resp(b'ok'),)
    assert uobj.set_zone_bypass(zone=1, state=False) is True
    assert _sent(mock_post) == {}


@mock.patch('requests.Session.post')
def test_xgen_zone_bypass(mock_post):
    """Plain xGen panels do not support bypass."""
    uobj = _zerowire(mock_post)
    uobj.vendor = NX595EVendor.XGEN
    assert uobj.set_zone_bypass(zone=1, state=True) is False
    assert mock_post.call_count == 0


@mock.patch('requests.Session.post')
def test_comnav_outputs(mock_post):
    """ComNav outputs are read at login and can be switched."""
    uobj = _comnav(mock_post)

    assert uobj.outputs == {
        1: {'name': 'Garage Door', 'state': '0'},
        2: {'name': 'Gate', 'state': '1'},
    }

    mock_post.side_effect = (_resp(b'ok'),)
    assert uobj.set_output_control(output=1, state=1) is True
    assert mock_post.call_args_list[-1][0][0] == \
        'http://zerowire/user/output.cgi'
    assert _sent(mock_post) == {
        'sess': uobj.session_id, 'onum': 1, 'ostate': 1}

    # Outputs that do not exist are refused
    assert uobj.set_output_control(output=3, state=1) is False
    assert uobj.set_output_control(output='1', state=1) is False

    # The panel rejects the request
    mock_post.side_effect = (_resp(status_code=500),)
    assert uobj.set_output_control(output=2, state=0) is False


@mock.patch('requests.Session.post')
def test_zerowire_outputs(mock_post):
    """Output control is only offered on ComNav panels."""
    uobj = _zerowire(mock_post)
    assert uobj.outputs == {}
    assert uobj.set_output_control(output=1, state=1) is False
    assert mock_post.call_count == 0
