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

    _user_agent = 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:69.0) ' \
                  'Gecko/20100101 Firefox/69.0'

    def __init__(self, pin=None, user=None, host=None, path=None,
                 user_agent=None, *args, **kwargs):
        """
        Initializes the configuration object
        """

        # Extra Details
        self._secure = False
        self._auth = None

        # Assign Defaults
        self._pin = pin if pin else os.environ.get(
            'ULTRASYNC_PIN', UltraSyncConfig._pin)
        self._user = user if user else os.environ.get(
            'ULTRASYNC_USER', UltraSyncConfig._user)
        self._host = host if host else os.environ.get(
            'ULTRASYNC_HOST', UltraSyncConfig._host)
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
        # Reset our variables to their defaults
        self._secure = False
        self._auth = None

        if re.match(r'^\s*https?://.+', self._host, re.I):
            # Parse our URL details and populate our other entries
            result = urlparse(self._host)
            self._host = result.netloc
            self._secure = result.scheme[-1].lower() == 's'
            if result.username and result.password:
                self._auth = (result.username, result.password)

        return True

    def load(self, path=None):
        """
        Loads the configuration specified by the path
        """

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
                    if hasattr(self, key):
                        setattr(self, key, match.group('value'))
                        logger.trace('Config: {} loaded as {}'.format(
                            key[1:], match.group('value')))

        except (IOError, OSError, TypeError):
            # Could not load configuration
            return False

        # Return our parsed content
        return self.__store()

    @property
    def host(self):
        """
        Returns environment variable ULTRASYNC_HOST if defined otherwise
        it falls back to the parsed content.
        """
        return self._host

    @property
    def user(self):
        """
        Returns environment variable ULTRASYNC_USER if defined otherwise
        it falls back to the parsed content.
        """
        return self._user

    @property
    def pin(self):
        """
        Returns environment variable ULTRASYNC_PIN if defined otherwise
        it falls back to the parsed content.
        """
        return self._pin

    @property
    def user_agent(self):
        """
        Returns environment variable ULTRASYNC_PIN if defined otherwise
        it falls back to the parsed content.
        """
        return os.environ.get('ULTRASYNC_USER_AGENT', self._user_agent)

    @property
    def url(self):
        """
        Returns request URL
        """
        return '{scheme}://{host}'.format(
            scheme='https' if self._secure else 'http',
            host=self._host)

    @property
    def auth(self):
        """
        Returns requests auth details
        """
        return self._auth
