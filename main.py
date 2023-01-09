#!/bin/python
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
                rom_prep.main()
            else:
                print(f'{event}: {values}')
            returned_at = time.perf_counter()
    window.close()


if __name__ == '__main__':
    tt.load('english')
    load_options()
    main_window()
    save_options()