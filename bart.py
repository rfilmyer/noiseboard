import requests
import xmltodict
import json
from collections import defaultdict

REQUEST_PARAMS = {'cmd': 'etd', 'orig': '16TH', 'key': 'MW9S-E7SL-26DU-VV8V'}
BART_URL = 'http://api.bart.gov/api/etd.aspx'


def get_bart_times(params=REQUEST_PARAMS):
    # type: () -> dict
    arrivals = defaultdict(list)
    response = xmltodict.parse(requests.get(BART_URL, params=REQUEST_PARAMS).text)
    for service in response['root']['station']['etd']:
        last_train = False
        destination = service['abbreviation']

        for arrival in service['estimate']:
            try:
                minutes = arrival['minutes']
            except TypeError:
                last_train = True
                minutes = service['estimate']['minutes'][0:2]

            if destination == '24TH' or len(arrivals[destination]) >= 2: continue

            if minutes == 'Leaving':
                minutes = 'Due'  # Shorten to prevent scrolling.
            elif last_train:
                arrivals[destination].append(minutes + ' Last')
                break
            elif int(minutes) <= 60:
                arrivals[destination].append(minutes)
            else:
                continue

    return arrivals

def format_bart_information(destination, etas):
    # type: (str, list(int)) -> str
    prediction = '<SA><CM>{}<CB> {}'.format(destination, ','.join(etas))
    return prediction

def get_predictions(orig='16TH'):
    # type: (str) -> str
    api_params = REQUEST_PARAMS
    api_params['orig'] = orig

    bart_text = '<CP>BART Arrivals<FI>'
    arrivals = get_bart_times(api_params)
    line_predictions = []

    for destination, minutes in arrivals.items():
        line_predictions.append(format_bart_information(destination, minutes))

    bart_text += '<FI>'.join(line_predictions)

    return bart_text
