import requests
import json
from xml.etree import ElementTree
from collections import defaultdict

REQUEST_PARAMS = {'cmd': 'etd', 'orig': '16TH', 'key': 'MW9S-E7SL-26DU-VV8V'}
BART_URL = 'http://api.bart.gov/api/etd.aspx'


def get_bart_times(params=REQUEST_PARAMS):
    # type: (dict) -> dict
    xml_string = requests.get(BART_URL, params=params).text
    root = ElementTree.fromstring(xml_string)
    
    predictions = []
    for etd in root.find('station').findall('etd'):
        line = etd.find('abbreviation').text
        color = etd.find('estimate').find('color').text
        times = []
        for estimate in etd.findall('estimate'):
            times.append(estimate.find('minutes').text)
        predictions.append({'line': line, 'color': color, 'times': times})
    return predictions



def format_bart_information(destination, etas, color=None):
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

    for line in arrivals:
        line_predictions.append(format_bart_information(line['line'], line['times'], line['color']))

    bart_text += '<FI>'.join(line_predictions)

    return bart_text
