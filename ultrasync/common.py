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

class PanelFunction(object):
    """
    Function Commands (fnum entries)
    """

    AREA_DISARM = 0
    AREA_STAY = 1
    AREA_CHIME_TOGGLE = 10
    AREA_AWAY = 15


class AreaBank(object):
    """
    Defines the Bank Identifiers for Area Queries

    By identifying the bank and breaking it down, it makes the code
    MUCH easier to read for others.  It also makes the code easier to
    debug down the road.

    This list has been purely generated through reverse engineering the
    information available to me using the existing Ultrasync Alarm Panel
    interface.

    """

    UNKWN_00 = 0
    UNKWN_01 = 1
    PARTIAL = 2
    ARMED = 3
    EXIT_MODE01 = 4
    EXIT_MODE02 = 5
    UNKWN_06 = 6
    UNKWN_07 = 7
    UNKWN_08 = 8
    UNKWN_09 = 9
    UNKWN_10 = 10
    UNKWN_11 = 11
    UNKWN_12 = 12
    UNKWN_13 = 13
    UNKWN_14 = 14
    UNKWN_15 = 15
    UNKWN_16 = 16
    UNKWN_17 = 17
    CHIME = 18
    UNKWN_19 = 19
    UNKWN_20 = 20
    UNKWN_21 = 21
    UNKWN_22 = 22
    UNKWN_23 = 23
    UNKWN_24 = 24
    UNKWN_25 = 25
    NIGHT = 26
    UNKWN_27 = 27
    UNKWN_28 = 28
    UNKWN_29 = 29
    UNKWN_30 = 30
    UNKWN_31 = 31
    UNKWN_32 = 32
    UNKWN_33 = 33
    UNKWN_34 = 34
    UNKWN_35 = 35
    UNKWN_36 = 36
    UNKWN_37 = 37
    UNKWN_38 = 38
    UNKWN_39 = 39

class AreaStatus(object):
    """
    Defines the panel display area status
    """

    # All sensor are active; occupants are not present.
    ARMED_AWAY = 'Armed Away'

    # Alarm state when user is present in the home; only perimeter sensors
    # are activated.
    ARMED_STAY = 'Armed Stay'

    READY = 'Ready'

    NOT_READY = 'Not Ready'

    NOT_READY_FORCEABLE = 'Not Ready*'

    DISARMED = 'Disarm'

    EXIT_DELAY_1 = 'Exit Delay 1'

    EXIT_DELAY_2 = 'Exit Delay 2'

    ENTRY_DELAY = 'Entry Delay'


AREA_STATES = (
    # These are intentially set and the order is very important
    # entries missing in this array but defined above is an intentional thing
    AreaStatus.ARMED_AWAY,
    AreaStatus.ARMED_STAY,
    AreaStatus.READY,
    'Fire Alarm',
    'Burg Alarm',
    'Panic Alarm',
    'Auxiliary Alarm',
    AreaStatus.EXIT_DELAY_1,
    AreaStatus.EXIT_DELAY_2,
    AreaStatus.ENTRY_DELAY,
    'Sensor Bypass',
    'Sensor Trouble',
    'Sensor Tamper',
    'Sensor Low Battery',
    'Sensor Supervision',
    '',
)


class ZoneBank(object):
    """
    Defines the Bank Identifiers for Zone/Sensor Queries

    By identifying the bank and breaking it down, it makes the code
    MUCH easier to read for others.  It also makes the code easier to
    debug down the road.

    This list has been purely generated through reverse engineering the
    information available to me using the existing Ultrasync Alarm Panel
    interface.

    """

    UNKWN_00 = 0
    UNKWN_01 = 1
    UNKWN_02 = 2
    UNKWN_03 = 3
    UNKWN_04 = 4
    UNKWN_05 = 5
    UNKWN_06 = 6
    UNKWN_07 = 7
    UNKWN_08 = 8
    UNKWN_09 = 9
    UNKWN_10 = 10
    UNKWN_11 = 11
    UNKWN_12 = 12
    UNKWN_13 = 13
    UNKWN_14 = 14
    UNKWN_15 = 15
    UNKWN_16 = 16
    BYPASS_DISABLED = 17


class ZoneStatus(object):
    """
    Defines the panel display zone/sensor status
    """

    READY = 'Ready'
    NOT_READY = 'Not Ready'

ZONE_STATES = (
    ZoneStatus.NOT_READY,
    'Tamper',
    'Trouble',
    '',
    'Inhibited',
    'Alarm',
    'Low Battery',
    'Supervision Fault',
    'Test Fail',
    '',
    'Entry Delay',
    '',
    'Test Active',
    'Activity Fail',
    'Antimask',
)


class AlarmScene(object):
    """
    Defines the different alarm panel states and/or macros
    """

    # All sensor are active; occupants are not present.
    AWAY = 'away'

    # Alarm state when user is present in the home; only perimeter sensors
    # are activated.
    STAY = 'stay'

    # Alarm system is disarmed
    DISARMED = 'disarm'



# A list of all valid alarm states used for validating
ALARM_SCENES = (
    AlarmScene.AWAY,
    AlarmScene.STAY,
    AlarmScene.DISARMED,
)
