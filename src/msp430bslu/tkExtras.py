#!/usr/bin/env python
#
# Enhanced widget-like classes built from Tkinter/ttk widgets
#
# (C) 2009-2010 Flying Camp Design
#
# All Rights Reserved.
#
# AUTHOR: Chris Wilson <cwilson@flyingcampdesign.com>
#
# Released under a BSD-style license (please see LICENSE)

# TODO change hard coded background color for osx to use system background color

import os
import glob
import platform
from Tkinter import *
from ttk import *
from tkMessageBox import *
from tkFileDialog import *
from ScrolledText import ScrolledText
from tkSimpleDialog import askstring

__version__ = '1.0.0'

FONT    = 'TkFixedFont'
PLATFORM = platform.platform()
WINDOWS = PLATFORM.lower().startswith('windows')
DARWIN = PLATFORM.lower().startswith('darwin')
LINUX = PLATFORM.lower().startswith('linux')

# Platform dependent initialization
if WINDOWS:
    THEME = 'xpnative'
elif LINUX:
    THEME = 'alt'
elif DARWIN:
    THEME = 'aqua'
    winGrey = 'grey91'
else:
    raise Exception("Platform %s not supported" % PLATFORM)

class tkExtrasError(Exception):
    pass

# Adapted from 'Programming Python' by Mark Lutz
class _window:
    """
    mixin shared by main and popup windows
    """
    foundicon = None                                       # shared by all inst
    iconpatt  = '*.ico'                                    # may be reset
    iconmine  = 'py.ico'
    
    def config_borders(self, app, kind, iconfile):
        self.style = Style()
        self.style.theme_use(THEME)
        self.style.configure('TLabelframe', labeloutside='false')
        if DARWIN: # this is a hack to make the background color match on OSX
            self.config(bg=winGrey,highlightbackground=winGrey)
        if not os.path.isfile(iconfile):                   # no icon passed?
            iconfile = self.find_icon()                    # try curr,tool dirs
        title = app
        if kind: title += ' - ' + kind
        self.title(title)                                  # on window border
        self.iconname(app)                                 # when minimized
        if iconfile:
            try:
                self.iconbitmap(iconfile)                  # window icon image
            except:                                        # bad py or platform
                pass
    
    def find_icon(self):
        if _window.foundicon:                              # already found one?
            return _window.foundicon
        iconfile  = None                                   # try curr dir auto
        iconshere = glob.glob(self.iconpatt)               # assume just one
        if iconshere:                                      # del icon for red Tk
            iconfile = iconshere[0]                        
        else:                                              # try tools dir icon
            mymod  = __import__(__name__)                  # import self for dir
            path   = __name__.split('.')                   # poss a package path
            for mod in path[1:]:                           # follow path to end
                mymod = getattr(mymod, mod)
            mydir  = os.path.dirname(mymod.__file__)
            myicon = os.path.join(mydir, self.iconmine)    # use myicon, not tk
            if os.path.exists(myicon): iconfile = myicon
        _window.foundicon = iconfile                       # dont search again
        return iconfile
    

# Adapted from 'Programming Python' by Mark Lutz
class MainWindow(Tk, _window):
    """
    when run in main toplevel window
    """
    def __init__(self, title='', kind='', iconfile=None):
        Tk.__init__(self)
        self._title = title
        self.config_borders(title, kind, iconfile)
        if WINDOWS:
            self.bind('<Alt-F4>', self.on_quit)
        elif DARWIN:
            self.bind('<Command-q>', self.on_quit)
        self.protocol('WM_DELETE_WINDOW', self.on_quit)    # dont close silent
    
    def quit(self):
        if self.okay_to_quit():                            # threads running?
            self.destroy()
        else:
            showinfo(self._title, 'Quit not allowed')      # or in okay_to_quit?
    
    def destroy(self, *args):                              # exit app silently
        Tk.quit(self)                                      # redef if exit ops
    
    def on_quit(self, *args):
        self.quit()
    
    def okay_to_quit(self):                                # redef me if used
        return True                                        # e.g., thread busy
    

