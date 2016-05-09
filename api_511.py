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

def format_service_prediction(headline, station_codes):
    # type: (str, dict) -> str
    opening = "<CP>{headline}<FI>".format(headline=headline)
    direction = "<SA>{routes}"
    service_predictions = []
    for station_code, direction in station_codes.items():
        route_predictions = []
        predictions = request_511_xml(station_code)
        for route, times in predictions.items():
            if times:
                route_predictions.append(format_route_times(route, times, direction))
        service_predictions.append(direction.format(routes='<FI>'.join(route_predictions)))

    return opening + "<FI>".join(service_predictions)

def predict():
    # type: () -> list(str)
    muni = {"name": "MUNI Arrivals", "stops": OrderedDict([('15553', 'NB'), ('13338', 'WB'), ('15554', 'SB')])}
    caltrain = {"name": "Caltrain@22nd", "stops": OrderedDict([('70022', 'SB')])}
    services = [muni, caltrain]
    return [format_service_prediction(line['name'], line['stops']) for line in services]
