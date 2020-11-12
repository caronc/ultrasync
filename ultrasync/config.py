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

import os
import re
from urllib.parse import urlparse

from .logger import logger


class UltraSyncConfig(object):
    """
    A very simple class that takes a file and extracts what it needs from
    it in order to work the UltraSync() object
    """

    # Default values
    _host = 'zerowire'
    _user = 'User 1'
    _pin = '1234'
    _verify = True

    _user_agent = 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:69.0) ' \
                  'Gecko/20100101 Firefox/69.0'

    def __init__(self, pin=None, user=None, host=None, path=None,
                 user_agent=None, verify=None, *args, **kwargs):
        """
        Initializes the configuration object
        """

        # Extra Details
        self.__secure = False
        self.__auth = None

        # Assign Defaults
        self._pin = pin if pin else os.environ.get(
            'ULTRASYNC_PIN', UltraSyncConfig._pin)
        self._user = user if user else os.environ.get(
            'ULTRASYNC_USER', UltraSyncConfig._user)
        self._host = host if host else os.environ.get(
            'ULTRASYNC_HOST', UltraSyncConfig._host)
        self._verify = verify if verify is not None else os.environ.get(
            'ULTRASYNC_SSL_VERIFY', UltraSyncConfig._verify)
        self._user_agent = \
            user_agent if user_agent else UltraSyncConfig._user_agent

        if path and not self.load(path):
            raise AttributeError('Invalid path specified: {}'.format(path))
        else:
            self.__store()

    def __store(self):
        """
        Takes the hostname and detects if it is a URL
        If it is, it further parses out details from it

        """
        if re.match(r'^\s*https?://.+', self._host, re.I):
            # Parse our URL details and populate our other entries
            result = urlparse(self._host)
            self._host = result.hostname
            self.__secure = result.scheme[-1].lower() == 's'
            if result.username and result.password:
                self.__auth = (result.username, result.password)

        # Ensure verify is of type boolean
        self._verify = self.parse_bool(self._verify, UltraSyncConfig._verify)

        return True

    def load(self, path=None):
        """
        Loads the configuration specified by the path
        """

        # Reset our variables to their defaults
        self.__secure = False
        self.__auth = None

        # Define what a valid line should look like
        valid_line_re = re.compile(
            r'^\s*(?P<key>[^:#;\s]+)\s*:\s*(?P<value>.+)$', re.I)

        try:
            # Open/Parse File
            with open(path, 'r') as reader:
                line = '\n'
                while line:
                    line = reader.readline()
                    match = valid_line_re.match(line)
                    if not match:
                        # keep reading
                        continue
                    key = '_{}'.format(match.group('key'))
                    if key[1] != '_' and hasattr(self, key):
                        setattr(self, key, match.group('value'))
                        logger.trace('Config: {} loaded as {}'.format(
                            key[1:], match.group('value')))

        except (IOError, OSError, TypeError):
            # Could not load configuration
            return False

        # Return our parsed content
        return self.__store()

    @staticmethod
    def parse_bool(arg, default=False):
        """
        Parse a boolean from the argument passed in
        """

        if isinstance(arg, str):
            # of = short for off - False
            # 0  = int for False
            # fa = short for False - False
            # f  = short for False - False
            # n  = short for No or Never - False
            # ne  = short for Never - False
            # d  = short for Disable(d) / Deny - False
            # -  = False
            if arg.lower()[0:2] in (
                    '-', 'd', 'di', 'de', 'ne', 'f', 'n', 'no', 'of', '0',
                    'fa'):
                return False
            # y = yes - True
            # on = short for off - True
            # 1  = int for True
            # tr = short for True - True
            # t  = short for True - True
            # al = short for Always (and Allow) - True
            # e  = short for Enable(d) - True
            # +  = True
            elif arg.lower()[0:2] in (
                    '+', 'e', 'en', 'al', 't', 'y', 'ye', 'on', '1', 'tr'):
                return True
            # otherwise
            return default

        # Handle other types
        return bool(arg)

    @property
    def host(self):
        """
        Returns Alarm Panel Host
        """
        return self._host

    @property
    def user(self):
        """
        Returns Alarm Panel User Login
        """
        return self._user

    @property
    def pin(self):
        """
        Returns Alarm Panel PIN
        """
        return self._pin

    @property
    def verify(self):
        """
        Returns the SSL Verify Flag
        """
        return self._verify

    @property
    def user_agent(self):
        """
        Returns User Agent Setting
        """
        return self._user_agent

    @property
    def url(self):
        """
        Returns request URL
        """
        return '{scheme}://{host}'.format(
            scheme='https' if self.__secure else 'http',
            host=self._host)

    @property
    def auth(self):
        """
        Returns requests auth details
        """
        return self.__auth
