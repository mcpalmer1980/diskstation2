import os, sys, shutil, time, random, pickle
from io import StringIO
from threading import Thread
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
    history = [],
    game_folders = []
)

platforms = {
    'linux': dict(dev='/dev/sda', part='ROMS'),
    'windows': dict(dev='hdd0', part='ROMS')
}
platform = platforms.get(sys.platform, platforms['linux'])

pfsshell = os.path.join(root, 'pfsshell')
hdl_dump = os.path.join(root, 'hdl_dump_090')

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
    
    backup = options.copy()
    for o in backup:
        if type(backup[o]) == dict:
            backup[o] = backup[o].copy()
        elif type(backup[o]) == list:
            backup[o] = backup[o][:]
    load_options.options = backup

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
        self._windows = {}
        self._prev = None
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
                self._windows[name] = window
            elif '::' in l:
                try:                
                    tool, *tools = l.split('::')
                    window[tool] = [t.split('==')[1] for t in tools]
                    window['d'+tool] = {t.split('==')[0]: t.split('==')[1] for t in tools}
                    for t in tools:
                        k, v = t.split('==')
                        window[k] = v
                except:
                    print('Lang error in:', l)
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
        window = self._windows.get(name, {})
        self._name = name
        self._name, self._prev = name, self._name
        for k, v in window.items():
            setattr(self, k, v)
    def reset(self):
        self.set(self._prev)
    def set_tooltips(self, window):
        if not options.get('tooltips', True):
            return
        missed = []; found = []
        tips = self.tooltips
        for e in window.key_dict:
            a = getattr(self, e, None) if type(e) == str else None
            if e in tips:
                try:
                    window[e].set_tooltip(tips[e])
                    found.append(e)
                except: print(f'tooltip error: {e}')
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

def size2str(s, digits=1):
    if isinstance(s, str):
        return encode_size_str(decode_size_str(s), digits)
    return encode_size_str(s, digits)
def size2int(s):
    if isinstance(s, str):
        return decode_size_str(s)
    return s

def encode_size_str(b, digits=1):
    frmt = f'0.{digits}f'
    if b < 1000:
        s = f'{b:{frmt}}B'
    elif 1024 <= b < 1024**2:
        s = f'{b/1024:{frmt}}K'
    elif 1024**2 <= b < 1024**3:
        s = f'{b/1024**2:{frmt}}M'
    elif 1024**3 <= b < 1024**4:
        s = f'{b/1024**3:{frmt}}G'
    else:
        s = f'{b/1024**4:{frmt}}T'
    return s.replace('.0', '')

def decode_size_str(s, _raise=False):
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

def popup_get_folder(message='', title='', path='', history=None, allow_new=True):
    tt.set('getfolder')
    browse_button = sg.FolderBrowse(tt.browse, initial_folder=path)
    layout = [[]]
    if message:
        layout += [[sg.Text(message, auto_size_text=True)]]

    if history:
        last_entry = history[0]
        layout += [[sg.Combo(history, default_value=last_entry, key='-INPUT-', bind_return_key=True),
                    browse_button]]
    else:
        layout += [[sg.InputText(default_text=path, key='-INPUT-'), browse_button]]

    layout += [[sg.Push(), sg.Button(tt.cancel, size=(6, 1)), sg.Button(tt.ok, size=(6, 1), bind_return_key=True)]]

    window = sg.Window(title=title or tt.title, layout=layout, auto_size_text=True, modal=True)
    val = None

    while True:
        event, values = window.read()
        if event in (tt.cancel, sg.WIN_CLOSED):
            break
        elif event in (tt.ok, '-INPUT-'):
            val = values['-INPUT-']
            if os.path.exists(val):
                if type(history) == list:
                    if val in history:
                        history.remove(val)
                    history.insert(0, val)
            elif allow_new and os.path.isdir(os.path.split(os.path.normpath(val))[0]):
                os.makedirs(val)
            else:
                val = None
            break

    window.close()
    return val

