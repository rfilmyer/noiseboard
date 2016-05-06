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
import muni
import caltrain

try:
    while True:
        messages = []

        messages.append(bart.get_predictions())
        messages.append(muni.get_predictions())
        messages.append(caltrain.get_predictions())
        text = '<FI>'.join(messages)
        display_text = "<ID01><PA>  <FD>{}{}  <FI>\r\n".format(text, datetime.now().strftime('%H:%M'))
        print(display_text)
        subprocess.call('printf "{text}" > /dev/ttyS0'.format(text=display_text), shell=True)
        sleep(60)
finally:
    display_text = 'printf "<ID01><PA><SE>  Noiseboard is dead - check console :(  \r\n" > /dev/ttyS0'
    subprocess.call(display_text, shell=True)
