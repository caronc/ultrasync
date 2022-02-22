#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
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

import requests
import json
import re
import os
import math
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError
from zipfile import ZipFile
from datetime import datetime
from datetime import timedelta
from .common import (
    AlarmScene, AreaStatus, CNAreaBank, XGZWAreaBank, ZoneStatus,
    ZoneBank, ALARM_SCENES, AREA_STATES, ZONE_STATES, CNPanelFunction,
    XGZWPanelFunction, NX595EVendor, AREA_STATUS_PROCESS_PRIORITY)
from .config import UltraSyncConfig
from urllib.parse import unquote
from .logger import logger


class HubResponseType(object):
    """
    A simple object for the handling of all query response types
    """
    # For the handling of just straight HTML files mostly
    # no changes are made to the response object
    RAW = 'raw'

    # JSON requests are used by the Interlogix ZeroWire Hub
    JSON = 'json'

    # XML requests are used by the ComNav Hub
    XML = 'xml'


class UltraSync(UltraSyncConfig):
    """
    A wrapper to the UltraSync Alarm Panel
    """

    # Tracks our Maximum Sequence Count
    max_sequence_count = 12

    # Tracks our Maximum Area Count
    max_area_count = 8

    panel_encoding = 'utf-8'

    # Requests timeout needs to be high as the panel is not always the most
    # responsive
    timeout = (8, 10)

    def __init__(self, *args, **kwargs):
        """
        prepares our UltraSync object
        """

        super(UltraSync, self).__init__(*args, **kwargs)

        # Create our session object
        self.session = requests.Session()

        # Our session id is retrieved after a successful login
        self.session_id = None

        # We need to track the vendor as it greatly impacts how we parse our
        # results
        self.vendor = "Unknown"
        self.version = "0.000"
        self.release = ""

        # User Status codes
        self.__is_master = None
        self.__is_installer = None

        # UltraSync devices include a System Fault (sysflt) keyword in it's
        # status return for older models.  If this value is set, we set it
        # here.
        self.__extra_area_status = []

        # Taken straight out of Interlogix ZeroWire status.js
        self.__xgzw_area_state_byte = [
            6, 4, 0, 16, 20, 18, 22, 8, 10, 12, 64, 66, 68, 70, 72, 14, 56]

        # Our zones get populated after we connect
        self.zones = {}
        self._zbank = None
        self._zsequence = None

        # Virtual bank for tracking individual sensor
        self._zvbank = {}

        # Our areas get populated after we connect
        self.areas = {}
        self._asequence = None

        # Track the time our information was polled from our panel
        self.__updated = None

        # Track the Panel URL path
        self.__panel_url_path = None

    def login(self):
        """
        Performs login to UltraSync (which then redirects to area.htm)

        """
        # Our initialiation
        self.session_id = None
        self.__updated = None

        payload = {
            'lgname': self.user,
            'lgpin': self.pin,
        }

        logger.info('Authenticating to {}'.format(self.host))
        response = self.__get(
            '/login.cgi', payload=payload,
            rtype=HubResponseType.RAW, auth_on_fail=False)
        if not response:
            logger.error('Failed to authenticate to {}'.format(self.host))
            return False

        #
        # Get our Session Identifier
        #
        # It looks like this in the login.cgi response:
        #  function getSession(){return "A2D6C62695D705D8";}
        match = re.search(
            r'function getSession\(\)[^"]+"(?P<session>[^"]+)".*',
            response, re.M)
        if not match:
            # No match and/or bad login
            logger.error('Failed to authenticate to {}'.format(self.host))
            return False

        # Store our session
        self.session_id = match.group('session')

        #
        # Get our Panel URL Path
        #
        # It is parsed from a reference like
        #   script src="/v_ZW_03.02-C/status.js"
        #                     ^
        #                     |

        # However, XGen8 use:
        #   - /javascript
        #   - /xGen __ Secure Network_file
        #
        match = re.search(
            r'script src="(?P<path>/(v_(?P<vendor>[^_]+)'
            r'_0?(?P<version>[0-9]\.[0-9.]*)(-(?P<release>[^/]+))?'
            r'|(?P<xgen8>(xGen __ Secure Network_files|javascript)))).*',
            response, re.M)
        if not match:
            # No match and/or bad login
            return False

        # Store our path
        self.__panel_url_path = match.group('path')

        if match.group('xgen8'):
            self.vendor = NX595EVendor.XGEN8
            self.version = '8.000'
            self.release = '0'

        # Determine our Vendor and Version information
        elif match.group('vendor') == 'ZW':
            self.vendor = NX595EVendor.ZEROWIRE
            self.version = match.group('version')
            self.release = match.group('release')

        elif match.group('vendor') == 'CN':
            self.vendor = NX595EVendor.COMNAV
            self.version = match.group('version')
            self.release = match.group('release')

        elif match.group('vendor') == 'XG':
            self.vendor = NX595EVendor.XGEN
            self.version = match.group('version')
            self.release = match.group('release')

        else:
            logger.error(
                'Unsupported vendor {}'.format(match.group('vendor')))
            return False

        logger.debug('Detected {} NX-595E, Web Interface v{}-{}'.format(
            self.vendor,
            self.version,
            self.release,
        ))

        if not self._areas(response=response) or not self._zones():
            # No match and/or bad login
            logger.error('Failed to authenticate to {}'.format(self.host))
            return False

        # Update our time reference
        self.__updated = datetime.now()

        # We're good
        return True if self.session_id else False

    def logout(self):
        """
        Performs login to UltraSync

        """
        if not self.session_id:
            # We're done
            return True

        logger.info('Graceful log off from {}'.format(self.host))
        # Reset our variables reguardless if we're successfully able to log
        # out or not
        self.session_id = None

        # Perform a logout
        response = self.__get('/logout.cgi', rtype=HubResponseType.RAW)
        if not response:
            logger.error('Failed to authenticate to {}'.format(self.host))
            return False

        return True

    def debug_dump(self, path=None, mode=0o755, full=False, compress=False,
                   progress=None):
        """
        Useful for checking for differences in alarm readings over time.

        if a progress object is passed in, the 'update()' function within the
        passed in object relative to a ratio of 100%
        """
        if path is None:
            path = datetime.now().strftime('%Y%m%d%H%M%S.ultrasync-dump')

        # Begin capturing data
        if not self.session_id and not self.login():
            return False

        logger.info('Performing a debug dump to: {}'.format(path))

        urls = {
            # Area URL
            'area.htm': {
                'path': '/user/area.htm',
            },

            # Zones URL
            'zones.htm': {
                'path': '/user/zones.htm',
            },

            # Config Main Screen
            'config2.htm': {
                'path': '/muser/config2.htm',
            },

            # Additional useful queries
            'master.js': {
                'path': '{}/master.js'.format(self.__panel_url_path),
                'method': 'GET'
            },
            'status.js': {
                'path': '{}/status.js'.format(self.__panel_url_path),
                'method': 'GET'
            },
        }

        if self.vendor in (NX595EVendor.ZEROWIRE, NX595EVendor.XGEN,
                           NX595EVendor.XGEN8):

            urls.update({
                # Used to acquire sequence
                'seq.json': {
                    'path': '/user/seq.json',
                },

                'zwave.js': {
                    'path': '{}/zwave.js'.format(self.__panel_url_path),
                    'method': 'GET'
                },

                # Room URL
                'rooms.htm': {
                    'path': '/user/rooms.htm',
                },

                'connect.xml': {
                    'path': '/protect/randmenu.xml',
                    'payload': {
                        'sess': self.session_id,
                        'item': 1,
                        'minc': 'protect/connect.xml'
                    },
                },
            })

            # status.json - All Area's
            urls.update({'status.{}.json'.format(no + 1): {
                'path': '/user/status.json',
                'payload': {
                    'sess': self.session_id,
                    'arsel': no,
                }} for no in range(0, 4)})

            # Scene Captures
            urls.update({'scenes.{}.xml'.format(no + 1): {
                'path': '/protect/randmenu.xml',
                'payload': {
                    'sess': self.session_id,
                    'item': no + 1,
                    'minc': 'protect/scenes.xml'
                }} for no in range(0, 16 if full else 1)})

            # Sensor Captures
            urls.update({'sensor.{}.xml'.format(no + 1): {
                'path': '/protect/randmenu.xml',
                'payload': {
                    'sess': self.session_id,
                    'item': no + 1,
                    'minc': 'protect/sensor.xml'
                }} for no in range(0, 16 if full else 1)})

            # Area Captures
            urls.update({'area.{}.xml'.format(no + 1): {
                'path': '/protect/randmenu.xml',
                'payload': {
                    'sess': self.session_id,
                    'item': no + 1,
                    'minc': 'protect/area.xml'
                }} for no in range(0, 4 if full else 1)})

            # zstate.json - All Zones
            urls.update({'zstate.{}.json'.format(no + 1): {
                'path': '/user/zstate.json',
                'payload': {
                    'sess': self.session_id,
                    'state': no,
                }} for no in range(0, 16 if full else 4)})

            # Grab our language file
            urls.update({
                'lang_engau.js': {
                    'path': '{}/eng_us.js'.format(
                        self.__panel_url_path),
                },
            })

        else:  # self.vendor is NX595EVendor.COMNAV

            urls.update({
                # Used to acquire sequence
                'seq.xml': {
                    'path': '/user/seq.xml',
                },
            })

            # status.xml - All Area's
            urls.update({'status.{}.xml'.format(no + 1): {
                'path': '/user/status.xml',
                'payload': {
                    'sess': self.session_id,
                    'arsel': no,
                }} for no in range(0, 4 if full else 1)})

            # zstate.xml - All Zones
            urls.update({'zstate.{}.xml'.format(no + 1): {
                'path': '/user/zstate.xml',
                'payload': {
                    'sess': self.session_id,
                    'state': no,
                }} for no in range(
                    0, UltraSync.max_sequence_count if full else 4)})

            if float(self.version) > 0.106:
                # Grab our language file
                urls.update({
                    'lang_engau.js': {
                        'path': '{}/lang_engau.js'.format(
                            self.__panel_url_path),
                    },
                })

        progress_ratio = 100.0 / len(urls)
        progress_track = 0.0

        if compress:
            with ZipFile('{}.zip'.format(path), 'w') as myzip:
                for to_file, kwargs in urls.items():
                    response = self.__get(rtype=HubResponseType.RAW, **kwargs)
                    if not response:
                        continue
                    logger.debug('Adding {} ({} bytes) to {}'.format(
                        to_file, len(response),
                        '{}.zip'.format(os.path.basename(path))))
                    myzip.writestr(
                        os.path.join(
                            os.path.basename(path), to_file), response)

                    if progress:
                        progress.update(progress_ratio)
                        progress_track += progress_ratio

        else:
            for to_file, kwargs in urls.items():
                response = self.__get(rtype=HubResponseType.RAW, **kwargs)
                if not response:
                    continue

                os.mkdir(path, mode=mode)
                with open(os.path.join(path, to_file), 'w',
                          encoding=self.panel_encoding) as fp:
                    # Write our content to disk
                    logger.debug(
                        'Writing {} bytes to {}'.format(
                            len(response), to_file))

                    fp.write(response)

                    if progress:
                        progress.update(progress_ratio)
                        progress_track += progress_ratio

        progress.update(100.001 - progress_track)
        return

    def set(self, area=1, state=AlarmScene.DISARMED):
        """
        This will be removed; it is only present for backwards compatibility

        """
        logger.deprecate(
            'set() is being depricated and replaced with set_alarm()')
        return self.set_alarm(areas=area, state=state)

    def set_alarm(self, areas=None, state=AlarmScene.DISARMED):
        """
        Sets Alarm

        """
        if not self.session_id and not self.login():
            return False

        if state not in ALARM_SCENES:
            logger.error(
                '{} is not valid alarm state'.format(state))
            return False

        if not areas:
            # Load all of our detected areas
            areas = [int(a) + 1 for a in self.areas.keys()]

        elif not isinstance(areas, (list, tuple, set)):
            # Ensure we're working with a set
            areas = [areas]

        # A boolean for tracking any errors
        has_error = False

        for area in areas:
            if not isinstance(area, int):
                try:
                    # Do our best to accomodate this situation
                    area = int(area)

                except (TypeError, ValueError):
                    logger.error(
                        'An invalid Area ({}) was specified.'.format(area))
                    has_error = True
                    continue

            if (area - 1) not in self.areas:
                logger.error(
                    'Area {} does not exist'.format(area))
                has_error = True
                continue

            # Start our payload off with our session identifier
            payload = {
                'sess': self.session_id,
            }

            if self.vendor in (NX595EVendor.ZEROWIRE, NX595EVendor.XGEN,
                               NX595EVendor.XGEN8):
                payload.update({
                    'start': int(math.floor((area - 1) / 8)),
                    'mask': 1 << (area - 1) % 8,
                })

                if state == AlarmScene.STAY:
                    payload.update({
                        'fnum': XGZWPanelFunction.AREA_STAY,
                    })

                elif state == AlarmScene.AWAY:
                    payload.update({
                        'fnum': XGZWPanelFunction.AREA_AWAY,
                    })

                else:   # AlarmScene.DISARMED
                    payload.update({
                        'fnum': XGZWPanelFunction.AREA_DISARM,
                    })

                rtype = HubResponseType.JSON

            else:  # self.vendor is NX595EVendor.COMNAV

                payload.update({
                    'comm': 80,
                    'data0': 2,
                    'data1': 1 << (area - 1) % 8,
                })

                if state == AlarmScene.STAY:
                    payload.update({
                        'data2': CNPanelFunction.AREA_STAY,
                    })

                elif state == AlarmScene.AWAY:
                    payload.update({
                        'data2': CNPanelFunction.AREA_AWAY,
                    })

                else:   # AlarmScene.DISARMED
                    payload.update({
                        'data2': CNPanelFunction.AREA_DISARM,
                    })

                rtype = HubResponseType.XML

            # Send our response
            response = self.__get(
                '/user/keyfunction.cgi', rtype=rtype, payload=payload)

            if not response:
                logger.info(
                    'Failed to send {} state to Area {}'.format(state, area))
                has_error = True

            logger.info(
                'Sent {} state to Area {} Successfully'.format(state, area))

        return not has_error

    def set_zone_bypass(self, zone, state=False):
        """
        Sets zone bypass

        """
        if not self.session_id and not self.login():
            return False

        if not isinstance(zone, int) or zone - 1 not in self.zones.keys():
            logger.error(
                '{} is not valid zone'.format(zone))
            return False

        # A boolean for tracking any errors
        has_error = False

        # Start our payload off with our session identifier
        payload = {
            'sess': self.session_id,
        }

        if self.vendor in (NX595EVendor.XGEN8):
            payload.update({
                'cmd': 5,
                'opt': int(state),
                'zone': zone - 1,
            })

        else:  # self.vendor is NX595EVendor.{COMNAV, ZEROWIRE, XGEN}

            logger.error(
                'Bypass not implemented for vendor {}'.format(self.vendor))
            return False

        # Send our response
        response = self.__get(
            '/user/zonefunction.cgi', payload=payload)

        if not response:
            logger.info(
                'Failed to set bypass={} for zone {}'.format(state, zone))
            has_error = True

        logger.info(
            'Set bypass={} for zone {} Successfully'.format(state, zone))

        return not has_error

    def update(self, ref=None, max_age_sec=1):
        """
        Updates classmeta information
        """

        if not self.session_id and not self.login():
            return False

        if ref is None:
            ref = datetime.now()

        if not max_age_sec or \
                (self.__updated + timedelta(seconds=max_age_sec)) <= ref:
            # Perform a sequence check; these trigger subsequent
            # checks if required
            if not self._sequence():
                return False

        else:
            # No update required
            return True

        # Update our time reference
        self.__updated = datetime.now()
        return True

    def details(self, max_age_sec=1):
        """
        Arranges the areas and zones into an easy to manage dictionary
        """
        if not self.update(max_age_sec=max_age_sec):
            return {}

        # Build our response object
        response = {
            'user': {
                'is_installer': self.__is_installer,
                'is_master': self.__is_master,
            },
            'zones': [z for z in self.zones.values()],
            'areas': [a for a in self.areas.values()],
            'date': self.__updated.strftime('%Y-%m-%d %H:%M:%S'),
        }

        return response

    def _areas(self, response=None):
        """
        Arranges the areas into an easier to read dictionary; since the
        login.cgi redirects users to this page by default, we allow users to
        pass a response object.

        the area.htm is rather a heavy set page, if we've already populated our
        area_names object then we can use a ligher query and just use the
        seq.json file to populate the same data.

        """
        logger.info('Retrieving initial Area information.')
        if not response:
            # No response object was specified; we need to query the area.htm
            # page.
            if not self.session_id and not self.login():
                return False

            # Perform our Query
            response = self.__get('/user/area.htm', rtype=HubResponseType.RAW)
            if not response:
                return False

        #
        # Get our Area Sequence
        #

        # Interlogix entries look like:
        #   It looks like this in the area.htm response
        #    var areaSequence = [149,0,0,0,0,0,0,0,0,0,0,0];

        # xGen entries look like:
        #    var areaSequence = [149];

        # ComNav looks like this:
        #  var areaSequence = new Array(104);
        match = re.search(
            r'var areaSequence\s*=\s*'
            r'((new\s+)?Array)?[\[(](?P<sequence>[^\])]+)[\])];.*',
            response, re.M)

        if not match:
            # No match and/or bad login
            return False
        self._asequence = json.loads(
            '[{}]'.format(match.group('sequence')))

        #
        # Get our Area Status (Bank States)
        #

        # Interlogix and XGen entries look like this:
        #  var areaStatus = ["0100000000...000000"];
        #
        # ComNav entries looks like this:
        #  var areaStatus = new Array(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);
        #
        # Every chunk of 17 bank states represents 1 area
        match = re.search(
            r'var areaStatus\s*=\s*'
            r'((new\s+)?Array)?[\[(](?P<states>[^\])]+)[\])];.*',
            response, re.M)
        if not match:
            # No match and/or bad login
            return False
        bank_states = json.loads('[{}]'.format(match.group('states')))

        #
        # Get our Area Names
        #

        # Interlogix and XGen entries look like this:
        #  var areaNames = ["","%21","%21","%21","%21","%21","%21","%21"];
        #
        # ComNav entries looks like this:
        # It looks like this in the area.htm response:
        #  new Array("","!","!","!","!","!","!","!");
        match = re.search(
            r'var areaNames\s*=\s*'
            r'((new\s+)?Array)?[\[(](?P<area_names>[^\])]+)[\])];.*',
            response, re.M)
        if not match:
            # No match and/or bad login
            return False
        area_names = json.loads('[{}]'.format(match.group('area_names')))

        # Ensure we've defined all of our possible sequences and areas
        self._asequence.extend(
            [0] * (UltraSync.max_sequence_count - len(self._asequence)))
        area_names.extend(['!'] * (UltraSync.max_area_count - len(area_names)))

        # Store our Areas ('%21' == '!'; these are un-used areas)
        self.areas = \
            {x: {'name': unquote(y).strip()
                 if unquote(y).strip() else 'Area {}'.format(x + 1),
                 'bank': x,
                 'bank_state': bank_states[math.floor(x / 8) * 17:
                                           (math.floor(x / 8) * 17) + 17]
                 if self.vendor is NX595EVendor.COMNAV
                 else bank_states[0]}

             for x, y in enumerate(area_names)
             if y != '%21' and y != '!'}

        return self.process_areas()

    def process_areas(self):
        """
        Processes our area information based on what was loaded in our
        configuration
        """
        # Xgen8 and Xgen share the same area processing
        vendor = self.vendor \
            if self.vendor != NX595EVendor.XGEN8 else NX595EVendor.XGEN
        return getattr(self, '{}_process_areas'.format(vendor))()

    def xgen_process_areas(self):
        """
        Process our area information based on current configuration

        Note: this gets called for both XGEN and XGEN8 models

        """
        # The following was reverse-engineered from status.js on the xGen
        # ZeroWire (UltraSync) NX-595E Device

        # from the function updateArea():
        for bank, area in self.areas.items():

            # define our mask
            mask = (1 << (bank % 8))

            # Prepare ourselves a virtual states for reference that can be
            # later indexed by name for readability. Basically in
            # status.js all references are by -> bank[idx:idx + 2];
            #
            # This just translate mappings to that:
            #   0:2 - index 0
            #   2:4 - index 1
            #   4:6 - index 2
            #   ...
            #   78:80 - index 39
            vbank = [int(area['bank_state'][s:s + 2], 16) & mask
                     for s in range(0, 80, 2)]

            # update our vbank to be more like the comnav one containing
            # only 17 entries:
            xg_vbank = [vbank[int(self.__xgzw_area_state_byte[s] / 2)]
                        for s in range(0, len(self.__xgzw_area_state_byte))]

            # Partially Armed State
            st_partial = bool(vbank[XGZWAreaBank.PARTIAL])

            # Armed State
            st_armed = bool(vbank[XGZWAreaBank.ARMED])

            # Exit Mode
            st_exit1 = bool(vbank[XGZWAreaBank.EXIT_MODE01])
            st_exit2 = bool(vbank[XGZWAreaBank.EXIT_MODE02])

            # Chime Set
            st_chime = bool(vbank[XGZWAreaBank.CHIME])

            # Priority, the lower, the higher it is; 6 being the lowest
            priority = 6

            # Now we'll attempt to detect our status
            status = None

            # Our initial index starting point
            idx = -1

            while not status:

                # Increment our working index
                idx += 1

                if idx >= len(AREA_STATES):
                    if self.__extra_area_status:
                        status = \
                            self.__extra_area_status[idx - len(AREA_STATES)]

                    else:
                        # Set status
                        status = AreaStatus.READY

                    continue

                # get our virtual index based on priority
                v_idx = AREA_STATUS_PROCESS_PRIORITY[idx]

                if xg_vbank[v_idx]:
                    if AREA_STATES[v_idx] != AreaStatus.READY \
                            or not (st_armed or st_partial):

                        status = AREA_STATES[v_idx]

                        if status in (AreaStatus.ARMED_STAY,
                                      AreaStatus.DELAY_EXIT_1,
                                      AreaStatus.DELAY_EXIT_2):

                            if vbank[XGZWAreaBank.NIGHT]:
                                status += ' - Night'

                            elif vbank[XGZWAreaBank.INSTANT]:
                                status += ' - Instant'

                    if AREA_STATES[v_idx] == AreaStatus.DELAY_EXIT_1:
                        # Bump to DELAY_EXIT_2; we'll eventually hit
                        # the bottom of our while loop and move past that too
                        idx += 1

                elif AREA_STATES[v_idx] == AreaStatus.READY \
                        and not (st_armed or st_partial):
                    # Update
                    status = AreaStatus.NOT_READY \
                        if not vbank[XGZWAreaBank.UNKWN_01] \
                        else AreaStatus.NOT_READY_FORCEABLE

            if vbank[XGZWAreaBank.UNKWN_08] or \
                    vbank[XGZWAreaBank.UNKWN_09] or \
                    vbank[XGZWAreaBank.UNKWN_10] or \
                    vbank[XGZWAreaBank.UNKWN_11]:

                # Assign priority to 1
                priority = 1

            elif vbank[XGZWAreaBank.UNKWN_33] or \
                    vbank[XGZWAreaBank.UNKWN_34] or \
                    vbank[XGZWAreaBank.UNKWN_35] or \
                    vbank[XGZWAreaBank.UNKWN_36] or \
                    self.__extra_area_status:

                # Assign priority to 2
                priority = 2

            elif st_partial or vbank[XGZWAreaBank.UNKWN_32]:
                # Assign priority to 3
                priority = 3

            elif st_armed:
                # Assign priority to 4
                priority = 4

            elif not vbank[XGZWAreaBank.UNKWN_00]:
                # Assign priority to 5
                priority = 5

            # Update our sequence
            sequence = UltraSync.next_sequence(
                area.get('sequence', 0)) \
                if area.get('status') != status \
                else area.get('sequence', 0)

            area.update({
                'priority': priority,
                'states': {
                    'armed': st_armed,
                    'partial': st_partial,
                    'chime': st_chime,
                    'exit1': st_exit1,
                    'exit2': st_exit2,
                },
                'status': status,
                'sequence': sequence,
            })

        return True

    def zerowire_process_areas(self):
        """
        Process our area information based on current configuration

        """
        # The following was reverse-engineered from status.js on the Interlogix
        # ZeroWire (UltraSync) NX-595E Device:

        # from the function updateArea():
        for bank, area in self.areas.items():

            # define our mask
            mask = (1 << (bank % 8))

            # Prepare ourselves a virtual states for reference that can be
            # later indexed by name for readability. Basically in
            # status.js all references are by -> bank[idx:idx + 2];
            #
            # This just translate mappings to that:
            #   0:2 - index 0
            #   2:4 - index 1
            #   4:6 - index 2
            #   ...
            #   78:80 - index 39
            vbank = [int(area['bank_state'][s:s + 2], 16) & mask
                     for s in range(0, 80, 2)]

            # update our vbank to be more like the comnav one containing
            # only 17 entries:
            zw_vbank = [vbank[int(self.__xgzw_area_state_byte[s] / 2)]
                        for s in range(0, len(self.__xgzw_area_state_byte))]

            # Partially Armed State
            st_partial = bool(vbank[XGZWAreaBank.PARTIAL])

            # Armed State
            st_armed = bool(vbank[XGZWAreaBank.ARMED])

            # Exit Mode
            st_exit1 = bool(vbank[XGZWAreaBank.EXIT_MODE01])
            st_exit2 = bool(vbank[XGZWAreaBank.EXIT_MODE02])

            # Chime Set
            st_chime = bool(vbank[XGZWAreaBank.CHIME])

            # Priority, the lower, the higher it is; 6 being the lowest
            priority = 6

            # Now we'll attempt to detect our status
            status = None

            # Our initial index starting point
            idx = -1

            while not status:

                # Increment our working index
                idx += 1

                if idx >= len(AREA_STATES):
                    if self.__extra_area_status:
                        status = \
                            self.__extra_area_status[idx - len(AREA_STATES)]

                    else:
                        # Set status
                        status = AreaStatus.READY

                    continue

                # get our virtual index based on priority
                v_idx = AREA_STATUS_PROCESS_PRIORITY[idx]

                if zw_vbank[v_idx]:
                    if AREA_STATES[v_idx] != AreaStatus.READY \
                            or not (st_armed or st_partial):

                        status = AREA_STATES[v_idx]

                        if status in (AreaStatus.ARMED_STAY,
                                      AreaStatus.DELAY_EXIT_1,
                                      AreaStatus.DELAY_EXIT_2):

                            if vbank[XGZWAreaBank.NIGHT]:
                                status += ' - Night'

                            elif vbank[XGZWAreaBank.INSTANT]:
                                status += ' - Instant'

                    if AREA_STATES[v_idx] == AreaStatus.DELAY_EXIT_1:
                        # Bump to DELAY_EXIT_2; we'll eventually hit
                        # the bottom of our while loop and move past that too
                        idx += 1

                elif AREA_STATES[v_idx] == AreaStatus.READY \
                        and not (st_armed or st_partial):
                    # Update
                    status = AreaStatus.NOT_READY \
                        if not vbank[XGZWAreaBank.UNKWN_01] \
                        else AreaStatus.NOT_READY_FORCEABLE

            if vbank[XGZWAreaBank.UNKWN_08] or \
                    vbank[XGZWAreaBank.UNKWN_09] or \
                    vbank[XGZWAreaBank.UNKWN_10] or \
                    vbank[XGZWAreaBank.UNKWN_11]:

                # Assign priority to 1
                priority = 1

            elif vbank[XGZWAreaBank.UNKWN_33] or \
                    vbank[XGZWAreaBank.UNKWN_34] or \
                    vbank[XGZWAreaBank.UNKWN_35] or \
                    vbank[XGZWAreaBank.UNKWN_36] \
                    or self.__extra_area_status:

                # Assign priority to 2
                priority = 2

            elif st_partial or vbank[XGZWAreaBank.UNKWN_32]:
                # Assign priority to 3
                priority = 3

            elif st_armed:
                # Assign priority to 4
                priority = 4

            elif not vbank[XGZWAreaBank.UNKWN_00]:
                # Assign priority to 5
                priority = 5

            # Update our sequence
            sequence = UltraSync.next_sequence(
                area.get('sequence', 0)) \
                if area.get('status') != status \
                else area.get('sequence', 0)

            area.update({
                'priority': priority,
                'states': {
                    'armed': st_armed,
                    'partial': st_partial,
                    'chime': st_chime,
                    'exit1': st_exit1,
                    'exit2': st_exit2,
                },
                'status': status,
                'sequence': sequence,
            })

        return True

    def comnav_process_areas(self):
        """
        Process our area information based on current configuration

        """
        # The following was reverse-engineered from status.js on the ComNav
        # (UltraSync) NX-595E Device:

        # from the function updateArea():
        for bank, area in self.areas.items():

            # define our mask
            mask = (1 << (bank % 8))

            # Prepare ourselves a virtual states for reference that can be
            # later indexed by name for readability.
            vbank = [int(a) & mask for a in area['bank_state']]

            # Partially Armed State
            st_partial = bool(vbank[CNAreaBank.PARTIAL])

            # Armed State
            st_armed = bool(vbank[CNAreaBank.ARMED])

            # Exit Mode
            st_exit1 = bool(vbank[CNAreaBank.EXIT_MODE01])
            st_exit2 = bool(vbank[CNAreaBank.EXIT_MODE02])

            # Chime Set
            st_chime = bool(vbank[CNAreaBank.CHIME])

            # Priority, the lower, the higher it is; 6 being the lowest
            priority = 6

            # Now we'll attempt to detect our status
            status = None

            # Our initial index starting point
            idx = -1

            while not status:

                # increment our index by one
                idx += 1

                if idx >= len(AREA_STATES):
                    if self.__extra_area_status:
                        status = \
                            self.__extra_area_status[idx - len(AREA_STATES)]

                        # Convert 'No System Faults' to Not Ready
                        if status == 'No System Faults':
                            status = AreaStatus.NOT_READY_FORCEABLE

                    else:
                        # Set status
                        status = AreaStatus.READY

                    continue

                # get our virtual index based on priority
                v_idx = AREA_STATUS_PROCESS_PRIORITY[idx]

                if vbank[v_idx]:
                    if AREA_STATES[v_idx] != AreaStatus.READY \
                            or not (st_armed or st_partial):

                        status = AREA_STATES[v_idx]

                    if AREA_STATES[v_idx] == AreaStatus.DELAY_EXIT_1:
                        # Bump to DELAY_EXIT_2; we'll eventually hit
                        # the bottom of our while loop and move past that
                        # too
                        idx += 1

                elif AREA_STATES[v_idx] == AreaStatus.READY \
                        and not (st_armed or st_partial):
                    # Update
                    status = AreaStatus.NOT_READY

            if vbank[CNAreaBank.UNKWN_03] or vbank[CNAreaBank.UNKWN_04] or \
                    vbank[CNAreaBank.UNKWN_05] or vbank[CNAreaBank.UNKWN_06]:

                # Assign priority to 1
                priority = 1

            elif vbank[CNAreaBank.UNKWN_11] or vbank[CNAreaBank.UNKWN_12] or \
                    vbank[CNAreaBank.UNKWN_13] or vbank[CNAreaBank.UNKWN_14] \
                    or self.__extra_area_status:

                # Assign priority to 2
                priority = 2

            elif vbank[CNAreaBank.UNKWN_10] or st_partial:
                # Assign priority to 3
                priority = 3

            elif st_armed:
                # Assign priority to 4
                priority = 4

            elif vbank[CNAreaBank.UNKWN_02]:
                # Assign priority to 5
                priority = 5

            # Update our sequence
            sequence = UltraSync.next_sequence(
                area.get('sequence', 0)) \
                if area.get('status') != status \
                else area.get('sequence', 0)

            area.update({
                'priority': priority,
                'states': {
                    'armed': st_armed,
                    'partial': st_partial,
                    'chime': st_chime,
                    'exit1': st_exit1,
                    'exit2': st_exit2,
                },
                'status': status,
                'sequence': sequence,
            })

        return True

    def process_zones(self):
        """
        Processes our zone/sensor information based on what was loaded in our
        configuration
        """
        return getattr(self, '{}_process_zones'.format(self.vendor))()

    def xgen_process_zones(self):
        """
        Updates our zone/sensor information based on new configuration
        """

        # The following was reverse-engineered from status.js
        # from the function updateZone():
        for bank, zone in self.zones.items():

            # some globals
            mask = 1 << bank % 8

            # Our initial offset
            idx = math.floor(bank / 8) * 2

            # Priority, the lower, the higher it is; 5 being the lowest
            priority = 5

            # prepare ourselves a virtual states for reference
            vbank = [int(self._zbank[s][idx:idx + 2], 16) & mask
                     for s in range(0, 18)]

            # Update our zone virtual bank
            self._zvbank[bank] = ''.join(
                [str(1 if b else 0) for b in vbank])

            # Track whether or not element is part of things
            can_bypass = not vbank[ZoneBank.BYPASS_DISABLED]

            if vbank[ZoneBank.UNKWN_05]:
                # red
                priority = 1

            elif vbank[ZoneBank.UNKWN_01] or vbank[ZoneBank.UNKWN_02] or \
                    vbank[ZoneBank.UNKWN_06] or vbank[ZoneBank.UNKWN_07] or \
                    vbank[ZoneBank.UNKWN_08] or vbank[ZoneBank.UNKWN_12]:
                # blue
                priority = 2

            elif vbank[ZoneBank.UNKWN_03] or vbank[ZoneBank.UNKWN_04]:
                # yellow
                priority = 3

            elif vbank[ZoneBank.UNKWN_00]:
                # grey
                priority = 4

            bank_no = 0

            status = None
            while not status:
                if vbank[bank_no]:
                    status = ZONE_STATES[bank_no]

                elif bank_no == 0:
                    status = ZoneStatus.READY

                # Increment our index
                bank_no += 1

            # Update our sequence
            sequence = UltraSync.next_sequence(
                zone.get('sequence', 0)) \
                if zone.get('bank_state') != self._zvbank[bank] \
                else zone.get('sequence', 0)

            zone.update({
                'priority': priority,
                'status': status,
                'can_bypass': can_bypass,
                'bank_state': self._zvbank[bank],
                'sequence': sequence,
            })
        return True

    def xgen8_process_zones(self):
        """
        Updates our zone/sensor information based on new configuration
        """

        # The following was reverse-engineered from status.js
        # from the function updateZone():
        for bank, zone in self.zones.items():

            # some globals
            mask = 1 << bank % 8

            # Our initial offset
            idx = math.floor(bank / 8) * 2

            # Priority, the lower, the higher it is; 5 being the lowest
            priority = 5

            # prepare ourselves a virtual states for reference
            vbank = [int(self._zbank[s][idx:idx + 2], 16) & mask
                     for s in range(0, 18)]

            # Update our zone virtual bank
            self._zvbank[bank] = ''.join(
                [str(1 if b else 0) for b in vbank])

            # Track whether or not element is part of things
            can_bypass = not vbank[ZoneBank.BYPASS_DISABLED]

            if vbank[ZoneBank.UNKWN_05]:
                # red
                priority = 1

            elif vbank[ZoneBank.UNKWN_01] or vbank[ZoneBank.UNKWN_02] or \
                    vbank[ZoneBank.UNKWN_06] or vbank[ZoneBank.UNKWN_07] or \
                    vbank[ZoneBank.UNKWN_08] or vbank[ZoneBank.UNKWN_12]:
                # blue
                priority = 2

            elif vbank[ZoneBank.UNKWN_03] or vbank[ZoneBank.UNKWN_04]:
                # yellow
                priority = 3

            elif vbank[ZoneBank.UNKWN_00]:
                # grey
                priority = 4

            bank_no = 0

            status = None
            while not status:
                if vbank[bank_no]:
                    status = ZONE_STATES[bank_no]

                elif bank_no == 0:
                    status = ZoneStatus.READY

                # Increment our index
                bank_no += 1

            # Update our sequence
            sequence = UltraSync.next_sequence(
                zone.get('sequence', 0)) \
                if zone.get('bank_state') != self._zvbank[bank] \
                else zone.get('sequence', 0)

            zone.update({
                'priority': priority,
                'status': status,
                'can_bypass': can_bypass,
                'bank_state': self._zvbank[bank],
                'sequence': sequence,
            })
        return True

    def zerowire_process_zones(self):
        """
        Updates our zone/sensor information based on new configuration

        """

        # The following was reverse-engineered from status.js
        # from the function updateZone():
        for bank, zone in self.zones.items():

            # some globals
            mask = 1 << bank % 8

            # Our initial offset
            idx = math.floor(bank / 8) * 2

            # Priority, the lower, the higher it is; 5 being the lowest
            priority = 5

            # prepare ourselves a virtual states for reference
            vbank = [int(self._zbank[s][idx:idx + 2], 16) & mask
                     for s in range(0, 18)]

            # Update our zone virtual bank
            self._zvbank[bank] = ''.join(
                [str(1 if b else 0) for b in vbank])

            # Track whether or not element is part of things
            can_bypass = not vbank[ZoneBank.BYPASS_DISABLED]

            if vbank[ZoneBank.UNKWN_05]:
                # red
                priority = 1

            elif vbank[ZoneBank.UNKWN_01] or vbank[ZoneBank.UNKWN_02] or \
                    vbank[ZoneBank.UNKWN_06] or vbank[ZoneBank.UNKWN_07] or \
                    vbank[ZoneBank.UNKWN_08] or vbank[ZoneBank.UNKWN_12]:
                # blue
                priority = 2

            elif vbank[ZoneBank.UNKWN_03] or vbank[ZoneBank.UNKWN_04]:
                # yellow
                priority = 3

            elif vbank[ZoneBank.UNKWN_00]:
                # grey
                priority = 4

            bank_no = 0

            status = None
            while not status:
                if vbank[bank_no]:
                    status = ZONE_STATES[bank_no]

                elif bank_no == 0:
                    status = ZoneStatus.READY

                # Increment our index
                bank_no += 1

            # Update our sequence
            sequence = UltraSync.next_sequence(
                zone.get('sequence', 0)) \
                if zone.get('bank_state') != self._zvbank[bank] \
                else zone.get('sequence', 0)

            zone.update({
                'priority': priority,
                'status': status,
                'can_bypass': can_bypass,
                'bank_state': self._zvbank[bank],
                'sequence': sequence,
            })
        return True

    def comnav_process_zones(self):
        """
        Updates our zone/sensor information based on new configuration

        """

        # The following was reverse-engineered from status.js
        # from the function updateZone():
        for bank, zone in self.zones.items():

            # some globals
            mask = 1 << bank % 16

            # Our initial offset
            idx = math.floor(bank / 16)

            # Priority, the lower, the higher it is; 5 being the lowest
            priority = 5

            # prepare ourselves a virtual states for reference
            vbank = [bool(int(self._zbank[s][idx]) & mask)
                     for s in range(0, len(self._zbank))]

            # Update our zone virtual bank
            self._zvbank[bank] = ''.join(
                [str(1 if b else 0) for b in vbank])

            if vbank[ZoneBank.UNKWN_05]:
                # red
                priority = 1

            elif vbank[ZoneBank.UNKWN_01] or vbank[ZoneBank.UNKWN_02] or \
                    vbank[ZoneBank.UNKWN_06] or vbank[ZoneBank.UNKWN_07]:

                # blue
                priority = 2

            elif vbank[ZoneBank.UNKWN_03] or vbank[ZoneBank.UNKWN_04]:
                # yellow
                priority = 3

            elif vbank[ZoneBank.UNKWN_00]:
                # grey
                priority = 4

            bank_no = 0

            status = None
            while not status:
                if vbank[bank_no]:
                    status = ZONE_STATES[bank_no]

                elif bank_no == 0:
                    status = ZoneStatus.READY

                # Increment our index
                bank_no += 1

            # Update our sequence
            sequence = UltraSync.next_sequence(
                zone.get('sequence', 0)) \
                if zone.get('bank_state') != self._zvbank[bank] \
                else zone.get('sequence', 0)

            zone.update({
                'priority': priority,
                'status': status,
                'can_bypass': None,
                'bank_state': self._zvbank[bank],
                'sequence': sequence,
            })

        return True

    def _zones(self):
        """
        Parses the Zone from our Ultrasync Panel
        """

        if not self.session_id and not self.login():
            return False

        logger.info('Retrieving initial Zone/Sensor information.')

        # Perform our Query
        response = self.__get('/user/zones.htm', rtype=HubResponseType.RAW)
        if not response:
            return False

        #
        # Get our Zone Sequence
        #

        # Interlogix and XGen look like this:
        #  var zoneSequence = [110,0,2,73,8,38,0,0,0,10,83,0,0,0,0,0,16,0];
        #
        # ComNav and XGen8 looks like this:
        #  var zoneSequence = new Array(27,0,0,0,239,182,0,0)
        match = re.search(
            r'var zoneSequence\s*=\s*'
            r'((new\s+)?Array)?[\[(](?P<sequence>[^\])]+)[\])];.*',
            response, re.M)
        if not match:
            # No match and/or bad login
            return False
        self._zsequence = json.loads(
            '[{}]'.format(match.group('sequence')))

        #
        # Get our Zone Sequence
        #
        if self.vendor in (NX595EVendor.ZEROWIRE, NX595EVendor.XGEN,
                           NX595EVendor.XGEN8):
            # XGen and Interlogix look like this:
            #  var zoneStatus = ["0100000000...000000"];

            # XGen8 looks like this
            #  var zoneStatus =["000000000000","000000000000", ... ];

            match = re.search(
                r'var zoneStatus\s*=\s*'
                r'((new\s+)?Array)?[\[(](?P<states>[^\])]+)[\])];.*',
                response, re.M)
            if not match:
                # No match and/or bad login
                return False
            self._zbank = json.loads('[{}]'.format(match.group('states')))

        else:  # self.vendor is NX595EVendor.COMNAV

            #  var zoneStatus = new Array(new Array(0,0),new Array(0,0),...
            match = re.search(
                r'var zoneStatus\s*=\s*'
                r'(new\s+)?Array\((?P<states>[^;]+?)\);.*', response, re.M)
            if not match:
                # No match and/or bad login
                return False

            # At this point we still have to further parse our many, many
            # 'new Array(x,y,z..)' entries...; We want to update our match
            match = re.findall(
                r'(?:new\s+)?Array\((?P<states>[^)]+)\)\s*'
                r'(?=$|,\s*(?:new\s+)?Array\()', match.group('states'))

            self._zbank = json.loads(
                '[{}]'.format(','.join(['[{}]'.format(x) for x in match])))

        #
        # Get our Zone Names
        #

        # Interlogix an XGen looks like:
        #  var zoneNames = ["Front%20door","Garage%20Door","..."];
        #
        # ComNav and XGen8 looks like this:
        #  var zoneNames = new Array("Front%20door","Garage%20Door","...");
        match = re.search(
            r'var zoneNames\s*=\s*'
            r'((new\s+)?Array)?[\[(](?P<zone_names>[^\])]+)[\])];.*',
            response, re.M)
        if not match:
            # No match and/or bad login
            return False

        zone_names = json.loads('[{}]'.format(match.group('zone_names')))

        # ComNav v0.106 does not support naming of zones. Determine if
        # we're this version
        zone_naming = False if self.vendor is NX595EVendor.COMNAV \
            and float(self.version) <= 0.106 else True

        # Store our Zones:
        # The following are unused sensors:
        # - '%21' == '!'
        # - '%2D' == '-'
        self.zones = \
            {x: {'name': unquote(y).strip()
                 if unquote(y).strip()
                 else 'Sensor {}'.format(x + 1), 'bank': x}
             for x, y in enumerate(zone_names)
             if not zone_naming or (y not in ('%21', '!', '%2D', '-', ''))}

        #
        # Get our Master Status
        #
        if self.vendor is NX595EVendor.ZEROWIRE:
            # It looks like this in the zone.htm response:
            #  var master = 1; # 1 if master, 0 if not
            match = re.search(
                r'var ismaster\s*=\s*(?P<flag>[01]+).*', response, re.M)
            if not match:
                # No match and/or bad login
                return False
            self.__is_master = True if int(match.group('flag')) else False

            #
            # Get our Installer Status
            #
            # It looks like this in the zone.htm response:
            #  var installer = 1; # 1 if installer, 0 if not
            match = re.search(
                r'var isinstaller\s*=\s*(?P<flag>[01]+).*', response, re.M)
            if not match:
                # No match and/or bad login
                return False
            self.__is_installer = True if int(match.group('flag')) else False

        return self.process_zones()

    def _area_status_update(self, bank=0):
        """
        Performs an area status check
        """
        return getattr(self, '_{}_area_status_update'
                             .format(self.vendor))(bank=bank)

    def _zerowire_area_status_update(self, bank=0):
        """
        Performs a area status check for the Interlogix ZeroWire Hub

        A status response could look like this:
        {
            "time":"5F834156",
            "abank":0,
            "aseq":109,
            "bankstates":"0100000000000000000000000000000000000100\
                          0000000000000000000000000000000000000000",
            "entry":[0,0,0,0],
            "exit":[0,0,0,0],
            "system":[],
            "zwtmp":[]
        }

        """

        logger.debug(
            'Updating Area information on bank {}'.format(bank))

        if not self.session_id and not self.login():
            return None

        payload = {
            'sess': self.session_id,

            # Select the Area Bank
            'arsel': bank,
        }

        # Perform our Query
        response = self.__get(
            '/user/status.json', rtype=HubResponseType.JSON, payload=payload)
        if not response:
            return None

        # Store our Fault Status (if set)
        self.__extra_area_status = \
            [unquote(e).strip() for e in response.get('system', [])]

        # Update our bank states
        self.areas[bank]['bank_state'] = response['bankstates']

        # Convert Hex time to Local Date Time
        response['time'] = datetime.fromtimestamp(
            int(response['time'], 16)).strftime('%Y-%m-%d %H:%M:%S')

        return response

    def _xgen_area_status_update(self, bank=0):
        """
        Performs a area status check for the Interlogix ZeroWire Hub

        A status response could look like this:
        {
            "time":"5F834156",
            "abank":0,
            "aseq":109,
            "bankstates":"0300000000000000000000000000000000000100\
                          0000000000000000000000000000000000000000",
            "entry":[0,0],
            "exit":[0,0],
            "system":[],
            "zwtmp":[]
        }

        """

        logger.debug(
            'Updating Area information on bank {}'.format(bank))

        if not self.session_id and not self.login():
            return None

        payload = {
            'sess': self.session_id,

            # Select the Area Bank
            'arsel': bank,
        }

        # Perform our Query
        response = self.__get(
            '/user/status.json', rtype=HubResponseType.JSON, payload=payload)
        if not response:
            return None

        # Store our Fault Status (if set)
        self.__extra_area_status = \
            [unquote(e).strip() for e in response.get('system', [])]

        # Update our bank states
        self.areas[bank]['bank_state'] = response['bankstates']

        # Convert Hex time to Local Date Time
        response['time'] = datetime.fromtimestamp(
            int(response['time'], 16)).strftime('%Y-%m-%d %H:%M:%S')

        return response

    def _xgen8_area_status_update(self, bank=0):
        """
        Performs a area status check for the Interlogix ZeroWire Hub

        A status response could look like this:
        {
            "time":"5F834156",
            "abank":0,
            "aseq":109,
            "bankstates":"0300000000000000000000000000000000000100\
                          0000000000000000000000000000000000000000",
            "entry":[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                     0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                     0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                     0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
            "exit":[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                    0,0,0,0,0,0,0,0,0,0,0,0],
            "system":[],
            "zwtmp":[]
        }
        """

        logger.debug(
            'Updating Area information on bank {}'.format(bank))

        if not self.session_id and not self.login():
            return None

        payload = {
            'sess': self.session_id,

            # Select the Area Bank
            'arsel': bank,
        }

        # Perform our Query
        response = self.__get(
            '/user/status.json', rtype=HubResponseType.JSON, payload=payload)
        if not response:
            return None

        # Store our Fault Status (if set)
        self.__extra_area_status = \
            [unquote(e).strip() for e in response.get('system', [])]

        # Update our bank states
        self.areas[bank]['bank_state'] = response['bankstates']

        # Convert Hex time to Local Date Time
        response['time'] = datetime.fromtimestamp(
            int(response['time'], 16)).strftime('%Y-%m-%d %H:%M:%S')

        return response

    def _comnav_area_status_update(self, bank=0):
        """
        Performs a area status check for the ComNav Hub

        A status response could look like this:
            <response>
              <abank>0</abank>
              <aseq>125</aseq>
              <stat0>0</stat0>
              <stat1>0</stat1>
              <stat2>0</stat2>
              <stat3>0</stat3>
              <stat4>0</stat4>
              <stat5>0</stat5>
              <stat6>0</stat6>
              <stat7>0</stat7>
              <stat8>0</stat8>
              <stat9>0</stat9>
              <stat10>0</stat10>
              <stat11>0</stat11>
              <stat12>0</stat12>
              <stat13>0</stat13>
              <stat14>0</stat14>
              <stat15>0</stat15>
              <stat16>0</stat16>
              <sysflt>No System Faults</sysflt>
            </response>

        """

        logger.debug(
            'Updating Area information on bank {}'.format(bank))

        if not self.session_id and not self.login():
            return None

        payload = {
            'sess': self.session_id,

            # Select the Area Bank
            'arsel': bank,
        }

        # Perform our Query
        response = self.__get(
            '/user/status.xml', rtype=HubResponseType.XML, payload=payload)
        if not response:
            return None

        try:
            # Store our Fault Status (if set)
            self.__extra_area_status = \
                re.split(r'\r*\n', response.find('sysflt').text)

        except AttributeError:
            # Not set (or not found); either way we don't need to
            # worry... set our flag to None and move along...
            self.__extra_area_status = []

        try:
            self.areas[bank]['bank_state'] = \
                [int(response.find('stat{}'.format(x)).text)
                 for x in range(0, 17)]

        except AttributeError:
            # <statX> stanza was not found
            return None

        return response

    def _zone_status_update(self, bank=0):
        """
        Performs a zone status check
        """
        return getattr(self, '_{}_zone_status_update'
                             .format(self.vendor))(bank=bank)

    def _zerowire_zone_status_update(self, bank=0):
        """
        Performs a zone status check for the Interlogix Zerowire Hub

        A status response could look like this:
        {
            "time":"5F8DE0C6",
            "zbank":0,
            "zseq":134,
            "bankstates":"000000000000000000000000",
            "system":[]
        }
        """

        logger.debug(
            'Updating Zone/Sensor information on bank {}'.format(bank))

        if not self.session_id and not self.login():
            return None

        payload = {
            'sess': self.session_id,

            # Select the Zone Bank
            'state': bank,
        }

        # Perform our Query
        response = self.__get(
            '/user/zstate.json', rtype=HubResponseType.JSON, payload=payload)
        if not response:
            return None

        # Update our bank states
        self._zbank[bank] = response['bankstates']

        # Convert Hex time to Local Date Time
        response['time'] = datetime.fromtimestamp(
            int(response['time'], 16)).strftime('%Y-%m-%d %H:%M:%S')

        return response

    def _xgen_zone_status_update(self, bank=0):
        """
        Performs a zone status check for the Xgen Zerowire Hub

        A status response could look like this:
        {
            "time":"5F8DE0C6",
            "zbank":0,
            "zseq":134,
            "bankstates":"000000000000000000000000",
            "system":[]
        }
        """

        logger.debug(
            'Updating Zone/Sensor information on bank {}'.format(bank))

        if not self.session_id and not self.login():
            return None

        payload = {
            'sess': self.session_id,

            # Select the Zone Bank
            'state': bank,
        }

        # Perform our Query
        response = self.__get(
            '/user/zstate.json', rtype=HubResponseType.JSON, payload=payload)
        if not response:
            return None

        # Update our bank states
        self._zbank[bank] = response['bankstates']

        # Convert Hex time to Local Date Time
        response['time'] = datetime.fromtimestamp(
            int(response['time'], 16)).strftime('%Y-%m-%d %H:%M:%S')

        return response

    def _xgen8_zone_status_update(self, bank=0):
        """
        Performs a zone status check for the Xgen8 Zerowire Hub

        A status response could look like this:
        {
            "time":"5F8DE0C6",
            "zbank":0,
            "zseq":134,
            "bankstates":"DE05",
            "system":[]
        }
        """

        logger.debug(
            'Updating Zone/Sensor information on bank {}'.format(bank))

        if not self.session_id and not self.login():
            return None

        payload = {
            'sess': self.session_id,

            # Select the Zone Bank
            'state': bank,
        }

        # Perform our Query
        response = self.__get(
            '/user/zstate.json', rtype=HubResponseType.JSON, payload=payload)
        if not response:
            return None

        # Update our bank states (by coverting it back to binary)
        self._zbank[bank] = response['bankstates']

        # Convert Hex time to Local Date Time
        response['time'] = datetime.fromtimestamp(
            int(response['time'], 16)).strftime('%Y-%m-%d %H:%M:%S')

        return response

    def _comnav_zone_status_update(self, bank=0):
        """
        Performs a zone status check for the ComNav Hub

        A status response could look like this:
            <response>
              <zstate>0</zstate>
              <zseq>153</zseq>
              <zdat>21,0,0,10,0,0,0,0,0,0,0,1,0,0</zdat>
            </response>
        """

        logger.debug(
            'Updating Zone/Sensor information on bank {}'.format(bank))

        if not self.session_id and not self.login():
            return None

        payload = {
            'sess': self.session_id,

            # Select the Zone Bank
            'state': bank,
        }

        # Perform our Query
        response = self.__get(
            '/user/zstate.xml', rtype=HubResponseType.XML, payload=payload)
        if not response:
            return None

        # Update our bank states
        try:
            for no, val in enumerate(response.find('zdat').text.split(',')):
                self._zbank[bank][no] = int(val)

        except AttributeError:
            # <zdat> stanza was not found
            return None

        return response

    def _sequence(self):
        """
        Returns the sequences for both the zones, entries, and areas
        """
        return getattr(self, '_{}_sequence'.format(self.vendor))()

    def _zerowire_sequence(self):
        """
        Returns the sequences for both the zones, entries, and areas

        A sequence response could look like this:
        {
            "time":"5F83415C",
            "area":[50,0,0,0,0,0,0,0,0,0,0,0],
            "zone":[82,1,3,242,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
            "chime":[3,0,0,0],
            "config":12345,
            "zwdevice":67890
        }

        A sequence is a way of polling the panel to see if there is anything
        new to report. If there are no changes, then the sequence values
        remain unchanged.

        If a sequence value is changed, the index of the 'area' is the bank
        that was updated.... so if index 0 was updated, then Area 1 changed.
        It is up to the user to call for an _area_status_update() with the
        respected index that needs updating.

        The same goes for if a 'zone' bank changes; a call to
        _zone_status_update() is required to be called referencing the
        respected bank that changed.

        """
        if not self.session_id and not self.login():
            return None

        # Perform our Query
        response = self.__get('/user/seq.json', rtype=HubResponseType.JSON)
        if not response:
            return None

        # Convert Hex time to Local Date Time
        response['time'] = datetime.fromtimestamp(
            int(response['time'], 16)).strftime('%Y-%m-%d %H:%M:%S')

        perform_area_update = False
        perform_zone_update = False

        # Process Zones/Sensors first
        for bank, sequence in enumerate(self._zsequence):
            if sequence != response['zone'][bank]:
                logger.debug('Zone Bank {}:{} changed'.format(bank, sequence))
                # We need to update our status here
                self._zsequence[bank] = response['zone'][bank]
                self._zone_status_update(bank=bank)
                perform_zone_update = True

        # Process Area now
        for bank, sequence in enumerate(self._asequence):
            if sequence != response['area'][bank]:
                logger.debug('Area Bank {}:{} changed'.format(bank, sequence))
                # We need to update our status here
                self._asequence[bank] = response['area'][bank]
                self._area_status_update(bank=bank)
                perform_area_update = True

        if perform_zone_update:
            # Update our zone sequence
            self._zsequence = response['zone']

            # Process all of our triggered zones/sensors
            self.process_zones()

        if perform_area_update:
            # Process all of our triggered areas
            self.process_areas()

        return response

    def _xgen_sequence(self):
        """
        Returns the sequences for both the zones, entries, and areas

        A sequence response could look like this:
        {
            "time":"5F83415C",
            "area":[50],
            "zone":[82,1,3,242,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
            "chime":[3,0,0,0],
            "config":12345,
            "zwdevice":67890
        }

        A sequence is a way of polling the panel to see if there is anything
        new to report. If there are no changes, then the sequence values
        remain unchanged.

        If a sequence value is changed, the index of the 'area' is the bank
        that was updated.... so if index 0 was updated, then Area 1 changed.
        It is up to the user to call for an _area_status_update() with the
        respected index that needs updating.

        The same goes for if a 'zone' bank changes; a call to
        _zone_status_update() is required to be called referencing the
        respected bank that changed.

        """
        if not self.session_id and not self.login():
            return None

        # Perform our Query
        response = self.__get('/user/seq.json', rtype=HubResponseType.JSON)
        if not response:
            return None

        # Convert Hex time to Local Date Time
        response['time'] = datetime.fromtimestamp(
            int(response['time'], 16)).strftime('%Y-%m-%d %H:%M:%S')

        perform_area_update = False
        perform_zone_update = False

        # Process Zones/Sensors first
        for bank, sequence in enumerate(self._zsequence):
            if sequence != response['zone'][bank]:
                logger.debug('Zone Bank {}:{} changed'.format(bank, sequence))
                # We need to update our status here
                self._zsequence[bank] = response['zone'][bank]
                self._zone_status_update(bank=bank)
                perform_zone_update = True

        # Process Area now
        for bank, sequence in enumerate(self._asequence):
            if bank >= len(response['area']):
                # We're done
                break

            if sequence != response['area'][bank]:
                logger.debug('Area Bank {}:{} changed'.format(bank, sequence))
                # We need to update our status here
                self._asequence[bank] = response['area'][bank]
                self._area_status_update(bank=bank)
                perform_area_update = True

        if perform_zone_update:
            # Update our zone sequence
            self._zsequence = response['zone']

            # Process all of our triggered zones/sensors
            self.process_zones()

        if perform_area_update:
            # Process all of our triggered areas
            self.process_areas()

        return response

    def _xgen8_sequence(self):
        """
        Returns the sequences for both the zones, entries, and areas

        A sequence response could look like this:
        {
            "time":"60D1B269",
            "area":[50],
            "zone":[160,0,0,83,196,79,0,0,140,0,43,62,234,0,0],
            "chime":[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                     0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                     0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                     0,0,0,0,0,0,0,0,0,0,0,0],
            "config":30757,
            "zwdevice":15396
        }

        A sequence is a way of polling the panel to see if there is anything
        new to report. If there are no changes, then the sequence values
        remain unchanged.

        If a sequence value is changed, the index of the 'area' is the bank
        that was updated.... so if index 0 was updated, then Area 1 changed.
        It is up to the user to call for an _area_status_update() with the
        respected index that needs updating.

        The same goes for if a 'zone' bank changes; a call to
        _zone_status_update() is required to be called referencing the
        respected bank that changed.

        """
        if not self.session_id and not self.login():
            return None

        # Perform our Query
        response = self.__get('/user/seq.json', rtype=HubResponseType.JSON)
        if not response:
            return None

        # Convert Hex time to Local Date Time
        response['time'] = datetime.fromtimestamp(
            int(response['time'], 16)).strftime('%Y-%m-%d %H:%M:%S')

        perform_area_update = False
        perform_zone_update = False

        # Process Zones/Sensors first
        for bank, sequence in enumerate(self._zsequence):
            if sequence != response['zone'][bank]:
                logger.debug('Zone Bank {}:{} changed'.format(bank, sequence))
                # We need to update our status here
                self._zsequence[bank] = response['zone'][bank]
                self._zone_status_update(bank=bank)
                perform_zone_update = True

        # Process Area now
        for bank, sequence in enumerate(self._asequence):
            if bank >= len(response['area']):
                # We're done
                break

            if sequence != response['area'][bank]:
                logger.debug('Area Bank {}:{} changed'.format(bank, sequence))
                # We need to update our status here
                self._asequence[bank] = response['area'][bank]
                self._area_status_update(bank=bank)
                perform_area_update = True

        if perform_zone_update:
            # Update our zone sequence
            self._zsequence = response['zone']

            # Process all of our triggered zones/sensors
            self.process_zones()

        if perform_area_update:
            # Process all of our triggered areas
            self.process_areas()

        return response

    def _comnav_sequence(self):
        """
        Returns the sequences for both the zones, entries, and areas

        A sequence response could look like this:
            <response>
              <areas>124</areas>
              <zones>21,0,0,10,0,0,0,0,0,0,0,1,0,0</zones>
            </response>

        Some older models, will only have a response like so:
            <response>
              <areas>124</areas>
              <zones>21,0</zones>
            </response>


        A sequence is a way of polling the panel to see if there is anything
        new to report. If there are no changes, then the sequence values
        remain unchanged.

        If a sequence value is changed, the index of the 'area' is the bank
        that was updated.... so if index 0 was updated, then Area 1 changed.
        It is up to the user to call for an _area_status_update() with the
        respected index that needs updating.

        The same goes for if a 'zone' bank changes; a call to
        _zone_status_update() is required to be called referencing the
        respected bank that changed.

        """
        if not self.session_id and not self.login():
            return None

        # Perform our Query
        response = self.__get('/user/seq.xml', rtype=HubResponseType.XML)
        if not response:
            return None

        perform_area_update = False
        perform_zone_update = False

        # Process Zones/Sensors first
        # Update our zone sequences
        try:
            z_seq = [int(x) for x in response.find('zones').text.split(',')]
            a_seq = [int(x) for x in response.find('areas').text.split(',')]

        except AttributeError:
            # <zones> and/or <areas> stanza was not found
            return None

        # Process Zones/Sensors first
        for bank, sequence in enumerate(z_seq):
            if sequence != self._zsequence[bank]:
                logger.debug('Zone Bank {}:{} changed'.format(bank, sequence))
                # We need to update our sequence here
                self._zsequence[bank] = z_seq[bank]
                self._zone_status_update(bank=bank)
                perform_zone_update = True

        # Process Area now
        for bank, sequence in enumerate(a_seq):
            if sequence != self._asequence[bank]:
                logger.debug('Area Bank {}:{} changed'.format(bank, sequence))
                # We need to update our status here
                self._asequence[bank] = a_seq[bank]
                self._area_status_update(bank=bank)
                perform_area_update = True

        if perform_zone_update:
            # Process all of our triggered zones/sensors
            self.process_zones()

        if perform_area_update:
            # Process all of our triggered areas
            self.process_areas()

        return response

    def __get(self, path, payload=None, rtype=HubResponseType.RAW,
              method='POST', auth_on_fail=True):
        """
        HTTP POST wrapper for interfacing with our panel
        """

        headers = {
            'Referer': 'http://{}/login.htm'.format(self.host),
            'User-Agent': self.user_agent
        }

        if payload is None:
            # Our default session
            payload = {
                'sess': self.session_id,
            }

        # Prepare our URL
        url = '{}{}'.format(self.url, path)

        logger.trace('{} {} Request to {}'.format(rtype.upper(), method, url))

        request = None

        try:
            if method == 'POST':
                # Make our POST request
                request = self.session.post(
                    url, data=payload, auth=self.auth, headers=headers,
                    verify=self.verify, timeout=self.timeout,
                    allow_redirects=False)

            else:
                # Make our request
                request = self.session.get(
                    url, data=payload, auth=self.auth, headers=headers,
                    verify=self.verify, timeout=self.timeout,
                    allow_redirects=False)

            logger.trace('URL: {}, status_code: {}'.format(
                url, request.status_code))
            logger.trace('URL: {}, response:\n{}'.format(
                url, request.content.decode(self.panel_encoding)))

        except requests.exceptions.ReadTimeout:
            logger.error('Connection read timeout')

        except requests.exceptions.ConnectTimeout:
            logger.error('Connection timeout')

        except requests.exceptions.ConnectionError:
            logger.error('Connection error')

        if auth_on_fail and (
                request is None or
                request.status_code == requests.codes.found):
            # A redirect implies that we were logged out
            # we also treat flat out failed connections as a logout
            # and attempt one more time...

            if not self.login():
                # We couldn't get back in; now we're definiely done
                return False

            # Recursively try our query again...

            if 'sess' in payload:
                # Update our session id
                payload['sess'] = self.session_id

            return self.__get(
                path, payload=payload, rtype=rtype, method=method,
                auth_on_fail=False)

        if not request or request.status_code != requests.codes.ok:
            logger.error('Failed to query {}'.format(url))
            return None

        # Our response object
        response = None

        if rtype is HubResponseType.JSON:
            try:
                response = json.loads(
                    request.content.decode(self.panel_encoding))

            except (AttributeError, TypeError, ValueError):
                # ValueError = request.content is Unparsable
                # TypeError = request.content is None
                # AttributeError = r is None
                logger.error(
                    'Failed to receive JSON response from {}'
                    .format(url))

        elif rtype is HubResponseType.XML:
            try:
                response = ET.fromstring(
                    request.content.decode(self.panel_encoding))

            except ParseError:
                logger.error(
                    'Failed to receive XML response from {}'
                    .format(url))

        else:
            response = request.content.decode(self.panel_encoding)

        # Return our results
        return response

    @staticmethod
    def next_sequence(last):
        """
        Returns a rotating sequence number (used for tracking changes that
        occur with zone/sensor data)
        """
        if last < 256:
            return last + 1

        # Zero is only used for disabled devices; start sequence at 1
        return 1
