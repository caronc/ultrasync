# Interlogix UltraSync ZeroWire Hub
[Interlogix](https://www.interlogix.com/) provides security solutions. One of which is their [Self Contained (ZeroWire) Hub](https://www.interlogix.com/intrusion/product/ultrasync-selfcontained-hub):<br/>![ZeroWire Hub Image](https://raw.githubusercontent.com/caronc/ultrasync/master/static/zerowire_hub.jpeg)

This is just a small library and accompaning CLI tool I wrote to allow me to interface with it.

## How Does It Work?
1. First you need to install it; this part is easy:
```bash
pip install ultrasync
```

2. Create a configuration file that identifies:
   1. The location the ZeroWire hub can be found on in your local nework.
   1. Your ZeroWire login User ID
   1. Your ZeroWire login pin
```python
# An example of what would be found in your configuration file:
# Use hashtags/pound symbols (#) to optionally add comments
# Syntax is simply <key>: <value>
#
# You must specify hostname, user, and pin
#
host: 192.168.0.30
user: My Username
pin: 1234
```
3. Use the **--scene** (*-s*) to set your security system's alarm scene.  The possible options are: `disarm`, `away`, and `stay`.
```bash
# By default if no --config= (-c) is specified; one will be automatically
# loaded from the following location (if present):
#  ~/.ultrasync
#  ~/.config/ultrasync

# Windows users can store their default configuration files here:
#  %APPDATA%/UltraSync/config
#  %LOCALAPPDATA%/UltraSync/config

# Disarm your security system
ultrasync --scene disarm

# Arm your security system and acctivate all of your sensors when setting the
# away mode macro
ultrasync --scene away

# Arm your security system and only activate your perimiter sensors:
ultrasync --scene stay
```

# Disclaimer
This is a heavy work in progress.  I only created it and tested it against my own security system. I make no promises that it will work with other versions (or even newer ones).

Please feel free to file bugs and use this at your sole discretion that I also have no control over how your own security system has been set up.
