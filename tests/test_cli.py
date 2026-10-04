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

import json
from unittest import mock
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

    # The panel sends us back to its login page when we log off
    lgobj = mock.Mock()
    lgobj.content = b''
    lgobj.status_code = requests.codes.found

    # Assign our response object to our mocked instance of requests
    mock_post.side_effect = (arobj, zrobj, lgobj)

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

        # stdout holds nothing but the JSON details
        assert json.loads(result.stdout)['areas']

        # The session we were given is closed again when we're done
        assert mock_post.call_args_list[-1][0][0] == \
            'http://ultrasync.example.com/logout.cgi'
        assert mock_post.call_args_list[-1][1]['data'] == \
            {'sess': '5B0E636502CB6649'}

    # Reset our object
    mock_post.reset_mock()
    # Assign our response object to our mocked instance of requests
    mock_post.side_effect = (arobj, zrobj, lgobj)

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


@mock.patch('ultrasync.cli.UltraSync')
def test_cli_actions(mock_usync, tmpdir):
    """
    Test UltraSync CLI scene, bypass and output actions

    """
    # Create a config file
    config = tmpdir.join("config")
    config.write('host: ultrasync.example.com\npin: 1234\nuser: Admin\n')

    # Every panel call works by default
    usync = mock_usync.return_value
    usync.load.return_value = True
    usync.set_alarm.return_value = True
    usync.set_zone_bypass.return_value = True
    usync.set_output_control.return_value = True

    runner = CliRunner()
    base = ['--config', str(config)]

    # Arm one area
    result = runner.invoke(cli.main, base + ['--scene', 'away', '-a', '1'])
    assert result.exit_code == 0
    usync.set_alarm.assert_called_with(areas=1, state='away')

    # An unknown scene never reaches the panel
    result = runner.invoke(cli.main, base + ['--scene', 'party'])
    assert result.exit_code == 1

    # Bypass a zone
    result = runner.invoke(cli.main, base + ['--bypass', '1', '--zone', '3'])
    assert result.exit_code == 0
    usync.set_zone_bypass.assert_called_with(zone=3, state=True)

    # Switch an output on
    result = runner.invoke(
        cli.main, base + ['--output', '1', '--switch', '1'])
    assert result.exit_code == 0
    usync.set_output_control.assert_called_with(output=1, state=1)

    # Only 0 and 1 are valid switch states
    result = runner.invoke(
        cli.main, base + ['--output', '1', '--switch', '2'])
    assert result.exit_code == 1

    # The panel refuses each action
    usync.set_alarm.return_value = False
    usync.set_zone_bypass.return_value = False
    usync.set_output_control.return_value = False

    result = runner.invoke(cli.main, base + ['--scene', 'away'])
    assert result.exit_code == 1

    result = runner.invoke(cli.main, base + ['--bypass', '0', '--zone', '3'])
    assert result.exit_code == 1

    result = runner.invoke(
        cli.main, base + ['--output', '1', '--switch', '0'])
    assert result.exit_code == 1

    # No action at all prints the help
    result = runner.invoke(cli.main, base)
    assert result.exit_code == 1

    # A config file that can not be loaded
    usync.load.return_value = False
    result = runner.invoke(cli.main, base + ['--details'])
    assert result.exit_code == 1


@mock.patch('ultrasync.cli.UltraSync')
def test_cli_debug_dump(mock_usync, tmpdir):
    """
    Test UltraSync CLI debug dumps

    """
    config = tmpdir.join("config")
    config.write('host: ultrasync.example.com\n')
    usync = mock_usync.return_value
    usync.load.return_value = True

    runner = CliRunner()

    # A regular dump
    result = runner.invoke(
        cli.main, ['--config', str(config), '--debug-dump'])
    assert result.exit_code == 0
    assert usync.debug_dump.call_args[1]['full'] is False
    assert usync.debug_dump.call_args[1]['compress'] is True

    # A full dump
    result = runner.invoke(
        cli.main, ['--config', str(config), '--full-debug-dump'])
    assert result.exit_code == 0
    assert usync.debug_dump.call_args[1]['full'] is True


@mock.patch('ultrasync.cli.time.sleep')
@mock.patch('ultrasync.cli.UltraSync')
def test_cli_watch(mock_usync, mock_sleep, tmpdir):
    """
    Test UltraSync CLI watch mode

    """
    config = tmpdir.join("config")
    config.write('host: ultrasync.example.com\n')

    zone = {'bank': 0, 'sequence': 1, 'name': 'Front Door',
            'status': 'Ready'}
    area = {'bank': 0, 'sequence': 1, 'name': 'Area 1', 'status': 'Ready'}

    usync = mock_usync.return_value
    usync.load.return_value = True
    usync.zones = {0: zone}

    # Two polls with the same state, then the panel stops answering
    usync.details.side_effect = (
        {'areas': [area]}, {'areas': [area]}, {})

    runner = CliRunner()
    result = runner.invoke(cli.main, ['--config', str(config), '--watch'])
    assert result.exit_code == 0

    # Each change is printed once, followed by a divider
    assert result.output.count('Front Door') == 1
    assert result.output.count('Area 1') == 1
    assert result.output.count('---') == 1
    assert mock_sleep.call_count == 2


@mock.patch('requests.Session.post')
def test_cli_details_failure(mock_post, tmpdir):
    """
    Test UltraSync CLI Details when the panel can not be reached

    """
    config = tmpdir.join("config")
    config.write('host: ultrasync.example.com\n')

    # The panel refuses every request
    bad = mock.Mock()
    bad.content = b''
    bad.status_code = 500
    mock_post.return_value = bad

    runner = CliRunner()
    result = runner.invoke(cli.main, ['--config', str(config), '--details'])

    # An empty result is still valid JSON, but the run is a failure
    assert result.exit_code == 1
    assert json.loads(result.stdout) == {}
