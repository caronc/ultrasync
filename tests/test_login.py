# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Chris Caron <lead2gold@gmail.com>
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
import pytest
from inspect import cleandoc

from ultrasync import UltraSync
from ultrasync.exceptions import (
    UltraSyncAuthentication, UltraSyncUnsupported)

# Disable logging for a cleaner testing output
import logging
logging.disable(logging.CRITICAL)


@mock.patch('requests.Session.post')
def test_login(mock_post):
    """
    Test Login and all forms of it's error handling

    """

    # A area response object
    arobj = mock.Mock()
    arobj.status_code = requests.codes.unauthorized
    arobj.content = b""

    # Our UltraSync Object
    uobj = UltraSync()

    # We're already logged out, so this will be successful
    assert uobj.logout() is True

    # We'll fail to login because there is no content
    mock_post.return_value = arobj
    assert uobj.login() is False
    assert mock_post.call_count == 1
    assert mock_post.call_args_list[0][0][0] == \
        'http://zerowire/login.cgi'

    # Reset our mock object
    mock_post.reset_mock()
    mock_post.return_value = arobj
    with pytest.raises(UltraSyncAuthentication):
        uobj.login(raise_on_error=True)
    assert mock_post.call_count == 1
    assert mock_post.call_args_list[0][0][0] == \
        'http://zerowire/login.cgi'

    # Even with positive status codes, we'll fail because there
    # is no content to extract authentication information from
    arobj.status_code = requests.codes.ok
    arobj.content = b"<!-- Useless content -->"

    # Reset our mock object
    mock_post.reset_mock()
    mock_post.return_value = arobj
    assert uobj.login() is False
    assert mock_post.call_count == 1
    assert mock_post.call_args_list[0][0][0] == \
        'http://zerowire/login.cgi'

    # Reset our mock object
    mock_post.reset_mock()
    mock_post.return_value = arobj
    with pytest.raises(UltraSyncAuthentication):
        uobj.login(raise_on_error=True)
    assert mock_post.call_count == 1
    assert mock_post.call_args_list[0][0][0] == \
        'http://zerowire/login.cgi'

    # empty session id
    # so that we satisfy a login
    arobj.content = cleandoc("""
    <!-- Satisfy Login -->
    function getSession(){return "A2D6C62695D705D8";}
    """).encode('utf-8')

    # We will however fail ot detect the model type at this point

    # Reset our mock object
    mock_post.reset_mock()
    mock_post.return_value = arobj
    assert uobj.login() is False
    assert mock_post.call_count == 1
    assert mock_post.call_args_list[0][0][0] == \
        'http://zerowire/login.cgi'

    # Reset our mock object
    mock_post.reset_mock()
    mock_post.return_value = arobj
    with pytest.raises(UltraSyncUnsupported):
        uobj.login(raise_on_error=True)

    assert mock_post.call_count == 1
    assert mock_post.call_args_list[0][0][0] == \
        'http://zerowire/login.cgi'

    # We want to write the bare minimum to our area/login.cgi
    # so that we satisfy a login
    arobj.content = cleandoc("""
    <!-- Satisfy Login -->
    function getSession(){return "A2D6C62695D705D8";}
    """).encode('utf-8')

    # We will however fail ot detect the model type at this point

    # Reset our mock object
    mock_post.reset_mock()
    mock_post.return_value = arobj
    assert uobj.login() is False
    assert mock_post.call_count == 1
    assert mock_post.call_args_list[0][0][0] == \
        'http://zerowire/login.cgi'

    # Reset our mock object
    mock_post.reset_mock()
    mock_post.return_value = arobj
    with pytest.raises(UltraSyncUnsupported):
        uobj.login(raise_on_error=True)

    assert mock_post.call_count == 1
    assert mock_post.call_args_list[0][0][0] == \
        'http://zerowire/login.cgi'

    # We want to write the bare minimum to our area/login.cgi
    # so that we satisfy a login and the model (XX) which is unsupported
    arobj.content = cleandoc("""
    <!-- Satisfy Login -->
    <script src="/v_XX_04.02-M/status.js" />
    function getSession(){return "A2D6C62695D705D8";}
    """).encode('utf-8')

    # Reset our mock object
    mock_post.reset_mock()
    mock_post.return_value = arobj
    assert uobj.login() is False
    assert mock_post.call_count == 1
    assert mock_post.call_args_list[0][0][0] == \
        'http://zerowire/login.cgi'

    # Reset our mock object
    mock_post.reset_mock()
    mock_post.return_value = arobj
    with pytest.raises(UltraSyncUnsupported):
        uobj.login(raise_on_error=True)
    assert mock_post.call_count == 1
    assert mock_post.call_args_list[0][0][0] == \
        'http://zerowire/login.cgi'

    # We want to write the bare minimum to our area/login.cgi
    # so that we satisfy a login and the model (ZW) which is zerowire
    arobj.content = cleandoc("""
    <!-- Satisfy Login -->
    <script src="/v_ZW_04.02-M/status.js" />
    function getSession(){{return "A2D6C62695D705D8";}}

    <!-- Satisfy Area Names for all Vendors -->
    var areaNames = ["Area","%21","%21","%21","%21","%21","%21","%21"];
    var areaNames = new Array("","!","!","!","!","!","!","!");

    <!-- Satisfy Area Sequence for all Vendors -->
    var areaSequence = [149,0,0,0,0,0,0,0,0,0,0,0];
    var areaSequence = new Array(104);

    <!-- Satisfy Area Status for all Vendors -->
    var areaStatus = ["{}"];
    var areaStatus = new Array(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);

    """.format('01' * 40)).encode('utf-8')

    # A zone response object
    zrobj = mock.Mock()
    zrobj.status_code = requests.codes.unauthorized
    zrobj.content = b""

    # Reset our mock object
    mock_post.reset_mock()
    mock_post.return_value = arobj
    assert uobj.login() is False
    assert mock_post.call_count == 2
    assert mock_post.call_args_list[0][0][0] == \
        'http://zerowire/login.cgi'
    assert mock_post.call_args_list[1][0][0] == \
        'http://zerowire/user/zones.htm'

    # Reset our mock object
    mock_post.reset_mock()
    with pytest.raises(UltraSyncAuthentication):
        uobj.login(raise_on_error=True)
    assert mock_post.call_count == 2
    assert mock_post.call_args_list[0][0][0] == \
        'http://zerowire/login.cgi'
    assert mock_post.call_args_list[1][0][0] == \
        'http://zerowire/user/zones.htm'

    # Make a valid Zone file now that supports all checks by all models
    zrobj.status_code = requests.codes.ok
    zrobj.content = cleandoc("""
    <!-- Satisfy Zone Name Checks -->
    var zoneNames = ["Front%20door","Garage%20Door"];
    var zoneNames = new Array("Front%20door","Garage%20Door");

    <!-- Satisfy Zone Sequence Checks -->
    var zoneSequence = [110,0,2,73,8,38,0,0,0,10,83,0,0,0,0,0,16,0];
    var zoneSequence = new Array(27,0,0,0,239,182,0,0);

    <!-- Satisfy Zone Status Checks -->
    var zoneStatus = ["{}"];
    var var zoneStatus = new Array(new Array(0,0),new Array(0,0));

    <!-- Extra ZeroWire Checks -->

    var ismaster = 0;
    var isinstaller = 1;
    """.format('01' * 18)).encode('utf-8')

    for code in ('ZW', 'CN', 'XG'):
        # We want to write the bare minimum to our area/login.cgi
        # so that we satisfy a login and the model (ZW)
        arobj.content = cleandoc("""
        <!-- Satisfy Login -->
        <script src="/v_{}_04.02-M/status.js" />
        function getSession(){{return "A2D6C62695D705D8";}}

        <!-- Satisfy Area Names for all Vendors -->
        var areaNames = ["Area","%21","%21","%21","%21","%21","%21","%21"];
        var areaNames = new Array("","!","!","!","!","!","!","!");

        <!-- Satisfy Area Sequence for all Vendors -->
        var areaSequence = [149,0,0,0,0,0,0,0,0,0,0,0];
        var areaSequence = new Array(104);

        <!-- Satisfy Area Status for all Vendors -->
        var areaStatus = ["{}"];
        var areaStatus = new Array(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);

        """.format(code, '01' * 40)).encode('utf-8')

        # A logout response object
        logout = mock.Mock()
        logout.status_code = requests.codes.ok
        logout.content = b"Logged Out"

        # Reset our mock object
        mock_post.reset_mock()
        mock_post.side_effect = (arobj, zrobj, logout)
        assert uobj.login() is True
        assert mock_post.call_count == 2
        assert mock_post.call_args_list[0][0][0] == \
            'http://zerowire/login.cgi'
        assert mock_post.call_args_list[1][0][0] == \
            'http://zerowire/user/zones.htm'

        # Log ourselves out
        mock_post.reset_mock()
        assert uobj.logout() is True
        assert mock_post.call_count == 1
        assert mock_post.call_args_list[0][0][0] == \
            'http://zerowire/logout.cgi'

        # Log ourselves back in

        # Mark a failure in our status for out logout
        logout.status_code = requests.codes.unauthorized

        # Reset our mock object
        mock_post.reset_mock()
        mock_post.side_effect = (arobj, zrobj, logout)
        assert uobj.login() is True
        assert mock_post.call_count == 2
        assert mock_post.call_args_list[0][0][0] == \
            'http://zerowire/login.cgi'
        assert mock_post.call_args_list[1][0][0] == \
            'http://zerowire/user/zones.htm'

        mock_post.reset_mock()
        assert uobj.logout() is False
        assert mock_post.call_count == 1
        assert mock_post.call_args_list[0][0][0] == \
            'http://zerowire/logout.cgi'
