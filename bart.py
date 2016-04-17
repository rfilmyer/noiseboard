'''
Thank you for taking your time to read the source code.
This code is, unfortunately, full of workarounds and redundant.
I might have to rewrite it later. In the meanwhile, at least it works!
'''
from collections import defaultdict
from time import sleep
import requests
import subprocess
import xmltodict
from datetime import datetime


while True:
    text = 'BART Arrivals '
    arrivals = defaultdict(list)

    BART_URL = 'http://api.bart.gov/api/etd.aspx?cmd=etd&orig=16TH&key=MW9S-E7SL-26DU-VV8V'
    response = xmltodict.parse(requests.get(BART_URL).text)

    for service in response['root']['station']['etd']:
        destination = service['abbreviation']

        try:
            for arrival in service['estimate']:
                minutes = arrival['minutes']
                if minutes == 'Leaving': minutes = 0
                if int(minutes) > 30 or destination == '24TH': continue
                arrivals[destination].append(int(minutes))

        except TypeError:
            # For trains that only have one arrival left.
            minutes = service['estimate']['minutes']
            if minutes == 'Leaving': minutes = 0
            if int(minutes) > 30 or destination == '24TH': continue
            arrivals[destination].append(int(minutes))


    for destination, minutes in arrivals.iteritems():
        text += '<SA><CM>{}<CB> {}<CP> | '.format(destination, ','.join(str(minute) for minute in sorted(arrivals[destination])))


    print text
    subprocess.call('printf "<ID01><PA>    <SB>{}    <SE>{}   \r\n" > /dev/ttyS0'.format(datetime.now().strftime('%H:%M'), text), shell=True)

    sleep(60)

