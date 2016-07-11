"""
The all-in-one module to make calls to the 511.org XML API.
"""
from xml.etree import ElementTree
from collections import OrderedDict

import requests

REQUEST_PARAMS = {'stopcode': '15553', 'token': 'ebda4c89-0c5f-40d8-9ed8-e9deff999a49'}
API_URL = 'http://services.my511.org/Transit2.0/GetNextDeparturesByStopCode.aspx'


class TransitServiceError(Exception):
    """
    An error from the request to the 511.org API.
    """
    pass


def request_511_xml(stopcode='15553'):
    """
    Sends a request to the 511.org XML API with a station code and 
    returns a dict of lines that serve it and the next predicted arrival times.

    Args:
        stopcode: The code uniquely identifying a MUNI stop, usually visible on a nearby sign post.
    Returns:
        OrderedDict: Lines and ETAs for routes at the station. Exists as an OrderedDict for predictibility's sake.

    Examples:
        >>>request_511_xml('15731') # Montgomery Station Inbound
        OrderedDict([('J', ['2', '11']), ('KT', ['5', '16']), ('L', ['4', '6']),
             ('M', ['1', '9']), ('N', ['4', '10'])])
    """
    api_request = REQUEST_PARAMS
    api_request['stopcode'] = stopcode
    xml_string = requests.get(API_URL, params=REQUEST_PARAMS).text
    root = ElementTree.fromstring(xml_string)
    if root.tag == 'transitServiceError':
        raise TransitServiceError(root.text)
    bus_lines = root.findall(".//Route")  # If only they used jQuery-style selectors
    predictions = OrderedDict()
    for bus in bus_lines:
        arrival_times = []
        for time in bus.findall(".//DepartureTime"):
            if len(arrival_times) < 2:  # Limit arrival outputs to two.
                arrival_times.append(str(time.text))
        predictions[bus.attrib.get('Code')] = arrival_times
    return predictions


def format_route_times(route, bus_times, direction=''):
    """
    Formats prediction times for an individual bus line at a given stop.

    Args:
        route (str): A bus route (ex: 33, 14R, J) that has predicted ETAs
        bus_times (list): Next arrival times for a given bus route (ex: [2, 22, 42])
        direction (str, optional): A optional direction to be sent along with the bus parameters

    Returns:
        Dict: The final string with routes and times.
            "fmt" contains the board-ready version, "text" contains a human-readable version.

    Examples:
        >>> format_route_times('14', [3, 11, 17], 'NB')
        {'fmt': '<CM>14 <CF>NB <CB>3,11,17', 'text': '14 (NB): 3,11,17'}
    """
    route_info_fmt = "<CM>{route} <CF>{dir} <CB>{times}"
    route_info_text = "{route} ({dir}): {times}"

    minutes = ','.join([str(x) for x in bus_times if int(x) <= 120])  # Get rid of abnormal predictions.

    return {"fmt":  route_info_fmt.format( route=route, times=minutes, dir=direction),
            "text": route_info_text.format(route=route, times=minutes, dir=direction)}


def format_service_prediction(headline, station_codes):
    """
    Returns a formatted string combining prediction times for different stops and lines
        under a single banner for a provider.

    Args:
        headline (str): Stop predictions will be preceded with this header,
            useful for distinguishing different transit providers.
        station_codes(dict): A dictionary where keys map to stop codes, and

    Returns:
        dict: Strings corresponding to bus stop predictions.
            Board-formatted string is in "fmt", Human-readable in "text"

    Examples:
        >>> format_service_prediction("MUNI Arrivals", {'15553': 'NB', '13338': 'WB'})
            {'text': 'MUNI Arrivals:\n14 (NB): 2,16\n33 (NB): 12,27\n49 (NB): 12,23',
                'fmt': '<CP>MUNI Arrivals<FI><SA><CM>33 <CF>WB <CB>3,18<FI><SA><CM>14 <CF>NB <CB>2,16<FI><CM>33'\
                       '<CF>NB <CB>12,27<FI><CM>49 <CF>NB <CB>12,23'}

    """
    opening_fmt = "<CP>{headline}<FI>".format(headline=headline)
    opening_text = "{headline}:\n".format(headline=headline)

    direction_color = "<SA>{routes}"
    service_predictions = []

    for station_code, direction in station_codes.items():
        route_predictions = []
        predictions = request_511_xml(station_code)
        for route, times in predictions.items():
            if times:
                # print('route:', route, 'times:', times, 'direction:', direction)
                route_predictions.append(format_route_times(route, times, direction))

        route_predictions_fmt = '<FI>'.join([route['fmt'] for route in route_predictions])
        route_predictions_text = '\n'.join([route['text'] for route in route_predictions])

        service_predictions.append(
            direction_color.format(routes=route_predictions_fmt))

    return {"fmt": opening_fmt + "<FI>".join(service_predictions),
            "text": opening_text + route_predictions_text}


def predict():
    """
    Pulls bus prediction info for some preconfigured stops, routes, and providers.
        This function exists for convenience, and is just sugar over the format_service_prediction function.

    Returns:
        list: Dicts containing formatted and human-readable route information for given providers and service times.

    Examples:
        >>> predict()
        ['fmt': 'abcde', 'text': 'defgh']
    """
    muni = {"name": "MUNI Arrivals",
            "stops": OrderedDict([('15553', 'NB'), ('13338', 'WB'), ('15554', 'SB')])}
    caltrain = {"name": "Caltrain@22nd", "stops": OrderedDict([('70022', 'SB')])}
    services = [muni, caltrain]
    return [format_service_prediction(line['name'], line['stops']) for line in services]
