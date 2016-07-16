"""
Thank you for taking your time to read the source code.
This code is, unfortunately, full of workarounds and redundant.
I might have to rewrite it later. In the meanwhile, at least it works!
>> You have to rewrite it? Sweet, I'll take that as consent to break everything.
"""

from datetime import datetime
from time import sleep

import subprocess
import argparse

import default_transit_services
from api_511 import TransitPredictor
import api_511

parser = argparse.ArgumentParser(description="Display transit info on Noiseboard")
parser.add_argument('-k', help="Manually specify an API key")
args = parser.parse_args()

manual_api_key = args.k


def get_default_predictors(api_key=None):
    transit_predictors = []
    default_services = [default_transit_services.bart, default_transit_services.muni]
    for transit_service in default_services:
        transit_predictors.append(
            TransitPredictor(transit_service.get('agency'), transit_service.get('stops'), api_key,
                             transit_service.get('name'), transit_service.get('mapping')))
    return transit_predictors

manual_api_key = '115b93e5-c32a-4fd7-a836-f9b90b89e9ff'  # TODO knock this testing token out

current_api_key = manual_api_key if manual_api_key else api_511.DEFAULT_NEXTGEN_TOKEN
# predictors = get_default_predictors(api_key)

try:
    while True:
        messages = []

        # for service in predictors:
        #     service.refresh_predictions()
        #     service.get_times_from_predictions()
        #     messages.append(service.get_prediction_strings())

        for service in api_511.predict_from_direct_call():
            messages.append(service)

        date_string = datetime.now().strftime('%m/%e %R')
        messages.append({'fmt': date_string, 'text': date_string})

        board_messages = [line['fmt'] for line in messages]
        terminal_messages = [line['text'] for line in messages]

        single_string_fmt = '<FI>'.join(board_messages)
        single_string_text = '\n'.join(terminal_messages)

        print(single_string_text)

        display_text = "<ID01><PA>  <FD>{}\r\n".format(single_string_fmt)
        subprocess.call('printf "{text}" > /dev/ttyS0'.format(text=display_text), shell=True)
        sleep(60)
finally:
    display_text = 'printf "<ID01><PA><SE>  Noiseboard is dead <FI> check console :(  \r\n" > /dev/ttyS0'
    subprocess.call(display_text, shell=True)
