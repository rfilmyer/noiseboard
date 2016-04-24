from xml.etree import ElementTree

import requests

REQUEST_PARAMS = {'stopcode': '15553', 'token': 'ebda4c89-0c5f-40d8-9ed8-e9deff999a49'}
API_URL = 'http://services.my511.org/Transit2.0/GetNextDeparturesByStopCode.aspx'
STATION_CODES = {'15553': 'NB', '15554': 'SB', '13338': 'WB'}

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
    predictions = {}
    for bus in bus_lines:
        arrival_times = []
        for time in bus.findall(".//DepartureTime"):
            if len(arrival_times) < 2:  # Limit arrival outputs to two.
                arrival_times.append(str(time.text))
        predictions[bus.attrib.get('Code')] = arrival_times
    return predictions

def format_route_times(route, bus_times, direction = ''):
    # type: (str, str) -> str
    route_info = "<CF>{dir} <CM>{route} <CB>{times}"
    minutes = ','.join([x for x in bus_times if int(x) <= 120])  # Get rid of abnormal predictions.
    return route_info.format(route=route, times=minutes, dir=direction)


def get_predictions():
    muni_predictions = "<CP>MUNI Arrivals<FI>"
    direction_string = "<FI><SA>{routes}<FI>"
    for station_code, direction in STATION_CODES.iteritems():
        route_predictions = []
        predictions = request_511_xml(station_code)
        for route, times in predictions.iteritems():
            route_predictions.append(format_route_times(route, times, direction))
        muni_predictions += direction_string.format(routes='<FI>'.join(route_predictions))

    return muni_predictions
