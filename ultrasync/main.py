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
from datetime import datetime
from datetime import timedelta
from .common import AlarmScene
from .common import ALARM_SCENES
from .config import UltraSyncConfig
from urllib.parse import unquote
from .logger import logger


class UltraSync(UltraSyncConfig):
    """
    A wrapper to the UltraSync Alarm Panel
    """

    panel_encoding = 'utf-8'

    def __init__(self, *args, **kwargs):
        """
        prepares our UltraSync object
        """

        super(UltraSync, self).__init__(*args, **kwargs)

        # Create our session object
        self.session = requests.Session()

        # Track if we're _authenticated or not
        self._authenticated = False

        # Our session id is retrieved after a successful login
        self.session_id = None

        # User Status codes
        self.__is_master = None
        self.__is_installer = None

        # Meta Information parsed on login (area.htm)
        self._area_names = None
        self._area_sequence = None
        self._area_status = None

        # Zone details; populated (zones.htm)
        self._zone_names = None
        self._zone_sequence = None
        self._zone_status = None

        # Track the time our information was polled from our panel
        self.__updated = None

        # Track the Panel URL path
        self.__panel_url_path = None

    def login(self):
        """
        Performs login to UltraSync (which then redirects to area.htm)

        """
        # Our initialiation
        self._authenticated = False
        self.session_id = None

        payload = {
            'lgname': self.user,
            'lgpin': self.pin,
        }

        response = self.__get('/login.cgi', payload=payload, is_json=False)
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

        if not self._areas(response=response):
            # No match and/or bad login
            logger.error('Failed to authenticate to {}'.format(self.host))
            return False

        # Set our authentication flag
        self._authenticated = True if self.session_id else False

        # We're good
        return self._authenticated

    def logout(self):
        """
        Performs login to UltraSync

        """
        if not self._authenticated:
            # We're done
            return True

        # Reset our variables reguardless if we're successfully able to log
        # out or not
        self._authenticated = False
        self.session_id = None

        # Area (area.htm) details
        self._area_names = None
        self._area_sequence = None
        self._area_status = None

        # Zone (zone.htm) details
        self._zone_names = None
        self._zone_sequence = None
        self._zone_status = None

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
        if not self._authenticated and not self.login():
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
            'zones.html': {
                'path': '/user/zones.htm',
            },

            # Used to acquire sequence
            'seq.json': {
                'path': '/user/seq.json',
            },

            # Additional useful queries
            'master.js': {
                'path': '{}/master.js'.format(self.__panel_url_path),
                'method': 'GET'
            },
            'status.js': {
                'path': '{}/status.js'.format(self.__panel_url_path),
                'method': 'GET'
            }
        }

        for to_file, kwargs in urls.items():

            response = self.__get(is_json=False, **kwargs)
            if not response:
                continue

            with open(os.path.join(path, to_file), 'w',
                      encoding=self.panel_encoding) as fp:
                # Write our content to disk
                _bytes = fp.write(response)
                logger.info('Wrote {} bytes to {}'.format(_bytes, to_file))

    def set(self, area_bank=0, state=AlarmScene.DISARMED):
        """
        Sets Alarm Scene
        """
        if not self._authenticated and not self.login():
            return False

        if state not in ALARM_SCENES:
            return False

        payload = {
            'sess': self.session_id,
            'start': int(area_bank),
            'mask': 1,
        }

        if state == AlarmScene.STAY:
            payload.update({
                'fnum': 1,
            })

        elif state == AlarmScene.AWAY:
            payload.update({
                'fnum': 15,
            })

        else:   # AlarmScene.DISARMED
            payload.update({
                'fnum': 0,
            })

        response = self.__get('/user/keyfunction.cgi', payload=payload)
        if not response:
            return False

        return response

    def update(self, ref=None, max_age_sec=5):
        """
        Updates class information
        """

        if ref is None:
            ref = datetime.now()

        if self.__updated is None:
            if not self._areas() or not self._zones():
                return False

        elif (self.__updated + timedelta(seconds=max_age_sec)) >= ref:
            if not self._sequence():
                return False

        # Update our time reference
        self.__updated = datetime.now()
        return True

    def details(self, meta=False):
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
            'zones': [],
            'areas': [],
            'date': self.__updated.strftime('%Y-%m-%d %H:%M:%S'),
        }

        if meta:
            response.update({
                '_zone_meta_': {
                    'names': self._zone_names,
                    'sequence': self._zone_sequence,
                    'status': self._zone_status,
                },
                '_area_meta_': {
                    'names': self._area_names,
                    'sequence': self._area_sequence,
                    'status': self._area_status,
                },
            })

        for _bank in sorted(self._zone_names.keys()):
            # Get our index
            bank = int(_bank)
            zone = {
                'bank': bank,
                'sequence': self._zone_sequence[bank],
                'name': self._zone_names[_bank]['name'],
                'status': self._zone_status[bank],
            }
            response['zones'].append(zone)

        for _bank in sorted(self._area_names.keys()):
            # Get our index
            bank = int(_bank)
            area = {
                'bank': bank,
                'sequence': self._area_sequence[bank],
                'name': self._area_names[_bank]['name'],
                'status': self._area_status[bank],
            }
            response['areas'].append(area)

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
        if not response:
            # No response object was specified; we need to query the area.htm
            # page.
            if not self._authenticated and not self.login():
                return False

            # Perform our Query
            response = self.__get('/user/area.htm', is_json=False)
            if not response:
                return False

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
        self._area_names = \
            {x: {'name': unquote(y).strip()
                 if unquote(y).strip() else 'Area {}'.format(x + 1)}
             for x, y in enumerate(json.loads(match.group('area_names')))
             if y != '%21'}

        #
        # Get our Area Sequence
        #
        # It looks like this in the login.cgi response:
        #  var areaSequence = [149,0,0,0,0,0,0,0,0,0,0,0];
        match = re.search(
            r'var areaSequence\s*=\s*(?P<area_sequence>[^]]+]).*',
            response, re.M)
        if not match:
            # No match and/or bad login
            return False
        self._area_sequence = json.loads(match.group('area_sequence'))

        #
        # Get our Area Sequence
        #
        # It looks like this in the login.cgi response:
        #  var areaStatus = ["0100000000...000000"];
        match = re.search(
            r'var areaStatus\s*=\s*(?P<area_status>[^]]+]).*',
            response, re.M)
        if not match:
            # No match and/or bad login
            return False
        self._area_status = json.loads(match.group('area_status'))

        return True

    def _zones(self):
        """
        Parses the zone Ultrasync
        """

        if not self._authenticated and not self.login():
            return False

        # Perform our Query
        response = self.__get('/user/zones.htm', is_json=False)
        if not response:
            return False

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
        self._zone_names = \
            {x: {'name': unquote(y).strip()}
             for x, y in enumerate(json.loads(match.group('zone_names')))
             if y != '%21'}

        #
        # Get our Zone Sequence
        #
        # It looks like this in the zone.htm response:
        #  var zoneSequence = [110,0,2,73,8,38,0,0,0,10,83,36,0,0,0,0,16,0];
        match = re.search(
            r'var zoneSequence\s*=\s*(?P<zone_sequence>[^]]+]);.*',
            response, re.M)
        if not match:
            # No match and/or bad login
            return False
        self._zone_sequence = json.loads(match.group('zone_sequence'))

        #
        # Get our Zone Sequence
        #
        # It looks like this in the zone.htm response:
        #  var zoneStatus = ["0100000000...000000"];
        match = re.search(
            r'var zoneStatus\s*=\s*(?P<zone_status>[^]]+]);.*',
            response, re.M)
        if not match:
            # No match and/or bad login
            return False
        self._zone_status = json.loads(match.group('zone_status'))

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

        return True

    def _status(self, area_bank=0):
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

        if not self._authenticated and not self.login():
            return None

        payload = {
            'sess': self.session_id,

            # Select the Area Bank
            'arsel': int(area_bank),
        }

        # Perform our Query
        response = self.__get('/user/status.json', payload=payload)
        if not response:
            return False

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

        """
        if not self._authenticated and not self.login():
            return False

        # Perform our Query
        response = self.__get('/user/seq.json')
        if not response:
            return False

        # Update our sequences
        self._area_sequence = response['area']
        self._zone_sequence = response['zone']

        # Convert Hex time to Local Date Time
        response['time'] = datetime.fromtimestamp(
            int(response['time'], 16)).strftime('%Y-%m-%d %H:%M:%S')

        return response

    def __get(self, path, payload=None, is_json=True, method='POST'):
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

        logger.debug('{} Request to {}'.format(method, url))

        if method == 'POST':
            # Make our POST request
            request = self.session.post(url, data=payload, headers=headers)

        else:
            # Make our request
            request = self.session.get(url, data=payload, headers=headers)

        logger.debug('URL: {}, status_code: {}'.format(
            url, request.status_code))
        logger.debug('URL: {}, response:\n{}'.format(
            url, request.content.decode(self.panel_encoding)))

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
