
import sys, os, time, subprocess as sp
import PySimpleGUI as sg



def run_process(cmd, inp='', title='', sudo=False, message='', quiet=False):
    def input_thread(p):
        def get_input():
            while p.poll() == None:
                l = p.stdout.readline().decode().strip()
                if l:
                    lines.append(l)
                    if not quiet:
                        print(l)
        Thread(target=get_input, daemon=True).start()

    if isinstance(cmd, str): 
        cmd = cmd.split(' ')
    else:
        cmd = list(cmd)
    if isinstance(inp, (list, tuple)):
        inp = '\n'.join(inp)

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
                        password = results + '\n'
                        run_process.password = password
                        cmd = ['sudo', '-kS', '-p', ""] + cmd
                        break
            else:
                sudo = False

    if title:
        layout = [
            [sg.Text(message, key='message', size=60)],
            [sg.Text('.', key='dots')]]
        window = sg.Window(title, layout, enable_close_attempted_event=True,
               finalize=True)

    lines = []; count = 0
    p = sp.Popen(cmd, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.STDOUT)
    if sudo:
        p.stdin.write(password.encode())
        p.stdin.flush()

    input_thread(p)
    if inp:
        print(inp)
        if not inp.endswith('\n'):
            inp += '\n'
        p.stdin.write(inp.encode())
        p.stdin.flush()

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
    return lines

inp = ('help', 'device /dev/sda', 'ls', 'exit')
cmd = 'pfsshell'

root = '/tmp/ramdisk/diskstation2'
pfsshell = os.path.join(root, 'pfsshell')
hdl_dump = os.path.join(root, 'hdl_dump_090')

def get_ps2_parts(dev):
    inp = f'device {dev}\nls\nexit\n'
    outp = run_process(pfsshell, inp, sudo=True)
    return [l[:-1] for l in outp if l.endswith('/')]

def get_ps2_driveinfo(dev):
    outp = run_process(f'{hdl_dump} toc {dev}', sudo=True, quiet=True)
    parts = []; games = []
    for l in outp[1:-1]:
        cols = l.split(maxsplit=4)
        if cols[-1].startswith('PP.HDL.'):
            games.append((cols[-1][7:], cols[-2]))
        else:
            parts.append((cols[-1], cols[-2]))

    s = outp[-1].replace(',', '').split()
    total, used, avail = [i for i in s if i.endswith('MB')]
    return dict(parts=parts, games=games, total=total, used=used, avail=avail)

r = get_ps2_driveinfo('/dev/sda')
for i in r:
    print(i, r[i])


