from common import *

default_partitions = [
        '+OPL (2G)',
        'POPS (50G)',
        'ROMS (5G)' ]

def edit_part_window(part, avail):
    if part:
        name, size = part.split()
        size = size2int(size.strip('()'))
        avail += size
        size = size2str(size)
    else:
        name = ''
        size = '1G'

    tt.set('editpart')
    layout = [
        [sg.Text(tt.available, size=18), sg.Text(size2str(avail))],
        [sg.Text(tt.name, size=18), sg.In(name, key='name')],
        [sg.Text(tt.size, size=18), sg.In(size, key='size')],
        [sg.Push()] + [sg.Button(b) for b in tt.buttons]]
    window = sg.Window(tt.title, layout, modal=True, finalize=True)
    window['name'].set_focus()
    tt.set_tooltips(window)
    event, values = window.read()
    rvalue = None
    if event == tt.ok:
        size = size2int(values['size'])
        name = values['name']
        if size and size < size2int(avail):
            rvalue = f'{name} ({size2str(size)})'
        else:
            print(f"Illegal size entered ({values['size']})")
    window.close()
    return rvalue

def format_menu():
    tt.set('format')
    choices, drives = get_linux_drives()
    cvalues = list(choices.keys())
    pvalues = default_partitions[:]

    layout = [
        [sg.Text(tt.drive),
            sg.Combo(cvalues, key='drive', readonly=True, enable_events=True)],
        [sg.Text(tt.partitions)],
        [sg.Listbox(pvalues, key='partitions', size=(40, 10), expand_x=True)],
        [sg.Button(b, disabled=True) for b in tt.pbuttons],
        [sg.Push(), sg.Button(tt.cancel), sg.Button(tt.format, disabled=True)]  ]
    
    window = sg.Window(tt.title, layout, modal=True, finalize=True)
    tt.set_tooltips(window)
    while True:
        event, values = window.read()
        total_size = sum([size2int(v.split()[1].strip('()')) for v in pvalues])
        if event in (sg.WIN_CLOSED, tt.cancel):
            break
        elif event == tt.edit:
            if values['partitions']:
                part = values['partitions'][0]
                new = edit_part_window(part, drive_size-total_size)
                if new:
                    i = pvalues.index(part)
                    pvalues[i] = new
                    window['partitions'].update(pvalues)
        elif event == tt.remove:
            item = values['partitions'][0]
            pvalues.remove(item)
            window['partitions'].update(pvalues)    
        elif event == tt.add:
            new = edit_part_window('new (1G)',  drive_size-total_size)     
            if new:
                pvalues.append(new)
                window['partitions'].update(pvalues)
        elif event == tt.format:
            if sg.popup_ok_cancel('All data will be destroyed. Please ensure that this'  
                    'is the correct drive', sel) == 'OK':
                window.close()
                format_drive(dev, pvalues)
                return

        elif event == 'drive':
            sel = values['drive']
            dev = choices[sel]
            drive_size = size2int(drives[dev]['SIZE'])
            
            pvalues = default_partitions[:]
            total_size = sum([size2int(v.split()[1].strip('()')) for v in pvalues])
            print(f'total {size2str(total_size)}, drive: {size2str(drive_size)}')
            while total_size > drive_size:
                pvalues.pop(-1)
                total_size = sum([size2int(v.split()[1].strip('()')) for v in pvalues])
            
            window['partitions'].update(pvalues)
            for b in tt.pbuttons:
                window[b].update(disabled = False)
            window[tt.format].update(disabled=False)
    window.close()