# Adapted from 'Programming Python' by Mark Lutz
class PopupWindow(Toplevel, _window):
    """
    when run in a secondary pop-up window
    """
    def __init__(self, title='', kind='', iconfile=None):
        Toplevel.__init__(self)
        self._title = title
        self.config_borders(title, kind, iconfile)
        self.protocol('WM_DELETE_WINDOW', self.on_close)
        if WINDOWS:
            self.bind('<Alt-F4>', self.on_close)
        elif DARWIN:
            self.bind('<Command-w>', self.on_close)
    
    def on_close(self, *args):
        self.destroy()
    
    def destroy(self, *args):
        Toplevel.destroy(self)
    

# Adapted from 'Programming Python' by Mark Lutz
class PopupScrolledText(PopupWindow):
    """
    Scrolled text output window with 'Save As...'
    """
    def __init__(self, title='', kind='', iconfile=None, var=None):
        PopupWindow.__init__(self, title=title, kind=kind, iconfile=iconfile)
        if var:
            self._var = var
        else:
            self._var = BooleanVar()
        self._var.trace_variable('w', self._visibility_control)
        self._text = ScrolledText(self)
        self._text.pack()
        self._text.config(font=FONT)
        self._make_menu()
        self._visibility_control()
    
    def on_close(self, *args):
        self._var.set(False)
    
    def _visibility_control(self, *args):
        if self._var.get():
            self.deiconify()
        else:
            self.withdraw()
    
    def _make_menu(self):
        topmenu = Menu(self)
        self.config(menu=topmenu)
        file = Menu(topmenu, tearoff=0)
        file.add_command(label='Save as...', command=self.on_save_as)
        file.add_command(label='Hide', command=self.on_close)
        topmenu.add_cascade(label='File', menu=file)
        edit = Menu(topmenu, tearoff=0)
        edit.add_command(label='Clear text', command=self.on_clear)
        topmenu.add_cascade(label='Edit', menu=edit)
    
    def on_save_as(self):
        filename = asksaveasfilename()
        if filename:
            alltext = self.gettext()
            f = open(filename, 'w')
            f.write(alltext)
            f.close()
    
    def on_clear(self):
        self._text.delete('0.0', END)
        self._text.update()
    
    def gettext(self):
        return self._text.get('1.0', END+'-1c')
    
    def hide(self):
        self._var.set(False)
    
    def show(self):
        self._var.set(True)
    

# Adapted from 'Programming Python' by Mark Lutz
class PopupGuiOutput(PopupScrolledText):
    """
    File-like GUI output window
    """
    def __init__(*args, **kwargs):
        PopupScrolledText.__init__(*args, **kwargs)
    
    def write(self, text):
        if self._text != None:
            self._text.insert(END, str(text))
            self._text.see(END)
            self._text.update()
    
    def writelines(self, lines):                 # lines already have '\n'
        for line in lines: self.write(line)      # or map(self.write, lines)
    
    def flush(self):
        if self._text != None:
            self._text.update()
    

# Adapted from 'Programming Python' by Mark Lutz
class PopupGuiInput():
    """
    File-like GUI input window
    """
    def __init__(self):
        self._buff = ''
    
    def input_line(self):
        line = askstring('Input', 'Enter input line + <crlf> (cancel=eof)')
        if line == None:
            return ''
        else:
            return line + '\n'
    
    def read(self, bytes=None):
        if not self._buff:
            self._buff = self.input_line()
        if bytes:
            text = self._buff[:bytes]
            self._buff = self._buff[bytes:]
        else:
            text = ''
            line = self._buff
            while line:
                text = text + line
                line = self.input_line()
        return text    
    
    def readline(self):
        text = self._buff or self.input_line()
        self._buff = ''
        return text
    
    def readlines(self):
        lines = []
        while 1:
            next = self.readline()
            if not next: break
            lines.append(next)
        return lines
    

class LabeledEntry(Frame):
    """
    Labeled entry form
    """
    def __init__(self, parent=None, label=None, **kwargs):
        Frame.__init__(self, parent)
        if label:
            self._label = Label(self, text=label)
            self._label.pack(side=TOP, anchor=W)
        self._entry = Entry(self, **kwargs)
        self._entry.pack(side=LEFT, anchor=W, expand=YES, fill=X)
    
    def get(self):
        return self._entry.get()
    
    def set(self, val):
        self._entry.delete(0, END)
        self._entry.insert(0, val)
    
    def focus(self):
        self._entry.focus_set()
    
    def enable(self):
        self._entry.config(state=NORMAL)
    
    def disable(self):
        self._entry.config(state=DISABLED)
    

