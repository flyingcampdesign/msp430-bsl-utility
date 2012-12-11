#!/usr/bin/env python
#
# (C) 2009-2010 Flying Camp Design
#
# All Rights Reserved.
#
# AUTHOR: Chris Wilson <cwilson@flyingcampdesign.com>
#
# Parts based on code from Chris Liechti <cliechti@gmx.net>:
# http://pyserial.svn.sourceforge.net/viewvc/pyserial/trunk/pyserial/serial/serialposix.py
# http://pyserial.svn.sourceforge.net/viewvc/pyserial/trunk/pyserial/examples/scanlinux.py
#
# Released under a BSD-style license (please see LICENSE)

import sys
import platform
import serial
import glob

PLATFORM = platform.platform()
if PLATFORM.lower().startswith('linux'):         # Linux
    portlist = glob.glob('/dev/ttyS*') + glob.glob('/dev/ttyUSB*') # usb <-> serial support
elif PLATFORM.lower().startswith('darwin'):      # OS X
    portlist = glob.glob('/dev/cuad*') + glob.glob('/dev/tty.usbserial*') # usb <-> serial support
else:
    raise Exception("Platform %s not supported" % PLATFORM)

def scan():
    """scan for available ports. return a list of device names."""
    available = []
    for i in portlist:
        try:
            s = serial.Serial(i)
            available.append(s.portstr)
            s.close()
        except (serial.SerialException, ValueError):
            pass
    return available

if __name__ == '__main__':
    print "Found ports:"
    for name in scan():
        print name
