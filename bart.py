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
    prediction = '<SA><CM>{}<CB> {} Min<CP>'.format(destination, ','.join(str(minute) for minute in sorted(etas)))
    return prediction

def bart_predictions(orig='16TH'):
    # type: (str) -> str
    api_params = REQUEST_PARAMS
    api_params['orig'] = orig

    bart_text = '<SE>BART Arrivals: '
    arrivals = get_bart_times(api_params)
    line_predictions = []

    for destination, minutes in arrivals.iteritems():
        line_predictions.append(format_bart_information(destination, minutes))

    bart_text += ' | '.join(line_predictions)

    return bart_text