def run_process(cmd, inp='', title='', sudo=False, message='', quiet=False):
    # THREAD HANDLER
    def input_thread(p):
        def get_input():
            while p.poll() == None:
                l = p.stdout.readline().decode().strip()
                if l:
                    outp.append(l)
                    if not quiet:
                        print(l)                    

            remaining = p.stdout.readlines()
            for l in remaining:
                outp.append(l.decode().strip())
                if not quiet:
                    print(l.decode().strip())

        Thread(target=get_input, daemon=True).start()

    # VERIFY PARAMETERS
    if isinstance(cmd, str): 
        cmd = cmd.split(' ')
    else:
        cmd = list(cmd)
    if isinstance(inp, (list, tuple)):
        inp = '\n'.join(inp)

    # GET AND VERIFY LINUX SUDO PASSWORD
    if sudo and sys.platform == 'linux':
        password = getattr(run_process, 'password', '')
        if password:
            cmd = ['sudo', '-kS', '-p', ""] + cmd
        else:
            for _ in range(3):
                results = sg.popup_get_text('Enter your ROOT password',
                    title='Validation', size=45, password_char='*')
                if results:
                    try:
                        r = sp.run(('sudo', '-vkS'), capture_output=True,
                                input=(results+'\n').encode(), timeout=1)
                    except: continue
                    if not r.returncode:
                        password = (results + '\n').encode()
                        run_process.password = password
                        cmd = ['sudo', '-kS', '-p', ""] + cmd
                        break
            else:
                sudo = False

    # PREPARE PROGRESS WINDOW
    if title:
        layout = [
            [sg.Text(message, key='message', size=60)],
            [sg.Text('.', key='dots')]]
        window = sg.Window(title, layout, enable_close_attempted_event=True,
               finalize=True)

    # OPEN PROCESS AND SEND PASSWORD
    outp = []; count = 0
    p = sp.Popen(cmd, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.STDOUT)
    if sudo:
        p.stdin.write(password)
        p.stdin.flush()

    # START THREAD AND SEND INPUT
    input_thread(p)
    if inp:
        if not quiet:
            print(inp)
        if not inp.endswith('\n'):
            inp += '\n'
        p.stdin.write(inp.encode())
        p.stdin.flush()

    # UPDATE DISPLAY AND AWAIT PROCESS TERMINATION
    while p.poll() == None:
        count += 1
        if title:
            window.read(timeout=250)
            dots = '.' * (count % 20 + 1)
            window['dots'].update(dots)
        else:
            if not quiet and not count % 3:
                print('.', end='', flush=True)
            time.sleep(.1)
    if title: window.close()
    if quiet and p.returncode:
        for l in outp:
            print(l)
    return p.returncode, outp
#run_process.password = 'Anpw4mnD!\n'.encode()

def run_process2(cmd, label, outputs, quiet=True):
    # THREAD HANDLER
    def output_thread(p):
        def get_output():
            while p.poll() == None:
                l = p.stdout.readline().decode().strip()
                if l:
                    outp.append(l)
                    if not quiet:
                        print(l)
            remaining = p.stdout.readlines()
            for l in remaining:
                outp.append(l.decode().strip())
                if not quiet:
                    print(l.decode().strip())
            if not p.returncode:
                outputs[label] = outp
        outp = []

        t = Thread(target=get_output, daemon=True)
        t.start()
        return t

    p = sp.Popen(cmd, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.STDOUT)
    return output_thread(p)

def run_processes(tasks, max_workers=5):
    workers = []
    output = {}
    total = len(tasks)
    finished = 1
    while tasks or workers:
        if len(workers) < max_workers and tasks:
            name, command = tasks.pop()
            t = run_process2(command, name, output)
            workers.append(t)
        elif workers:
            for t in reversed(workers):
                if not t.is_alive():
                    workers.remove(t)
                    finished += 1
        else:
            time.sleep(.1)

        if not sg.one_line_progress_meter('Progress Bar', finished, total,
                'Scanning for Games', 'Multi threaded'):
            break




    while workers:
        for t in reversed(workers):
            if not t.is_alive():
                workers.remove(t)
        time.sleep(.1)
    return output


run_process.password = 'Anpw4mnD!\n'.encode()















import disks, games