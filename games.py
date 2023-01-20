from common import *

def_path = '/home/michael/Roms/genesis'
def_max = 32

platforms = {
    'linux': dict(dev='/dev/sda', part='ROMS'),
    'windows': dict(dev='hdd0', part='ROMS')
}
platform = platforms.get(sys.platform, platforms['linux'])
print(f'Platform: {sys.platform} - {platform}')

def_path = '/home/michael/Roms/genesis'
def_max = 32

def install_roms():
    path, subs = popup_get_folder('Choose Rom Path', 'Source', def_path,
            options['history'], True, True)
    if path and os.path.exists(path):
        exts = filter_exts(path)
        if exts:
            opts = filename_options()
            if opts:
                r = prep_names(path, exts, opts)
                if r:
                    roms, long = r
                    selected = filter_files(roms.values())
                    if selected:
                        roms = {k: v for k, v in roms.items() if v in selected}
                        roms = edit_long_names(roms, long, opts)
                        if roms:
                            #print_roms(roms, 'Rom List')
                            finish(path, roms)
                            return
    print('User Canceled')

def install_games():
    def update_games(path):
        print('Updating game list:', path)
        if path:
            games = scan_for_games(path)
            game_names = sorted([g[0] for g in games.values() 
                    if g[1] not in installed_games], key=nocase)
            window['list'].update(game_names)
        else:
            return [], ['No games to install']
        return games, game_names
    def update_buttons():
        sel = values.get('list', [])
        items = window['list'].get_list_values()
        window[tt.selected].update(disabled=not bool(sel))
        window[tt.unselected].update(disabled=len(sel) == len(items))
        if items and info:
            window[tt.all].update(disabled=False)
        else:
            [window[e].update(disabled=True) for e in tt.buttons]
    def install(picked):
        picked = {fn: g for fn, g in games.items() if g[0] in picked}
        commands = {}

        finished = 0
        total = len(picked)
        for fn, (name, code, typ) in picked.items():
            inj = 'inject_dvd' if typ == 'DVD' else 'inject_cd'
            cmd = (hdl_dump, inj, dev, name, fn, code)
            msg = f'Installing {name} ({finished+1}/{total})'
            run_process(cmd, None, "Please Wait", True, msg, True)

    tt.set('gameinstall')
    choices, drives = disks.get_linux_drives()
    drivelist = list(choices.keys())
    installed_games = []
    values = {}
    info = path = None
    
    history = options['game_folders']
    if history and os.path.isdir(history[0]):
        path = history[0]
        games = scan_for_games(history[0])
        game_names = sorted([g[0] for g in games.values()], key=nocase)
    else:
        history = ['']
        game_names = [tt.select]

    layout = [
        [sg.Text(tt.folder, size=12), sg.Combo(history, default_value=history[0],
                key='folder', expand_x=True, enable_events=True, bind_return_key=True),
                sg.FolderBrowse()],
        [sg.Text(tt.drive, size=12),
            sg.Combo(drivelist, readonly=True, key='drive', expand_x=True,
                enable_events=True)],
        [sg.Push(), sg.Text('', key='driveinfo')],
        [sg.Text(tt.list)],
        [sg.Listbox(game_names, size=(60, 10), key='list', expand_x=True, expand_y=True,
                enable_events=True, select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE)],
        [sg.Push(), sg.Text(tt.install)] + [sg.Button(b, disabled=True) for b in tt.buttons]]
    window = sg.Window(tt.title, layout, modal=True, finalize=True)
    update_buttons()
    tt.set_tooltips(window)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED,):
            break
        elif event == 'folder':
            path = values['folder']
            if os.path.isdir(path):
                if path in history:
                    history.remove(path)
                options['game_folders'].insert(0, path)
                history = options['game_folders']
                window['folder'].update(path, values=history)
                games, game_names = update_games(path)
            update_buttons()
        elif event == 'drive':
            sel = values['drive']
            dev = choices[sel]
            info = disks.get_ps2_driveinfo(dev)
            if info:
                t = tt.info.format(info.total, info.used, info.avail)
            else: t = tt.nonps2
            window['driveinfo'].update(t)
            installed_games = [g[1] for g in info.games] if info else []
            games, game_names = update_games(path)
            update_buttons()
        elif event == 'list':
            update_buttons()
        elif event == tt.all:
            install(game_names)
        elif event == tt.selected:
            install(values['list'])
        elif event == tt.unselected:
            install([g for g in game_names if g not in values['list']])


