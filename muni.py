from collections import OrderedDict

import api_511

STATION_CODES = OrderedDict([('15553', 'NB'), ('13338', 'WB'), ('15554', 'SB')])


def get_predictions():
    muni_predictions = "<CP>MUNI Arrivals<FI>"
    direction_string = "<SA>{routes}<FI>"
    for station_code, direction in STATION_CODES.items():
        route_predictions = []
        predictions = api_511.request_511_xml(station_code)
        for route, times in predictions.items():
            route_predictions.append(api_511.format_route_times(route, times, direction))
        muni_predictions += direction_string.format(routes='<FI>'.join(route_predictions))

    return muni_predictions
