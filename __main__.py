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


while True:
    text = 'BART Arrivals '
    arrivals = bart.get_bart_times()


    for destination, minutes in arrivals.iteritems():
        text += bart.format_bart_information(destination, minutes)

    print text
    subprocess.call('printf "<ID01><PA>    <SB>{}    <SE>{}   \r\n" > /dev/ttyS0'.format(datetime.now().strftime('%H:%M'), text), shell=True)

    sleep(60)

