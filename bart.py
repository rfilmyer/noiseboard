import requests
from xml.etree import ElementTree

API_KEY = 'MW9S-E7SL-26DU-VV8V'
BART_URL = 'http://api.bart.gov/api/etd.aspx'


def get_bart_times(params=REQUEST_PARAMS):
    """
    Makes a request to BART's XML API

    Args:
        params (dict): Parameters that will be passed to the HTTP request
            in the style {"key": "value"} -> "index.html?key=value"

    Returns:
        list: A list of dicts with the keys "line", "color", and "times"
            corresponding to prediction times on each line for a given station.
    """
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


def format_bart_information(destination, etas):
    """
    Combines a route name and a list of times into a string.

    Args:
        destination (str): Where a train is headed.
        etas (list): A list of arrival times for a train line (can be `str`s or `int`s)

    Returns:
        string: The formatted string, ready to be put into the board.
    """
    prediction = '<SA><CM>{}<CB> {}'.format(destination, ','.join(etas))
    return prediction

def get_predictions(orig='16TH'):
    # type: (str) -> str
    """
    Given a BART stop, returns predictions formatted for the LED board.
    """
    api_params = {"cmd": "etd", "orig": orig, "key": API_KEY}

    bart_text = '<CP>BART Arrivals<FI>'
    arrivals = get_bart_times(api_params)
    line_predictions = []

    for line in arrivals:
        line_predictions.append(format_bart_information(line['line'], line['times']))

    bart_text += '<FI>'.join(line_predictions)

    return bart_text