def partition_menu():
    def update(info):
        if info:
            window['driveinfo'].update(tt.info.format(info.total, info.used, info.avail))

            print(info.games)

            items = []
            if boxes[tt.parts]:
                items = [f'{d} ({s})' for d, s in info.parts]
            if boxes[tt.games]:
                items += [f'{g[0]} ({g[3]})' for g in info.games]
            items.sort(key=nocase)
            window['list'].update(items)
            window[tt.remove].update(disabled=False)
            window[tt.add].update(disabled=False)

        else:
            items = []
            window['driveinfo'].update(tt.nonps2)
            window['list'].update([])
            window[tt.remove].update(disabled=True)
            window[tt.add].update(disabled=True)
        return items

    tt.set('partedit')
    choices, drives = get_linux_drives()
    values = list(choices.keys())
    info = None

    layout = [
        [sg.Text('Drive:', size=8),
            sg.Combo(values, readonly=True, key='drive', expand_x=True,
                enable_events=True)],
        [sg.Push(), sg.Text('', key='driveinfo')],
        [sg.Text(tt.partitions)],
        [sg.Listbox(['Select a drive above'], size=(60, 10), key='list', expand_x=True, expand_y=True)],
        [[sg.Checkbox(b, True, key=b, enable_events=True) for b in tt.boxes]],
        [sg.Push()] + [sg.Button(b, disabled=True) for b in tt.buttons]]
    window = sg.Window(tt.title, layout, modal=True, finalize=True)
    boxes = {b: True for b in tt.boxes}
    tt.set_tooltips(window)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED,):
            break
        elif event in tt.boxes:
            boxes = {b: values[b] for b in tt.boxes}
            update(info)
        elif event == 'drive':
            sel = values['drive']
            dev = choices[sel]
            info = get_ps2_driveinfo(dev)
            items = update(info)
        elif event == tt.remove:
            sel = values['list'][0].rsplit(maxsplit=1)[0]
            if sg.popup_yes_no(f'Remove "{sel}" partition from {dev}?', title='Confirm') == 'Yes':
                if sel in [i[0] for i in info.games]:
                    remove_game(dev, sel)
                else:
                    remove_partition(dev, sel)
                info = get_ps2_driveinfo(dev)
                items = update(info)
        elif event == tt.add:
            avail = size2str(info.avail)
            part = edit_part_window(None, avail)
            name = part.split()[0]
            if part:                
                if name in [i.split()[0] for i in items]:
                    print(f'Partition "{name}" already exists')
                else:
                    create_partition(dev, part)
                    info = get_ps2_driveinfo(dev)
                    items = update(info)


# =======================================
# =======================================
class PS2DriveInfo:
    __slots__ = ('parts games total used avail'.split())
    def __init__(self, *params):
        for z in zip(self.__slots__, params):
            s, p = z
            self.__setattr__(s, p)
    def __str__(self):
        return '\n'.join([
            self.__repr__(),
            f" Partitions: {', '.join([f'{n}({s})' for n, s in self.parts])}",
            f" PS2 Games: {', '.join([f'{n}({s})' for n, s in self.games])}"])
    def __repr__(self):
        return f"PS2HDD: ({self.total}, {len(self.games)} games, {self.avail} available)"


# =======================================
# =======================================
def create_partition(dev, part):
    print(f'Creating "{part}" partition on "{dev}"')
    name, size = part.split()
    size = size2str(size.strip('()'))
    cmd = pfsshell
    inp = f'device {dev}\nmkpart {name} {size} PFS\nexit\n'
    run_process(cmd, inp, sudo=True, quiet=True)

def format_drive(device, parts):
    cmd = os.path.join(root, 'pfsshell')
    inp  = f'device {device}\n'
    inp += f'initialize yes\n'
    inp += f'mount {device}\n'
    for part in parts:
        name, size = part.split()
        size = size.strip('()')
        inp += f'mkpart {name} {size} PFS\n'
    inp += 'exit\n'
    print('\nRunning command', cmd)

    run_process(cmd, inp, 'Formating Drive', True,
            'Please wait while your drive is formated for the PS2')

