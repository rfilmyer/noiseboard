"""
The all-in-one module to make calls to the 511.org XML API.
"""
from collections import OrderedDict
from datetime import datetime
from xml.etree import ElementTree

import default_transit_services
import requests

XML_TOKEN = 'ebda4c89-0c5f-40d8-9ed8-e9deff999a49'
XML_URL = 'http://services.my511.org/Transit2.0/GetNextDeparturesByStopCode.aspx'\

DEFAULT_NEXTGEN_TOKEN = '61c0dc9d-b356-4a4f-9190-3cc687c24397'
NEXTGEN_URL = 'http://api.511.org/transit/StopMonitoring'


class TransitServiceError(Exception):
    """
    An error from the request to the 511.org API.
    """
    pass


def parse_511_json(base_dict, mapping=None):
    """
    Sends a request to the 511.org JSON/GTFS API with an agency name and station code and
    returns lines that serve the stop and their next predicted arrival times.

    Args:
        api_key: The API key used to pull from the 511 API.
        agency: Stop information from this agency (including 'sf-muni' and others)
        stopcode: The code uniquely identifying a MUNI stop, usually visible on a nearby sign post.
    Returns:
        OrderedDict: Lines and ETAs for routes at the station. Exists as an OrderedDict for predictability's sake.

    Examples:
        >>> parse_511_json('<uuid>', 'sf-muni', '14305') # Geary & Laguna Inbound
        OrderedDict([('38', [datetime.datetime(2016, 7, 15, 4, 57, 34),
                             datetime.datetime(2016, 7, 15, 5, 03, 19),
                             datetime.datetime(2016, 7, 15, 5, 07, 42)]),
                      ('38R', [datetime.datetime(2016, 7, 15, 5, 00, 22)])])
    """
    # base_dict = request_511_json(api_key, agency, stopcode)
    predictions = OrderedDict()

    for journey in base_dict['ServiceDelivery']['StopMonitoringDelivery']['MonitoredStopVisit']:
        route_number = journey['MonitoredVehicleJourney']['LineRef']
        if mapping:
            if mapping.get(route_number):
                route_number = mapping.get(route_number)

        arrival_time = journey['MonitoredVehicleJourney']['MonitoredCall']['AimedArrivalTime']
        arrival_datetime = datetime.strptime(arrival_time, "%Y-%m-%dT%H:%M:%SZ")

        if not predictions.get(route_number):
            predictions[route_number] = []

        if len(predictions.get(route_number)) < 3:
            predictions[route_number].append(arrival_datetime)

    return predictions


def request_511_json(api_key, agency, stopcode):
    api_request = {'format': 'json', 'api_key': api_key,
                   'agency': agency, 'stopCode': stopcode}

    response = requests.get(NEXTGEN_URL, params=api_request)
    response.encoding = "utf-8-sig"
    if response.status_code != 200:
        if response.status_code == 429:
            raise TransitServiceError("Rate Limited/HTTP Error 429:" + "\n" + response.text)
        elif response.status_code == 401:
            raise TransitServiceError("Unauthorized/HTTP Error 401:" + "\n" + response.text)
        else:
            raise TransitServiceError("HTTP Error {code}".format(code=response.status_code))
    base_dict = response.json()
    return base_dict


def get_minutes_until_arrival(time):
    delta = time - datetime.utcnow()
    mins = int(delta.total_seconds() / 60)
    return mins


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


def format_service_prediction(route_predictions, headline):
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
        >>> api_to_strings("MUNI Arrivals", "sf-muni", {'15553': 'NB', '13338': 'WB'})
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
        #route_predictions = format_factored_out_from_a_t_s(direction, api_key, station_code, mapping, legacy)

        route_predictions_fmt = '<FI>'.join([route['fmt'] for route in route_predictions])
        route_predictions_text = '\n'.join([route['text'] for route in route_predictions])

        service_predictions_fmt.append(direction_color.format(routes=route_predictions_fmt))
        service_predictions_text.append(route_predictions_text)

    return {"fmt": opening_fmt + "<FI>".join(service_predictions_fmt),
            "text": opening_text + "\n".join(service_predictions_text)}


def format_factored_out_from_a_t_s(predictions, direction, mapping):
    route_predictions = []
    for route, times in predictions.items():
        if times:
            route_predictions.append(format_route_times(route, times, direction, mapping))
    return route_predictions


def predict_factored_out_from_a_t_s(api_key, agency, station_code, mapping, legacy=False):
    if legacy:
        predictions = request_511_xml(station_code)
    else:
        predictions = parse_511_json(api_key, agency, station_code, mapping)
    return predictions


def api_to_strings(api_key, agency, station_codes, mapping, legacy, headline):
    for station_code, direction in station_codes.items():
        predictions = predict_factored_out_from_a_t_s(api_key, agency, station_code, mapping, legacy)
        route_predictions = format_factored_out_from_a_t_s(predictions, direction, mapping)
        formatted_prediction = format_service_prediction(route_predictions, headline, station_code)
    return



def predict_from_direct_call(api_key=None):
    """
    Pulls bus prediction info for some preconfigured stops, routes, and providers.
        This function exists for convenience, and is just sugar over the format_service_prediction function.

    Returns:
        list: Dicts containing formatted and human-readable route information for given providers and service times.

    Examples:
        >>> predict_from_direct_call()
        ['fmt': 'abcde', 'text': 'defgh']
    """
    if not api_key:
        api_key = XML_TOKEN

    # services = [default_transit_services.bart, default_transit_services.muni]
    #
    predictions = []
    # for line in services:
    #     name = line['name']
    #     agency = line['agency']
    #     stops = line['stops']
    #     mapping = line['mapping'] if line.get('mapping') else {}
    #     predictions.append(api_to_strings(headline=name, agency=agency, station_codes=stops, api_key=api_key, mapping=mapping))

    # Caltrain Hack
    caltrain = default_transit_services.caltrain
    predictions.append(api_to_strings(caltrain['name'], caltrain['agency'], caltrain['stops'], api_key=XML_TOKEN, legacy=True))

    return predictions


class TransitPredictor(object):
    """
    """
    def __init__(self, agency, station_codes, api_key, headline=None, mapping=None):
        self.agency = agency
        self.station_codes = station_codes
        self.api_key = api_key
        self.headline = headline if headline else agency
        self.mapping = mapping if mapping else {}
        self.prediction_times = {} # OrderedDict of OrderedDicts
        self.prediction_etas = {} # OrderedDict of OrderedDicts
    
    def refresh_predictions(self):
        predictions = OrderedDict()
        for station_code, direction in self.station_codes.items():
            raw_prediction = request_511_json(self.api_key, self.agency, station_code)
            predictions[station_code] = parse_511_json(raw_prediction, self.mapping)
        self.prediction_times = predictions

    def get_times_from_predictions(self):
        prediction_etas = OrderedDict()
        for station_code, lines_times in self.prediction_times.items():
            stop_etas = OrderedDict()
            for line, times in lines_times.items():
                stop_etas[line] = [get_minutes_until_arrival(time) for time in times]
            prediction_etas[station_code] = stop_etas
        self.prediction_etas = prediction_etas

    def get_prediction_strings(self):
        prediction_strings = []
        for station_code, route_predictions in self.prediction_etas.items():
            # OrderedDict of routes/times
            for route, arrivals in route_predictions.items():
                direction = self.station_codes[station_code]
                prediction_strings.append(format_route_times(route, arrivals, direction, self.mapping))
        return prediction_strings


