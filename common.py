import os, sys, shutil, pyperclip, time, random
import rom_prep
from io import StringIO
import PySimpleGUI as sg

themes = sg.theme_list()
temp_dir = '/tmp'
MAX_HISTORY = 9
MAX_FILES = 50000
options = dict(
    font = ('Arial', 16),
    theme = random.choice(themes),
)

platforms = {
    'linux': dict(dev='/dev/sda', part='ROMS'),
    'windows': dict(dev='hdd0', part='ROMS')
}
platform = platforms.get(sys.platform, platforms['linux'])

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

    def pause(self):
        self.paused = True
    def unpause(self):
        self.paused = False
        try:
            self.window['CONSOLE'].update(print.buffer.getvalue())
            self.window.Refresh()
        except:
            pass
print = Printer()