def scan_for_games(path):
    path = os.path.normpath(path) + os.sep

    commands = []
    for fn in os.listdir(path):
        if os.path.splitext(fn)[1] in ('.iso', '.ISO'):
            cmd = (hdl_dump, 'cdvd_info2', path+fn)
            commands.append((path+fn, cmd))

    games = {}
    output = run_processes(commands)
    for fn, v in output.items():
        typ, _, _, code = v[-1].split()[-4:]
        path, name = os.path.split(fn)
        name, ext = os.path.splitext(name)
        if name[:12].count('.') > 1:
            name = name.rsplit('.', 1)[1]
        code = code.strip('"')
        games[fn] = name, code, typ
    return games

def finish(path, roms):
    def _rename(roms, path, reverse=False):
        path = path.rstrip(os.sep) + os.sep
        if reverse:
            for fn, n in roms.items():
                if fn != n:
                    os.rename(path+n, path+fn)
        else:
            for fn, n in roms.items():
                if fn != n:
                    os.rename(path+fn, path+n)
    tt.set('finishroms')
    count = len(roms)
    ps2path = path.split(os.sep)[-1]
    devices, devinfo = disks.get_linux_drives()
    values = list(devices.keys())
    total_size = 0
    dev = part = None
    out_path = '/'
    files = target = None
    for r in roms:
        p = os.path.join(path, r)
        total_size += os.path.getsize(p)
    print('total size:', total_size)

    layout = [
        [sg.Text(tt.drive, size=12), sg.Combo(values, 'select one', key='drive', readonly=True,
                expand_x=True, enable_events=True)],
        [sg.Text(tt.part, size=12), sg.Combo([], key='part', readonly=True,
                expand_x=True, enable_events=True, disabled=True)],
        [sg.Text(tt.path, size=12), sg.In(ps2path, key='path', expand_x=True)],
        [sg.Text(tt.folders)],
        [sg.Listbox([], size=(60, 8), key='list', enable_events=True,
                expand_x=True, expand_y=True)],
        [sg.Push()] + [sg.Button(b, disabled=b == tt.install) for b in tt.buttons] ]

    window = sg.Window('Finish', layout, modal=True, finalize=True)
    tt.set_tooltips(window)
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break

        elif event == 'drive':
            window[tt.install].update(disabled=True)
            sel = values['drive']
            dev = devices[sel]
            drive_size = size2int(devinfo[dev]['SIZE'])
            info = disks.get_ps2_driveinfo(dev)
            
            if info:
                choices = [f'{k} ({v})' for (k, v) in info.parts]
                window['part'].update('select one', values=choices, disabled=False)
            else:
                window['part'].update('select a PS2 HDD above', [])
                print('Not a PS2 formated HDD')

        elif event == 'part':
            part = values['part']
            part, size = values['part'].split()
            partsize = size.strip('()')
            print('part size:', size)
            r = disks.get_ps2_path(dev, part, out_path)
            folders = [i for i in r if i.endswith('/')]
            window['list'].update(folders)
            window[tt.install].update(disabled=False)
        elif event == 'list':
            if values['list']:
                val = values['list'][0]
                if val == '..':
                    out_path = os.path.split(out_path.strip('/'))[0] + '/'
                    val = ''
                out_path = out_path + val
                r = disks.get_ps2_path(dev, part, out_path)
                folders = [i for i in r if i.endswith('/')]
                if out_path != '/': folders = ['..'] + folders
                window['list'].update(folders)
                window['path'].update(out_path+ps2path)

        elif event == tt.rename:
            target = path
            for k, v in roms.items():
                os.rename(
                    os.path.join(path, k),
                    os.path.join(path, v))
            files = roms.values()
            window[tt.rename].update(disabled=True)
            window[tt.copy].update(disabled=True)
            save_script(dev, part, values['path'], files, target)
        elif event == tt.copy:
            target = popup_get_folder('Choose Target Path', 'Target', path)
            if not target:
                continue
            elif os.path.isfile(target):
                popup_error('Target is a file!')
                print('Target is a file!')
                return
            elif not os.path.exists(target):
                os.makedirs(target)
            for k, v in roms.items():
                shutil.copy(
                    os.path.join(path, k),
                    os.path.join(target, v) )
            window[tt.rename].update(disabled=True)
            window[tt.copy].update(disabled=True)
            save_script(dev, part, values['path'], files, target)
        elif event == tt.install:
            if files:
                rename = False
            else:
                rename = True
                target = path
                files = roms.values()
                _rename(roms, path)
            for b in tt.buttons:
                window[b].update(disabled=True)
            outpath = values['path']
            disks.make_ps2_path(dev, part, outpath)
            outp = f'device {dev}\nmount {part}\ncd {outpath}\nlcd {target}\n'
            for f in files:
                outp += f'put "{f}"\n'
            outp += 'exit\n'
            print(outp)
            run_process(pfsshell, outp, "Copying Files", quiet=True, sudo=True)
            if rename:
                _rename(roms, path, True)
        else:
            print(event, values)

    window.close()

