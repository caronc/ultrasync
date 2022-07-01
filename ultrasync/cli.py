# -*- coding: utf-8 -*-

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

import time
import click
import logging
import platform
import json
import sys
from datetime import datetime
from os.path import isfile
from os.path import expanduser
from os.path import expandvars

from . import UltraSync
from . import ALARM_SCENES

from .logger import logger

from . import __title__
from . import __version__
from . import __license__
from . import __copywrite__

# Defines our click context settings adding -h to the additional options that
# can be specified to get the help menu to come up
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

# Define our default configuration we use if nothing is otherwise specified
DEFAULT_SEARCH_PATHS = (
    '~/.ultrasync',
    '~/.config/ultrasync',
)

# Detect Windows
if platform.system() == 'Windows':
    # Default Search Path for Windows Users
    DEFAULT_SEARCH_PATHS = (
        expandvars('%APPDATA%/UltraSync/config'),
        expandvars('%LOCALAPPDATA%/UltraSync/config'),
    )


def print_help_msg(command):
    """
    Prints help message when -h or --help is specified.

    """
    with click.Context(command) as ctx:
        click.echo(command.get_help(ctx))


def print_version_msg():
    """
    Prints version message when -V or --version is specified.

    """
    result = list()
    result.append('{} v{}'.format(__title__, __version__))
    result.append(__copywrite__)
    result.append(
        'This code is licensed under the {} License.'.format(__license__))
    click.echo('\n'.join(result))


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--config', '-c', default=None, type=str, metavar='FILE',
              help='Specify configuration file.')
@click.option('--watch', '-w', is_flag=True, help='Watch panel')
@click.option('--details', '-d', is_flag=True, help='Print status')
@click.option('--scene', '-s', type=str,
              metavar='STATE',
              help='Specify the alarm scene to change to. Possible values '
              'are "{}", and "{}".'.format(
                  '", "'.join(ALARM_SCENES[:-1]), ALARM_SCENES[-1]))
@click.option('--bypass', type=bool,
              metavar='BYPASS',
              help='Set to 1 to bypass a zone, set to 0 to unbypass.')
@click.option('--area', '-a', default=0, type=int, metavar='AREA',
              help='Specify the Area you wish to target with a --scene (-s) '
              'action. If no area is specified, then *all* areas are '
              'targeted.')
@click.option('--zone', type=int, metavar='ZONE',
              help='Specify the Zone you wish to target with a --bypass '
              'action.')
@click.option('--full-debug-dump', is_flag=True,
              help='Dump a full set of tracing files to a archive for '
              'comparison/debug purposes. Usually the --debug-dump is '
              'satisfactory enough.')
@click.option('--debug-dump', is_flag=True,
              help='Dump tracing files to a archive for comparison/debug '
              'purposes.')
@click.option('--verbose', '-v', count=True)
@click.option('--version', '-V', is_flag=True,
              help='Display the version of the ultrasync library and exit.')
def main(config, debug_dump, full_debug_dump, scene, bypass, details, watch,
         area, zone, verbose, version):
    """
    Wrapper to ultrasync library.
    """
    # Note: Click ignores the return values of functions it wraps, If you
    #       want to return a specific error code, you must call sys.exit()
    #       as you will see below.

    # Logging
    ch = logging.StreamHandler(sys.stdout)
    if verbose > 3:
        # -vvvv: Most Verbose Debug Logging
        logger.setLevel(logging.TRACE)

    elif verbose > 2:
        # -vvv: Debug Logging
        logger.setLevel(logging.DEBUG)

    elif verbose > 1:
        # -vv: INFO Messages
        logger.setLevel(logging.INFO)

    elif verbose > 0:
        # -v: WARNING Messages
        logger.setLevel(logging.WARNING)

    else:
        # No verbosity means we display ERRORS only AND any deprecation
        # warnings
        logger.setLevel(logging.ERROR)

    # Format our logger
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if version:
        print_version_msg()
        sys.exit(0)

    # Handle our scene
    if scene and scene not in ALARM_SCENES:
        logger.error(
            'An invalid alarm scene was specified: {}'.format(scene))
        sys.exit(1)

    # Get our configuration
    if not config:
        config = next((expanduser(f) for f in DEFAULT_SEARCH_PATHS
                      if isfile(expanduser(f))), None)
        if not config:
            # Still no config? Okay, we're done then
            logger.error('No ultrasync configuration found.')
            sys.exit(1)

    # Create our object to work with
    usync = UltraSync()
    if not usync.load(config):
        # Still no config? Okay, we're done then
        logger.error(
            'Could not load ultrasync configuration: {}'.format(config))
        sys.exit(1)

    # toggles to true if at least one item is actioned
    actioned = False

    if details:
        print(json.dumps(usync.details(), indent=2, sort_keys=True))
        actioned = True

    if debug_dump or full_debug_dump:
        with click.progressbar(length=100,
                               label='Creating debug archive') as bar:
            usync.debug_dump(compress=True, full=full_debug_dump, progress=bar)
            actioned = True

    if scene:
        if not usync.set_alarm(areas=area, state=scene):
            sys.exit(1)
        actioned = True

    if bypass is not None:
        if not usync.set_zone_bypass(zone=zone, state=bypass):
            sys.exit(1)
        actioned = True

    if watch:
        area_delta = {}
        zone_delta = {}
        while True:
            # Get our details
            results = usync.details()
            if not results:
                logger.error('Could not retrieve alarm status')
                break

            delim = False
            for bank, zone in usync.zones.items():
                if zone_delta.get(zone['bank']) != zone['sequence']:
                    # Locate the difference
                    print('{datetime} [{seq:0>3}] {name: <24}: '
                          '{status}'.format(
                              datetime=datetime.now().strftime(
                                  '%Y-%m-%d %H:%M:%S'),
                              seq=zone['sequence'],
                              name=zone['name'],
                              status=zone['status']))

                    # Update our sequence
                    zone_delta[zone['bank']] = zone['sequence']
                    delim = True

            for area in results.get('areas', []):
                if area_delta.get(area['bank']) != area['sequence']:
                    print('{datetime} [{seq:0>3}] {name: <24}: '
                          '{status}'.format(
                              datetime=datetime.now().strftime(
                                  '%Y-%m-%d %H:%M:%S'),
                              seq=area['sequence'],
                              name=area['name'],
                              status=area['status']))

                    # Update our sequence
                    area_delta[area['bank']] = area['sequence']
                    delim = True

            if delim:
                # Provides a little sanity in the output
                print('---')

            time.sleep(0.5)

        actioned = True

    if not actioned:
        # Print help
        logger.error('No action was specified.')
        print_help_msg(main)
        sys.exit(1)

    # else:  We're good!
    sys.exit(0)
