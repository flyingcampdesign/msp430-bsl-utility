#!/usr/bin/env python
#
# Serial bootstrap loader utility for the MSP430 embedded proccessor
#
# (C) 2009-2010 Flying Camp Design
#
# All Rights Reserved.
#
# AUTHOR: Chris Wilson <cwilson@flyingcampdesign.com>
#
# Parts based on code from Chris Liechti <cliechti@gmx.net>:
# http://mspgcc.cvs.sourceforge.net/viewvc/mspgcc/python/msp430-bsl.py
# This app also imports a modified version of the 'mspgcc' python package
# http://mspgcc.cvs.sourceforge.net/viewvc/mspgcc/python/mspgcc/
#
# Released under a BSD-style license (please see LICENSE)

# FIXME sscan is broken on osx when you hit the scan button

import os
import sys
import errno
import platform
import ConfigParser
import serial
import sscan
from Tkinter import *
from ttk import *
from tkFileDialog import *
from tkMessageBox import *
from tkExtras import *
from mspgcc.util import hexdump, makeihex
from mspgcc import memory, bsl
from pkg_resources import resource_filename

__version__ = '0.9.1'

DESCRIPTION = 'MSP430 BSL Utility'
VERSION = __version__
AUTHOR = 'Chris Wilson'
AUTHOR_EMAIL = 'cwilson@flyingcampdesign.com'
COMPANY = 'Flying Camp Design'
COPYRIGHT = "(C) 2009-2010 %s\nAll Rights Reserved." % COMPANY
LICENSE = 'BSD-style'
URL = 'http://www.flyingcampdesign.com'
LONG_DESCRIPTION = 'Serial bootstrap loader utility for the MSP430 embedded proccessor'

DEBUG = 0
MAX_DEBUG = 4 # Maximum debug level in app AND imported modules (such as bsl)
CONFIG_EXT = '.cfg'
CONFIG_FILE_TYPES = [
    ('Config Files', CONFIG_EXT),
    ('All Files', '*'),
]
INFO_OPTS = 'App Info'
APP_OPTS = 'App Options'
BSL_OPTS = 'BSL Options'
BAUDS = [9600, 19200, 38400]
FILE_TYPES = ['Auto Select', 'IntelHex', 'TI-Text']
CPU_TYPES = ['Auto Select', 'F1x', 'F4x']
UPLOAD_FORMATS = ['hex', 'ihex', 'bin']
FIRMWARE_FILE_TYPES = [
    ('hex Files', '.hex'),
    ('ihex Files', '.ihex'),
    ('bin Files', '.bin'),
    ('All Files', '*'),
]
HEX = 0
INTELHEX = 1
BINARY = 2
PLATFORM = platform.platform()
WINDOWS = PLATFORM.lower().startswith('windows')
DARWIN = PLATFORM.lower().startswith('darwin')
LINUX = PLATFORM.lower().startswith('linux')

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST:
            pass
        else: raise

if WINDOWS:
    INIDIR = os.path.join(os.environ['APPDATA'], COMPANY, DESCRIPTION)
    mkdir_p(INIDIR)
    ININAME = 'msp430-bsl-utility'
    INIEXT = '.ini'
else:
    INIDIR = os.path.expanduser('~')
    ININAME = '.msp430-bsl-utility'
    INIEXT = ''
INIFILE = os.path.join(INIDIR, (ININAME + INIEXT))

if DARWIN:
    ICONFILE = resource_filename(__name__, 'resources/ic.icns')
else:
    ICONFILE = resource_filename(__name__, 'resources/ic.ico')

if os.path.isdir(os.path.join(os.path.expanduser('~'), 'Documents')):
    FILEINIDIR = os.path.join(os.path.expanduser('~'), 'Documents')
elif os.path.isdir(os.path.join(os.path.expanduser('~'), 'My Documents')):
    FILEINIDIR = os.path.join(os.path.expanduser('~'), 'My Documents')
else:
    FILEINIDIR = os.path.expanduser('~')

def set_debug(level):
    """
    Sets DEBUG level for this app and some imported modules
    """
    global DEBUG
    DEBUG = level
    bsl.DEBUG = level
    memory.DEBUG = level

def get_tk_var_name(var):
    """
    Returns the internal name for a Tkinter variable
    """
    return var._name

def set_tk_var_name(var, name):
    """
    Sets the internal name for a Tkinter variable
    """
    var._name = name

class AppError(Exception):
    pass

class UpdatingBootStrapLoader(bsl.BootStrapLoader):
    """
    BootStrapLoader wrapper class that updates a progress object
    """
    def __init__(self, progress_obj=None, *args, **kwargs):
        bsl.BootStrapLoader.__init__(self, *args, **kwargs)
        self.progress_obj = progress_obj
    
    def progress_update(self, count, total=100):
        """
        Overloads the bsl.progress_update method in bsl.BootStrapLoader
        """
        if bsl.DEBUG:
            pcnt = (100*count/total)
            sys.stderr.write("  %d%%\n" % pcnt)
            sys.stderr.flush()
        if self.progress_obj != None:
            self.progress_obj.set(count, total)
    

