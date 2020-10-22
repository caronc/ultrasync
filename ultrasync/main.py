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
from datetime import datetime
from datetime import timedelta
from .common import (
    AlarmScene, AreaStatus, AreaBank, ZoneStatus, ZoneBank, ALARM_SCENES,
    AREA_STATES, ZONE_STATES, PanelFunction)
from .config import UltraSyncConfig
from urllib.parse import unquote
from .logger import logger


class UltraSync(UltraSyncConfig):
    """
    A wrapper to the UltraSync Alarm Panel
    """

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

        # User Status codes
        self.__is_master = None
        self.__is_installer = None

        # Taken straight out of status.js
        self.__area_state_byte = [
            6, 4, 0, 16, 20, 18, 22, 8, 10, 12, 64, 66, 68, 70, 72, 14, 56]

        # Our zones get populated after we connect
        self.zones = {}
        self.__zbank = None
        self.__zsequence = None

        # Virtual bank for tracking individual sensor
        self.__zvbank = {}

        # Our areas get populated after we connect
        self.areas = {}

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
            '/login.cgi', payload=payload, is_json=False, auth_on_fail=False)
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
        match = re.search(
            r'script src="(?P<path>/?[^/]+).*', response, re.M)
        if not match:
            # No match and/or bad login
            return False

        # Store our path
        self.__panel_url_path = match.group('path')

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
        response = self.__get('/logout.cgi', is_json=False)
        if not response:
            logger.error('Failed to authenticate to {}'.format(self.host))
            return False

        return True

    def debug_dump(self, path=None, mode=0o755):
        """
        Useful for checking for differences in alarm readings over time.

        """
        if path is None:
            path = datetime.now().strftime('%Y%m%d%H%M%S.ultrasync-dump')

        # Begin capturing data
        if not self.session_id and not self.login():
            return False

        logger.info('Performing a debug dump to: {}'.format(path))
        os.mkdir(path, mode=mode)

        urls = {
            # status.json - Bank 0
            'status.0.json': {
                'path': '/user/status.json',
                'payload': {
                    'sess': self.session_id,
                    'arsel': 0,
                },
            },
            # status.json - Bank 1
            'status.1.json': {
                'path': '/user/status.json',
                'payload': {
                    'sess': self.session_id,
                    'arsel': 1,
                },
            },
            # Area URL
            'area.htm': {
                'path': '/user/area.htm',
            },

            # Zones URL
            'zones.htm': {
                'path': '/user/zones.htm',
            },

            # Room URL
            'rooms.htm': {
                'path': '/user/rooms.htm',
            },

            # Zones URL
            'addrem.json': {
                'path': '/user/zones.htm',
            },

            # Used to acquire sequence
            'seq.json': {
                'path': '/user/seq.json',
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
            'zwave.js': {
                'path': '{}/zwave.js'.format(self.__panel_url_path),
                'method': 'GET'
            },
            'status.js': {
                'path': '{}/status.js'.format(self.__panel_url_path),
                'method': 'GET'
            },
            'connect.xml': {
                'path': '/protect/randmenu.xml',
                'payload': {
                    'sess': self.session_id,
                    'item': 1,
                    'minc': 'protect/connect.xml'
                },
            },
        }

        # Scene Captures
        urls.update({'scenes.{}.xml'.format(no + 1): {
            'path': '/protect/randmenu.xml',
            'payload': {
                'sess': self.session_id,
                'item': no + 1,
                'minc': 'protect/scenes.xml'
            }} for no in range(0, 16)})

        # Sensor Captures
        urls.update({'sensor.{}.xml'.format(no + 1): {
            'path': '/protect/randmenu.xml',
            'payload': {
                'sess': self.session_id,
                'item': no + 1,
                'minc': 'protect/sensor.xml'
            }} for no in range(0, 16)})

        # Area Captures
        urls.update({'area.{}.xml'.format(no + 1): {
            'path': '/protect/randmenu.xml',
            'payload': {
                'sess': self.session_id,
                'item': no + 1,
                'minc': 'protect/area.xml'
            }} for no in range(0, 4)})

        for to_file, kwargs in urls.items():
            response = self.__get(is_json=False, **kwargs)
            if not response:
                continue

            with open(os.path.join(path, to_file), 'w',
                      encoding=self.panel_encoding) as fp:
                # Write our content to disk
                _bytes = fp.write(response)
                logger.info('Wrote {} bytes to {}'.format(_bytes, to_file))

    def set(self, area=1, state=AlarmScene.DISARMED):
        """
        Sets Alarm Scene

        """
        if not self.session_id and not self.login():
            return False

        if state not in ALARM_SCENES:
            return False

        mask = 1 << (area - 1) % 8
        start = math.floor((area - 1) / 8)

        payload = {
            'sess': self.session_id,
            'start': int(start),
            'mask': mask,
        }

        if state == AlarmScene.STAY:
            payload.update({
                'fnum': PanelFunction.AREA_STAY,
            })

        elif state == AlarmScene.AWAY:
            payload.update({
                'fnum': PanelFunction.AREA_AWAY,
            })

        else:   # AlarmScene.DISARMED
            payload.update({
                'fnum': PanelFunction.AREA_DISARM,
            })

        response = self.__get('/user/keyfunction.cgi', payload=payload)
        if not response:
            return False

        return response

    def update(self, ref=None, max_age_sec=1):
        """
        Updates classmeta information
        """

        if not self.session_id and not self.login():
            return False

        if ref is None:
            ref = datetime.now()

        if (self.__updated + timedelta(seconds=max_age_sec)) <= ref:
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

    def details(self):
        """
        Arranges the areas and zones into an easy to manage dictionary
        """
        if not self.update():
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
            response = self.__get('/user/area.htm', is_json=False)
            if not response:
                return False

        #
        # Get our Area Sequence
        #
        # It looks like this in the login.cgi response:
        #  var areaSequence = [149,0,0,0,0,0,0,0,0,0,0,0];
        match = re.search(
            r'var areaSequence\s*=\s*(?P<sequence>[^]]+]).*', response, re.M)
        if not match:
            # No match and/or bad login
            return False
        sequence = json.loads(match.group('sequence'))

        #
        # Get our Area Status (Bank States)
        #
        # It looks like this in the login.cgi response:
        #  var areaStatus = ["0100000000...000000"];
        match = re.search(
            r'var areaStatus\s*=\s*(?P<states>[^]]+]).*', response, re.M)
        if not match:
            # No match and/or bad login
            return False
        bank_states = json.loads(match.group('states'))

        #
        # Get our Area Names
        #
        # It looks like this in the login.cgi response:
        #  var areaNames = ["","%21","%21","%21","%21","%21","%21","%21"];
        match = re.search(
            r'var areaNames\s*=\s*(?P<area_names>[^]]+]);.*', response, re.M)
        if not match:
            # No match and/or bad login
            return False

        # Store our Areas ('%21' == '!'; these are un-used areas)
        self.areas = \
            {x: {'name': unquote(y).strip()
                 if unquote(y).strip() else 'Area {}'.format(x + 1),
                 'bank': x,
                 'sequence': sequence[x],
                 'bank_state': bank_states[x]}
             for x, y in enumerate(json.loads(match.group('area_names')))
             if y != '%21'}

        return self.process_areas()

    def process_areas(self):
        """
        Updates our area information based on new configuration

        """
        # The following was reverse-engineered from status.js
        # from the function updateArea():
        for bank, area in self.areas.items():

            # some globals
            mask = 1 << bank % 8

            # prepare ourselves a virtual states for reference that can be
            # later indexed by name for readability.
            # Basically in status.js all references are by bank[idx:idx + 2];
            # This just translate mappings to that:
            #   0:2 - index 0
            #   2:4 - index 1
            #   4:6 - index 2
            #   ...
            #   78:80 - index 39
            vbank = [int(area['bank_state'][s:s + 2], 16) & mask
                     for s in range(0, 80, 2)]

            # Partially Armed State
            st_partial = bool(vbank[AreaBank.PARTIAL])

            # Armed State
            st_armed = bool(vbank[AreaBank.ARMED])

            # Exit Mode
            st_exit1 = bool(vbank[AreaBank.EXIT_MODE01])
            st_exit2 = bool(vbank[AreaBank.EXIT_MODE02])

            # Chime Set
            st_chime = bool(vbank[AreaBank.CHIME])

            # ?
            st_night = bool(vbank[AreaBank.NIGHT])

            # Priority, the lower, the higher it is; 6 being the lowest
            priority = 6

            # Now we'll attempt to detect our status
            status = None

            # Our initial index starting point
            bank_no = AreaBank.ARMED \
                if st_exit1 or st_exit2 else AreaBank.UNKWN_00

            while not status:

                if bank_no >= len(AREA_STATES):
                    # Set status
                    status = AreaStatus.READY
                    break

                # The old working way (based on status.js
                # bool(int(bank_state[self.__area_state_byte[bank_no]:
                #      self.__area_state_byte[bank_no] + 2], 16))
                if vbank[int(self.__area_state_byte[bank_no] / 2)]:
                    if st_partial:
                        status = AREA_STATES[bank_no]
                        if status in (AreaStatus.ARMED_STAY,
                                      AreaStatus.EXIT_DELAY_1,
                                      AreaStatus.EXIT_DELAY_2):
                            if st_night:
                                status += ' - Night'

                            elif vbank[AreaBank.UNKWN_07]:
                                status += ' - Instant'

                    if status == AreaStatus.EXIT_DELAY_1:
                        # Bump to EXIT_DELAY_2; we'll eventually hit
                        # the bottom of our while loop and move past that too
                        bank_no += 1

                elif AREA_STATES[bank_no] == AreaStatus.READY \
                        and not (st_armed or st_partial):
                    # Update
                    status = AreaStatus.NOT_READY \
                        if not vbank[AreaBank.UNKWN_01] \
                        else AreaStatus.NOT_READY_FORCEABLE

                # increment our index by one
                bank_no += 1

            if vbank[AreaBank.UNKWN_08] or vbank[AreaBank.UNKWN_09] or \
                    vbank[AreaBank.UNKWN_10] or vbank[AreaBank.UNKWN_11]:

                # Assign priority to 1
                priority = 1

            elif vbank[AreaBank.UNKWN_33] or vbank[AreaBank.UNKWN_34] or \
                    vbank[AreaBank.UNKWN_35] or vbank[AreaBank.UNKWN_36]:

                # Assign priority to 2
                priority = 2

            elif st_partial or vbank[AreaBank.UNKWN_32]:
                # Assign priority to 3
                priority = 3

            elif st_armed:
                # Assign priority to 4
                priority = 4

            elif not vbank[AreaBank.UNKWN_00]:
                # Assign priority to 5
                priority = 5

            area.update({
                'priority': priority,
                'states': {
                    'armed': st_armed,
                    'partial': st_partial,
                    'night': st_night,
                    'chime': st_chime,
                    'exit1': st_exit1,
                    'exit2': st_exit2,
                },
                'status': status,
            })

        return True

    def process_zones(self):
        """
        Updates our zone/sensor information based on new configuration

        """

        # The following was reverse-engineered from status.js
        # from the function updateArea():
        for bank, zone in self.zones.items():

            # some globals
            mask = 1 << bank % 8

            # Our initial offset
            idx = math.floor(bank / 8) * 2

            # Priority, the lower, the higher it is; 5 being the lowest
            priority = 5

            # prepare ourselves a virtual states for reference
            vbank = [int(self.__zbank[s][idx:idx + 2], 16) & mask
                     for s in range(0, 18)]

            # Update our virtual bank
            self.__zvbank[bank] = ''.join(
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
                if zone.get('bank_state') != self.__zvbank[bank] \
                else zone.get('sequence', 0)

            zone.update({
                'priority': priority,
                'status': status,
                'can_bypass': can_bypass,
                'bank_state': self.__zvbank[bank],
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
        response = self.__get('/user/zones.htm', is_json=False)
        if not response:
            return False

        #
        # Get our Zone Sequence
        #
        # It looks like this in the zone.htm response:
        #  var zoneSequence = [110,0,2,73,8,38,0,0,0,10,83,36,0,0,0,0,16,0];
        match = re.search(
            r'var zoneSequence\s*=\s*(?P<sequence>[^]]+]);.*', response, re.M)
        if not match:
            # No match and/or bad login
            return False
        # Store our sequence
        self.__zsequence = json.loads(match.group('sequence'))

        #
        # Get our Zone Sequence
        #
        # It looks like this in the zone.htm response:
        #  var zoneStatus = ["0100000000...000000"];
        match = re.search(
            r'var zoneStatus\s*=\s*(?P<states>[^]]+]);.*', response, re.M)
        if not match:
            # No match and/or bad login
            return False
        self.__zbank = json.loads(match.group('states'))

        #
        # Get our Zone Names
        #
        # It looks like this in the zones.htm response:
        #  var zoneNames = ["Front%20door%20","Garage%20Door","..."];
        match = re.search(
            r'var zoneNames\s*=\s*(?P<zone_names>[^]]+]);.*', response, re.M)
        if not match:
            # No match and/or bad login
            return False

        # Store our Zones ('%21' == '!'; these are un-used sensors)
        self.zones = \
            {x: {'name': unquote(y).strip()
                 if unquote(y).strip() else '{}'.format(x + 1), 'bank': x}
             for x, y in enumerate(json.loads(match.group('zone_names')))
             if y != '%21'}

        #
        # Get our Master Status
        #
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
        Performs a status check

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

        logger.info(
            'Updating Area information on bank {}'.format(bank))

        if not self.session_id and not self.login():
            return None

        payload = {
            'sess': self.session_id,

            # Select the Area Bank
            'arsel': bank,
        }

        # Perform our Query
        response = self.__get('/user/status.json', payload=payload)
        if not response:
            return None

        # Update our bank states
        self.areas[bank]['bank_state'] = response['bankstates']

        # Convert Hex time to Local Date Time
        response['time'] = datetime.fromtimestamp(
            int(response['time'], 16)).strftime('%Y-%m-%d %H:%M:%S')

        return response

    def _zone_status_update(self, bank=0):
        """
        Performs a zone status check

        A status response could look like this:
        {
            "time":"5F8DE0C6",
            "zbank":0,
            "zseq":134,
            "bankstates":"000000000000000000000000",
            "system":[]
        }
        """

        logger.info(
            'Updating Zone/Sensor information on bank {}'.format(bank))

        if not self.session_id and not self.login():
            return None

        payload = {
            'sess': self.session_id,

            # Select the Zone Bank
            'state': bank,
        }

        # Perform our Query
        response = self.__get('/user/zstate.json', payload=payload)
        if not response:
            return None

        # Update our bank states
        self.__zbank[bank] = response['bankstates']

        # Convert Hex time to Local Date Time
        response['time'] = datetime.fromtimestamp(
            int(response['time'], 16)).strftime('%Y-%m-%d %H:%M:%S')

        return response

    def _sequence(self):
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
        response = self.__get('/user/seq.json')
        if not response:
            return None

        # Convert Hex time to Local Date Time
        response['time'] = datetime.fromtimestamp(
            int(response['time'], 16)).strftime('%Y-%m-%d %H:%M:%S')

        perform_area_update = False
        perform_zone_update = False
        for bank, area in self.areas.items():
            if area['sequence'] != response['area'][bank]:
                logger.debug('Area {} sequence changed'.format(bank + 1))
                # We need to update our status here
                area['sequence'] = response['area'][bank]
                self._area_status_update(bank=bank)
                perform_area_update = True

        if perform_area_update:
            self.process_areas()

        for bank, sequence in enumerate(self.__zsequence):
            if sequence != response['zone'][bank]:
                logger.debug('Zone {} sequence changed'.format(bank + 1))
                # We need to update our status here
                self.__zbank[bank] = response['zone'][bank]
                self._zone_status_update(bank=bank)
                perform_zone_update = True

        if perform_zone_update:
            # Update our zone sequence
            self.__zsequence = response['zone']

            # Process all of our zones/sensors
            self.process_zones()

        return response

    def __get(self, path, payload=None, is_json=True, method='POST',
              auth_on_fail=True):
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
        url = 'http://{}{}'.format(self.host, path)

        logger.trace('{} Request to {}'.format(method, url))

        request = None

        try:
            if method == 'POST':
                # Make our POST request
                request = self.session.post(
                    url, data=payload, headers=headers, timeout=self.timeout,
                    allow_redirects=False)

            else:
                # Make our request
                request = self.session.get(
                    url, data=payload, headers=headers, timeout=self.timeout,
                    allow_redirects=False)

            logger.trace('URL: {}, status_code: {}'.format(
                url, request.status_code))
            logger.trace('URL: {}, response:\n{}'.format(
                url, request.content.decode(self.panel_encoding)))

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
                path, payload=payload, is_json=is_json, method=method,
                auth_on_fail=False)

        if request.status_code != requests.codes.ok:
            logger.error('Failed to query {}'.format(url))
            return None

        # Our response object
        response = None

        if is_json:
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
        return 0
