import os, sys, shutil, pyperclip, time, random, pickle
from io import StringIO
import PySimpleGUI as sg, subprocess as sp

root = os.path.split(__file__)[0]
themes = sg.theme_list()
temp_dir = '/tmp'
MAX_HISTORY = 9
MAX_FILES = 50000
options = dict(
    font = ('Arial', 16),
    theme = random.choice(themes),
    tooltips = True,
)

platforms = {
    'linux': dict(dev='/dev/sda', part='ROMS'),
    'windows': dict(dev='hdd0', part='ROMS')
}
platform = platforms.get(sys.platform, platforms['linux'])

def load_options():
    opts = {}
    try:
        inp = open('options.cfg', 'rb')
        opts = pickle.load(inp)
        print('config loaded')
    except:
        print('error loading config')
    options.update(opts)
    print(options)
    load_options.options = options.copy()

def save_options():
    if options == load_options.options:
        print('Options unchanged')
    else:
        with open('options.cfg', 'wb') as outp:
            pickle.dump(options, outp)
        print('Options saved')

_print = print
class Printer():
    buffer = StringIO()
    window = None
    quiet = False
    paused = False

    def __init__(self):
        self.buffer = StringIO()
        self.window = None
        self.quiet = False
        self.paused = False
    def __call__(self, *args, **kargs):
        if self.quiet:
            return
        _print(*args, **kargs)
        if 'file' not in kargs:
            _print(*args, file=print.buffer, **kargs)
        if self.window and not self.paused:
            try:
                self.window['CONSOLE'].update(print.buffer.getvalue())
                self.window.Refresh()
            except:
                pass
    def set_window(self, window):
        self.window = window
        self.unpause()
    def pause(self):
        self.paused = True
    def unpause(self):
        self.paused = False
        try:
            self.window['CONSOLE'].update(print.buffer.getvalue())
            self.window.Refresh()
        except:
            pass

class Lang():
    def __init__(self):
        self.windows = {}
        pass
    def load(self, fn):         
        fn = os.path.join(root, 'lang', fn)
        with open(fn) as inp:
            lines = [l.strip() for l in inp.readlines()]
        for l in lines:
            if l.startswith('::'):
                _, name, title = l.split('::') 
                window = {}
                tooltips = {}
                window['title'] = title
                window['tooltips'] = tooltips
                self.windows[name] = window
            elif '::' in l:
                tool, *tools = l.split('::')
                window[tool] = [t.split('==')[1] for t in tools]
                for t in tools:
                    k, v = t.split('==')
                    window[k] = v
            elif l.count('==') == 1:
                name, text = l.split('==')
                window[name] = text
            elif l.count('||') == 1:
                k, tip = l.split('||')
                name = window[k]
                tooltips[name] = tip
            elif l.count('==') == 2:
                name, text, tip = l.split('==')
                window[name] = text
                tooltips[text] = tip

    def set(self, name):
        window = self.windows.get(name, {})
        for k, v in window.items():
            setattr(self, k, v)
    def set_tooltips(self, window):
        if not options.get('tooltips', True):
            return
        missed = []; found = []
        tips = self.tooltips
        for e in window.key_dict:
            a = getattr(self, e, None) if type(e) == str else None
            if e in tips:
                window[e].set_tooltip(tips[e])
                found.append(e)
            elif a and a in tips:
                window[e].set_tooltip(tips[a])
                found.append(a)
            else:
                missed.append(e)
        #print('loaded tooltips:', found)
        #print('elements without tips:', missed)

def nocase(x):
    return x.lower()

def _globals():
    if not hasattr(_globals, 'loaded'):
        _globals.print = Printer()
        _globals.tt = Lang()
    global tt, print
    print = _globals.print
    tt = _globals.tt
_globals()

def format_size(b, digits=1):
    frmt = f'0.{digits}f'
    if b < 1000:
        s = f'{b:{frmt}}B'
    elif 1024 <= b < 1024**2:
        s = f'{b/1024:{frmt}}K'
    elif 1024**2 <= b < 1024**3:
        s = f'{b/1024**2:{frmt}}M'
    elif 1024**3 <= b < 1024**4:
        s = f'{b/1024**3:{frmt}}G'
    elif 1024**5 <= b:
        s = f'{b/1024**4:{frmt}}T'
    return s.replace('.0', '')

def unformat_size(s, _raise=False):
    multi = 1
    size = s
    if s[-1:].lower() == 't':
        size = s[:-1]
        multi = 1024**4
    elif s[-2:].lower() == 'tb':
        size = s[:-2]
        multi = 1024**4
    if s[-1:].lower() == 'g':
        size = s[:-1]
        multi = 1024**3
    elif s[-2:].lower() == 'gb':
        size = s[:-2]
        multi = 1024**3
    if s[-1:].lower() == 'm':
        size = s[:-1]
        multi = 1024**2
    elif s[-2:].lower() == 'mb':
        size = s[:-2]
        multi = 1024**2
    if s[-1:].lower() == 'k':
        size = s[:-1]
        multi = 1024**4
    elif s[-2:].lower() == 'kb':
        size = s[:-2]
        multi = 1024
    try:
        size = int(float(size) * multi)
    except:
        if _raise:
            raise Exception('Error converting filesize')
        print('error converting')
        return 0
    return size
        

import rom_prep, disks