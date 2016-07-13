"""
The all-in-one module to make calls to the 511.org XML API.
"""
from xml.etree import ElementTree
from collections import OrderedDict
from datetime import datetime
import re

import requests

XML_TOKEN = 'ebda4c89-0c5f-40d8-9ed8-e9deff999a49'
XML_URL = 'http://services.my511.org/Transit2.0/GetNextDeparturesByStopCode.aspx'\

NEXTGEN_TOKEN = '61c0dc9d-b356-4a4f-9190-3cc687c24397'
NEXTGEN_URL = 'http://api.511.org/transit/StopMonitoring'


class TransitServiceError(Exception):
    """
    An error from the request to the 511.org API.
    """
    pass


def request_511_json(agency='sf-muni', stopcode='15553', mapping=None):
    """
    Sends a request to the 511.org JSON/GTFS API with an agency name and station code and
    returns lines that serve the stop and their next predicted arrival times.

    Args:
        agency: Stop information from this agency (including 'sf-muni' and others)
        stopcode: The code uniquely identifying a MUNI stop, usually visible on a nearby sign post.
    Returns:
        OrderedDict: Lines and ETAs for routes at the station. Exists as an OrderedDict for predictability's sake.

    Examples:
        >>> request_511_json('sf-muni', '15731') # Montgomery Station Inbound
        OrderedDict([('J', ['2', '11']), ('KT', ['5', '16']), ('L', ['4', '6']),
             ('M', ['1', '9']), ('N', ['4', '10'])])
    """
    api_request = {'format': 'json', 'api_key': NEXTGEN_TOKEN,
                   'agency': agency, 'stopCode': stopcode}

    response = requests.get(NEXTGEN_URL, params=api_request)
    response.encoding = "utf-8-sig"
    if response.status_code != 200:
        if response.status_code == 429:
            raise TransitServiceError("Rate Limited/HTTP Error 429" + "\n" + response.text)
        else:
            raise TransitServiceError("HTTP Error {code}".format(code=response.status_code))
    base_dict = response.json()

    predictions = OrderedDict()

    for journey in base_dict['ServiceDelivery']['StopMonitoringDelivery']['MonitoredStopVisit']:
        route_number = journey['MonitoredVehicleJourney']['LineRef']
        if mapping:
            if mapping.get(route_number):
                route_number = mapping.get(route_number)

        arrival_time = journey['MonitoredVehicleJourney']['MonitoredCall']['AimedArrivalTime']
        arrival_datetime = datetime.strptime(arrival_time, "%Y-%m-%dT%H:%M:%SZ")
        arrival_delta =  arrival_datetime - datetime.utcnow()

        arrival_mins = int(arrival_delta.total_seconds()/60)
        if not predictions.get(route_number):
            predictions[route_number] = [arrival_mins]
        elif len(predictions.get(route_number)) < 3:
            predictions[route_number].append(arrival_mins)

    return predictions


def request_511_xml(stopcode='15553'):
    """
    Sends a request to the 511.org XML API with a station code and 
    returns a dict of lines that serve it and the next predicted arrival times.

    Args:
        stopcode: The code uniquely identifying a MUNI stop, usually visible on a nearby sign post.
    Returns:
        OrderedDict: Lines and ETAs for routes at the station. Exists as an OrderedDict for predictability's sake.

    Examples:
        >>>request_511_xml('15731') # Montgomery Station Inbound
        OrderedDict([('J', ['2', '11']), ('KT', ['5', '16']), ('L', ['4', '6']),
             ('M', ['1', '9']), ('N', ['4', '10'])])
    """
    api_request = {'stopcode': stopcode, 'token': XML_TOKEN}
    xml_string = requests.get(XML_URL, params=api_request).text
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


def format_route_times(route, bus_times, direction='', mapping=None):
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
    if mapping:
        if mapping.get(route):
            route = mapping.get(route)
    route_info_fmt = "<CM>{route}{dir} <CB>{times}"
    route_info_text = "{route}{dir}: {times}"

    minutes = ','.join([str(x) for x in bus_times if int(x) <= 120])  # Get rid of abnormal predictions.
    direction_fmt = ' <CF>' + direction + '' if direction else ''
    direction_text = ' (' + direction + ')' if direction else ''
    return {"fmt":  route_info_fmt.format( route=route, times=minutes, dir=direction_fmt),
            "text": route_info_text.format(route=route, times=minutes, dir=direction_text)}


def format_service_prediction(headline, agency, station_codes, mapping=None, legacy=False):
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
        >>> format_service_prediction("MUNI Arrivals", "sf-muni", {'15553': 'NB', '13338': 'WB'})
            {'text': 'MUNI Arrivals: 14 (NB): 2,16 33 (NB): 12,27 49 (NB): 12,23',
                'fmt': '<CP>MUNI Arrivals<FI><SA><CM>33 <CF>WB <CB>3,18<FI><SA><CM>14 <CF>NB <CB>2,16<FI><CM>33'\
                       '<CF>NB <CB>12,27<FI><CM>49 <CF>NB <CB>12,23'}

    """
    opening_fmt = "<CP>{headline}<FI>".format(headline=headline)
    opening_text = "{headline}:\n".format(headline=headline)

    direction_color = "<SA>{routes}"
    service_predictions_fmt = []
    service_predictions_text = []

    for station_code, direction in station_codes.items():
        route_predictions = []
        if legacy:
            predictions = request_511_xml(station_code)
        else:
            predictions = request_511_json(agency, station_code, mapping)

        for route, times in predictions.items():
            if times:
                route_predictions.append(format_route_times(route, times, direction, mapping))

        route_predictions_fmt = '<FI>'.join([route['fmt'] for route in route_predictions])
        route_predictions_text = '\n'.join([route['text'] for route in route_predictions])

        service_predictions_fmt.append(direction_color.format(routes=route_predictions_fmt))
        service_predictions_text.append(route_predictions_text)

    return {"fmt": opening_fmt + "<FI>".join(service_predictions_fmt),
            "text": opening_text + "\n".join(service_predictions_text)}


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
    muni = {"name": "MUNI Arrivals", "agency": "sf-muni",
            "stops": OrderedDict([('15553', 'NB'), ('13338', 'WB'), ('15554', 'SB')])}
    caltrain = {"name": "Caltrain@22nd", "agency": "caltrain", "stops": OrderedDict([('70022', 'SB')])}
    bart = {"name": "BART", "agency": "bart", "stops": OrderedDict([('10', ''),('99', '')]),
            "mapping": {"1561": "SFO/M", "385": "Daly", "389": "Daly", "720": "SFO",
                        "1230": "Pitt", "237": "Rich", "736": "Frmt", "920": "Dubl",
                        "764": "Mbrae", "243": "Daly", "722": "SFO", "917": "Frmt", "1351": "Rich"}}
    services = [bart, muni]

    predictions = []
    for line in services:
        name = line['name']
        agency = line['agency']
        stops = line['stops']
        mapping = line['mapping'] if line.get('mapping') else {}
        predictions.append(format_service_prediction(name, agency, stops, mapping))

    # Caltrain Hack
    predictions.append(format_service_prediction(caltrain['name'], caltrain['agency'], caltrain['stops'], legacy=True))

    return predictions
