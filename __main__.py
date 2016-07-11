'''
Thank you for taking your time to read the source code.
This code is, unfortunately, full of workarounds and redundant.
I might have to rewrite it later. In the meanwhile, at least it works!
>> You have to rewrite it? Sweet, I'll take that as consent to break everything.
'''

from time import sleep
import subprocess
from datetime import datetime
import bart
import api_511

try:
    while True:
        messages = []

        # messages.append(bart.get_predictions())
        for bus_line in api_511.predict():
            messages.append(bus_line)

        date_string = datetime.now().strftime('%m/%e %R')
        messages.append({'fmt': date_string, 'text': date_string})

        board_messages = [line['fmt'] for line in messages]
        terminal_messages = [line['text'] for line in messages]

        single_string_fmt = '<FI>'.join(board_messages)
        single_string_text = '\n'.join(terminal_messages)

        print(single_string_text)

        display_text = "<ID01><PA>  <FD>{}\r\n".format(single_string_fmt)
        subprocess.call('printf "{text}" > /dev/ttyS0'.format(text=display_text), shell=True)
        sleep(60)
finally:
    display_text = 'printf "<ID01><PA><SE>  Noiseboard is dead - check console :(  \r\n" > /dev/ttyS0'
    subprocess.call(display_text, shell=True)
