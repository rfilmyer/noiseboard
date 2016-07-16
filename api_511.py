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


def parse_511_json(parsed_response, mapping=None):
    """
    Extracts useful information of the JSON response from 511.org's stop prediction API.

    Args:
        parsed_response (dict): The dict from the parsed JSON of the 511 API response.
        mapping (dict):
    Returns:
        OrderedDict: Lines and ETAs for routes at the station. Exists as an OrderedDict for consistent order.
    """
    predictions = OrderedDict()

    for journey in parsed_response['ServiceDelivery']['StopMonitoringDelivery']['MonitoredStopVisit']:
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


def request_511_json(api_key, agency, stopcode, session=None):
    """
    Makes a request

    Args:
        api_key (str): The API token to authorize the request.
        agency (str): The agency identifier (eg 'sf-muni') for which to get stop responses.
        stopcode (str or int): The stopcode/ stop ID to pull requests for.
            In the future, this can be made optional, which returns every stopcode
                but takes 5-7 seconds for larger transit agencies.
        session (requests.Session): If you are making multiple requests,
            consider using a Session object from the requests library.

    Returns:
        dict: The parsed JSON from the response to the API.

    """
    api_request = {'format': 'json', 'api_key': api_key,
                   'agency': agency, 'stopCode': stopcode}

    if session:
        response = session.get(NEXTGEN_URL, params=api_request)
    else:
        response = requests.get(NEXTGEN_URL, params=api_request)
    if response.status_code != 200:
        if response.status_code == 429:
            raise TransitServiceError("Rate Limited/HTTP Error 429:" + "\n" + response.text)
        elif response.status_code == 401:
            raise TransitServiceError("Unauthorized/HTTP Error 401:" + "\n" + response.text)
        else:
            raise TransitServiceError("HTTP Error {code}".format(code=response.status_code))

    response.encoding = "utf-8-sig"
    base_dict = response.json()
    return base_dict


def get_minutes_until_arrival(time):
    """
    Returns the number of minutes between a specified time (in UTC) and now.

    Args:
        time (datetime.datetime): A given time, in UTC.

    Returns:
        int: How many minutes until the given time.

    """
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
        mapping (dict): A dict that is used to convert route designations
            (for example, BART line 1561 is a SFO/Millbrae train, so an entry {"1561": "SFO/M"}
            is useful to convert these internal numbers into something more readable)

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
    return {"fmt":  route_info_fmt.format(route=route, times=minutes, dir=direction_fmt),
            "text": route_info_text.format(route=route, times=minutes, dir=direction_text)}


def format_service_prediction(route_predictions, headline):
    """
    Returns a formatted string combining prediction times for different stops and lines
        under a single banner for a provider.

    Args:
        route_predictions (list): List containing dicts of pre-formatted predictions for one or multiple stops.
            Board-formatted string is in "fmt", Human-readable in "text".
        headline (str): Stop predictions will be preceded with this header,
            useful for distinguishing different transit providers.

    Returns:
        dict: Strings corresponding to bus stop predictions.
            Board-formatted string is in "fmt", Human-readable in "text".
    """
    opening_fmt = "<CP>{headline}<FI>".format(headline=headline)
    opening_text = "{headline}:\n".format(headline=headline)

    direction_color = "<SA>{routes}"
    service_predictions_fmt = []
    service_predictions_text = []

    route_predictions_fmt = '<FI>'.join([route['fmt'] for route in route_predictions])
    route_predictions_text = '\n'.join([route['text'] for route in route_predictions])

    service_predictions_fmt.append(direction_color.format(routes=route_predictions_fmt))
    service_predictions_text.append(route_predictions_text)

    return {"fmt": opening_fmt + "<FI>".join(service_predictions_fmt),
            "text": opening_text + "\n".join(service_predictions_text)}


def direct_api_call(station_code, api_key=None, agency=None, mapping=None, legacy=False):
    """
    One-size-fits-all function returning raw predictions from either the old or the new API

    Args:
        station_code (int or str): The ID of the station getting requests
        api_key (str): A token used to get requests. Not needed for legacy.
        agency (str): An agency identifier for the new API
        mapping (dict): Renaming line numbers to something else
        legacy (bool): Whether to use the new or the old 511.gov API.

    Returns:
        OrderedDict: Lines and ETAs for routes at the station. Exists as an OrderedDict for predictability's sake.

    """
    if legacy:
        predictions = request_511_xml(station_code)
    else:
        request = request_511_json(api_key, agency, station_code)
        predictions = parse_511_json(request, mapping)
    return predictions


def api_to_strings(headline, station_codes, api_key=None, agency=None, mapping=None, legacy=False):
    """
    The old, non-classed based method of fetching and formatting predictions

    Args:
        headline:
        station_codes (dict): A dict where keys are stopcodes/IDs
            and values are their direction ('NB', 'IB') or empty strings.
        api_key: A token used to get requests. Not needed for legacy.
        agency: An agency identifier for the new API
        mapping (dict): Renaming line numbers to something else
        legacy (bool): Whether to use the new or the old 511.gov API.

    Returns:
        dict: formatted and human-readable strings containing predictions

    """
    route_predictions = []
    for station_code, direction in station_codes.items():
        predictions = direct_api_call(station_code, api_key, agency, mapping, legacy)
        for route, times in predictions.items():
            if times:
                route_predictions.append(format_route_times(route, times, direction, mapping))

    formatted_predictions = format_service_prediction(route_predictions, headline)
    return formatted_predictions


def predict_from_direct_call(api_key=None):
    """
    Pulls bus prediction info for some pre-configured stops, routes, and providers.
        This function exists for convenience, and is just sugar over the format_service_prediction function.

    Returns:
        list: Dicts containing formatted and human-readable route information for given providers and service times.

    Examples:
        >>> predict_from_direct_call()
        ['fmt': 'abcde', 'text': 'defgh']
    """
    if not api_key:
        api_key = XML_TOKEN

    predictions = []

    # Caltrain Hack
    caltrain = default_transit_services.caltrain
    caltrain['stops'] = OrderedDict([('15553', 'NB'), ('13338', 'WB'), ('15554', 'SB')])
    predictions.append(api_to_strings(caltrain['name'], caltrain['stops'], api_key=XML_TOKEN, legacy=True))

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
        self.prediction_times = {}  # OrderedDict of OrderedDicts
        self.prediction_etas = {}  # OrderedDict of OrderedDicts
    
    def refresh_predictions(self, session=None):
        predictions = OrderedDict()
        for station_code, direction in self.station_codes.items():
            raw_prediction = request_511_json(self.api_key, self.agency, station_code, session)
            predictions[station_code] = parse_511_json(raw_prediction, self.mapping)
        self.prediction_times = predictions

    def get_times_from_predictions(self):
        prediction_etas = OrderedDict()
        for station_code, lines_times in self.prediction_times.items():
            stop_etas = OrderedDict()
            for line, times in lines_times.items():
                etas = []
                for time in times:
                    eta = get_minutes_until_arrival(time)
                    if eta <= 0:
                        etas.append(eta)
                stop_etas[line] = etas
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


