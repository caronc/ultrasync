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
from .common import AlarmScene
from .common import ALARM_SCENES
from .config import UltraSyncConfig
from urllib.parse import unquote


class UltraSync(UltraSyncConfig):
    """
    A wrapper to the UltraSync Alarm Panel
    """

    # Login URL
    url_login = 'http://{}/login.cgi'

    # Logout URL
    url_logout = 'http://{}/logout.cgi'

    # Status URL
    url_status = 'http://{}/user/status.json'

    # Used to acquire sequence
    url_sequence = 'http://{}/user/seq.json'

    # Used set macro
    url_macro = 'http://{}/user/keyfunction.cgi'

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

        # Meta Information parsed on login
        self._area_sequence = None
        self._area_status = None
        self._zone_names = None
        self._zone_sequence = None
        self._zone_status = None

    def login(self):
        """
        Performs login to UltraSync

        """
        headers = {
            'Referer': 'http://{}/login.htm'.format(self.host),
            'User-Agent': self.user_agent
        }
        payload = {
            'lgname': self.user,
            'lgpin': self.pin,
        }

        r = self.session.post(
            self.url_login.format(self.host),
            data=payload,
            headers=headers,
        )

        #
        # Get our Session Identifier
        #
        # It looks like this in the login.cgi response:
        #  function getSession(){return "A2D6C62695D705D8";}
        match = re.search(
            r'function getSession\(\)[^"]+"(?P<session>[^"]+)".*',
            r.content.decode('utf-8'), re.M)
        if not match:
            # No match and/or bad login
            return False

        # Store our session
        self.session_id = match.group('session')

        #
        # Get our Area Sequence
        #
        # It looks like this in the login.cgi response:
        #  var areaSequence = [149,0,0,0,0,0,0,0,0,0,0,0];
        match = re.search(
            r'var areaSequence\s*=\s*(?P<area_sequence>[^]]+]).*',
            r.content.decode('utf-8'), re.M)
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
            r.content.decode('utf-8'), re.M)
        if not match:
            # No match and/or bad login
            return False
        self._area_status = json.loads(match.group('area_status'))

        self._authenticated = r.status_code == requests.codes.ok \
            and self.session_id

        return self._authenticated

    def logout(self):
        """
        Performs login to UltraSync

        """
        if not self._authenticated:
            # We're done
            return

        headers = {
            'Referer': 'http://{}/login.htm'.format(self.host),
            'User-Agent': self.user_agent
        }

        payload = {
            'sess': self.session_id,
        }

        self.session.post(
            self.url_logout.format(self.host),
            data=payload,
            headers=headers,
        )

        # Reset our variables
        self._authenticated = False
        self.session_id = None
        self._area_sequence = None
        self._area_status = None
        self._zone_names = None
        self._zone_sequence = None
        self._zone_status = None

    def _zones(self):
        """
        Returns a dictionary of configured Zones
        """

        if not self._authenticated and not self.login():
            return None

        headers = {
            'Referer': self.url_login.format(self.host),
            'User-Agent': self.user_agent
        }
        payload = {
            'sess': self.session_id,
        }

        r = self.session.post(
            self.url_status.format(self.host),
            data=payload,
            headers=headers,
        )

        if r.status_code != requests.codes.ok:
            return None

        #
        # Get our Zone Names
        #
        # It looks like this in the zones.htm response:
        #  var zoneNames = ["Front%20door%20","Garage%20Door","..."];
        match = re.search(
            r'var zoneNames\s*=\s*(?P<zone_names>[^]]+]);.*',
            r.content.decode('utf-8'), re.M)
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
            r.content.decode('utf-8'), re.M)
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
            r.content.decode('utf-8'), re.M)
        if not match:
            # No match and/or bad login
            return False
        self._zone_status = json.loads(match.group('zone_status'))
        return True

    def _status(self):
        """
        Performs a status check
        """

        if not self._authenticated and not self.login():
            return None

        headers = {
            'Referer': self.url_login.format(self.host),
            'User-Agent': self.user_agent
        }
        payload = {
            'sess': self.session_id,
            'arsel': '0',
        }

        r = self.session.post(
            self.url_status.format(self.host),
            data=payload,
            headers=headers,
        )

        if r.status_code != requests.codes.ok:
            return None

        try:
            response = json.loads(r.content.decode('utf-8'))

        except (AttributeError, TypeError, ValueError):
            # ValueError = r.content is Unparsable
            # TypeError = r.content is None
            # AttributeError = r is None
            response = None

        return response

    def _sequence(self):
        """
        Returns the sequence response type
        """
        if not self._authenticated and not self.login():
            return None

        headers = {
            'Referer': self.url_login.format(self.host),
            'User-Agent': self.user_agent
        }
        payload = {
            'sess': self.session_id,
        }
        r = self.session.post(
            self.url_sequence.format(self.host),
            data=payload,
            headers=headers,
        )

        if r.status_code != requests.codes.ok:
            return None

        try:
            response = json.loads(r.content.decode('utf-8'))

        except (AttributeError, TypeError, ValueError):
            # ValueError = r.content is Unparsable
            # TypeError = r.content is None
            # AttributeError = r is None
            response = None

        return response

    def set(self, state=AlarmScene.DISARMED):
        """
        Sets Alarm Scene
        """
        if not self._authenticated and not self.login():
            return False

        if state not in ALARM_SCENES:
            return False

        headers = {
            'Referer': self.url_login.format(self.host),
            'User-Agent': self.user_agent
        }

        payload = {
            'sess': self.session_id,
            'start': 0,
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

        r = self.session.post(
            self.url_macro.format(self.host),
            data=payload,
            headers=headers,
        )

        if r.status_code != requests.codes.ok:
            return False

        try:
            response = json.loads(r.content.decode('utf-8'))

        except (AttributeError, TypeError, ValueError):
            # ValueError = r.content is Unparsable
            # TypeError = r.content is None
            # AttributeError = r is None
            response = None

        return response