def get_linux_drives():
    print('Scanning for Linux drives')
    cmd = 'lsblk -o PATH,TYPE,SIZE,RM,LABEL -P'
    info = {}
    for l in sp.getoutput(cmd).split('\n'):
        d = {}
        for i in l.split():
            k, v = i.split('=')
            d[k] = v.strip('"')            
        d['LABEL'] = d['LABEL'] or os.path.split(d['PATH'])[1]
        info[d['PATH']] = d
    disks = sorted([i for i in info if info[i]['TYPE']=='disk'], key=nocase)
    parts = sorted([i for i in info if info[i]['TYPE']=='part'], key=nocase)

    choices = {}
    for d in disks:
        inf = info[d]
        size = info[d]['SIZE']
        _parts = sorted([info[p]['LABEL'] for p in parts if p.startswith(d)
                ], key=lambda x: x.lower())
        rem = 'Internal' if inf['RM'] == '0' else 'Removable'
        contents = ", ".join(_parts) if _parts else 'empty'
        key = f'{inf["LABEL"]} - {inf["SIZE"]} ({contents})' # {rem}'
        choices[key] = d
    for i in choices.values():
        print(' ', i)
    return choices, info


def get_ps2_driveinfo(dev):
    print(f'Getting PS2 Drive Info ({dev})')

    # scan partitions
    err, outp = run_process(f'{hdl_dump} toc {dev}', sudo=True, quiet=True)
    if err: return
    parts = []; games = []
    for l in outp[1:-1]:
        cols = l.split(maxsplit=4)
        if not cols[-1].startswith('PP.'):
            parts.append((cols[-1], size2str(cols[-2])))

    # scan size and remaining space
    s = outp[-1].replace(',', '').split()
    total, used, avail = [size2str(i) for i in s if i.endswith('MB')]

    # scan games
    err, outp = run_process(f'{hdl_dump} hdl_toc {dev}', sudo=True, quiet=True)
    if err: return
    start = outp[0].find('startup')
    for l in outp[1:-1]:
        code, name = l[start:].split(maxsplit=1)
        typ, size = l.split()[:2]
        games.append((name, code, typ, size2str(size))  )

    return PS2DriveInfo(parts, games, total, used, avail)

def get_ps2_path(dev, part, path, full=False):
    cmd = pfsshell
    inp = f'device {dev}\nmount {part}\ncd {path}\nls\nexit\n'
    err, outp = run_process(cmd, inp, sudo=True, quiet=True)

    done = False
    lines = []
    for l in reversed(outp):
        if l.endswith('driver start.'):
            done = True
        elif l.startswith('(!)'):
            return None
        elif not (done or l in ('./', '../')):
            l = path+l if full else l
            lines.append(l)
    return lines

def make_ps2_path(dev, part, path):
    print(f'making "{path}" in {part} on {dev}')
    subs = path.strip('/').split('/')
    inp = f'device {dev}\nmount {part}\n'
    for i in range(len(subs)):
        inp += f"mkdir {'/'.join(subs[:i+1])}\n"
    inp += 'exit\n'
    run_process(pfsshell, inp, sudo=True, quiet=True)

def remove_partition(dev, part):
    print(f'Removing "{part}" partition from "{dev}"')
    cmd = pfsshell
    inp = f'device {dev}\nrmpart {part}\nexit\n'
    run_process(cmd, inp, sudo=True, quiet=True)
def remove_game(dev, game):
    cmd = (hdl_dump, 'delete', dev, game)
    run_process(cmd, None, sudo=True, quiet=True)

def remove_ps2_path(dev, part, path):
    print(f'removing "{path}" from {part} on {dev}')
    files, folders = walk_ps2_path(dev, part, path, True, quiet=True)
    inp = f'device {dev}\nmount {part}\n'
    for f in files:
        inp += f'rm "{f}"\n'
    for f in reversed(folders):
        inp += f'rmdir "{f}"\n'

    if path == '/':
        inp += f'exit\n'
    else:
        inp += f'rmdir "{path}"\nexit\n'
    run_process(pfsshell, inp, sudo=True, quiet=True)