class StringEntry(LabeledEntry):
    """
    Labeled string entry form
    """
    def __init__(self, parent=None, label=None, var=None):
        if var:
            self._var = var
        else:
            self._var = StringVar()
        LabeledEntry.__init__(self, parent, label, validate='focusout', validatecommand=self.validate)
    
    def get(self):
        if self.validate():
            return self._var.get()
        else:
            raise tkExtrasError('Error: Unable to get value')
    
    def set(self, val):
        if val in [None, '']:
            self._var.set('')
            LabeledEntry.set(self, '')
        elif type(val) in [str, unicode]:
            self._var.set(val)
            LabeledEntry.set(self, val)
        else:
            raise tkExtrasError("Error: Unable to set entry (%s is not a valid 'str')" % val)
    
    def validate(self):
        val = LabeledEntry.get(self)
        if self._var.get() != val:
            self._var.set(val)
        return True
    

class IntEntry(LabeledEntry):
    """
    Labeled integer entry form
    """
    def __init__(self, parent=None, label=None, var=None):
        if var:
            self._var = var
        else:
            self._var = IntVar()
        self._none = True
        LabeledEntry.__init__(self, parent, label, validate='focusout', validatecommand=self.validate)
    
    def get(self):
        if self.validate():
            if LabeledEntry.get(self) == '':
                return None
            else:
                return self._var.get()
        else:
            raise tkExtrasError('Error: Unable to get value')
    
    def set(self, val):
        if val in [None, '']:
            self._var.set(0)
            LabeledEntry.set(self, '')
            self._none = True
        elif type(val) is int:
            self._var.set(val)
            LabeledEntry.set(self, val)
            self._none = False
        else:
            raise tkExtrasError("Error: Unable to set entry (%s is not type 'int')" % val)
    
    def validate(self):
        val = LabeledEntry.get(self)
        if val == '':
            if not self._none:
                self._var.set(0)
                self._none = True
            return True
        else:
            try:
                ival = int(val, 0)
                if ival == 0 and self._none:
                    self._var.set(0)
                    self._none = False
                elif self._var.get() != ival:
                    self._var.set(ival)
                    self._none = False
                return True
            except ValueError, error:
                showerror('Error', error)
                self.focus()
                return False
    

class FloatEntry(LabeledEntry):
    """
    Labeled float entry form
    """
    def __init__(self, parent=None, label=None, var=None):
        if var:
            self._var = var
        else:
            self._var = DoubleVar()
        self._none = True
        LabeledEntry.__init__(self, parent, label, validate='focusout', validatecommand=self.validate)
    
    def get(self):
        if self.validate():
            if LabeledEntry.get(self) == '':
                return None
            else:
                return self._var.get()
        else:
            raise tkExtrasError('Error: Unable to get value')
    
    def set(self, val):
        if val in [None, '']:
            self._var.set(0)
            LabeledEntry.set(self, '')
            self._none = True
        elif type(val) is float:
            self._var.set(val)
            LabeledEntry.set(self, val)
            self._none = False
        else:
            raise tkExtrasError("Error: Unable to set entry (%s is not type 'float')" % val)
    
    def validate(self):
        val = LabeledEntry.get(self)
        if val == '':
            if not self._none:
                self._var.set(0)
                self._none = True
            return True
        else:
            try:
                fval = float(val)
                if fval == 0 and self._none:
                    self._var.set(0)
                    self._none = False
                elif self._var.get() != fval:
                    self._var.set(fval)
                    self._none = False
                return True
            except ValueError, error:
                showerror('Error', error)
                self.focus()
                return False
    

class IntRangeEntry(StringEntry):
    """
    Labeled integer range entry form (i.e. 'int1 - int2')
    """
    def __init__(self, parent=None, label=None, var=None):
        if var:
            self._var = var
        else:
            self._var = StringVar()
        StringEntry.__init__(self, parent, label, var)
    
    def get(self):
        if self.validate():
            return LabeledEntry.get(self)
        else:
            raise tkExtrasError('Error: Unable to get value')
    
    def set(self, val):
        if val in [None, '']:
            self._var.set('')
            StringEntry.set(self, '')
        elif type(val) not in [str, unicode]:
            raise tkExtrasError("Error: Unable to set entry (%s is not a valid 'str')" % val)
        else:
            try:
                if '-' in val:
                    str1, str2 = val.split('-', 1)
                    int(str1, 0)
                    int(str2, 0)
                else: # '-' not in val
                    int(val, 0)
            except ValueError, error:
                raise tkExtrasError("Error: Unable to set entry (cannot convert values in %s to type 'int')" % val)
            else:
                StringEntry.set(self, val)
    
    def validate(self):
        val = LabeledEntry.get(self)
        if self._var.get() == val:
            return True
        else:
            if val == '':
                self._var.set(val)
                return True
            else:
                try:
                    if '-' in val:
                        str1, str2 = val.split('-', 1)
                        int(str1, 0)
                        int(str2, 0)
                    else: # '-' not in val
                        int(val, 0)
                except (TypeError, ValueError), error:
                    showerror('Error', error)
                    self.focus()
                    return False
                else:
                    self._var.set(val)
                    return True
    

