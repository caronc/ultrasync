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

import pytest
from ultrasync.config import UltraSyncConfig

# Disable logging for a cleaner testing output
import logging
logging.disable(logging.CRITICAL)


def test_config_bool_parse():
    """
    Tests boolean parsing function
    """

    assert UltraSyncConfig.parse_bool(True) is True
    assert UltraSyncConfig.parse_bool(1) is True
    assert UltraSyncConfig.parse_bool('Yes') is True
    assert UltraSyncConfig.parse_bool('Y') is True
    assert UltraSyncConfig.parse_bool('True') is True
    assert UltraSyncConfig.parse_bool('T') is True
    assert UltraSyncConfig.parse_bool('Enable') is True
    assert UltraSyncConfig.parse_bool('E') is True
    assert UltraSyncConfig.parse_bool('+') is True

    assert UltraSyncConfig.parse_bool(False) is False
    assert UltraSyncConfig.parse_bool(0) is False
    assert UltraSyncConfig.parse_bool('No') is False
    assert UltraSyncConfig.parse_bool('N') is False
    assert UltraSyncConfig.parse_bool('False') is False
    assert UltraSyncConfig.parse_bool('F') is False
    assert UltraSyncConfig.parse_bool('Disable') is False
    assert UltraSyncConfig.parse_bool('Deny') is False
    assert UltraSyncConfig.parse_bool('D') is False
    assert UltraSyncConfig.parse_bool('-') is False

    # Test defaults from bad inputs
    assert UltraSyncConfig.parse_bool('%', True) is True
    assert UltraSyncConfig.parse_bool('!', False) is False


def test_config_file(tmpdir):
    """
    Test a configuration file

    """
    # We can't load invalid files
    with pytest.raises(AttributeError):
        UltraSyncConfig(path='invalid-file')

    # Create a config file
    t = tmpdir.join("config")
    content = [
        'host: ultrasync.example.com',
        'pin: 1234',
        'user: Admin',
    ]
    t.write('\n'.join(content))

    obj = UltraSyncConfig(path=str(t))
    assert obj.host == 'ultrasync.example.com'
    assert obj.pin == '1234'
    assert obj.user == 'Admin'
    assert obj.url == 'http://ultrasync.example.com'
    assert obj.auth is None
    assert obj.verify is True
    assert obj.user_agent.startswith('Mozilla')

    t = tmpdir.join("config1")
    content = [
        'host: https://user:pass@zerowire.local',
        'pin: 4321',
        'user: User',
        'verify: no',
        'user_agent: ultrasync',
        'ignored_entry: ignored',
    ]
    t.write('\n'.join(content))

    obj = UltraSyncConfig(path=str(t))
    assert obj.host == 'zerowire.local'
    assert obj.pin == '4321'
    assert obj.user == 'User'
    assert obj.url == 'https://zerowire.local'
    assert obj.auth == ('user', 'pass')
    assert obj.verify is False
    assert obj.user_agent == 'ultrasync'