def save_script(dev, part, devpath, files, filepath):
    if not dev or not part or not files:
        return
    script_path = os.path.join(filepath, '_install.sh')
    with open(script_path, 'w') as outp:
        print(f"device {dev}", file=outp)
        print(f"mount {part}", file=outp)
        # check/make dir, file=outp)
        print(f"cd {devpath}", file=outp)
        print(f"lcd {filepath}", file=outp)
        for f in files:
            print(f'put "{f}"', file=outp)
        print('exit', file=outp)


def filter_exts(path):
    tt.set('filterexts')
    path = os.path.join(path, '')
    exts = {}
    for f in os.listdir(path):
        if os.path.isfile(path + f):
            n, x = os.path.splitext(f)
            x = x or 'NONE'
            c = exts.get(x, 0)
            exts[x] = c+1

    entries = sorted([f'{k:<6}({v})' for k, v in exts.items()])
    print(f'Extensions found: {", ".join(entries    )}')
    
    layout = [[sg.Listbox(entries, size = (40, 8), key='list', enable_events=True)],
              [sg.Push(), sg.Button(tt.reset), sg.Button(tt.invert), sg.Button(tt.done)] ]

    window = sg.Window(tt.title, layout, modal=True, finalize=True)
    tt.set_tooltips(window)
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            return
        elif event == tt.done:
            exts = [i.split(' ')[0] for i in entries if not i.startswith('NONE')]
            break
        elif event == tt.reset:
            entries = sorted([f'{k:<6}({v})' for k, v in exts.items()])
            window['list'].update(entries)
        elif event == tt.invert:
            all = sorted([f'{k:<6}({v})' for k, v in exts.items()])
            entries = [i for i in all if i not in entries]
            window['list'].update(entries)
        elif event == 'list':
            i = values[event][0]
            entries.remove(i)
            window[event].update(entries)
    window.close()
    return exts

def prep_names(path, exts, opts):
    roms = {}
    long = {}
    for fn in sorted(os.listdir(path), key=lambda x: x.lower()):
        n, x = os.path.splitext(fn)

        # options: .. ' ,the the - ? word max
        if x in exts:
            if opts.get('(', True):
                n = n.split('(')[0].strip()
            if opts.get('..', True):
                n = n.replace('..', '.')
            if opts.get("'", True):
                n = n.replace("'", '')
            if opts.get(',the', True) or opts.get('the', False):
                n = n.replace(', the', '')
                n = n.replace(', The', '')
            if opts.get('the', False):
                n.replace(' the ', ' ')
                n.replace(' The ', ' ')
            if opts.get('-', True):
                n = n.replace(' - ', ' ')
            if opts.get('?', True):
                for s in '?!,':
                    n = n.replace(s, '')

            mx = opts.get('max', 32)
            if mx:
                if len(n+x) > mx:
                    sn = n[:mx-len(x)]
                    if opts.get('word'):
                        sn = n.rsplit(' ', 1)[0]
                    long[fn] = n, sn
                    n = sn.strip()

            roms[fn] = n+x
    return roms, long

