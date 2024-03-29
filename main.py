#!/bin/python
'Just testing git'
from common import *

def main_window(theme='DarkBlack1', size=16):
    tt.set('main')

    theme = options.get('theme', theme)
    print('Setting theme:', theme)
    sg.theme(theme)
    font = options.get('font', ('Arial', size))
    sg.set_options(font=font, tooltip_font=font, icon='icon.png')
    layout = [[sg.Button(tool) for tool in tt.tools1] + [
                    sg.Push(), sg.Button('?')],
              [sg.Button(tool) for tool in tt.tools2],
              [sg.Multiline(default_text=print.buffer.getvalue(),enable_events=False,
                    size=(120, 20), expand_x=True, expand_y=True, font=('mono', font[1]),
                    key="CONSOLE", write_only=True, disabled=True, autoscroll=True)],
              [sg.Push(), sg.Button(tt.close)] ]
    window = sg.Window('DriveStationGui', layout, enable_close_attempted_event=True,
            resizable=True, finalize=True)
    returned_at = time.perf_counter() - 1
    print.set_window(window)

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        tt.set('main')
        tt.set_tooltips(window)
        event, values = window.read()

        if event == sg.WIN_X_EVENT or event == 'Cancel':
            if time.perf_counter() - returned_at > .5: 
                break
        else:
            if event == 'Clear':
                print.buffer = StringIO()
            elif event == tt.theme:
                reset = theme_menu()
                if reset:
                    window.close()
                    main_window()
                    return
            elif event == tt.format:
                disks.format_menu()
            elif event == tt.partitions:
                disks.partition_menu()
            elif event == tt.roms:
                games.install_roms()
            elif event == tt.install:
                games.install_games()
            elif event == tt.remove:
                disks.remove_window()
            elif event == tt.convps1:
                disks.conv_ps1()
            else:
                print(f'{event}: {values}')
            returned_at = time.perf_counter()
    window.close()


def theme_menu(theme=False):
    font, size = options['font']
    if theme:
        sg.theme(theme)
    else:
        print('Changing theme')    

    tt.set('themes')
    layout = [[sg.Listbox(values=themes, size=(30,10), key='List',
                    enable_events=True)],
             [sg.Text('Size:'), sg.Slider(default_value=size, range=(6,24),
                    key='size', orientation='h')],
             [sg.Checkbox(tt.tips, default=options['tooltips'],
                    key='tooltips')],
             [sg.Push(), sg.Button(tt.cancel), sg.Button(tt.change)]]
 
    window = sg.Window("Theme Chooser", layout, modal=True, finalize=True)
    tt.set_tooltips(window)

    if theme in themes:
        i = themes.index(theme)
        window['List'].update(set_to_index=[i], scroll_to_index=max(i-3, 0))
    tooltips = options['tooltips']
    changed = False
    while True:
        event, values = window.read()
        if event == tt.change:
            theme = values.get('List')
            new_size = int(values.get('size', size))
            options['font'] = (font, new_size)
            options['tooltips'] = values['tooltips']
            if options['tooltips'] != tooltips:
                changed = True
            if new_size != size:
                print(f'Size changed to {new_size}')
                changed = True
            if theme and theme[0] in themes:
                theme = theme[0]
                print(f'Theme changed to {theme}')
                options['theme'] = theme
                changed = True
            window.close()
            return changed
              
        elif event in (sg.WIN_CLOSED, tt.cancel):
            sg.theme(options['theme'])
            print('Canceled theme change')
            window.close()
            break
        elif event == 'List':
            theme = values['List'][0]
            window.close()            
            return theme_menu(theme)
    return


def perf(message=None):
    if message:
        t = time.perf_counter() - perf.last_time
        print(f'{message}: {t*1000:0.0f}')
        perf.last_time = time.perf_counter()
    else:
        perf.last_time = time.perf_counter()
perf.last_time = 0


if __name__ == '__main__':
    tt.load('english')
    load_options()
    main_window()
    save_options()

'''
bchunk [Ridge Racer V.bin] [Ridge Racer V.cue] [Ridge Racer V.iso]



'''
