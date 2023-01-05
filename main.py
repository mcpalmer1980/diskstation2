import os, sys, shutil, pyperclip, time
import rom_prep
from io import StringIO
import PySimpleGUI as sg
from common import *

def main_window(theme='DarkBlack1', size=16):
    #set_tooltips(window, 'main')
    #options = load_options()    
    #tooltips = load_tooltips('README.md')
    tools1 = ('Format HDD', 'Create Partition', 'Install Roms')
    tools2 = ('Change Theme'),

    theme = options.get('theme', theme)
    print('starting', theme)
    font = options.get('font', ('Arial', size))
    sg.set_options(font=font, tooltip_font=font, icon='icon.png')
    sg.theme(theme)
    layout = [[sg.Button(tool) for tool in tools1] + [
                    sg.Push(), sg.Button('?')],
              [sg.Button(tool) for tool in tools2],
              [sg.Multiline(default_text=print.buffer.getvalue(),enable_events=False,
                    size=(120, 20), expand_x=True, expand_y=True, font=('mono', font[1]),
                    key="CONSOLE", write_only=True, disabled=True, autoscroll=True)],
              [sg.Push(), sg.Button('Close')] ]
    window = sg.Window('DriveStationGui', layout, font=options['font'],
            enable_close_attempted_event=True, resizable=True, finalize=True)
    returned_at = time.perf_counter() - 1
    print.window = window

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()

        if event == sg.WIN_X_EVENT or event == 'Cancel':
            if time.perf_counter() - returned_at > .5: 
                break
        else:
            if event == 'Clear':
                print.buffer = StringIO()
            elif event == "Change Theme":
                r = theme_menu()
                if r:
                    window.close()
                    main_window()
                    return
            elif event == "Install Roms":
                rom_prep.main()
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

    layout = [[sg.Listbox(values=themes, size=(30,10), key='List',
                    enable_events=True)],
             [sg.Text('Size:'), sg.Slider(default_value=size, range=(6,24),
                    key='size', orientation='h')],
             #[sg.Checkbox('Show Tooltips', default=options['tooltips'],
             #       key='tooltips')],
             [sg.Push(), sg.Button('Cancel'), sg.Button('Change')]]
 
    window = sg.Window("Theme Chooser", layout, modal=True,
            font=options['font'], finalize=True)

    if theme in themes:
        i = themes.index(theme)
        window['List'].update(set_to_index=[i], scroll_to_index=max(i-3, 0))
    while True:
        event, values = window.read()
        if event == 'Change':
            theme = values.get('List')
            new_size = int(values.get('size', size))
            options['font'] = (font, new_size)
            #options['tooltips'] = values['tooltips']
            if new_size != size:
                print(f'Size changed to {new_size}')
                theme = options['theme']
            if theme and theme[0] in themes:
                theme = theme[0]
                print(f'Theme changed to {theme}')
                options['theme'] = theme
            window.close()
            return theme
              
        elif event in (sg.WIN_CLOSED, 'Cancel'):
            print('Canceled theme change')
            window.close()
            break
        elif event == 'List':
            theme = values['List'][0]
            window.close()            
            return theme_menu(theme)
            #return theme_menu(parent, theme)
    return

if __name__ == '__main__':
    main_window()