def remove_ps2_files(dev, part, files):
    print(f'removing {len(files)} files from {part} on {dev}')
    inp = f'device {dev}\nmount {part}\n'
    inp += '\n'.join([f'rm "{f}"' for f in files]) + '\nexit\n'
    run_process(pfsshell, inp, sudo=True, quiet=False   )

def walk_ps2_path(dev, part, path='/', separate=False, _deep=False, quiet=False):
    if not _deep:
        path = path if path.endswith('/') else path+'/'
        if not quiet:
            print(f'walking "{path}" in {part} on {dev}')
    sep = os.sep
    files = get_ps2_path(dev, part, path, True)
    more = []
    folders = [f for f in files if f.endswith('/')]

    for f in folders:
        more += walk_ps2_path(dev, part, f, _deep=True)

    if _deep:
        return files + more
    elif separate:
        l = sorted(files+more)
        return [i for i in l if not i.endswith('/')], [i for i in l if i.endswith('/')]
    else:
        return sorted(files+more, key=nocase)

def remove_window():
    def update_games(path):
        pass
    def update_buttons():
        sel = window['list'].get()
        items = [i for i in window['list'].get_list_values() if not i.endswith('/')]
        window[tt.selected].update(disabled=not bool(sel))
        window[tt.unselected].update(disabled=len(sel) == len(items)-1)
        if items and part != None:
            window[tt.all].update(disabled=False)
        else:
            [window[e].update(disabled=True) for e in tt.buttons]

    tt.set('fileremove')
    choices, drives = get_linux_drives()
    drivelist = list(choices.keys())
    values = {}
    info = {}
    dev = path = part = None
    
    history = options['game_folders']
    if history and os.path.isdir(history[0]):
        path = history[0]
        filelist = []
    else:
        history = ['']
        filelist = [tt.select]

    layout = [
        [sg.Text(tt.drive, size=12),
            sg.Combo(drivelist, readonly=True, key='drive', expand_x=True,
                enable_events=True)],
        [sg.Push(), sg.Text('', key='driveinfo')],
        [sg.Text(tt.list)],
        [sg.Listbox(filelist, size=(60, 10), key='list', expand_x=True, expand_y=True,
                enable_events=True, select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE)],
        [sg.Checkbox(tt.confirm, key='confirm'), sg.Push(), sg.Text(tt.remove)] + [sg.Button(b, disabled=True) for b in tt.buttons]]
    window = sg.Window(tt.title, layout, modal=True, finalize=True)
    update_buttons()
    tt.set_tooltips(window)

    while True:
        event, values = window.read()
        if values:
            confirm = values['confirm']
        if event in (sg.WIN_CLOSED,):
            break
        elif event == 'drive':
            sel = values['drive']
            dev = choices[sel]
            info = get_ps2_driveinfo(dev)
            if info:
                path = None
                t = tt.info.format(info.total, info.used, info.avail)
                filelist = [p[0] for p in info.parts]
            else:
                t = tt.nonps2
                filelist = []
            window['driveinfo'].update(t)
            window['list'].update(filelist)
            update_buttons()
        elif event == 'list':
            sel = values['list'][-1] if values['list'] else None
            vals =  values['list'] if sel else []
            if info and part == None:
                window['list'].update(['scanning...'])
                path = '/'
                part = sel
                filelist = ['..'] + get_ps2_path(dev, part, path)
                window['list'].update(filelist)
            elif '..' in vals:
                window['list'].update(['scanning...'])
                path = os.path.split(path.rstrip('/'))[0]
                print(path)
                if path:
                    filelist = ['..'] + get_ps2_path(dev, part, path)
                else:
                    part = None
                    filelist = [p[0] for p in info.parts]
                window['list'].update(filelist)
            elif sel and sel.endswith('/'):
                path += sel
                window['list'].update(['scanning...'])
                filelist = ['..'] + get_ps2_path(dev, part, path)
                window['list'].update(filelist)
            update_buttons()
        elif event == tt.selected:
            if confirm or sg.popup_ok_cancel(tt.rmsel, title=tt.confirm) == 'OK':
                files = [path+f for f in values['list'] if f != '..']
                window['list'].update(['Please wait...'])
                remove_ps2_files(dev, part, files)
                filelist = ['..'] + get_ps2_path(dev, part, path)
                window['list'].update(filelist)
        elif event == tt.unselected:
            if confirm or sg.popup_ok_cancel(tt.rmunsel, title=tt.confirm) == 'OK':
                files = [path+f for f in filelist
                        if f not in values['list'] and  f != '..']
                window['list'].update(['Please wait...'])
                remove_ps2_files(dev, part, files)
                filelist = ['..'] + get_ps2_path(dev, part, path)
                window['list'].update(filelist)
        elif event == tt.all:
            if sg.popup_ok_cancel(tt.rmall.format(path), title=tt.confirm) == 'OK':
                window['list'].update(['Please wait...'])
                remove_ps2_path(dev, part, path)
                path = os.path.split(path.rstrip('/'))[0]
                filelist = ['..'] + get_ps2_path(dev, part, path)
                window['list'].update(filelist)

