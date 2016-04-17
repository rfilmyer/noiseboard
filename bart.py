import requests
import xmltodict
from collections import defaultdict


BART_URL = 'http://api.bart.gov/api/etd.aspx?cmd=etd&orig=16TH&key=MW9S-E7SL-26DU-VV8V'


def get_bart_times():
    # type: () -> dict
    arrivals = defaultdict(list)
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


    return arrivals

def format_bart_information(destination, etas):
    # type: (str, list(int)) -> str
    prediction = '<SA><CM>{}<CB> {}<CP> | '.format(destination, ','.join(str(minute) for minute in sorted(etas)))
    return prediction
