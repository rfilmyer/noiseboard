from xml.etree import ElementTree
from collections import OrderedDict

import requests

REQUEST_PARAMS = {'stopcode': '15553', 'token': 'ebda4c89-0c5f-40d8-9ed8-e9deff999a49'}
API_URL = 'http://services.my511.org/Transit2.0/GetNextDeparturesByStopCode.aspx'

class TransitServiceError(Exception):
    pass

def request_511_xml(stopcode='15553'):
    # type: (str) -> dict(str: list(str))
    api_request = REQUEST_PARAMS
    api_request['stopcode'] = stopcode
    xml_string = requests.get(API_URL, params=REQUEST_PARAMS).text
    root = ElementTree.fromstring(xml_string)
    if root.tag == 'transitServiceError':
        raise TransitServiceError(root.text)
    bus_lines = root.findall(".//Route") # If only they used jQuery-style selectors
    predictions = OrderedDict()
    for bus in bus_lines:
        arrival_times = []
        for time in bus.findall(".//DepartureTime"):
            if len(arrival_times) < 2:  # Limit arrival outputs to two.
                arrival_times.append(str(time.text))
        predictions[bus.attrib.get('Code')] = arrival_times
    return predictions

def format_route_times(route, bus_times, direction = ''):
    # type: (str, str) -> str
    route_info = "<CM>{route} <CF>{dir} <CB>{times}"
    minutes = ','.join([x for x in bus_times if int(x) <= 120])  # Get rid of abnormal predictions.
    return route_info.format(route=route, times=minutes, dir=direction)