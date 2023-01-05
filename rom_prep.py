import os, sys, shutil, pyperclip, PySimpleGUI as sg
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

def main():
    path = get_path(def_path)
    if path:
        exts = get_exts(path)
        if exts:
            opts = get_options()
            if opts:
                r = prep_names(path, exts, opts)
                if r:
                    roms, long = r
                    roms = filter_roms(roms)
                    if roms:
                        roms = edit_long_names(roms, long, opts)
                        if roms:
                            print_roms(roms, 'Rom List')
                            finish(path, roms)
                            return
    print('User Canceled')

def finish(path, roms):
    count = len(roms)
    buttons=('Neither', 'Copy', 'Rename')
    ps2path = path.split(os.sep)[-1]

    layout = [
        [sg.Text(f'You have {count} roms selected from {path}.')],
        [sg.Text('You may copy them to a new path, rename them in place,')],
        [sg.Text('or just create an install script.')],
        [sg.Text('PS2 HDD:', size=12), sg.In(platform['dev'], key='dev')],
        [sg.Text('PS2 partition:', size=12), sg.In(platform['part'], key='part')],
        [sg.Text('PS2 path:', size=12), sg.In(ps2path, key='path')],        
        [sg.Push()] + [sg.Button(b) for b in buttons]] 

    window = sg.Window('Finish', layout)
    button, values = window.read()

    if button not in buttons:
        return
    if button == 'Rename':
        target = path
        for k, v in roms.items():
            os.rename(
                os.path.join(path, k),
                os.path.join(path, v))
        files = roms.values()
    if button == 'Copy':
        target = sg.popup_get_folder('Choose Target Path', 'Target', path, initial_folder=path)
        if os.path.isfile(target):
            popup_error('Target is a file!')
            print('Target is a file!')
            return
        elif not os.path.exists(target):
            os.makedirs(target)
        for k, v in roms.items():
            shutil.copy(
                os.path.join(path, k),
                os.path.join(target, v) )
        files = roms.values()
    else:
        target = path
        files = roms.values()
    window.close()

    script_path = os.path.join(target, '_install.sh')
    with open(script_path, 'w') as outp:
        print(f"device {values['dev']}", file=outp)
        print(f"mount {values['part']}", file=outp)
        # check/make dir, file=outp)
        print(f"cd {values['path']}", file=outp)
        print(f"lcd {target}", file=outp)
        for f in files:
            print(f'put "{f}"', file=outp)
        print('exit', file=outp)

def get_path(default):
    path = sg.popup_get_folder('Choose Rom Path', 'Source', default, initial_folder=default)
    return path or default

def get_exts(path):
    exts = {}
    for f in os.listdir(path):
        n, x = os.path.splitext(f)
        x = x or 'NONE'
        c = exts.get(x, 0)
        exts[x] = c+1

    entries = sorted([f'{k:<6}({v})' for k, v in exts.items()])
    print(f'Extensions found: {", ".join(entries    )}')
    
    layout = [[sg.Listbox(entries, size = (40, 8), key='list', enable_events=True)],
              [sg.Push(), sg.Button('Reset'), sg.Button('Invert'), sg.Button('Done')] ]

    window = sg.Window("Select ROM Extensions", layout)
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            return
        elif event == 'Done':
            exts = [i.split(' ')[0] for i in entries if not i.startswith('NONE')]
            break
        elif event == 'Reset':
            entries = sorted([f'{k:<6}({v})' for k, v in exts.items()])
            window['list'].update(entries)
        elif event == 'Invert':
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
                    n = sn

            roms[fn] = n+x
    return roms, long

def get_options():
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

    layout = [[sg.Push(), sg.Text('Max length'), sg.In(def_max, key='MAX', size=4)],
            [ [sg.Checkbox(v, size=32, key=k, default=k in checked)] for k,v in options.items()],
            [sg.Push(), sg.Button('Done')] ]
    
    window = sg.Window('Select filename options', layout)
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

def filter_roms(roms):
    fixed = {}
    items = sorted(roms.values(), key=lambda x: x.lower())
    layout = [
        [sg.Listbox(items, size=(60, 10), key='list', select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE)],
        [sg.Push(), sg.Button('Remove Unselected'), sg.Button('Remove Selected')] ]
    window = sg.Window('Filter Roms', layout)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            return
        elif event == 'Remove Selected':
            selected = values['list']
            r = {k: v for k, v in roms.items() if v not in selected}
            break
        elif event == 'Remove Unselected':
            selected = values['list']
            r = {k: v for k, v in roms.items() if v in selected}
            break
        elif event == 'list':
            selected = values['list'][0]
            index = items.index(selected)
            items.remove(selected)
            window['list'].update(items, scroll_to_index=index-2)

    window.close()
    return r

def edit_long_names(roms, long, opts):
    def get_values(term):
        for k, v in long.items():
            if term in v:
                return k, *v

    if not opts.get('edit', False) or not opts.get('max', False):
        return roms
    mx = opts.get(max, def_max)

    fixed = {}
    items = [v[1] for v in long.values()]
    layout = [
        [sg.Listbox(items, size=(60, 10), key='list', enable_events=True)],
        [sg.Push(), sg.Button('Done')] ]
    window = sg.Window('Edit Long Filenames', layout)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            return
        elif event == 'Done':
            break
        elif event == 'list':
            selected = values['list'][0]
            index = items.index(selected)
            r = get_values(selected)
            if r:
                k, l, s = r
                x = os.path.splitext(k)[1]
                name = sg.popup_get_text(l, 'Edit Name', s) + x
                if name:
                    fixed[k] = name
                    long.pop(k)
                    items = [v[1] for v in long.values()]
                    window['list'].update(items, scroll_to_index=index-1)

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
    for k, v in roms.items():
        print(f'{k:<{longest+1}}{v}')
    print('\n\n')
    print.unpause()

if __name__ == '__main__':
    main()



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