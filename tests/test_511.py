from unittest import TestCase
import json
import api_511
from collections import OrderedDict


class TestJSONParse(TestCase):
    def setUp(self):
        import datetime
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

    def test_caltrain_blank(self):
        with open("sample_blank_response.json", "r") as response_file:
            import json
            response_dict = json.load(response_file)
            arrivals = api_511.parse_511_json(response_dict)
            self.assertEqual(arrivals, OrderedDict())



TestJSONParse()
