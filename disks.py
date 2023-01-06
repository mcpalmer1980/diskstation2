from common import *

default_partitions = [
        '+OPL (2G)',
        'POPS (50G)',
        'ROMS (500G)' ]

def format_HDD():
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
        total_size = sum([unformat_size(v.split()[1].strip('()')) for v in pvalues])
        if event in (sg.WIN_CLOSED, tt.cancel):
            break
        elif event == tt.edit:
            if values['partitions']:
                part = values['partitions'][0]
                new = edit_part(part, drive_size-total_size)
                if new:
                    i = pvalues.index(part)
                    pvalues[i] = new
                    window['partitions'].update(pvalues)
        elif event == tt.remove:
            item = values['partitions'][0]
            pvalues.remove(item)
            window['partitions'].update(pvalues)    
        elif event == tt.add:
            new = edit_part('new (1G)',  drive_size-total_size)     
            if new:
                pvalues.append(new)
                window['partitions'].update(pvalues)
        elif event == tt.format:
            format_drive(dev, pvalues)
        elif event == 'drive':
            sel = values['drive']
            dev = choices[sel]
            drive_size = unformat_size(drives[dev]['SIZE'])
            
            pvalues = default_partitions[:]
            total_size = sum([unformat_size(v.split()[1].strip('()')) for v in pvalues])
            print(f'total {format_size(total_size)}, drive: {format_size(drive_size)}')
            print(total_size > drive_size)
            while total_size > drive_size:
                pvalues.pop(-1)
                total_size = sum([unformat_size(v.split()[1].strip('()')) for v in pvalues])
            
            window['partitions'].update(pvalues)
            for b in tt.pbuttons:
                window[b].update(disabled = False)
            window[tt.format].update(disabled=False)

    window.close()

def edit_part(part, avail):
    name, size = part.split()
    size = unformat_size(size.strip('()'))
    avail += size
    size = format_size(size)
    tt.set('editpart')
    layout = [
        [sg.Text(tt.available, size=18), sg.Text(format_size(avail))],
        [sg.Text(tt.name, size=18), sg.In(name, key='name')],
        [sg.Text(tt.size, size=18), sg.In(size, key='size')],
        [sg.Push()] + [sg.Button(b) for b in tt.buttons]]
    window = sg.Window(tt.title, layout, modal=True, finalize=True)
    tt.set_tooltips(window)
    event, values = window.read()
    rvalue = None
    if event == tt.ok:
        size = unformat_size(values['size'])
        name = values['name']
        if size and size < avail:
            print('new', name, size)
            rvalue = f'{name} ({format_size(size)})'
        else:
            print(f"Illegal size entered ({values['size']})")
    window.close()
    return rvalue




class DriveInfo():
    def __init__(self, device, text):
        self.device = device
        lines = text.split('\n')
        _, size, _, used, _, avail = lines[-1].replace(',','').split()
        self.size = size
        self.used = used
        self.avail = avail
        self.games = []
        self.parts = []
    def __repr__(self):
        return f'PS2 HDD {self.device} {self.size}'

def get_drive_info(device):
    PIPE = sp.PIPE
    cmd = os.path.join(root, 'hdl_dump_090')
    r = sp.getoutput(f'{cmd} hdl_toc {device}')
    if r.endswith('aborting.'):
        print(tt.notps2)
        return None
    return DriveInfo(device, r)

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
        key = f'{inf["LABEL"]} - {inf["SIZE"]} ({contents}) {rem}'
        choices[key] = d
    for i in choices.values():
        print(' ', i)
    return choices, info

