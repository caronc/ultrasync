# UltraSync Python Tool

This tool is designed to allow 'API' access through a CLI wrapper to several types of alarm system IP modules that use the UltraSync+ mobile app. These modules are generally found in or can be added to systems produced by the below vendors:
 - Hills Ltd (Business defunct in 2023, now operating as Aritech (a division of Kidde Global Solutions))
 - United Technologies Corporation (Alarm division defunct in 2021)

The tool can be leveraged by other scripts/integrations such as https://github.com/caronc/ha-ultrasync for integration into Home Automation systems.

# Compatibility

The tool is written to be compatible with the NX-595E [Hills/Aritech](https://aritech.com.au/) ComNav, [Interlogix](https://www.interlogix.com/index.html) xGen, xGen8 (such as [NXG-8-Z-BO]), and [ZeroWire](https://www.interlogix.com/index.html) UltraSync-based alarm solutions. It is possible that more systems are supported that utilise the UltraSync+ app and share similar code structure, however any not listed here are untested by the code author/contributors.

Later model systems or systems running newer firmware have blocked local network login due to security concerns, so may only allow access through remote/online login (over the internet). Compatibility has been added for this in the tool, however relies on the web service continuining to support it.

As the original manufacturer(s) are mostly defunct, new software development is generally not expected at the vendor level.

![ZeroWire Hub Image](https://raw.githubusercontent.com/caronc/ultrasync/master/static/zerowire_hub.jpeg)

[![Paypal](https://img.shields.io/badge/paypal-donate-green.svg)](https://paypal.me/lead2gold?locale.x=en_US)
[![Follow](https://img.shields.io/twitter/follow/l2gnux)](https://twitter.com/l2gnux/)<br/>
[![Python](https://img.shields.io/pypi/pyversions/ultrasync.svg?style=flat-square)](https://pypi.org/project/ultrasync/)
[![Build Status](https://github.com/caronc/ultrasync/actions/workflows/tests.yml/badge.svg)](https://github.com/caronc/ultrasync/actions/workflows/tests.yml)
[![CodeCov Status](https://codecov.io/github/caronc/ultrasync/branch/master/graph/badge.svg)](https://codecov.io/github/caronc/ultrasync)
[![Downloads](http://pepy.tech/badge/ultrasync)](https://pypi.org/project/ultrasync/)

## How Does It Work?

1. First you need to install it; this part is easy:

   ```bash
   # Install ultrasync onto your system
   pip install ultrasync
   ```

2. Create a configuration file that identifies:
   1. The hostname or IP address of the ComNav/ZeroWire hub you've got setup on some the network.
   1. Your alarm system login User ID (case-sensitive)
   1. Your alarm system login pin.

   **Note**: You can generally only be logged into the alarm system with the same user *once*; a subsequent login with the same user logs out the other. Since this tool actively polls and maintains a login session to your Hub, it can prevent you from being able to log into at the same time elsewhere (via it's website).  **It is strongly recommended that you create a second user account on your system dedicated to just this service.**

   ```yaml
   # An example of what would be found in your configuration file:
   # Use hashtags/pound symbols (#) to optionally add comments
   # Syntax is simply <key>: <value>
   #
   # For local network login you must specify an ip/hostname, user, and pin
   #
   # For remote/online login you must specify the online flag, plus a serial number, passcode, and user agent in addition to the above required fields
   #
   host: 192.168.0.30 (or https://webauth-a.ultraconnect.com for remote/online login)
   user: My Username (case-sensitive)
   pin: 1234
   # Optional for remote/online login
   online: True
   serial_number: 12345678
   passcode: 91011121314
   user_agent: UltraConnect/0487 CFNetwork/1474 Darwin/23.0.0
   ```

3. Use the **--scene** (**-s**) to set your security system's alarm scene.  The possible options are: `disarm`, `away`, `stay`, `fire`, `medical`, and `panic`. The latter 3 are only available for NX-595E currently.

   ```bash
   # By default if no --config= (-c) is specified, one will be automatically
   # loaded from the following location (if present):
   #  ~/.ultrasync
   #  ~/.config/ultrasync

   # Windows users can store their default configuration files here:
   #  %APPDATA%/UltraSync/config
   #  %LOCALAPPDATA%/UltraSync/config

   # Disarm your security system
   ultrasync --scene disarm

   # Arm your security system and activate all of your sensors when setting the
   # away mode macro
   ultrasync --scene away

   # Arm your security system and only activate your perimeter sensors:
   ultrasync --scene stay
   
   # Trigger the fire alarm (ComNav Only):
   ultrasync --scene fire
   
   # Trigger the medical alarm (ComNav Only):
   ultrasync --scene medical
   
   # Trigger the panic alarm (ComNav Only):
   ultrasync --scene panic
   ```

## What Else Can It Do?

- You can put up a live monitor of your device by typing the following:

  ```bash
  # A live monitoring of your home security system:
  ultrasync --watch
  ```
![UltraSync Watch Mode](https://raw.githubusercontent.com/caronc/ultrasync/master/static/ultrasync-watch.gif)

- You can generate a snapshot (in JSON format) that greatly details everything taking place through your security home setup. It provides MUCH greater detail than the `--watch` which allows it to also be integrated with [Home Assistant](https://www.home-assistant.io/integrations/ultrasync/).

  ```bash
  # Print a JSON formatted snapshot of all home security details
  ultrasync --details
  ```

- You can perform a dump of all of the web based files (*that I've found to be useful so far*) to disk.  This makes troubleshooting much easier.

  ```bash
  # Extracts information from your system that can be
  # incredibly useful in debugging and/or adding enhancements
  # later on:
  ultrasync --debug-dump
  ```

  The debug content gets written to a zip file (residing in the same folder you ran this command from) in the form of: `YYYYmmddHHMMSS.ultrasync-dump.zip`.

## Reverse Proxy

If you've exposed your panel to the internet, you can access it by setting your `host` to the full URL to it (instead of just the hosthame/ip).  For example:

```yaml
# A sample UltraSync configuration that requires you to pass through
# a proxy in order to get to your destination:
host: https://your.security.panel/
user: My Username
pin: 1234
```

If you've also protected your panel behind an additional user/pass combo using *Basic Auth* at the reverse proxy level, you can pass through it like so:

```yaml
# A sample ultrasync configuration that requires you to pass through
# a proxy expecting authentication in order to get to your destination:
host: https://user:pass@your.security.panel/
user: My Username
pin: 1234
# You can also optionally turn off the secure hostname verification
# by using the verify switch.  But default this is set to yes if not
# specified:
verify: no
```

## Global Variables

You can also (optionally) set the following global variables to provide the equivalent of what the configuration file could have.  If a configuration file is also loaded, it's settings will always prevail.  If an entry is missing, then the environment variable is used instead (if it's defined):

| Global Variable | Description |
| --- | --- |
| **ULTRASYNC_PIN** | Provides the `pin` variable to the library
| **ULTRASYNC_USER** | Provides the `user` variable to the library
| **ULTRASYNC_HOST** | Provides the `host` variable to the library
| **ULTRASYNC_SSL_VERIFY** | Provides the `verify` variable to the library (optional, defaults to yes if not set)
| **ULTRASYNC_ONLINE** | Provides the `online` variable to the library (optional, defaults to no if not set)
| **ULTRASYNC_SERIAL_NUMBER** | Provides the `serial number` variable to the library (required for remote/online login)
| **ULTRASYNC_PASSCODE** | Provides the `passcode` variable to the library (required for remote/online login)
| **ULTRASYNC_USER_AGENT** | Provides the `user agent` variable to the library (required for remote/online login)

## Disclaimer

This tool was created through reverse engineering and has been expanded through crowdsourced data. All of this code was generated through trial and error since there is no official documentation available that explains the registers. If you can help out by filling in some of the blanks throughout the code base, I would be greatly appreciative of it! Alternatively [buying me a coffee](https://paypal.me/lead2gold?locale.x=en_US) greatly inspires me to continue improving the application.
