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

import os
from datetime import datetime
from datetime import timedelta
from os.path import join
from os.path import dirname
from unittest import mock
from zipfile import ZipFile

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


def _zerowire_login():
    """Return the responses a ZeroWire panel sends during login."""
    return (
        _resp(path=join(ZEROWIRE_VAR_DIR, 'area.htm')),
        _resp(path=join(ZEROWIRE_VAR_DIR, 'zones.htm')),
    )


def _comnav_login():
    """Return the responses a ComNav panel sends during login."""
    return (
        _resp(path=join(COMNAV_VAR_DIR, 'area.htm')),
        _resp(path=join(COMNAV_VAR_DIR, 'zones.htm')),
        # outputs.htm
        _resp(),
        _resp(path=join(COMNAV_VAR_DIR, 'history.htm')),
    )


@mock.patch('requests.Session.post')
def test_login_failures(mock_post):
    """Login fails cleanly for each kind of unusable login page."""
    uobj = UltraSync()

    # The panel refuses the request outright
    mock_post.side_effect = (_resp(status_code=500),)
    assert uobj.login() is False

    # A page without a session id means the pin was wrong
    mock_post.side_effect = (_resp(b'<html>Bad Login</html>'),)
    assert uobj.login() is False

    # A session id alone is not enough; the panel type is also needed
    session = b'function getSession(){return "ABCD";}\n'
    mock_post.side_effect = (_resp(session),)
    assert uobj.login() is False

    # A panel type that is not supported
    mock_post.side_effect = (_resp(
        session + b'<script src="/v_XX_03.02-C/status.js">'),)
    assert uobj.login() is False
    assert uobj.session_id == 'ABCD'

    # A supported panel whose area details can not be read
    mock_post.side_effect = (_resp(
        session + b'<script src="/v_ZW_03.02-C/status.js">'),)
    assert uobj.login() is False
    assert uobj.vendor is NX595EVendor.ZEROWIRE


@mock.patch('requests.Session.post')
def test_xgen8_login(mock_post):
    """An xGen8 panel is detected from its script path."""
    # Borrow the ZeroWire pages, swapping in the xGen8 script path
    area = _resp(path=join(ZEROWIRE_VAR_DIR, 'area.htm'))
    area.content = area.content.replace(b'/v_ZW_03.02-C/', b'/javascript/')
    mock_post.side_effect = (
        area, _resp(path=join(ZEROWIRE_VAR_DIR, 'zones.htm')))

    uobj = UltraSync()
    assert uobj.login() is True
    assert uobj.vendor is NX595EVendor.XGEN8
    assert uobj.version == '8.000'
    assert uobj.release == '0'


@mock.patch('requests.Session.post')
def test_logout(mock_post):
    """Logging out clears the session even when the panel fails to reply."""
    uobj = UltraSync()

    # Nothing to do when we were never logged in
    assert uobj.logout() is True
    assert mock_post.call_count == 0

    # A normal log off
    mock_post.side_effect = _zerowire_login() + (_resp(b'bye'),)
    assert uobj.login() is True
    assert uobj.logout() is True
    assert uobj.session_id is None
    assert mock_post.call_args_list[-1][0][0] == \
        'http://zerowire/logout.cgi'

    # The panel errors on log off; the session is still forgotten
    mock_post.reset_mock()
    mock_post.side_effect = _zerowire_login() + (_resp(status_code=500),)
    assert uobj.login() is True
    assert uobj.logout() is False
    assert uobj.session_id is None


@mock.patch('requests.Session.post')
def test_connection_errors(mock_post):
    """Each kind of connection failure triggers one login retry."""
    for error in (
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ConnectionError):

        # Login works, the next request fails, and so does the re-login
        mock_post.side_effect = _zerowire_login() + (error(), error())
        uobj = UltraSync()
        assert uobj.login() is True
        assert uobj.details(max_age_sec=0) == {}


@mock.patch('requests.Session.post')
def test_session_expired(mock_post):
    """A redirect means the session expired, so log in and try again."""
    uobj = UltraSync()
    mock_post.side_effect = _zerowire_login()
    assert uobj.login() is True

    # The panel redirects, accepts a new login and then answers
    mock_post.side_effect = (_resp(status_code=requests.codes.found),) + \
        _zerowire_login() + \
        (_resp(path=join(ZEROWIRE_VAR_DIR, 'seq.json')),
         _resp(path=join(ZEROWIRE_VAR_DIR, 'zstate.json')),
         _resp(path=join(ZEROWIRE_VAR_DIR, 'status.json')))
    assert uobj.details(max_age_sec=0)

    # The retried request carries the new session id
    assert mock_post.call_args_list[-3][0][0] == \
        'http://zerowire/user/seq.json'
    assert mock_post.call_args_list[-3][1]['data']['sess'] == \
        uobj.session_id


@mock.patch('requests.Session.post')
def test_unreadable_replies(mock_post):
    """Replies that are not valid JSON or XML are treated as failures."""
    # A ZeroWire panel returns broken JSON for its sequence
    uobj = UltraSync()
    mock_post.side_effect = _zerowire_login() + (_resp(b'{not json'),)
    assert uobj.login() is True
    assert uobj.details(max_age_sec=0) == {}

    # A ComNav panel returns broken XML for its sequence
    uobj = UltraSync()
    mock_post.side_effect = _comnav_login() + (_resp(b'<response>'),)
    assert uobj.login() is True
    assert uobj.details(max_age_sec=0) == {}

    # A ComNav sequence reply without its zones and areas
    uobj = UltraSync()
    mock_post.side_effect = _comnav_login() + (_resp(b'<response/>'),)
    assert uobj.login() is True
    assert uobj.details(max_age_sec=0) == {}