def filename_options():
    options = {
        '..': 'remove double periods',
        "'": "remove apostrophe",
        ",the": "remove ', the'",
        'the': "remove all the(s)",
        '?': "remove (?!) symbols",
        'max': "strip long filenames",
        'word': "strip partial words",
        'edit': 'edit long filenames' }
    checked = ('..', ',the', 'max')
    tt.set('fnoptions')
    options = tt.dboxes.copy()

    layout = [[sg.Push(), sg.Text(tt.maxlength), sg.In(def_max, key='MAX', size=4)],
            [ [sg.Checkbox(v, size=32, key=k, default=k in checked)] for k,v in options.items()],
            [sg.Push(), sg.Button('Done')] ]
    
    window = sg.Window('Select filename options', layout, modal=True)
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
           return
        elif event == 'Done':
            break
    for k in options:
        options[k] = values[k]
    if options['max']:
        s = values['MAX']
        try:
            n = int(s)
        except:
            n = def_max
        options['max'] = n
    else:
        options['max'] = False
    window.close()
    print('Filename options: ', options)
    return options    


def edit_long_names(roms, long, opts):
    def get_values(term):
        for k, v in long.items():
            if term in v:
                return k, *v

    if not opts.get('edit', False) or not opts.get('max', False) or not long:
        return roms
    mx = opts.get(max, def_max)

    fixed = {}
    items = [long[v][1] for v in long if v in roms]

    tt.set('edlongfns')
    layout = [
        [sg.Listbox(items, size=(60, 10), key='list', enable_events=True)],
        [sg.Push(), sg.Button(tt.done)] ]
    window = sg.Window(tt.title, layout, modal=True)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        elif event == 'Done':
            break
        elif event == 'list':
            selected = values['list'][0]
            index = items.index(selected)
            r = get_values(selected)
            if r:
                k, l, s = r
                x = os.path.splitext(k)[1]
                r = sg.popup_get_text(l, 'Edit Name', s)
                if r:
                    fixed[k] = r + x
                    long.pop(k)
                    items = [long[v][1] for v in long if v in roms]
                    window['list'].update(items, scroll_to_index=index-1)
            if not long:
                break

    window.close()
    for k, n in fixed.items():
        roms[k] = n
    return roms

def print_roms(roms, message=''):
    longest = 0
    print.pause()
    print(message)
    for k in roms:
        longest = max(longest, len(k))
    print(f'\n{"Source":<{longest+1}}Dest:')
    print('='*int(longest*1.5))
    for k, v in roms.items():
        print(f'{k:<{longest+1}}{v}')
    print.unpause()



'''
You can do this with standard linux utilities:

lsblk -n --scsi --output PATH,RM | \
  grep 0 | \
  awk -F ' ' '{print $1}'

lsblk --scsi --output PATH,RM will list all SCSI devices along with the path to them and whether they are removable or not. On my system, it looks like this:

/dev/sda  1
/dev/sdb  0
/dev/sdc  0
/dev/sdd  0
/dev/sde  0


windows names hdd1, hdd2 etc

def hdl_dump(path):
    for f in os.listdir(path)[:10]:
        fn = os.path.join(path, f)
        cmd = 'hdl_dump_090 cdvdinfo2 {fn}'
        res = subprocess.check_output(cmd).decode()
        print(res)

Usage:
hdl_dump_090 command arguments

Where command is one of:
dump, compare_iin, toc, hdl_toc, delete*,
info, extract, inject_cd*, inject_dvd*, install*,
cdvd_info, cdvd_info2, poweroff, initialize*, backup_toc,
restore_toc*, diag, modify*, copy_hdd*

Usage:  toc device
Displays PlayStation 2 HDD TOC.
hdl_dump_090 toc hdd1:
hdl_dump_090 toc /dev/sda

Usage:  hdl_toc device
Displays a list of all HD Loader games on the PlayStation 2 HDD.


get partition list from pfsshell ls and subtract hdl_toc to find non-game partitions


additional featurs:
    list/delete ps2 games
    format drive
    install ps2 games
    install ps1 games
    install roms
    create my whole setup - format, size of (opl, pops, roms)

'''