class FloatRangeEntry(StringEntry):
    """
    Labeled float range entry form (i.e. 'float1 - float2')
    """
    def __init__(self, parent=None, label=None, var=None):
        if var:
            self._var = var
        else:
            self._var = StringVar()
        StringEntry.__init__(self, parent, label, var)
    
    def get(self):
        if self.validate():
            return LabeledEntry.get(self)
        else:
            raise tkExtrasError('Error: Unable to get value')
    
    def set(self, val):
        if val in [None, '']:
            self._var.set('')
            StringEntry.set(self, '')
        elif type(val) not in [str, unicode]:
            raise tkExtrasError("Error: Unable to set entry (%s is not a valid 'str')" % val)
        else:
            try:
                if '-' in val:
                    str1, str2 = val.split('-', 1)
                    float(str1)
                    float(str2)
                else: # '-' not in val
                    float(val)
            except ValueError, error:
                raise tkExtrasError("Error: Unable to set entry (cannot convert values in %s to type 'float')" % val)
            else:
                StringEntry.set(self, val)
    
    def validate(self):
        val = LabeledEntry.get(self)
        if self._var.get() == val:
            return True
        else:
            if val == '':
                self._var.set(val)
                return True
            else:
                try:
                    if '-' in val:
                        str1, str2 = val.split('-', 1)
                        float(str1)
                        float(str2)
                    else: # '-' not in val
                        float(val)
                except (TypeError, ValueError), error:
                    showerror('Error', error)
                    self.focus()
                    return False
                else:
                    self._var.set(val)
                    return True
    

class LabeledButtonEntry(StringEntry):
    """
    Labeled string entry form with button
    """
    def __init__(self, parent=None, label=None, buttonText=None, var=None):
        StringEntry.__init__(self, parent, label, var)
        self._button = Button(self, text=buttonText, command=self._on_press)
        self._button.pack(side=RIGHT, anchor=E)
    
    def _on_press(self):
        pass
    
    def enable(self):
        StringEntry.enable(self)
        self._button.config(state=NORMAL)
    
    def disable(self):
        StringEntry.disable(self)
        self._button.config(state=DISABLED)
    

# No validate() method; File validity should be checked on open()
class OpenFileEntry(LabeledButtonEntry):
    """
    'Open...' file entry form
    """
    def __init__(self, parent=None, label=None, var=None, **kwargs):
        LabeledButtonEntry.__init__(self, parent, label, 'Open...', var)
        self.open_args = kwargs
    
    def _on_press(self):
        self.set(askopenfilename(**self.open_args))
    

# No validate() method; File validity should be checked on open()
class SaveAsFileEntry(LabeledButtonEntry):
    """
    'Save as...' file entry form
    """
    def __init__(self, parent=None, label=None, var=None, **kwargs):
        LabeledButtonEntry.__init__(self, parent, label, 'Save As...', var)
        self.save_args = kwargs
    
    def _on_press(self):
        self.set(asksaveasfilename(**self.save_args))
    

class CheckButton(Frame):
    """
    Check button entry form
    """
    def __init__(self, parent=None, text=None, var=None):
        Frame.__init__(self, parent)
        if var:
            self._var = var
        else:
            self._var = BooleanVar()
        self._cb = Checkbutton(self, text=text, variable=self._var)
        self._cb.pack()
    
    def get(self):
        return bool(self._var.get())
    
    def set(self, val):
        if type(val) is bool:
            self._var.set(val)
        else:
            raise tkExtrasError("Error: Unable to set check button (%s is not type 'bool')" % val)
    
    def enable(self):
        self._cb.config(state=NORMAL)
    
    def disable(self):
        self._cb.config(state=DISABLED)
    
    def focus(self):
        self._cb.focus_set()
    

