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
from importlib import reload
import requests
from os.path import join
from os.path import dirname
from click.testing import CliRunner
from ultrasync import cli
from ultrasync.common import NX595EVendor

# Disable logging for a cleaner testing output
import logging
logging.disable(logging.CRITICAL)

# Reference Directory
ULTRASYNC_TEST_VAR_DIR = \
    join(dirname(__file__), 'var', NX595EVendor.ZEROWIRE, 'general')


def test_cli_help():
    """
    Test UltraSync CLI Help Options

    """

    # Initialize our Runner
    runner = CliRunner()

    # Returns CLI Help
    result = runner.invoke(cli.main)

    # no configuration specified; we return 1 (non-zero)
    assert result.exit_code == 1

    # Returns CLI Help
    result = runner.invoke(cli.main, [
        '-h'
    ])

    # Spit version and exit
    assert result.exit_code == 0


def test_cli_verbose_logging():
    """
    Test UltraSync CLI Verbose Logging Options

    """

    # Initialize our Runner
    runner = CliRunner()
    for no in range(0, 4):
        result = runner.invoke(cli.main, [
            '-{}'.format('v' * (no + 1)),
            '-V'
        ])

        # Spit version and exit
        assert result.exit_code == 0


def test_cli_version():
    """
    Test UltraSync CLI Version Output

    """

    # Initialize our Runner
    runner = CliRunner()

    # Returns UltraSync CLI Version Details
    result = runner.invoke(cli.main, [
        '-V'
    ])

    # Spit version and exit
    assert result.exit_code == 0

    # Returns UltraSync CLI Version Details
    result = runner.invoke(cli.main, [
        '--version'
    ])

    # Spit version and exit
    assert result.exit_code == 0


@mock.patch('requests.Session.post')
def test_cli_details(mock_post, tmpdir):
    """
    Test UltraSync CLI Details

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

    # Assign our response object to our mocked instance of requests
    mock_post.side_effect = (arobj, zrobj)

    # Initialize our Runner
    runner = CliRunner()

    with mock.patch('ultrasync.cli.DEFAULT_SEARCH_PATHS', []):
        # Returns UltraSync CLI Version Details
        result = runner.invoke(cli.main, [
            '--details'
        ])

        # no configuration specified; we return 1 (non-zero)
        assert result.exit_code == 1

    # Create a config file
    config = tmpdir.join("config")
    content = [
        'host: ultrasync.example.com',
        'pin: 1234',
        'user: Admin',
    ]
    config.write('\n'.join(content))

    with mock.patch('ultrasync.cli.DEFAULT_SEARCH_PATHS', []):
        # Returns UltraSync CLI Version Details
        result = runner.invoke(cli.main, [
            '--details',
            '--config', str(config),
        ])

        # now we have configuration
        assert result.exit_code == 0

    # Reset our object
    mock_post.reset_mock()
    # Assign our response object to our mocked instance of requests
    mock_post.side_effect = (arobj, zrobj)

    with mock.patch('ultrasync.cli.DEFAULT_SEARCH_PATHS', [str(config)]):
        result = runner.invoke(cli.main, [
            '--details',
        ])

        # We'll load our configuration from the default path
        assert result.exit_code == 0


@mock.patch('platform.system')
def test_apprise_cli_windows_env(mock_system):
    """
    CLI: Windows Environment

    """
    # Force a windows environment
    mock_system.return_value = 'Windows'

    # Reload our module
    reload(cli)
