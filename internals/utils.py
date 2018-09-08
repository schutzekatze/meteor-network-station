from shutil import disk_usage
import traceback
import time
import random
import logging
import requests
import json
import math
import pprint
from os.path import realpath
from . import constants

def sleep():
    delay = random.randint(int(constants.WAKEUP_PERIOD_MIN * 60), int(constants.WAKEUP_PERIOD_MAX * 60))
    logging.getLogger("Utils").debug("Sleeping for {}.".format(delay))
    time.sleep(delay)

def is_night():
    current_time = time.strftime('%H:%M')
    return (constants.NIGHT_START <= current_time <= constants.NIGHT_END) or \
           ( \
               ((constants.NIGHT_START <= current_time) or (current_time <= constants.NIGHT_END)) and \
                 constants.NIGHT_END < constants.NIGHT_START \
            )

def get_trace(exception):
    return str(''.join(traceback.format_tb(exception.__traceback__))) + str(exception)

def station_get_status(network_id, station_info, ucontrollers):
    logger = logging.getLogger("Utils")
    logger.debug("Gathering status data...")

    station_status = {}

    if network_id != None: station_status['network_id'] = network_id
    station_status['timestamp'] = int(time.time())

    for key in station_info.get('station'):
        value = station_info.get('station', key)
        try:
            value = float(value)
        except ValueError:
            pass
        station_status[key] = value

    components = []

    computer = {}
    computer['name'] = 'Computer'

    measurements = {}
    total_bytes, used_bytes, free_bytes = disk_usage(realpath('/'))
    measurements['Disk used'] = str(used_bytes / (1024 ** 3))
    measurements['Disk cap'] = str(total_bytes / (1024 ** 3))
    computer['measurements'] = measurements

    components.append(computer)

    measurements_list = ucontrollers.get_measurements_list()
    for measurement in measurements_list:
        component = {}
        component['name'] = measurement['name']
        component['measurements'] = measurement['data']
        components.append(component)

    station_status['components'] = components

    maintainers = []
    i = 1
    while True:
        maintainer = station_info.get('maintainer' + str(i))
        maintainer_data = {}
        if maintainer == None:
            break
        for key in maintainer:
            maintainer_data[key] = maintainer[key]
        maintainers.append(maintainer_data)
        i += 1
    station_status['maintainers'] = maintainers

    logger.debug("Status data gathered.")
    logger.debug("Status:\n" + pprint.pformat(station_status))

    return station_status

def status_format(status):
    data = {}
    for key in status:
        value = status[key]
        if type(value) is dict or type(value) is list or type(value) is tuple:
            data[key] = json.dumps(value)
        else:
            data[key] = value
    return data

def station_register(station_status):
    logger = logging.getLogger("Utils")

    try:
        logger.info("Registering station...")

        response = requests.post(constants.URL_REGISTER, data=status_format(station_status), verify=False)
        response.raise_for_status()

        logger.info("Station registered successfully.")
        return response.text
    except requests.exceptions.ConnectionError:
        logger.warning("Could not connect to the registration server.")
    except requests.exceptions.RequestException:
        logger.warning("The registration server returned an error.")

    return None
