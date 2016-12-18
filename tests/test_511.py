from unittest import TestCase
import json
import datetime
import api_511
from collections import OrderedDict


class TestJSONParse(TestCase):
    def setUp(self):
        self.now = datetime.datetime(2016, 7, 15, 14, 22)
        self.now_string = "2016-07-15T14:22Z"
    def test_BART_normal(self):
        import datetime
        with open("sample_response.json", 'r') as response_file:
            response_dict = json.load(response_file)
            arrivals = api_511.parse_511_json(response_dict)
            self.assertEqual(list(arrivals.keys()), ['764', '243', '722', '385', '671'])
            expected_result = OrderedDict([('764', [datetime.datetime(2016, 7, 15, 14, 24),
                                                    datetime.datetime(2016, 7, 15, 14, 39),
                                                    datetime.datetime(2016, 7, 15, 14, 54)]),
                                           ('243', [datetime.datetime(2016, 7, 15, 14, 29),
                                                    datetime.datetime(2016, 7, 15, 14, 44),
                                                    datetime.datetime(2016, 7, 15, 14, 59)]),
                                           ('722', [datetime.datetime(2016, 7, 15, 14, 32),
                                                    datetime.datetime(2016, 7, 15, 14, 47),
                                                    datetime.datetime(2016, 7, 15, 15, 2)]),
                                           ('385', [datetime.datetime(2016, 7, 15, 14, 35),
                                                    datetime.datetime(2016, 7, 15, 14, 50)]),
                                           ('671', [datetime.datetime(2016, 7, 15, 14, 52),
                                                    datetime.datetime(2016, 7, 15, 15, 7),
                                                    datetime.datetime(2016, 7, 15, 15, 22)])])
            self.assertEqual(arrivals, expected_result)

    def test_bart_with_mapping(self):
        pass

    def test_caltrain_blank(self):
        with open("sample_blank_response.json", "r") as response_file:
            import json
            response_dict = json.load(response_file)
            arrivals = api_511.parse_511_json(response_dict)
            self.assertEqual(arrivals, OrderedDict())


class TestMinutesUntilArrival(TestCase):
    def test_5_minutes(self):
        now = datetime.datetime(2016,1,1,0,0,0)
        arrival = datetime.datetime(2016,1,1,0,5,0)
        self.assertEqual(api_511.get_minutes_until_arrival(arrival, now), 5)

    def test_90_seconds(self):
        now = datetime.datetime(2016, 1, 1, 0, 0, 0)
        arrival = datetime.datetime(2016, 1, 1, 0, 1, 30)
        self.assertEqual(api_511.get_minutes_until_arrival(arrival, now), 1)

class TestFormatRouteTimes(TestCase):
    def test_like_doctest(self):
        self.assertEqual(api_511.format_route_times('14', [3, 11, 17], 'NB'),
                         {'fmt': '<CM>14 <CF>NB <CB>3,11,17', 'text': '14 (NB): 3,11,17'})