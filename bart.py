import requests
from xml.etree import ElementTree

API_KEY = 'MW9S-E7SL-26DU-VV8V'
BART_URL = 'http://api.bart.gov/api/etd.aspx'


def get_bart_times(params):
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
        dict: Contains 2 parts: the text to print ("text"), and the text to send to the board ("fmt")
    """
    prediction_fmt = '<SA><CM>{}<CB> {}'.format(destination, ','.join(etas))
    prediction_text = "{0}: {1}".format(destination, ','.join(etas))

    return {"fmt": prediction_fmt, "text": prediction_text}


def get_predictions(orig='16TH'):
    """
    Given a BART stop, returns predictions formatted for the LED board.

    Returns:
        dict: Contains 2 parts: the text to print ("text"), and the text to send to the board ("fmt")
    """
    api_params = {"cmd": "etd", "orig": orig, "key": API_KEY}

    bart_fmt = '<CP>BART Arrivals<FI>'
    bart_text = ''

    arrivals = get_bart_times(api_params)
    line_predictions = []

    for line in arrivals:
        line_predictions.append(format_bart_information(line['line'], line['times']))

    bart_fmt += '<FI>'.join([line["fmt"] for line in line_predictions])
    bart_text += '\n'.join([line["text"] for line in line_predictions])

    return {"fmt": bart_fmt, "text": bart_text}