@mock.patch('requests.Session.post')
def test_update_cache(mock_post):
    """Recent results are reused instead of asking the panel again."""
    uobj = UltraSync()

    # The first update logs in for us
    mock_post.side_effect = _zerowire_login()
    assert uobj.update() is True
    assert mock_post.call_count == 2

    # Still fresh, so the panel is not contacted
    assert uobj.update(max_age_sec=60) is True
    assert mock_post.call_count == 2

    # Stale results trigger a sequence check
    mock_post.side_effect = (
        _resp(path=join(ZEROWIRE_VAR_DIR, 'seq.json')),
        _resp(path=join(ZEROWIRE_VAR_DIR, 'zstate.json')),
        _resp(path=join(ZEROWIRE_VAR_DIR, 'status.json')))
    assert uobj.update(
        ref=datetime.now() + timedelta(seconds=120),
        max_age_sec=60) is True
    assert mock_post.call_count == 5

    # Nothing works when the panel can not be reached at all
    uobj = UltraSync()
    mock_post.side_effect = (
        _resp(status_code=500), _resp(status_code=500))
    assert uobj.update() is False
    assert uobj.details() == {}


def test_next_sequence():
    """Sequence numbers wrap back to 1 after 256."""
    assert UltraSync.next_sequence(1) == 2
    assert UltraSync.next_sequence(255) == 256
    assert UltraSync.next_sequence(256) == 1


@mock.patch('requests.Session.get')
@mock.patch('requests.Session.post')
def test_debug_dump_zip(mock_post, mock_get, tmpdir):
    """A compressed dump saves each captured page into one zip file."""
    # Every page request is answered with the same small page
    mock_post.return_value = _resp(b'<html>page</html>')
    mock_get.return_value = _resp(b'var x = 1;')

    uobj = UltraSync()
    mock_post.side_effect = _zerowire_login()
    assert uobj.login() is True
    mock_post.side_effect = None

    # Track how far the progress bar was moved
    progress = mock.Mock()
    path = str(tmpdir.join('panel'))
    uobj.debug_dump(path=path, compress=True, progress=progress)

    with ZipFile('{}.zip'.format(path)) as myzip:
        names = myzip.namelist()

    assert 'panel/area.htm' in names
    assert 'panel/seq.json' in names
    assert 'panel/master.js' in names
    assert progress.update.call_count == len(names) + 1


@mock.patch('requests.Session.get')
@mock.patch('requests.Session.post')
def test_debug_dump_full(mock_post, mock_get, tmpdir):
    """A full dump captures more pages than a regular one."""
    mock_post.return_value = _resp(b'<html>page</html>')
    mock_get.return_value = _resp(b'var x = 1;')

    uobj = UltraSync()
    mock_post.side_effect = _zerowire_login()
    assert uobj.login() is True
    mock_post.side_effect = None

    # Regular dump first, then a full one
    regular = str(tmpdir.join('regular'))
    uobj.debug_dump(path=regular, compress=True)
    full = str(tmpdir.join('full'))
    uobj.debug_dump(path=full, compress=True, full=True)

    with ZipFile('{}.zip'.format(regular)) as myzip:
        regular_count = len(myzip.namelist())

    with ZipFile('{}.zip'.format(full)) as myzip:
        full_count = len(myzip.namelist())

    assert full_count > regular_count


@mock.patch('requests.Session.get')
@mock.patch('requests.Session.post')
def test_debug_dump_directory(mock_post, mock_get, tmpdir):
    """An uncompressed ComNav dump writes each page into a folder."""
    uobj = UltraSync()
    mock_post.side_effect = _comnav_login()
    assert uobj.login() is True

    # The panel answers every page except area.htm
    mock_post.side_effect = None
    mock_post.return_value = _resp(b'<html>page</html>')
    mock_get.return_value = _resp(b'var x = 1;')
    pages = []

    def _post(url, **kwargs):
        # Remember which page was asked for
        pages.append(url)
        return _resp(status_code=500) if url.endswith('/user/area.htm') \
            else _resp(b'<html>page</html>')

    mock_post.side_effect = _post

    path = str(tmpdir.join('panel'))
    progress = mock.Mock()
    uobj.debug_dump(path=path, progress=progress)

    files = os.listdir(path)
    assert 'zones.htm' in files
    assert 'seq.xml' in files
    assert 'lang_engau.js' in files

    # The failed page is skipped, not written
    assert 'area.htm' not in files
    assert progress.update.call_count == len(files) + 1


@mock.patch('requests.Session.get')
@mock.patch('requests.Session.post')
def test_debug_dump_old_comnav(mock_post, mock_get, tmpdir):
    """Older ComNav panels have no language file to capture."""
    mock_get.return_value = _resp(b'var x = 1;')

    uobj = UltraSync()
    mock_post.side_effect = _comnav_login()
    assert uobj.login() is True
    uobj.version = '0.106'

    mock_post.side_effect = None
    mock_post.return_value = _resp(b'<html>page</html>')

    # A dump without a progress bar
    path = str(tmpdir.join('panel'))
    uobj.debug_dump(path=path)
    assert 'lang_engau.js' not in os.listdir(path)


@mock.patch('requests.Session.post')
def test_debug_dump_no_login(mock_post, tmpdir):
    """No dump is written when the panel can not be logged into."""
    mock_post.side_effect = (_resp(status_code=500),)
    path = str(tmpdir.join('panel'))
    assert UltraSync().debug_dump(path=path) is False
    assert not os.path.exists(path)