class RadioSelect(LabelFrame):
    """
    Multiple choice radio button selection form
    """
    def __init__(self, parent=None, text=None, options=[], var=None):
        LabelFrame.__init__(self, parent, text=text)
        if var:
            self._var = var
        else:
            self._var = StringVar()
        self._radiobuttons = []
        self._values = []
        for option in options:
            rb = Radiobutton(self, text=option, value=option, variable=self._var)
            self._radiobuttons.append(rb)
            self._values.append(option)
            rb.pack(anchor=W)
    
    def get(self):
        return self._var.get()
    
    def set(self, val):
        if val in self._values:
            self._var.set(val)
        else:
            raise tkExtrasError("Error: Value %s is not a valid radio button option" % val)
    
    def enable(self):
        for option in self._radiobuttons:
            option.config(state=NORMAL)
    
    def disable(self):
        for option in self._radiobuttons:
            option.config(state=DISABLED)
    
    def focus(self):
        self.focus_set()
    

class ProgressBar(Frame):
    """
    Progress bar visual status indicator
    """
    def __init__(self, parent=None, label=None, var=None, orient=None, length=None):
        Frame.__init__(self, parent)
        self._parent = parent
        if label:
            self._label = Label(self, text=label)
            self._label.pack(side=TOP, anchor=W)
        if var:
            self._var = var
        else:
            self._var = IntVar()
        self._pbar = Progressbar(self, variable=self._var, mode='determinate', orient=orient, length=length)
        self._pbar.pack(side=LEFT, anchor=W)
    
    def get(self):
        return self._var.get()
    
    def set(self, count, total=100):
        if type(count) is not int:
            raise tkExtrasError("Error: Unable to set entry (%s is not type 'int')" % count)
        elif type(total) is not int:
            raise tkExtrasError("Error: Unable to set entry (%s is not type 'int')" % total)
        else:
            self._var.set(count)
            self._pbar.configure(maximum=total)
            self._parent.update()
    
    def reset(self):
        self.set(0)
    

class ScrolledList(Frame):
    """
    Scrolled list multiple input form
    """
    def __init__(self, parent=None, options=[]):
        Frame.__init__(self, parent)
        self._make_widgets(options)
    
    def _make_widgets(self, options):
        sbar = Scrollbar(self)
        list = Listbox(self, relief=SUNKEN)
        sbar.config(command=list.yview)
        list.config(yscrollcommand=sbar.set)
        sbar.pack(side=RIGHT, fill=Y)
        list.pack(side=LEFT, expand=YES, fill=BOTH)
        for label in options:
            list.insert(END, label)
        list.config(selectmode=EXTENDED)
        self._listbox = list
    
    def get(self):
        indices = self._listbox.curselection()
        labels = []
        for index in indices:
            labels.append(self._listbox.get(index))
        return labels
    
    def enable(self):
        self._listbox.config(state=NORMAL)
    
    def disable(self):
        self._listbox.config(state=DISABLED)
    
    def focus(self):
        self._listbox.focus_set()
    

class ComboSelector(Frame):
    """
    Combobox selection form
    """
    def __init__(self, parent=None, label=None, values=[], var=None):
        Frame.__init__(self, parent)
        if label:
            self._label = Label(self, text=label)
            self._label.pack(side=TOP, anchor=W)
        if var:
            self._var = var
        else:
            self._var = StringVar()
        self._values = values
        self._combo = Combobox(self, values=values, state='readonly', textvariable=self._var)
        if values:
            self._combo.set(values[0])
        self._combo.pack(side=LEFT, anchor=W, expand=YES, fill=X)
    
    def get(self):
        try:
            return self._var.get()
        except:
            return None
    
    def set(self, val):
        if val in self._values:
            self._var.set(val)
        else:
            raise tkExtrasError("Error: Value %s is not a valid combo selector option" % val)
    
    def update(self, values):
        prev = self._combo.get()
        self._values = values
        self._combo.configure(values=values)
        if values:
            if prev in values:
                self._combo.set(prev)
            else:
                self._combo.set(values[0])
    
    def enable(self):
        self._combo.config(state=NORMAL)
    
    def disable(self):
        self._combo.config(state=DISABLED)
    
    def focus(self):
        self._combo.focus_set()
    

