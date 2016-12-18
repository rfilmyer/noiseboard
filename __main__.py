"""
Thank you for taking your time to read the source code.
This code is, unfortunately, full of workarounds and redundant.
I might have to rewrite it later. In the meanwhile, at least it works!
>> You have to rewrite it? Sweet, I'll take that as consent to break everything.
"""

from datetime import datetime
from time import sleep

#import subprocess
import argparse

import requests

import default_transit_services
from api_511 import TransitPredictor
import api_511

import serial

parser = argparse.ArgumentParser(description="Display transit info on Noiseboard")
parser.add_argument('-k', help="Manually specify an API key")
parser.add_argument('-p', type=str, help="Send data to Prolite board on a given serial port")
args = parser.parse_args()

manual_api_key = args.k
serial_port = args.p


def get_default_predictors(api_key=None):
    """
    Returns the preconfigured TransitPredictors

    Args:
        api_key: An API key used to make calls to the 511 API

    Returns:
        list: A list of TransitPredictor objects

    """
    transit_predictors = []
    default_services = [default_transit_services.bart, default_transit_services.muni, default_transit_services.caltrain]
    for transit_service in default_services:
        transit_predictors.append(
            TransitPredictor(transit_service.get('agency'), transit_service.get('stops'), api_key,
                             transit_service.get('name'), transit_service.get('mapping')))
    return transit_predictors

current_api_key = manual_api_key if manual_api_key else api_511.DEFAULT_NEXTGEN_TOKEN
predictors = get_default_predictors(current_api_key)

refresh_time_in_minutes = 6  # Refresh API predictions every X minutes.
# This should be equal to the number of stops you have. The current API rate limits to 60 requests per hour.

with serial.Serial(serial_port, 300) as prolite:
    while True:
        with requests.Session() as session:
            for minutes_in_loop in range(refresh_time_in_minutes):
                messages = []

                for service in predictors:
                    if minutes_in_loop == 0:
                        service.refresh_predictions(session)
                    service.get_times_from_predictions()
                    messages.append(service.get_prediction_strings())

                date_string = datetime.now().strftime('%m/%e %R')
                messages.append({'fmt': date_string, 'text': date_string})

                board_messages = [line['fmt'] for line in messages]
                terminal_messages = [line['text'] for line in messages]

                single_string_fmt = '<FI>'.join(board_messages)
                single_string_text = '\n'.join(terminal_messages)

                print(single_string_text)

                display_text = "<ID01><PA>  <FD>{}\r\n".format(single_string_fmt)
                #subprocess.call('printf "{text}" > /dev/ttyS0'.format(text=display_text), shell=True)
                prolite.write(display_text)
                sleep(60)