class AppMainWindow(MainWindow):
    """
    Main app window
    """
    def __init__(self):
        # order matters!
        MainWindow.__init__(self, title=DESCRIPTION, iconfile=ICONFILE)
        self.resizable(width=FALSE, height=FALSE)
        self.enable_sanity_checks = False
        self.enable_errors = True
        self.enable_warnings = True
        self.running = False
        self.configfile = ''
        self.make_defaults()
        self.make_vars()
        self.make_menu()
        self.make_widgets()
        self.make_callback_list()
        self.log = PopupGuiOutput(title=DESCRIPTION, kind='Log', iconfile=ICONFILE, var=self.logwinvisible)
        self.log.resizable(width=FALSE, height=FALSE)
        sys.stderr = self.log
        self.out = PopupGuiOutput(title=DESCRIPTION, kind='Output', iconfile=ICONFILE, var=self.outwinvisible)
        self.out.resizable(width=FALSE, height=FALSE)
        sys.stdout = self.out
        self.bind('<Return>', self.on_go)
        self.set_defaults()
        self.enable_sanity_checks = True
        if os.path.isfile(INIFILE):
            self.load_config(INIFILE)
        self.initialize_widgets()
        self.update()
    
    def error(self, message):
        """
        Displays a GUI pop up info window
        """
        if self.enable_errors:
            showerror('Error', message)
    
    def logged_error(self, message):
        """
        Prints an error message to the log and displays a pop up error window
        """
        if self.enable_errors:
            self.log.write(message)
            self.error(message)
    
    def warning(self, message):
        """
        Displays a GUI pop up warning window
        """
        if self.warnings.get() and self.enable_warnings:
            showwarning('Warning', message)
    
    def enable_popups(self):
        self.enable_errors = True
        self.enable_warnings = True
    
    def disable_popups(self):
        self.enable_errors = False
        self.enable_warnings = False
    
    def get_val(self, name):
        """
        Gets the value of an attribute that defines a 'get()' method
        """
        return getattr(self, name).get()
    
    def set_val(self, name, value):
        """
        Sets the value of an attribute that defines a 'set()' method
        """
        getattr(self, name).set(value)
    
    def make_defaults(self):
        """
        Creates default value dicts
        """
        # App Info
        self.app_info = {}
        self.app_info['version'] = VERSION
        self.app_info['platform'] = PLATFORM
        
        # App Defaults
        self.app_defaults = {}
        self.app_defaults['useini'] = False
        self.app_defaults['logwinvisible'] = False
        self.app_defaults['outwinvisible'] = False
        self.app_defaults['warnings'] = True
        self.app_defaults['debuglevel'] = 0
        
        # BSL Defaults
        self.bsl_defaults = {}
        self.bsl_defaults['comport'] = None
        self.bsl_defaults['password'] = None
        self.bsl_defaults['filename'] = None
        self.bsl_defaults['framesize'] = 224
        self.bsl_defaults['erasecycles'] = 1
        self.bsl_defaults['unpatched'] = False
        self.bsl_defaults['filetype'] = 'Auto Select'
        self.bsl_defaults['timeout'] = 1
        self.bsl_defaults['bslfile'] = None
        self.bsl_defaults['speed'] = BAUDS[0]
        self.bsl_defaults['cpu'] = 'Auto Select'
        self.bsl_defaults['invertrst'] = False
        self.bsl_defaults['inverttest'] = False
        self.bsl_defaults['swapresettest'] = False
        self.bsl_defaults['testontx'] = False
        self.bsl_defaults['ignoreanswer'] = False
        self.bsl_defaults['nodownloadbsl'] = False
        self.bsl_defaults['forcebsl'] = False
        self.bsl_defaults['slowmode'] = False
        self.bsl_defaults['masserase'] = False
        self.bsl_defaults['mainerase'] = False
        self.bsl_defaults['erase'] = None
        self.bsl_defaults['erasecheck'] = False
        self.bsl_defaults['program'] = False
        self.bsl_defaults['verify'] = False
        self.bsl_defaults['bslversion'] = False
        self.bsl_defaults['startaddr'] = None
        self.bsl_defaults['size'] = 2
        self.bsl_defaults['outputformat'] = 'hex'
        self.bsl_defaults['uploadfile'] = None
        self.bsl_defaults['goaddr'] = None
        self.bsl_defaults['reset'] = False
        self.bsl_defaults['wait'] = False
    
    def make_vars(self):
        """
        Creates app variables and traces
        """
        
        # variables that should only be accessed through a widget wrapper are prefixed with v_
        
        # Non option vars
        self.v_progress = IntVar()
        self.v_progress.set(0)
        
        # App info vars
        self.version = StringVar()
        self.platform = StringVar()
        
        # App vars
        self.useini = BooleanVar()
        self.logwinvisible = BooleanVar()
        self.outwinvisible = BooleanVar()
        self.warnings = BooleanVar()
        self.debuglevel = IntVar()
        self.debuglevel.trace_variable('w', lambda *args: set_debug(self.debuglevel.get()))
        
        # BSL vars
        self.v_comport = StringVar()
        set_tk_var_name(self.v_comport, 'comport')
        
        self.v_password = StringVar()
        set_tk_var_name(self.v_password, 'password')
        self.v_password.trace_variable('w', self.cb_3)
        
        self.v_filename = StringVar()
        set_tk_var_name(self.v_filename, 'filename')
        
        self.v_framesize = IntVar()
        set_tk_var_name(self.v_framesize, 'framesize')
        
        self.v_erasecycles = IntVar()
        set_tk_var_name(self.v_erasecycles, 'erasecycles')
        self.v_erasecycles.trace_variable('w', self.cb_2)
        
        self.v_unpatched = BooleanVar()
        set_tk_var_name(self.v_unpatched, 'unpatched')
        
        self.v_filetype = StringVar()
        set_tk_var_name(self.v_filetype, 'filetype')
        
        self.v_timeout = IntVar()
        set_tk_var_name(self.v_timeout, 'timeout')
        self.v_timeout.trace_variable('w', self.cb_1)
        
        self.v_bslfile = StringVar()
        set_tk_var_name(self.v_bslfile, 'bslfile')
        
        self.v_speed = IntVar()
        set_tk_var_name(self.v_speed, 'speed')
        
        self.v_cpu = StringVar()
        set_tk_var_name(self.v_cpu, 'cpu')
        
        self.v_invertrst = BooleanVar()
        set_tk_var_name(self.v_invertrst, 'invertrst')
        
        self.v_inverttest = BooleanVar()
        set_tk_var_name(self.v_inverttest, 'inverttest')
        
        self.v_swapresettest = BooleanVar()
        set_tk_var_name(self.v_swapresettest, 'swapresettest')
        
        self.v_testontx = BooleanVar()
        set_tk_var_name(self.v_testontx, 'testontx')
        
        self.v_ignoreanswer = BooleanVar()
        set_tk_var_name(self.v_ignoreanswer, 'ignoreanswer')
        
        self.v_nodownloadbsl = BooleanVar()
        set_tk_var_name(self.v_nodownloadbsl, 'nodownloadbsl')
        
        self.v_forcebsl = BooleanVar()
        set_tk_var_name(self.v_forcebsl, 'forcebsl')
        
        self.v_slowmode = BooleanVar()
        set_tk_var_name(self.v_slowmode, 'slowmode')
        
        self.v_masserase = BooleanVar()
        set_tk_var_name(self.v_masserase, 'masserase')
        
        self.v_mainerase = BooleanVar()
        set_tk_var_name(self.v_mainerase, 'mainerase')
        
        self.v_erase = StringVar()
        set_tk_var_name(self.v_erase, 'erase')
        
        self.v_erasecheck = BooleanVar()
        set_tk_var_name(self.v_erasecheck, 'erasecheck')
        
        self.v_program = BooleanVar()
        set_tk_var_name(self.v_program, 'program')
        
        self.v_verify = BooleanVar()
        set_tk_var_name(self.v_verify, 'verify')
        
        self.v_bslversion = BooleanVar()
        set_tk_var_name(self.v_bslversion, 'bslversion')
        self.v_bslversion.trace_variable('w', self.cb_3)
        
        self.v_startaddr = IntVar()
        set_tk_var_name(self.v_startaddr, 'startaddr')
        self.v_startaddr.trace_variable('w', self.cb_1)
        
        self.v_size = IntVar()
        set_tk_var_name(self.v_size, 'size')
        
        self.v_outputformat = StringVar()
        set_tk_var_name(self.v_outputformat, 'outputformat')
        
        self.v_uploadfile = StringVar()
        set_tk_var_name(self.v_uploadfile, 'uploadfile')
        
        self.v_goaddr = IntVar()
        set_tk_var_name(self.v_goaddr, 'goaddr')
        self.v_goaddr.trace_variable('w', self.cb_1)
        
        self.v_reset = BooleanVar()
        set_tk_var_name(self.v_reset, 'reset')
        self.v_reset.trace_variable('w', self.cb_1)
        
        self.v_wait = BooleanVar()
        set_tk_var_name(self.v_wait, 'wait')
        self.v_wait.trace_variable('w', self.cb_1)
    
    def make_menu(self):
        """
        Make top level menu
        """
        topmenu = Menu(self)
        self.config(menu=topmenu)
        
        # File menu
        file = Menu(topmenu, tearoff=0)
        file.add_command(label='Open config...', command=self.on_open_config)
        file.add_command(label='Save config...', command=self.on_save_config)
        file.add_command(label='Save config as...', command=self.on_save_config_as)
        file.add_command(label='Quit', command=self.on_quit)
        topmenu.add_cascade(label='File', menu=file)
        
        # Options menu
        options = Menu(topmenu, tearoff=0)
        options.add_checkbutton(label='Remember settings', variable=self.useini)
        options.add_checkbutton(label='Show log window', variable=self.logwinvisible)
        options.add_checkbutton(label='Show output window', variable=self.outwinvisible)
        options.add_checkbutton(label='Show warnings', variable=self.warnings)
        debugmenu = Menu(options, tearoff=0)
        for i in range(MAX_DEBUG + 1):
            debugmenu.add_radiobutton(label=("%s" % i), command=self.on_debug_level, variable=self.debuglevel, value=i)
        options.add_cascade(label='Debug level', menu=debugmenu)
        topmenu.add_cascade(label='Options', menu=options)
        
        # Help menu
        help = Menu(topmenu, tearoff=0)
        help.add_command(label='About', command=self.on_help)
        topmenu.add_cascade(label='Help', menu=help)
    
    def make_widgets(self):
        """
        Creates and packs the GUI widgets
        """
        self.widgets = []
        
        # Top level frames
        options_frame = Frame(self)
        options_frame.pack(side=TOP, padx=5, pady=5, expand=YES, fill=BOTH)
        
        status_frame = Frame(self)
        status_frame.pack(side=TOP, padx=5, pady=5, expand=YES, fill=BOTH)
        
        button_frame = Frame(self)
        button_frame.pack(side=TOP, padx=5, pady=5, expand=YES, fill=BOTH)
        
        # Options notebook and notebook tabs
        notebook = Notebook(options_frame)
        notebook.pack(side=TOP, padx=5, pady=5)
        
        serial_frame = Frame(notebook)
        notebook.add(serial_frame, text='Serial Port')
        
        firmware_frame = Frame(notebook)
        notebook.add(firmware_frame, text='Firmware')
        
        bsl_frame = Frame(notebook)
        notebook.add(bsl_frame, text='BSL')
        
        upload_frame = Frame(notebook)
        notebook.add(upload_frame, text='Upload')
        
        actions_frame = Frame(notebook)
        notebook.add(actions_frame, text='Actions')
        
        exit_frame = Frame(notebook)
        notebook.add(exit_frame, text='On Exit')
        
        # Serial Port Options
        self.comport = ComboSelector(serial_frame, 'Device', sscan.scan(), var=self.v_comport)
        self.widgets.append(self.comport)
        self.comport.pack(side=TOP, anchor=W, padx=5, pady=5, fill=X)
        
        self.speed = ComboSelector(serial_frame, 'Baud Rate', BAUDS, var=self.v_speed)
        self.widgets.append(self.speed)
        self.speed.pack(side=TOP, anchor=W, padx=5, pady=5, fill=X)
        
        self.invertrst = CheckButton(serial_frame, 'Invert RESET', var=self.v_invertrst)
        self.widgets.append(self.invertrst)
        self.invertrst.pack(side=TOP, anchor=W, padx=5, pady=5)
        
        self.inverttest = CheckButton(serial_frame, 'Invert TEST', var=self.v_inverttest)
        self.widgets.append(self.inverttest)
        self.inverttest.pack(side=TOP, anchor=W, padx=5, pady=5)
        
        self.swapresettest = CheckButton(serial_frame, 'Swap RESET and TEST', var=self.v_swapresettest)
        self.widgets.append(self.swapresettest)
        self.swapresettest.pack(side=TOP, anchor=W, padx=5, pady=5)
        
        self.testontx = CheckButton(serial_frame, 'TEST Toggles TX', var=self.v_testontx)
        self.widgets.append(self.testontx)
        # self.testontx.pack(side=TOP, anchor=W, padx=5, pady=5) # FIXME currently disabled, please see release notes
        
        self.slowmode = CheckButton(serial_frame, 'Slow Mode', var=self.v_slowmode)
        self.widgets.append(self.slowmode)
        self.slowmode.pack(side=TOP, anchor=W, padx=5, pady=5)
        
        self.timeout = IntEntry(serial_frame, 'Timeout', var=self.v_timeout)
        self.widgets.append(self.timeout)
        self.timeout.pack(side=TOP, anchor=W, padx=5, pady=5, fill=X)
        
        # Firmware Options
        self.filename = OpenFileEntry(firmware_frame, 'Input File', var=self.v_filename, filetypes=FIRMWARE_FILE_TYPES, initialdir=FILEINIDIR)
        self.widgets.append(self.filename)
        self.filename.pack(side=TOP, anchor=W, padx=5, pady=5, fill=X)
        
        self.filetype = RadioSelect(firmware_frame, 'File Type', FILE_TYPES, var=self.v_filetype)
        self.widgets.append(self.filetype)
        self.filetype.pack(side=TOP, anchor=W, padx=10, pady=5)
        
        self.cpu = RadioSelect(firmware_frame, 'CPU Family', CPU_TYPES, var=self.v_cpu)
        self.widgets.append(self.cpu)
        self.cpu.pack(side=TOP, anchor=W, padx=10, pady=5)
        
        # BSL Options
        self.password = OpenFileEntry(bsl_frame, 'Password File', var=self.v_password, filetypes=FIRMWARE_FILE_TYPES, initialdir=FILEINIDIR)
        self.widgets.append(self.password)
        self.password.pack(anchor=NW, padx=5, pady=5, fill=X)
        
        self.bslfile = OpenFileEntry(bsl_frame, 'BSL File', var=self.v_bslfile, filetypes=FIRMWARE_FILE_TYPES, initialdir=FILEINIDIR)
        self.widgets.append(self.bslfile)
        self.bslfile.pack(anchor=NW, padx=5, pady=5, fill=X)
        
        self.unpatched = CheckButton(bsl_frame, 'Leave BSL Unpatched', var=self.v_unpatched)
        self.widgets.append(self.unpatched)
        self.unpatched.pack(anchor=NW, padx=5, pady=5)
        
        self.ignoreanswer = CheckButton(bsl_frame, 'Ignore BSL Responses', var=self.v_ignoreanswer)
        self.widgets.append(self.ignoreanswer)
        self.ignoreanswer.pack(anchor=NW, padx=5, pady=5)
        
        self.nodownloadbsl = CheckButton(bsl_frame, 'No BSL Download', var=self.v_nodownloadbsl)
        self.widgets.append(self.nodownloadbsl)
        self.nodownloadbsl.pack(anchor=NW, padx=5, pady=5)
        
        self.forcebsl = CheckButton(bsl_frame, 'Force BSL Download', var=self.v_forcebsl)
        self.widgets.append(self.forcebsl)
        self.forcebsl.pack(anchor=NW, padx=5, pady=5)
        
        self.framesize = IntEntry(bsl_frame, 'Frame Size', var=self.v_framesize)
        self.widgets.append(self.framesize)
        self.framesize.pack(anchor=NW, padx=5, pady=5, fill=X)
        
        self.erasecycles = IntEntry(bsl_frame, 'Mass Erase Cycles', var=self.v_erasecycles)
        self.widgets.append(self.erasecycles)
        self.erasecycles.pack(anchor=NW, padx=5, pady=5, fill=X)
        
        # Upload Options
        self.startaddr = IntEntry(upload_frame, 'Upload Block Address', var=self.v_startaddr)
        self.widgets.append(self.startaddr)
        self.startaddr.pack(anchor=NW, padx=5, pady=5, fill=X)
        
        self.size = IntEntry(upload_frame, 'Upload Block Size', var=self.v_size)
        self.widgets.append(self.size)
        self.size.pack(anchor=NW, padx=5, pady=5, fill=X)
        
        self.outputformat = RadioSelect(upload_frame, 'Upload Format', UPLOAD_FORMATS, var=self.v_outputformat)
        self.widgets.append(self.outputformat)
        self.outputformat.pack(anchor=NW, padx=10, pady=5)
        
        self.uploadfile = SaveAsFileEntry(upload_frame, 'Save Upload Directly To File', var=self.v_uploadfile, filetypes=FIRMWARE_FILE_TYPES, initialdir=FILEINIDIR)
        self.widgets.append(self.uploadfile)
        self.uploadfile.pack(anchor=NW, padx=5, pady=5, fill=X)
        
        # Actions Options
        self.masserase = CheckButton(actions_frame, 'Erase All Flash Memory', var=self.v_masserase)
        self.widgets.append(self.masserase)
        self.masserase.pack(side=TOP, anchor=W, padx=5, pady=5)
        
        self.mainerase = CheckButton(actions_frame, 'Erase Main Flash Memory', var=self.v_mainerase)
        self.widgets.append(self.mainerase)
        self.mainerase.pack(side=TOP, anchor=W, padx=5, pady=5) # requires password to be set
        
        self.erase = IntRangeEntry(actions_frame, 'Erase segment or segment range', var=self.v_erase)
        self.widgets.append(self.erase)
        self.erase.pack(side=TOP, anchor=W, padx=5, pady=5, fill=X) # requires password to be set
        
        self.erasecheck = CheckButton(actions_frame, 'Erase Check By File', var=self.v_erasecheck)
        self.widgets.append(self.erasecheck)
        self.erasecheck.pack(side=TOP, anchor=W, padx=5, pady=5)
        
        self.program = CheckButton(actions_frame, 'Program File', var=self.v_program)
        self.widgets.append(self.program)
        self.program.pack(side=TOP, anchor=W, padx=5, pady=5)
        
        self.verify = CheckButton(actions_frame, 'Verify', var=self.v_verify)
        self.widgets.append(self.verify)
        self.verify.pack(side=TOP, anchor=W, padx=5, pady=5)
        
        self.bslversion = CheckButton(actions_frame, 'Read BSL Version', var=self.v_bslversion)
        self.widgets.append(self.bslversion)
        self.bslversion.pack(anchor=NW, padx=5, pady=5)
        
        # On Exit Options
        self.goaddr = IntEntry(exit_frame, 'Start Execution Address', var=self.v_goaddr)
        self.widgets.append(self.goaddr)
        self.goaddr.pack(anchor=NW, padx=5, pady=5, fill=X) #Implies wait
        
        self.wait = CheckButton(exit_frame, 'Wait', var=self.v_wait)
        self.widgets.append(self.wait)
        self.wait.pack(anchor=NW, padx=5, pady=5)
        
        self.reset = CheckButton(exit_frame, 'Reset', var=self.v_reset)
        self.widgets.append(self.reset)
        self.reset.pack(anchor=NW, padx=5, pady=5)
        
        # Progress Bar
        self.progressbar = ProgressBar(status_frame, 'BSL Progress...', var=self.v_progress, length=200)
        self.widgets.append(self.progressbar)
        self.progressbar.pack(side=TOP)
        
        # Buttons
        Button(button_frame, text='Defaults', command=self.set_defaults).pack(side=LEFT, anchor=W, padx=5, pady=5)
        Button(button_frame, text='Scan', command=self.on_serial_scan).pack(side=LEFT, anchor=W, padx=0, pady=5)
        Button(button_frame, text='Go', command=self.on_go).pack(side=RIGHT, anchor=E, padx=5, pady=5)
        # Button(button_frame, text='Print', command=self.print_vars).pack(side=LEFT, anchor=S, padx=5, pady=5) # DEBUG
    
    # Variable callback methods
    def cb_default(self, *args):
        """
        Default callback
        """
        return True
    
    def cb_1(self, *args):
        if self.enable_sanity_checks:
            timeout = self.timeout.get()
            goaddr = self.goaddr.get()
            startaddr = self.startaddr.get()
            reset = self.reset.get()
            wait = self.wait.get()
            rval = True
            
            if timeout in [0, None]:
                if goaddr != None and startaddr != None:
                    if 'goaddr' in args:
                        self.warning('Start Execution Address can not be specified if Timeout is disabled and Upload Block Address is specified!')
                    elif 'startaddr' in args:
                        self.warning('Upload Block Address can not be specified if Timeout is disabled and Start Execution Address is specified!')
                    elif 'timeout' in args:
                        self.warning('Timeout can not be disabled if Start Execution Address and Upload Block Address are both specified!')
                    elif not args:
                        self.error('Timeout can not be disabled if Start Execution Address and Upload Block Address are both specified')
                    rval = False
                elif 'goaddr' not in args and 'startaddr' not in args:
                    self.warning('Disabling the timeout can cause improper function in some cases!')
            
            if goaddr != None and reset:
                if 'goaddr' in args:
                    self.warning('Start Execution Address can not be specified if Reset is enabled!')
                elif 'reset' in args:
                    self.warning('Reset can not be enabled if Start Execution Address is specified!')
                elif not args:
                    self.error('Reset can not be enabled if Start Execution Address is specified!')
                rval = False
                    
            if startaddr != None and wait:
                if 'startaddr' in args:
                    self.warning('Upload Block Address can not be specified if Wait is enabled!')
                elif 'wait' in args:
                    self.warning('Wait can not be enabled if Upload Block Address is specified!')
                elif not args:
                    self.error('Wait can not be enabled if Upload Block Address is specified!')
                rval = False
            return rval
        else:
            return False
    
    def cb_2(self, *args):
        if self.enable_sanity_checks:
            meraseCycles = self.erasecycles.get()
            if meraseCycles < 1:
                if 'erasecycles' in args:
                    self.warning('Erase cycles must be a positive number')
                elif not args:
                    self.error('Erase cycles must be a positive number')
                return False
            elif meraseCycles > 20:
                self.warning("Erase cycles set to a large number (>20): %d" % meraseCycles)
            return True
        else:
            return False
    
    def cb_3(self, *args):
        if self.enable_sanity_checks:
            if self.bslversion.get() and not self.password.get():
                if 'password' in args or 'bslversion' in args:
                    self.warning('Unable to read BSL version without a valid password file')
                elif not args:
                    self.error('Unable to read BSL version without a valid password file')
                return False
            else:
                return True
        else:
            return False
    
    def make_callback_list(self):
        self.var_callbacks = []
        self.var_callbacks.append(self.cb_1)
        self.var_callbacks.append(self.cb_2)
        self.var_callbacks.append(self.cb_3)
    
    def sanity_check_options(self):
        rval = True
        for callback in self.var_callbacks:
                if not callback():
                    rval = False
        return rval
    
    def initialize_widgets(self, *args):
        # testontx currently DOES NOT work because it relies on 
        # serial.win32file provided by pySerial releases OLDER than 2.5.
        # pySerial releases 2.5 and later on windows no longer rely on pywin32
        # and therefore do not provide serial.win32file!
        self.testontx.set(False)
        self.testontx.disable()
    
    def print_vars(self):
        """
        Prints current app variable values to the log
        """
        for keys in [self.app_info.keys(), self.app_defaults.keys(), self.bsl_defaults.keys()]:
            for opt in keys:
                try:
                    val = self.get_val(opt)
                    if type(val) == str:
                        val = "'%s'" % val
                    self.log.write("self.%s = %s\n" % (opt, val))
                except:
                    self.log.write("Error (%s): Couldn't get value for variable\n" % opt)
        self.log.write('\n')
    
    def set_defaults(self):
        """
        Initializes default GUI values
        """
        self.disable_popups()
        for opt_dict in [self.app_info.items(), self.app_defaults.items(), self.bsl_defaults.items()]:
            for opt, val in opt_dict:
                try:
                    self.set_val(opt, val)
                except tkExtrasError, err:
                    if opt == 'comport': # there is no comport default value that makes sense
                        pass
                    else:
                        raise err
        self.enable_popups()
    
    def check_config_version(self, version):
        if version > VERSION:
            return False
        else:
            return True
    
    def load_config(self, filename):
        """
        Loads a saved configuration from a file
        """
        self.log.write("Loading saved config from %s..." % filename)
        # Save the current settings
        opts_list = [(BSL_OPTS, self.bsl_defaults.keys()), (APP_OPTS, self.app_defaults.keys())]
        current_settings = {BSL_OPTS:{}, APP_OPTS:{}}
        for section, opts in opts_list:
            for opt in opts:
                current_settings[section][opt] = self.get_val(opt)
        # Load new settings from file
        cfg = ConfigParser.RawConfigParser()
        cfg.read(filename)
        info = cfg.items(INFO_OPTS)
        for key, value in info:
            value = value.strip("'") # strip the enclosing ' on 'value'
            if key == 'version':
                if not self.check_config_version(value):
                    self.log.write('FAIL\n')
                    self.error("Configuration file can not be opened! Configuration file version (%s) is not supported by this release (%s)" % (value, VERSION))
                    return False
            elif key == 'platform':
                pass # not checked
        self.disable_popups()
        for opts in [APP_OPTS, BSL_OPTS]:
            for opt, val in cfg.items(opts):
                if val.startswith("'") and val.endswith("'"):
                    val = val[1:-1]
                else:
                    val = eval(val)
                try:
                    self.set_val(opt, val)
                except tkExtrasError, err:
                    if opt == 'comport':
                        pass
                    else:
                        raise err
        # If the new settings will cause errors, ask to revert back to the old settings
        if not self.sanity_check_options():
            if askyesno('Error', 'The new configuration settings will result in errors on "Go"! Would you like to view the error messages?'):
                self.enable_popups()
                self.sanity_check_options()
            if not askyesno('Error', 'Do you still wish to load these configuration options?'):
                self.disable_popups()
                for section, opts in opts_list:
                    for opt in opts:
                        self.set_val(opt, current_settings[section][opt])
                self.enable_popups()
                self.log.write('FAIL\n')
                return False
        self.enable_popups()
        self.log.write('SUCCESS\n')
        if DEBUG:
            for key, value in info:
                self.log.write("Config file %s: %s\n" % (key, value))
        return True
    
    def write_config(self, filename):
        """
        Writes the current configuration to a file
        """
        # Check if the current options will generate errors
        self.disable_popups()
        if not self.sanity_check_options():
            self.enable_popups()
            if askyesno('Error', 'The current configuration settings will result in errors on "Go"! Would you like to view the error messages?'):
                self.sanity_check_options()
            if not askyesno('Error', "Do you still want to save these configuration settings to %s?" % filename):
                self.log.write('FAIL\n')
                return False
        # If it's ok to save, then actually save the config to file
        self.enable_popups()
        self.log.write("Saving config to %s..." % filename)
        opts_list = [(BSL_OPTS, self.bsl_defaults.keys()), (APP_OPTS, self.app_defaults.keys()), (INFO_OPTS, self.app_info.keys())]
        cfg = ConfigParser.RawConfigParser()
        for section, opts in opts_list:
            cfg.add_section(section)
            for opt in opts:
                val = self.get_val(opt)
                if type(val) in [str, unicode]:
                    val = "'%s'" % val
                cfg.set(section, opt, val)
        try:
            cfgfile = open(filename, 'w')
            cfg.write(cfgfile)
            cfgfile.close()
        except(IOError):
            self.log.write('FAIL\n')
            self.error("Could not save configuration to %s\n" % filename)
        self.log.write('SUCCESS\n')
        return True
    
    def on_open_config(self, *args):
        """
        Prompts the user for a filename
        """
        filename = askopenfilename(filetypes=CONFIG_FILE_TYPES, initialdir=FILEINIDIR)
        if filename:
            self.configfile = filename
            self.load_config(self.configfile)
    
    def on_save_config(self, *args):
        """
        Saves the current configuration to the config file
        """
        if self.configfile == '':
            self.on_save_config_as()
        else:
            if askyesno('Save', "Are you sure you want to save configuration to %s?" % self.configfile):
                self.write_config(self.configfile)
    
    def on_save_config_as(self, *args):
        """
        Prompts the user for a file to save the current configuration into
        """
        filename = asksaveasfilename(filetypes=CONFIG_FILE_TYPES, defaultextension=CONFIG_EXT, initialdir=FILEINIDIR)
        if filename:
            self.configfile = filename
            self.write_config(self.configfile)
    
    def on_help(self, *args):
        """
        Displays the 'Help' window
        """
        showinfo("About", "%s\nVersion: %s\n%s\n%s" % (DESCRIPTION, VERSION, COPYRIGHT, URL))
    
    def on_serial_scan(self, *args):
        """
        Update available serial ports
        """                                                                         
        if self.warnings.get():
            if not askyesno('Warning', 'This will attempt to open and close all serial ports on this system.  This has the potential to reset devices connected to the serial port.  Do you wish to proceed?'):
                return
        self.log.write('Scanning for available serial ports...')
        comports = sscan.scan()
        self.log.write('SUCCESS\n')
        if comports:
            for comport in comports:
                self.log.write("%s\n" % comport)
        else:
            self.log.write('No available serial ports.\n')
        self.comport.update(comports)
    
    def on_debug_level(self, *args):
        """
        Writes the current debug level to the log
        """
        self.log.write("Debug level set to %d\n" % self.debuglevel.get())
    
    def on_quit(self, *args):
        """
        Quits the app and optionally saves the configuration
        """
        if self.useini.get():
            if not self.write_config(INIFILE):
                if askyesno('Error', 'Would you like to discard all current settings and quit anyway?'):
                    if os.path.isfile(INIFILE):
                        os.remove(INIFILE)
                else:
                    return
        elif os.path.isfile(INIFILE):
            os.remove(INIFILE)
        self.quit()
    
    # Most of the bsl logic below is adapted from msp430-bsl.py by Chris Liechti
    def on_go(self, *args):
        try:
            
            if self.running:
                return
            else:
                if not self.sanity_check_options():
                    return
                self.running = True
            
            # Initialize BSL variables
            bslobj = None
            warnings = self.warnings.get()
            wait = self.wait.get()
            maxData = self.framesize.get()
            meraseCycles = self.erasecycles.get()
            masserase = self.masserase.get()
            mainerase = self.mainerase.get()
            erasecheck = self.erasecheck.get()
            program = self.program.get()
            verify = self.verify.get()
            reset = self.reset.get()
            goaddr = self.goaddr.get()
            unpatched = self.unpatched.get()
            startaddr = self.startaddr.get()
            size = self.size.get()
            invertrst = self.invertrst.get()
            inverttest = self.inverttest.get()
            forcebsl = self.forcebsl.get()
            slowmode = self.slowmode.get()
            swapresettest = self.swapresettest.get()
            testontx = self.testontx.get()
            ignoreanswer = self.ignoreanswer.get()
            uploadfile = self.uploadfile.get()
            bslversion = self.bslversion.get()
            
            timeout = self.timeout.get()
            if not timeout:
                timeout = 0
            
            comPort = self.comport.get()
            if comPort.startswith('COM'):
                try:
                    comPort = int(comPort.lstrip('COM'), 0) - 1
                except ValueError:
                    raise AppError('Invalid COM port\n')
            
            password = self.password.get()
            if password == '':
                password = None
            elif not os.path.isfile(password):
                self.password.focus()
                raise AppError('Invalid password file\n')
            
            erase = self.erase.get()
            if erase:
                if '-' in erase:
                    str1, str2 = erase.split('-', 1)
                    adr1 = int(str1, 0)
                    adr2 = int(str2, 0)
                else:
                    adr1 = int(erase, 0)
                    adr2 = None
            else:
                adr1 = None
                adr2 = None
            
            outputformat = self.outputformat.get()
            if outputformat == 'hex':
                outputformat = HEX
            elif outputformat == 'bin':
                outputformat = BINARY
            elif outputformat == 'ihex':
                outputformat = INTELHEX
            else:
                raise AppError('Invalid output format\n')
            
            filetype = self.filetype.get()
            if filetype == 'Auto Select':
                filetype = None
            elif filetype == 'IntelHex':
                filetype = 0
            elif filetype == 'TI-Text':
                filetype = 1
            else:
                raise AppError('Invalid firmware file type\n')
            
            bslfile = self.bslfile.get()
            if bslfile == '':
                bslfile = None
            elif not os.path.isfile(bslfile):
                raise AppError('Invalid BSL file\n')
            
            speed = self.speed.get()
            if speed not in BAUDS:
                raise AppError("Unspported baud rate: %d\nSupported baud rates: %s" % (speed, BAUDS))
            
            cpu = self.cpu.get()
            if cpu == 'Auto Select':
                cpu = None
            elif cpu == 'F1x':
                cpu = bsl.F1x
            elif cpu == 'F4x':
                cpu = bsl.F4x
            else:
                raise AppError('Invalid device type\n')
            
            mayusebsl = not self.nodownloadbsl.get()
            
            filename = self.filename.get()
            if filename == '':
                filename = None
            elif filename == '-': # FIXME
                pass
            elif program and not os.path.isfile(filename):
                raise AppError('Invalid firmware input file\n')
            
            # BSL Init
            self.log.write("%s Version: %s\n" % (DESCRIPTION, VERSION))
            if DEBUG:
                self.log.write("Debug level set to %d\n" % DEBUG)
                self.log.write("Python version: %s\n" % sys.version)
                self.log.write("Tcl version: %s\n" % TclVersion)
                self.log.write("Tk version: %s\n" % TkVersion)
            
            bslobj = UpdatingBootStrapLoader(progress_obj=self.progressbar)
            bslobj.showprogress = 1
            toinit = []
            todo = []
            
            if timeout:
                bslobj.timeout = timeout
                if DEBUG: self.log.write("Timeout set to %d.\n" % timeout)
            
            if password:
                bslobj.passwd = memory.Memory(password).getMemrange(0xffe0, 0xffff)
                if DEBUG: self.log.write("Using password file: %s.\n" % password)
            
            # Make sure that conditions for maxData are met:
            # ( >= 16 and == n*16 and <= MAX_DATA_BYTES!)
            if maxData > bsl.BootStrapLoader.MAX_DATA_BYTES:
                maxData = bsl.BootStrapLoader.MAX_DATA_BYTES
            elif maxData < 16:
                maxData = 16
            bslobj.maxData = maxData - (maxData % 16)
            if DEBUG: self.log.write("Max. number of data bytes within one frame set to %d.\n" % maxData)
            
            bslobj.meraseCycles = meraseCycles
            if DEBUG: self.log.write("Number of mass erase cycles set to %d.\n" % meraseCycles)
            
            if masserase:
                toinit.append(bslobj.actionMassErase) # Erase entire Flash
            
            if mainerase:
                toinit.append(bslobj.actionMainErase) # Erase main Flash
            
            if adr1:
                if adr2:
                    while adr1 <= adr2:
                        if adr1 < 0x1100:
                            modulo = 64 # F2xx:64: F1xx, F4xx: 128 (segments get erased twice)
                        elif adr1 < 0x1200:
                            modulo = 256
                        else:
                            modulo = 512
                        adr1 = adr1 - (adr1 % modulo)
                        toinit.append(bslobj.makeActionSegmentErase(adr1))
                        adr1 = adr1 + modulo
                else:
                    toinit.append(bslobj.makeActionSegmentErase(adr1))
            
            if erasecheck:
                toinit.append(bslobj.actionEraseCheck) # Erase Check (by file)
            
            if program:
                todo.append(bslobj.actionProgram) # Program file
            
            if verify:
                todo.append(bslobj.actionVerify) # Verify file
            
            if bslfile:
                bslrepl = memory.Memory() # File to program
                bslrepl.loadFile(bslfile)
            else:
                bslrepl = None
            
            if bslversion:
                todo.append(bslobj.actionReadBSLVersion) # load replacement BSL as first item
            
            if cpu:
                bslobj.cpu = cpu
            
            bslobj.invertRST = invertrst
            
            bslobj.invertTEST = inverttest
            
            bslobj.slowmode = slowmode
            
            bslobj.swapResetTest = swapresettest
            
            bslobj.testOnTX = testontx
            
            bslobj.ignoreAnswer = ignoreanswer
            
            if toinit:
                if DEBUG > 0:
                    # show a nice list of sheduled actions
                    self.log.write('TOINIT list:\n')
                    for f in toinit:
                        try:
                            self.log.write("   %s\n" % f.func_name)
                        except AttributeError:
                           self.log.write("   %r\n" % f)
            if todo:
                if DEBUG > 0:
                    # show a nice list of sheduled actions
                    self.log.write('TODO list:\n')
                    for f in todo:
                        try:
                            self.log.write("   %s\n" % f.func_name)
                        except AttributeError:
                            self.log.write("   %r\n" % f)
            
            # prepare data to download
            bslobj.data = memory.Memory() # prepare downloaded data
            if filename is not None: # if the filename is given...
                file = open(filename, 'rb') # or from a file
                if filetype is not None:
                    if filetype == 0: # select load function
                        bslobj.data.loadIHex(file) # intel hex
                    elif filetype == 1:
                        bslobj.data.loadTIText(file) # TI's format
                    else:
                        raise ValueError('Illegal filetype specified')
                else: # no filetype given...
                    bslobj.data.loadFile(filename) # autodetect otherwise
            if DEBUG > 3: self.log.write("File: %r" % filename)
            
            bslobj.comInit(comPort) # init port
            
            # initialization list
            if toinit: # erase and erase check
                if DEBUG: self.log.write('Preparing device ...\n')
                # bslobj.actionStartBSL(usepatch=0, adjsp=0) # no workarounds needed
                # if speed: bslobj.actionChangeBaudrate(speed) # change baud rate as fast as possible
                for f in toinit: f()
            
            if todo or goaddr or startaddr:
                if DEBUG: self.log.write('Actions ...\n')
                # connect to the BSL
                bslobj.actionStartBSL(
                    usepatch=not unpatched,
                    replacementBSL=bslrepl,
                    forceBSL=forcebsl,
                    mayuseBSL=mayusebsl,
                    speed=speed,
                )
            
            # work list
            if todo:
                for f in todo: f() # work through todo list
            
            if reset: # reset device first if desired
                bslobj.actionReset()
            
            if goaddr is not None: # start user programm at specified address
                bslobj.actionRun(goaddr) # load PC and execute
            
            # upload datablock and output
            if startaddr is not None:
                if goaddr: # if a program was started...
                    # don't restart BSL but wait for the device to enter it itself
                    if DEBUG: self.log.write('Waiting for device to reconnect for upload: ')
                    bslobj.txPasswd(bslobj.passwd, wait=1) # synchronize, try forever...
                    data = bslobj.uploadData(startaddr, size) # upload data
                else:
                    data = bslobj.uploadData(startaddr, size) # upload data
                if outputformat == HEX: # depending on output format
                    if uploadfile:
                        self.log.write("Uploading hex data to %s..." % uploadfile)
                        f = open(uploadfile, 'wb')
                        hexdump((startaddr, data), output=f)
                        f.close()
                        self.log.write('SUCCESS\n')
                    else:
                        if DEBUG: self.log.write('Uploading hex data to output window...')
                        hexdump((startaddr, data), output=self.out)
                        if DEBUG: self.log.write('SUCCESS\n')
                elif outputformat == INTELHEX:
                    if uploadfile:
                        self.log.write("Uploading ihex data to %s..." % uploadfile)
                        f = open(uploadfile, 'wb')
                        makeihex((startaddr, data), output=f)
                        f.close()
                        self.log.write('SUCCESS\n')
                    else:
                        if DEBUG: self.log.write('Uploading ihex data to output window...')
                        makeihex((startaddr, data), output=self.out)
                        if DEBUG: self.log.write('SUCCESS\n')
                else:
                    if uploadfile:
                        self.log.write("Uploading binary data to %s..." % uploadfile)
                        f = open(uploadfile, 'wb')
                        f.write(data)
                        f.close()
                        self.log.write('SUCCESS\n')
                    else:
                        if DEBUG: self.log.write('Uploading binary data to output window...')
                        self.out.write(data) #binary output w/o newline!
                        if DEBUG: self.log.write('SUCCESS\n')
            
            if wait: # wait at the end if desired
                showinfo('Wait', "Press 'OK' to continue...")
                
            if bslobj:
                bslobj.comDone() # Release serial communication port
        
        except serial.SerialException, err:
            self.log.write('\n')
            self.logged_error("%s\n" % err)
        except bsl.BSLException, err:
            if bslobj:
                bslobj.comDone() # Release serial communication port
            self.log.write('\n')
            self.logged_error("%s\n" % err)
        except AppError, err:
            self.log.write('\n')
            self.logged_error("%s\n" % err)
        finally:
            self.progressbar.reset()
            self.log.write('Done.\n')
            self.running = False
    

def main():
    app = AppMainWindow()
    app.mainloop()
    return 0

if __name__ == '__main__':
    sys.exit(main())
