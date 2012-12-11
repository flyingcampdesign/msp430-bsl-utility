#!/usr/bin/env python
#
# (C) 2009-2010 Flying Camp Design
#
# All Rights Reserved.
#
# AUTHOR: Chris Wilson <cwilson@flyingcampdesign.com>
#
# Parts based on code from Chris Liechti <cliechti@gmx.net>:
# http://pyserial.svn.sourceforge.net/viewvc/pyserial/trunk/pyserial/examples/scan.py
#
# Released under a BSD-style license (please see LICENSE)

import serial

def scan():
    """scan for available ports. return a list of device names."""
    available = []
    for i in range(256):
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
