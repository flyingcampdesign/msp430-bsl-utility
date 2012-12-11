#!/usr/bin/env python
#
# (C) 2009-2010 Flying Camp Design
#
# All Rights Reserved.
#
# AUTHOR: Chris Wilson <cwilson@flyingcampdesign.com>
#
# Released under a BSD-style license (please see LICENSE)

import os

if os.name == 'nt':
    from scanwin32 import *
elif os.name == 'posix':
    from scanposix import *
# TODO no java support yet
# elif os.name == 'java':
#     from scanjava import *
else:
    raise Exception("Error: '%s' is not a supported OS" % os.name)