def conv_ps1():
    tt.set('convps1')
    exts = ('.cue', '.chd')
    files = get_popup_folder_files(tt.source, tt.choose, options['history'],
            exts, True)
    files = filter_files(files)

    if files:
        remove = sg.popup_yes_no(tt.remove, title=tt.confirm) == 'Yes'
        if sys.platform == 'linux':
            conv_ps1_linux(files, remove)

def get_popup_folder_files(title, message, path, exts=None, allow_subs=False):
    if isinstance(path, str):
        path = path; history = []
    elif isinstance(path, list):
        history = path
        path = history[0] if history else ''
    else:
        history = []
        path = ''
    chosen = []

    if allow_subs:
        path, subs = popup_get_folder(message, title, path, history, False, allow_subs)
    else:
        path = popup_get_folder(message, title, path, history, False, allow_subs)
        subs = False

    if subs:
        lp = len(path)
        for root, folders, files in os.walk(path):
            for f in files:
                if not exts or os.path.splitext(f)[1].lower() in exts:
                    chosen.append(os.path.join(root, f))
    else:
        chosen = [os.path.join(path, f) for f in os.listdir(path)
                if not exts or os.path.splitext(f)[1].lower() in exts]
    return chosen


def conv_ps1_linux(files, remove=False):
    count = len(files)
    for i, fn in enumerate(files):
        path, name = os.path.split(fn)
        path = path.rstrip(os.sep) + os.sep
        base, ext = os.path.splitext(name)

        if ext.lower() in ('.chd', ):
            cmd = (chdman, 'extractcd', '-i', path+name, '-o',
                    path+base+'.cue', '-ob', path+base+'.bin')
            err, outp = run_process(cmd, None, tt.converting,
                    False, tt.convstr.format(fn, i+1, count), True)
            if err:
                print('error, skipping file', name)
                continue
            elif remove:
                os.remove(path+name)

            cmd = (cue2pops, path+base+'.cue')
            err, outp = run_process(cmd, None, tt.converting,
                    False, tt.convstr.format(fn, i+1, count), True)
            if remove and not err:
                os.remove(path+base+'.cue')
                os.remove(path+base+'.bin')
        elif ext.lower() in ('.cue',):
            cmd = (cue2pops, path+base+'.cue')
            err, outp = run_process(cmd, None, tt.converting,
                    False, tt.convstr.format(fn, i+1, count), True)
            if remove and not err:
                os.remove(path+base+'.cue')
                os.remove(path+base+'.bin')