if __name__ == '__main__':
    def default_callback(*args):
        print "%s changed. Callback args: %s" % (args[0], args)
    
    def pack(wname):
        widgets[wname].pack()
    
    def unpack(wname):
        widgets[wname].pack_forget()
    
    def show_widget(*args):
        global cur_wid
        unpack(cur_wid)
        cur_wid = wselect.get()
        pack(cur_wid)
    
    def get_widget():
        widget = widgets[cur_wid]
        try:
            if type(widget.get()) == str:
                print widget.__class__.__name__, "-> '%s'" % widget.get()
            else:
                print widget.__class__.__name__, '->', widget.get()
            setgetentry.delete(0, END)
            setgetentry.insert(0, str(widget.get()))
        except AttributeError, err:
            print err
    
    def set_widget():
        widget = widgets[cur_wid]
        val = setgetentry.get()
        bint = setint.get()
        bbool = setbool.get()
        bfloat = setfloat.get()
        try:
            if bint:
                widget.set(int(val, 0))
            elif bbool:
                if val in ['True', '1']:
                    widget.set(True)
                elif val in ['False', '0']:
                    widget.set(False)
            elif bfloat:
                widget.set(float(val))
            else:
                widget.set(val)
            if not bint and not bbool and not bfloat:
                print widget.__class__.__name__, "<- '%s'" % val
            else:
                print widget.__class__.__name__, '<-', val
        except (AttributeError, ValueError, tkExtrasError), err:
            print err
    
    def enable_widget():
        widget = widgets[cur_wid]
        try:
            widget.enable()
            print 'Enabled', widget.__class__.__name__
        except AttributeError, err:
            print err
    
    def disable_widget():
        widget = widgets[cur_wid]
        try:
            widget.disable()
            print 'Disabled', widget.__class__.__name__
        except AttributeError, err:
            print err
    
    def focus_widget():
        widget = widgets[cur_wid]
        try:
            widget.focus()
            print 'Set focus to', widget.__class__.__name__
        except AttributeError, err:
            print err
    
    # Make a window to test widgets
    root = MainWindow('Test Widgets')
    
    # Make frames
    select_frame = Frame(root)
    select_frame.pack(anchor=NW, expand=YES, fill=X)
    widget_frame = LabelFrame(root, text='Widget')
    widget_frame.pack(anchor=W)
    inp_frame = Frame(root)
    inp_frame.pack(anchor=SW)
    io_frame = Frame(root)
    io_frame.pack(anchor=SW, expand=YES, fill=X)
    control_frame = Frame(root)
    control_frame.pack(anchor=SW, expand=YES, fill=X)
    
    # Set up control variables
    setint = BooleanVar()
    setint.set(False)
    setbool = BooleanVar()
    setbool.set(False)
    setfloat = BooleanVar()
    setfloat.set(False)
    setrange = BooleanVar()
    setrange.set(False)
    
    # Make Widgets
    widgets = {}
    
    text = 'StringEntry with external var'
    ss = StringVar()
    ss.trace_variable('w', default_callback)
    see = StringEntry(widget_frame, text, var=ss)
    widgets[text] = see
    
    text = 'StringEntry'
    se = StringEntry(widget_frame, text)
    widgets[text] = se
    
    text = 'IntEntry with external var'
    ii = IntVar()
    ii.trace_variable('w', default_callback)
    iee = IntEntry(widget_frame, text, var=ii)
    widgets[text] = iee
    
    text = 'IntEntry'
    ie = IntEntry(widget_frame, text)
    widgets[text] = ie
    
    text = 'IntRangeEntry with external var'
    sire = StringVar()
    sire.trace_variable('w', default_callback)
    iree = IntRangeEntry(widget_frame, text, var=sire)
    widgets[text] = iree
    
    text = 'IntRangeEntry'
    ire = IntRangeEntry(widget_frame, text)
    widgets[text] = ire
    
    text = 'FloatRangeEntry with external var'
    sfre = StringVar()
    sfre.trace_variable('w', default_callback)
    free = FloatRangeEntry(widget_frame, text, var=sfre)
    widgets[text] = free
    
    text = 'FloatRangeEntry'
    fre = FloatRangeEntry(widget_frame, text)
    widgets[text] = fre
    
    text = 'FloatEntry with external var'
    df = DoubleVar()
    df.trace_variable('w', default_callback)
    fee = FloatEntry(widget_frame, text, var=df)
    widgets[text] = fee
    
    text = 'FloatEntry'
    fe = FloatEntry(widget_frame, text)
    widgets[text] = fe
    
    text = 'CheckButton with external var'
    bb = BooleanVar()
    bb.trace_variable('w', default_callback)
    cbe = CheckButton(widget_frame, text, var=bb)
    widgets[text] = cbe
    
    text = 'CheckButton'
    cb = CheckButton(widget_frame, text)
    widgets[text] = cb
    
    text = 'OpenFileEntry with external var'
    sofe = StringVar()
    sofe.trace_variable('w', default_callback)
    ofee = OpenFileEntry(widget_frame, text, var=sofe)
    widgets[text] = ofee
    
    text = 'OpenFileEntry'
    ofe = OpenFileEntry(widget_frame, text)
    widgets[text] = ofe
    
    text = 'SaveAsFileEntry with external var'
    ssafe = StringVar()
    ssafe.trace_variable('w', default_callback)
    safee = SaveAsFileEntry(widget_frame, text, var=ssafe)
    widgets[text] = safee
    
    text = 'SaveAsFileEntry'
    safe = SaveAsFileEntry(widget_frame, text)
    widgets[text] = safe
    
    text = 'RadioSelect with external var'
    srs = StringVar()
    srs.trace_variable('w', default_callback)
    rse = RadioSelect(widget_frame, text, ['0', '1', '2'], var=srs)
    widgets[text] = rse
    
    text = 'RadioSelect'
    rs = RadioSelect(widget_frame, text, ['0', '1', '2'])
    widgets[text] = rs
    
    text = 'ProgressBar with external var'
    ip = IntVar()
    ip.trace_variable('w', default_callback)
    pbe = ProgressBar(widget_frame, text, var=ip)
    widgets[text] = pbe
    
    text = 'ProgressBar'
    pb = ProgressBar(widget_frame, text)
    widgets[text] = pb
    
    text = 'ScrolledList'
    sl = ScrolledList(widget_frame, ['0', '1', '2'])
    widgets[text] = sl
    
    text = 'ComboSelector'
    cs = ComboSelector(widget_frame, text, ['0', '1', '2'])
    widgets[text] = cs
    
    text = 'PopupScrolledText with external var'
    beste = BooleanVar()
    bestebutton = Checkbutton(widget_frame, text=text, variable=beste)
    este = PopupScrolledText(var=beste, title=text)
    widgets[text] = bestebutton
    
    text = 'PopupScrolledText'
    best = BooleanVar()
    def est_control(*args):
        if best.get():
            est.show()
        else:
            est.hide()
    
    best.trace_variable('w', est_control)
    bestbutton = Checkbutton(widget_frame, text=text, variable=best)
    est = PopupScrolledText(title=text)
    widgets[text] = bestbutton
    
    # Make widget selection
    wselect = Combobox(select_frame, values=widgets.keys(), state='readonly')
    wselect.bind('<<ComboboxSelected>>', show_widget)
    wselect.pack(side=LEFT, expand=YES, fill=X)
    cur_wid = widgets.keys()[0]
    wselect.set(cur_wid)
    pack(cur_wid)
    
    # Make the controls
    intbutton = Checkbutton(inp_frame, text='Int?', variable=setint)
    intbutton.pack(side=LEFT)
    boolbutton = Checkbutton(inp_frame, text='Bool?', variable=setbool)
    boolbutton.pack(side=LEFT)
    floatbutton = Checkbutton(inp_frame, text='Float?', variable=setfloat)
    floatbutton.pack(side=LEFT)
    setgetentry = Entry(io_frame)
    setgetentry.pack(side=LEFT, anchor=W, expand=YES, fill=X)
    button = Button(io_frame, text='Set', command=set_widget)
    button.pack(side=LEFT)
    button = Button(io_frame, text='Get', command=get_widget)
    button.pack(side=RIGHT)
    button = Button(control_frame, text='Quit', command=root.on_quit)
    button.pack(side=RIGHT)
    button = Button(control_frame, text='Focus', command=focus_widget)
    button.pack(side=RIGHT)
    button = Button(control_frame, text='Disable', command=disable_widget)
    button.pack(side=RIGHT)
    button = Button(control_frame, text='Enable', command=enable_widget)
    button.pack(side=RIGHT)
    
    root.mainloop()
