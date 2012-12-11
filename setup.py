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
import sys
import platform
import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages

PY2EXE = 'py2exe' in sys.argv
PY2APP = 'py2app' in sys.argv

PLATFORM = platform.platform()
WINDOWS = PLATFORM.lower().startswith('windows')
DARWIN = PLATFORM.lower().startswith('darwin')
LINUX = PLATFORM.lower().startswith('linux')

pkg_name = "msp430bslu"
src_dir_name = "src"
scr_dir_name = "scripts"
res_dir_name = "resources"

sys.path.append(src_dir_name)
import msp430bslu.app

app_script = os.path.join(scr_dir_name, 'msp430-bsl-utility.pyw')
app_icon = msp430bslu.app.ICONFILE

# Platform independent setup
setup_options = {}
setup_args = dict(
    name = pkg_name,
    description = msp430bslu.app.DESCRIPTION,
    version = msp430bslu.app.VERSION,
    author = msp430bslu.app.AUTHOR,
    author_email = msp430bslu.app.AUTHOR_EMAIL,
    url = msp430bslu.app.URL,
    license = msp430bslu.app.LICENSE,
    long_description = msp430bslu.app.LONG_DESCRIPTION,
    packages = find_packages(where=src_dir_name),
    package_dir = {pkg_name: os.path.join(src_dir_name, pkg_name)},
    package_data = {pkg_name: [app_icon]},
    scripts = [app_script],
    options = setup_options,
)

# Platform dependent setup
if WINDOWS:
    if PY2EXE:
        import py2exe
        target = dict( 
            name = msp430bslu.app.DESCRIPTION,
            description = msp430bslu.app.DESCRIPTION,
            version = msp430bslu.app.VERSION,
            company_name = msp430bslu.app.COMPANY,
            copyright = msp430bslu.app.COPYRIGHT,
            script = app_script,
            icon_resources = [(1, app_icon)],
            dest_base = msp430bslu.app.DESCRIPTION,
        )
        setup_args['windows'] = [target]
        setup_args['data_files'] = [
            ("", [app_icon]),
        ]
        setup_options["py2exe"] = {
            "unbuffered": True,
            "optimize": 2,
            'bundle_files': 3, # for some reason, "1" and "2" failed
            'skip_archive': True, # required for resource_filename() in app.py to work correctly
        }
elif DARWIN:
    if PY2APP:
        setup_args['name'] = msp430bslu.app.DESCRIPTION
        setup_args['app'] = [app_script]
        setup_args['setup_requires'] = ["py2app"]
        setup_options["py2app"] = {
            # "argv_emulation": 1, # FIXME
            "iconfile": app_icon,
            "optimize": 2,
            "resources": [app_icon],
        }
elif LINUX:
    pass
else:
    raise Exception("Platform %s not supported" % PLATFORM)

setup(**setup_args)
