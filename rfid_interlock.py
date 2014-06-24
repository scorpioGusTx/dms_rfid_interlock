#! /usr/bin/python

#
#  contact Brooks Scarff for Networks
#  contact Paul Brown for config
#
#  Gus Reiter todo:
#    rfid reader from ebay.
#    fix: "active": {"output": "ON", "seconds": 2}
#    play with current sensing
#    play with PIR
#    handle errors
#    document
#

from datetime import datetime, timedelta
import time, json, serial, threading, Queue, sys, fcntl, os
#, collections

from evdev import InputDevice, ecodes
import lcd_i2c_p018

import urllib2
from uuid import getnode as get_mac_address

import Adafruit_BBIO.ADC  as ADC
import Adafruit_BBIO.GPIO as GPIO

import configuration

import logging
import logging.config
import logging.handlers

################################################################################
#
#  action_queue
#
################################################################################
POWER_UP          = "power_up"
ACTIVE            = "active"
INACTIVE_SOON     = "inactive_soon"
INACTIVE          = "inactive"
ERROR             = "error"
ERROR_CONFIG      = "error:config"
ERROR_NETWORK     = "error:network"
ERROR_MAINTENANCE = "error:maintenance"

TESTING_NETWORK   = "testing_network"
CHECKING_BADGE    = "checking_badge"
LOGIN_DENIED      = "login_denied"

RESET_TIMER       = "reset_timer"

INTERLOCK_STATES = [
    POWER_UP,
    ACTIVE,
    INACTIVE_SOON,
    INACTIVE,
    ERROR,
    ERROR_CONFIG,
    ERROR_NETWORK,
    ERROR_MAINTENANCE,
    TESTING_NETWORK,
    CHECKING_BADGE,
    LOGIN_DENIED
]

INTERLOCK_INFO_ONLY = [
    TESTING_NETWORK,
    CHECKING_BADGE,
    LOGIN_DENIED
]

INTERLOCK_MESSAGES = INTERLOCK_STATES + [ RESET_TIMER ]

################################################################################
#
#  custom logging handler
#
################################################################################

class ErrorArrayHandler(logging.Handler):
    #
    # http://pantburk.info/?blog=77
    #
    """
    this is a logging handler which puts all messages that it receives into an
    array so that you can display them later if you like.
    """
    def __init__(self):
        logging.Handler.__init__(self)
        self.clear_errors()

    def emit(self, record):
        self.errors.append(record)

    def clear_errors(self):
        self.errors = []

    def get_errors(self):
        return self.errors

################################################################################
#
#  generic rfid_reader
#
################################################################################

class rfid_reader(threading.Thread):
    """ 
    an object which hides the details of the rfid reader.
    As long as read() is provided, its all good. 

    Badge 10216663 is active for all 4 tools. 
       So, you can switch tool=4 to 1,2, or 3 to get different timeouts. 
    Badge 11861477 is active for tools 1 and 2 
    Badge 10216663 is valid only on tool 1

    blue keyfob:    21505625070
    white circle:   12885801092
    white rectangle 25779665946
    """
    def __init__(self, rfid_config, tool_id, action_queue):
        log = logging.getLogger("rfid_reader.init")
        log.info("tool_id is " + tool_id)
        #
        # Help adapt to understand the rfid code
        #
        self.code_skip_chars = rfid_config.get("code_skip_chars", None)
        self.code_len = rfid_config.get("code_len", None)
        self.code_base = rfid_config.get("code_base", 16)

        threading.Thread.__init__(self)
        self.tool_id      = tool_id
        self.action_queue = action_queue

        #
        # for caching the rfid codes so that we are not unnecessarily hitting 
        # makermanager
        #
        self.ignore_for_now = dict()
        self.last_status = None

    def translate_test(self, badge_decimal):
        log= logging.getLogger("rfid_reader.translate")
        log.info("in translate_test()")

        badge_translation = {
            "21505625070": {
                "description": "blue keyfob",
                "translate_to": "11861477", 
                "valid_tools": [1, 2]
            },
            "12885801092": {
                "description": "white circle",
                "translate_to": "10216663", 
                "valid_tools": [1]
            },
            "25779665946": {
                "description": "white rectangle", 
                "translate_to": "10216663",
                "valid_tools": [1, 2, 3, 4]
            }
        }
        # tool 1: Cabinet Saw
        # tool 2: Laser Cutter
        # tool 3: Plasma Cutter
        # tool 4: Mill

        if badge_decimal in badge_translation:
            log.info("translating: " + badge_decimal + " to: " + 
                        badge_translation[badge_decimal]['translate_to'])

            badge_decimal = badge_translation[badge_decimal]['translate_to']
        return badge_decimal

    def run(self):
        """ 
        tells the interlock when we scan a badge indicating a person has 
        permission to use this equipment
        """

        log_run = logging.getLogger("rfid_reader.run")
        log_read = logging.getLogger("rfid_reader.read")
        log_throttle = logging.getLogger("rfid_reader.throttle")
        log_code = logging.getLogger("rfid_reader.code")
        log_makermanager = logging.getLogger("rfid_reader.makermanager")

        log_run.info("in rfid_reader.run()")

        ignore_scan_period = timedelta(seconds = 3)

        while True:
            badge_raw = self.input.readline().rstrip()
            log_read.info("read in badge '" + badge_raw + "'")
            self.action_queue.put((CHECKING_BADGE, "rfid_reader.run()") )

            #
            # delete old scans
            #
            for del_badge in self.ignore_for_now.keys():
                log_throttle.info("comparing: " + 
                        str(self.ignore_for_now[del_badge]) +
                        " with " + str(datetime.now()))
                if self.ignore_for_now[del_badge] < datetime.now():
                    log_throttle.info("removing " + str(del_badge))
                    del self.ignore_for_now[del_badge]

            #
            # if the badge has been recently scanned, do not process it, but 
            # remember that it was just now scanned.
            #
            log_throttle.debug("checking for " + badge_raw + " in " + 
                    str(self.ignore_for_now))
            if badge_raw in self.ignore_for_now:
                if badge_raw <> "":
                    log_throttle.debug("ignoring " + badge_raw + " for now")
                    badge_raw = ""
            else:
                ignore_until = datetime.now() + ignore_scan_period
                self.ignore_for_now[badge_raw] = ignore_until
                log_throttle.debug("added " + badge_raw + " to " + 
                        str(self.ignore_for_now))

            #
            # let's check to see if we have an authorized badge
            #
            if (badge_raw <> ""):
                try:
                    badge_raw = badge_raw[self.code_skip_chars: self.code_len]; # drop the checksum
                    badge_decimal = str(int(badge_raw, self.code_base)) 
                    log_code.info("rfid_reader.run(): badge code is " + 
                                str(badge_decimal))
                    #
                    # translate
                    #
                    badge_decimal = self.translate_test(badge_decimal)

                    url = ''.join([
                        "https://dallasmakerspace.org/makermanager/index.php?",
                        "r=api/toolValidate",
                        "&badge=" + badge_decimal,
                        "&tool=" + self.tool_id ])
                    log_makermanager.info("rfid_reader.run(): sent: " + url)
                    json_response = urllib2.urlopen(url).readline()
                    log_makermanager.info("rfid_reader.run(): got: " + 
                            json_response)

                    if json_response <> "":
                        response = json.loads(json_response)
                        if response['authorized'] == True:
                            if str(response['machine_id']) == self.tool_id:
                                self.action_queue.put((ACTIVE, "rfid_reader.run()"))
                        else:
                            self.action_queue.put((LOGIN_DENIED, "rfid_reader.run()") )
                except ValueError, e:
                    log_read.error("Cannot convert " + badge_raw + " into decimal")
                except urllib2.HTTPError, e:
                    self.action_queue.put((ERROR_NETWORK, "rfid_reader: Cannot contact makermanager (HTTP)"))
                    log_run.error("Cannot contact makermanager (HTTP)")
                except urllib2.URLError, e:
                    self.action_queue.put((ERROR_NETWORK, "rfid_reader: Cannot contact makermanager (URL)"))

    def update(self, status):
        log_update = logging.getLogger("rfid_reader.update")
        if self.last_status <> status:
            self.ignore_for_now.clear()
            self.last_status = status
            log_update.info("rfid_reader.update():" + 
                        " status changed, clearing rfid cache")


class serial_rfid_reader(rfid_reader):
    """
    serial rfid_reader
    """
    def __init__(self, rfid_config, connection, tool_id, action_queue):
        log = logging.getLogger("serial_rfid_reader.init")
        log.info("in serial_rfid_reader.__init__()")
        rfid_reader.__init__(self, rfid_config, tool_id, action_queue)
        if 'baud' in rfid_config:
            self.input = serial.Serial(connection, rfid_config['baud'])
        else:
            raise 

################################################################################
#
#  stdin rfid_reader
#
################################################################################

class keyboard_rfid_reader(rfid_reader):
    def __init__(self, rfid_config, connection, tool_id, action_queue):
        log = logging.getLogger("keyboard_rfid_reader.init")
        log.info("in keyboard_rfid_reader.__init__()")
        #
        # may need to pass connection into the parent __init__
        rfid_reader.__init__(self, rfid_config, tool_id, action_queue)
        if connection == "stdin":
            self.input = sys.stdin
        else:
            raise 

################################################################################
#
#  input_event rfid_reader
#
################################################################################

class input_event_stream:
    """
    This class provides a stream like interface into a device file that only
    responds to input event calls
    """
    def __init__(self, device_filename, scan_to_char = None):
        log = logging.getLogger("input_event_rfid_reader.init")
        try:
            self.device = InputDevice(device_filename)
        except OSError:
            log.error("cannot open " + device_filename)
            throw

        default_scan_to_char = ["", ""] + [str(x) for x in range(1, 10)] + ['0'] + ([""] * 16) + ["\n"] + [""] * 100
        self.scan_to_char = scan_to_char if scan_to_char <> None else default_scan_to_char

    def readline(self):
        line = ""
        for event in self.device.read_loop():
            if event.type == ecodes.EV_KEY and event.value == 1:
                if self.scan_to_char[event.code] == "\n":
                    break
                else:
                    line += self.scan_to_char[event.code]
        return line

class input_event_rfid_reader(rfid_reader):
    def __init__(self, rfid_config, connection, tool_id, action_queue):
        log = logging.getLogger("input_event_rfid_reader.init")
        log.info("in input_event_rfid_reader.__init__()")
        rfid_reader.__init__(self, rfid_config, tool_id, action_queue)
        self.input = input_event_stream(connection)

################################################################################
#
#  generic output controls
#
################################################################################

class status_indicator:
    """ 
    a generic status indicator, 
    providing base functionality regardless of the output
    """

    def update(self, status):
        """ 
        call with one of these parameters:
        : ACTIVE
        : INACTIVE_SOON
        : INACTIVE
        """
        pass

################################################################################
#
#  digital gpio status_indicator
#
################################################################################

class lcd_p018_output(status_indicator, threading.Thread):
    def __init__(self, connection_config, connection):
        log = logging.getLogger("lcd_p018_output.init")
        log.info("creating: " + connection)
        self.mode = None
        self.lcd = None
        self.timer = None
        self.saved_status = None

        connection_parts = connection.split(":")
        error_prefix =  connection + ": "

        if connection not in ("i2c:0:x38", "i2c:1:x38", "i2c:0:0x38", "i2c:1:0x38"):
            log.error(error_prefix + "needs to be i2c:0:x38, i2c:1:x38, i2c:0:0x38, or i2c:1:0x38")
        else:
            self.i2c_bus_number = int(connection.split(":")[1])
            self.lcd = lcd_i2c_p018.lcd(self.i2c_bus_number)

        #
        # these are indexed by INTERLOCK_STATES
        #
        self.state_to_actions = {}
        state_configs = {
                state: state_config 
                for state, state_config in connection_config.items()
                if state in INTERLOCK_STATES}

        for state, state_config in state_configs.items():
            error_prefix =  connection + ": " + state + ": "
            log.info(connection + ": " + state + ", " + 
                    "state_config: " + str(state_config))

            if isinstance(state_config, dict):
                #
                # process more complex configuration, such as:
                #    "active": {
                #               "color":   (0, 255, 255),
                #        "message": ["line 1 message", "line 2 message"]
                #        "timeout": 3,
                #    }
                # timeout specifies how many seconds to stay on before going back to the previous message
                #

                #
                # get the color
                #
                action = {
                    "message": [" -- oo OO oo -- ", " -- oo OO oo -- "], 
                    "color":     (128, 128, 128), 
                    "timeout": None
                }
                if 'message' not in state_config:
                    log.error(error_prefix + "message: missing")
                elif (type(state_config['message']) <> list or 
                        len(state_config['message']) != 2 or
                        len([ len(message) for message in state_config['message'] if len(message) > self.lcd.columns ]) > 0):
                    log.error(error_prefix + "message: needs to be an array of 2 strings of " + self.lcd.columns + " characters")
                else:
                    action["message"] = state_config['message']

                #
                # get the color
                #
                if 'color' not in state_config:
                    log.error(error_prefix + "color: missing")
                elif (type(state_config['color']) <> list or
                        len(state_config['color']) <> 3 or
                        len([ elment for element in state_config['color'] if type(element) not in (int, float) ]) or
                        len([ number for number in state_config['color'] if number > 255 or number < 0 ]) ):
                    log.error(error_prefix + "message: needs to be a tuple of 3 numbers between 0 and 255")
                else:
                    action["color"] = state_config['color']

                #
                # get the timeout
                #
                try:
                    timeout = float(state_config['timeout'])
                    log.info(error_prefix + ": timeout:" + str(timeout))
                except KeyError:
                    timeout = None
                    log.info(error_prefix + ': timeout defaulting to "always"')
                except ValueError:
                    timeout = None
                    log.error(error_prefix + state_config['timeout'] + 
                            " needs to be a float or an int")
                action["timeout"] = timeout

                self.state_to_actions[state] = action
            else:
                #
                # not quite sure how to process this
                #
                log.error(error_prefix + str(state_config) + \
                            ": should be one of: " + ", ".join(state_to_function_mapping.keys()) )
        self.update(POWER_UP)

    def update(self, status):
        """ 
        call with one of these parameters:
        : ACTIVE
        : INACTIVE_SOON
        : INACTIVE
        """

        log = logging.getLogger("lcd_p018_output.update")
        log.info(str(self.i2c_bus_number) + " gets " +  status)

        if status in self.state_to_actions:
            log.info(str(self.i2c_bus_number) + " displays " +  status)
            action = self.state_to_actions[status]

            log.debug(str(self.i2c_bus_number) + ": color:   " + str(action['color']))
            log.debug(str(self.i2c_bus_number) + ": message: " + str(action['message']))
            log.debug(str(self.i2c_bus_number) + ": timeout: " + str(action['timeout']))

            self.lcd.show_rgb(action['message'], action['color'])

            if self.timer <> None:
                self.timer.cancel()

            if action['timeout']:
                self.timer = threading.Timer(action['timeout'], self.reset_message)
                self.timer.start()
            elif status not in INTERLOCK_INFO_ONLY:
                self.saved_status = status

            log.debug(str(self.i2c_bus_number) + ": returned from call")

        else:
            log.info("nothing configured")

    def reset_message(self):
        if self.saved_status != None:
            action = self.state_to_actions[self.saved_status]
            self.lcd.show_rgb(action['message'], action['color'])


################################################################################
#
#  digital gpio status_indicator
#
################################################################################

class digital_output(status_indicator, threading.Thread):
    """ 
    control the works with digital output
    """

    def __init__(self, connection_config, connection):
        log = logging.getLogger("digital_output.init")
        log.info("creating: " + connection)

        #
        # figure out what to do with this pin for all states
        #
        self.control_pin = connection
        self.timer = None
        self.blink_time = None

        #
        # do we want a GPIO.HIGH or GPIO.LOW to turn it "on"
        #
        if connection_config.get("on", "HIGH") == "LOW":
            self.ON = GPIO.LOW
            self.OFF = GPIO.HIGH
        else:
            self.ON = GPIO.HIGH
            self.OFF = GPIO.LOW

        #
        # put one level lower ?
        #
        action_to_function = {
                "OFF":   self.turn_off,
                "ON":    self.turn_on,
                "BLINK": self.blink,
                "SOS":   self.sos
        }

        #
        # these are indexed by INTERLOCK_STATES
        #
        self.state_to_actions = {}
        state_configs = {
                state: state_config 
                for state, state_config in connection_config.items()
                if state in INTERLOCK_STATES}

        for state, state_config in state_configs.items():
            error_prefix =  connection + ": " + state + ": "
            log.info(connection + ": " + state + ", " + 
                    "state_config: " + str(state_config))

            if isinstance(state_config, dict):
                #
                # process more complex configuration, such as:
                #    "active": {
                #        "output": "ON",
                #        "seconds": 3,
                #
                if 'output' not in state_config:
                    log.error(error_prefix + "output: missing")
                elif state_config['output'] in action_to_function:
                    function = action_to_function[state_config['output']]
                    try:
                        seconds = float(state_config['seconds'])
                        self.state_to_actions[state] = {"function": function, "parameter": seconds}
                        log.info(error_prefix + ": seconds:" + str(seconds))
                    except KeyError:
                        seconds = None
                        self.state_to_actions[state] = {"function": function, "parameter": seconds}
                        log.info(error_prefix + ': seconds defaulting to "always"')
                    except ValueError:
                        seconds = None
                        log.error(error_prefix + str(state_config['seconds']) + 
                                " needs to be a float or an int")
                else:
                    log.error(error_prefix + "output: " + state_config['output'] + 
                            ": should be one of: " + ", ".join(action_to_function.keys()) )
            elif state_config in action_to_function:
                #
                # process simple configuration, such as:
                #    "active": "ON"
                #
                function = action_to_function[state_config]
                self.state_to_actions[state] = {"function": function, "parameter": None}
            else:
                #
                # not quite sure how to process this
                #
                log.error(error_prefix + str(state_config) + \
                            ": should be one of: " + ", ".join(state_to_function_mapping.keys()) )

        GPIO.setup(self.control_pin, GPIO.OUT)
        log.info(self.control_pin + "): state actions are: " + ", ".join(self.state_to_actions))
        self.update(INACTIVE)

    def update(self, status):
        """ 
        call with one of these parameters:
        : ACTIVE
        : INACTIVE_SOON
        : INACTIVE
        """

        log = logging.getLogger("digital_output.update")
        log.info(self.control_pin + " gets " +  status)

        if status in self.state_to_actions:
            log.info(self.control_pin + " gets " +  status)
            # print str(self.state_to_actions[status])
            #    self.state_to_actions[state] = {"function": function, "parameter": seconds}

            #
            # just call it
            #
            # self.state_to_actions[status]['function'](self.state_to_actions[status]['parameter'])

            #
            # assign to a temp variable
            #
            # action = self.state_to_actions[status]
            # action['function'](action['parameter'])

            #
            # break it into tiny steps
            #
            # function = self.state_to_actions[status]['function']
            # parameter = self.state_to_actions[status]['parameter']
            # function(parameter)

            #
            # break it into teeny tiny steps
            #
            action = self.state_to_actions[status]

            log.debug(self.control_pin + ": action[parameter]: " + str(action['parameter']))
            log.debug(self.control_pin + ": action.keys(): " + str(action.keys()))

            function = action['function']
            parameter = action['parameter']
            if parameter <> None:
                function(parameter)
            else:
                function()
            log.debug(self.control_pin + ": returned from call")

        elif status == "ERROR": 
            log.info(self.control_pin + ": found ERROR to do")
            self.sos()
        else:
            log.info("nothing configured")

    def turn_on(self, seconds = None):
        log = logging.getLogger("digital_output.turn_on")
        log.info(self.control_pin + ": seconds: " + str(seconds))
        self.clear_threads()
        if seconds == None:
            GPIO.output(self.control_pin, self.ON)
            self.timer = None
        else:
            GPIO.output(self.control_pin, self.ON)
            self.timer = threading.Timer(seconds, self.turn_off)
            # lambda: GPIO.output(self.control_pin, self.OFF))
            log.debug(self.control_pin + ": starting timer")
            self.timer.start()

    def turn_off(self, seconds = None):
        log = logging.getLogger("digital_output.turn_off")
        log.info(self.control_pin + ": (" + str(seconds) + ")")
        self.clear_threads()
        if seconds == None:
            GPIO.output(self.control_pin, self.OFF)
        else:
            self.timer = threading.Timer(seconds, self.turn_on)
            log.debug(self.control_pin + ": starting timer")
            self.timer.start()

    def blink(self, seconds = .5):
        log = logging.getLogger("digital_output.blink")
        log.info(self.control_pin + ": (" + str(seconds) + ")")
        self.clear_threads()
        self.blink_time = seconds
        threading.Thread.__init__(self)
        self.start()

    def sos(self, seconds = None):
        log = logging.getLogger("digital_output.sos")
        log.info(self.control_pin + ": (" + str(seconds) + ")")
        self.clear_threads()
        self.blink_time = "sos"
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        """
        This is used when we blink the output
        """
        log = logging.getLogger("digital_output.run")
        log.info(self.control_pin + ": (" + str(self.blink_time) + ")")
        while self.blink_time <> None:
            if self.blink_time == "sos":
                self.run_sos()
            else:
                self.run_blink()

    def run_blink(self):
        log = logging.getLogger("digital_output.blink")
        log.info(self.control_pin + ": cycle time: " + str(self.blink_time))
        blink_high = True
        while self.blink_time <> None:
            GPIO.output(self.control_pin, 
                    {True: self.ON, False: self.OFF}[blink_high])
            blink_high = not(blink_high)
            time.sleep(self.blink_time)

    def run_sos(self):
        log = logging.getLogger("digital_output.sos")
        log.info(self.control_pin)
        sequence = [
                (.3, self.ON), (.3, self.OFF),
                (.3, self.ON), (.3, self.OFF),
                (.3, self.ON),
                
                (1, self.OFF),

                (1, self.ON), (.3, self.OFF),
                (1, self.ON), (.3, self.OFF),
                (1, self.ON),

                (1, self.OFF),

                (.3, self.ON), (.3, self.OFF),
                (.3, self.ON), (.3, self.OFF),
                (.3, self.ON),

                (2, self.OFF),
        ]

        index = 0
        while self.blink_time == "sos":
            seconds, value = sequence[index]
            GPIO.output(self.control_pin, value)
            time.sleep(seconds)

            index += 1
            index = 0 if index >= len(sequence) else index

    def clear_threads(self):
        if self.timer <> None:
            self.timer.cancel()
        self.blink_time = None

################################################################################
#
#  stdio status_indicator
#
################################################################################

class stdio_output(status_indicator):
    """ 
    show our current state on stdout
    """

    def __init__(self, connection_config, connection):
        log = logging.getLogger("stdio_output.init")
        log.info(connection)
        #
        # these are indexed by INTERLOCK_STATES
        #
        self.state_actions = {}
        state_configs = {
                status: state_config 
                for status, state_config in connection_config.items()
                if status in INTERLOCK_STATES}

        for status, state_config in state_configs.items():
            log.info("adding " + str(status) + " as " + str(state_config))
            self.state_actions[status] = str(state_config)
        self.update(POWER_UP)


    def update(self, status):
        """ 
        call with one of these parameters:
        : ACTIVE
        : INACTIVE_SOON
        : INACTIVE
        """

        if status in self.state_actions:
            print(self.state_actions[status])

################################################################################
#
#  generic monitor
#
################################################################################

class monitor(threading.Thread):
    def __init__(self, digital_config, action_queue):
        self.action_queue = action_queue
        threading.Thread.__init__(self)


################################################################################
#
#  digital monitor
#
################################################################################
class digital_monitor(monitor):
    def __init__(self, digital_config, connection, action_queue):
        log = logging.getLogger("digital_monitor.init")

        monitor.__init__(self, digital_config, action_queue)

        self.connection = connection

        GPIO.setup(self.connection, GPIO.IN)

        #
        # read in the configuration
        #
        triggers = ["FALLING", "RISING"]
        self.trigger_to_new_state = {
                trigger: status
                for status, trigger in digital_config.items()
                if status in INTERLOCK_MESSAGES and trigger in triggers }

        log.info(self.connection + ": " + str(self.trigger_to_new_state))

    def run(self):
        log = logging.getLogger("digital_monitor.run")
        while True:
            if GPIO.input(self.connection):
                GPIO.wait_for_edge(self.connection, GPIO.FALLING)
                message = self.trigger_to_new_state.get("FALLING")
            else:
                GPIO.wait_for_edge(self.connection, GPIO.RISING)
                message = self.trigger_to_new_state.get("RISING")

            if message:
                packet = (message, "digital_monitor: " + self.connection)
                log.info(self.connection + ': sending ' + str(packet))
                self.action_queue.put(packet)


###############################################################################e
#
#  adc monitor
#
################################################################################
class adc_monitor(threading.Thread):
    def __init__(self, adc_config, connection, action_queue):
        monitor.__init__(self, digital_config, action_queue)
        self.connection = connection

        self.message_conditions = dict()
        adc_configs = {
                message: message_config
                for state_config in adc_config.items()
                if message in INTERLOCK_STATES and type(message_config) == dict }

        for message, adc_config in adc_configs:
            conditions = {}
            for key in ['higher', 'lower']:
                try:
                    conditions[key] = float(digital_config.get(key))
                except keyValue, TypeError:
                    pass

            conditions['evaluate'] = "or"
            if "higher" in conditions and "lower" in conditions:
                if conditions['higher'] < conditions['lower']:
                    #
                    # in other words, we are specifying a range
                    #
                    conditions['evaluate'] = "and"
            if conditions:
                self.message_conditions[message] = conditions

        ADC.setup()

    def run(self):
        trash = ADC.read(self.connection)
        while True:
            sleep(.01)
            value = ADC.read(self.connection)
            for message, conditions in self.message_conditions.items():
                if conditions['evaluate'] == "and":
                    trigger = True
                    if 'higher' in conditions:
                        trigger &= value > conditions['higher']
                    if 'lower' in conditions:
                        trigger &= value < conditions['lower']
                else:
                    trigger = False
                    if 'higher' in conditions:
                        trigger |= value > conditions['higher']
                    if 'lower' in conditions:
                        trigger |= value < conditions['lower']
            if trigger:
                self.action_queue.put((
                    message,
                    "digital_monitor: " + self.connection))
                sleep(.5)


class heartbeat(threading.Thread):
    def __init__(self):
        error_maintenance = False
        error_network = False

    def update(self, new_status):
        pass
        # POWER_UP
        # ACTIVE
        # INACTIVE_SOON
        # INACTIVE
        # ERROR
        # ERROR_CONFIG
        # ERROR_NETWORK
        # ERROR_MAINTENANCE

        # TESTING_NETWORK
        # CHECKING_BADGE
        # LOGIN_DENIED

    def run(self):
        log = logging.getLogger("heartbeat.run")
        log.info("start")

        #
        # check the makermanager
        #
        try:
            url = ''.join([
               "https://dallasmakerspace.org/makermanager/index.php?",
               "r=api/toolValidate&badge&tool" ])
            log.info("heartbeat.run(): sent: " + url)
            json_response = urllib2.urlopen(url).readline()
            log.info("heartbeat.run(): got: " + json_response)
            response = json.loads(json_response)
        except ValueError, e:
            self.action_queue.put((ERROR_NETWORK, "heartbeat: makermanager is not returning valid JSON"))
            log.error("Makermanager is not returning valid JSON")
        except urllib2.HTTPError, e:
            self.action_queue.put((ERROR_NETWORK, "heartbeat: Cannot contact makermanager (HTTP)"))
            log.error("Cannot contact makermanager (HTTP)")
        except urllib2.URLError, e:
            self.action_queue.put((ERROR_NETWORK, "heartbeat: Cannot contact makermanager (URL)"))

        #
        # check the maintenance status
        #

################################################################################
#
#  The interlock
#
################################################################################

class interlock(threading.Thread):
    """ 
    the is the main interlock class used to insure that people have permission
    to use this tool
    """
    
    def __init__(self, interlock_config, error_log):
        log = logging.getLogger("interlock.init")
        log.info("in __init__")

        #
        # this is where all errors get logged
        #
        self.error_log = error_log

        #
        # start our threaded environment that we require
        #
        threading.Thread.__init__(self)
        self.action_queue = Queue.Queue()
        self.configuration = interlock_config
        try:
            self.timeout = int(interlock_config.get('timeout', 0))
        except ValueError:
            log.error("timeout is; " + 
                    interlock_config['timeout'] + 
                    " needs to be a float or int")

        try:
            self.warning_seconds = int(interlock_config.get('warning', 0))
        except ValueError:
            log.error("warningis: " + 
                    interlock_config['warning'] + 
                    " needs to be float or int")

        self.timer_to_warning = None
        self.timer_to_deactivate = None

        #
        # get the tool id
        #
        if interlock_config['tool_id'] == "":
            self.tool_id = hex(get_mac_address())[2:-1]
        else:
            self.tool_id = interlock_config['tool_id']

        #
        # process what to do when triggers occur
        #
        output_mapping = {
            "digital":   digital_output,
            "stdio":     stdio_output,
            "lcd_p018":  lcd_p018_output,
            #
            # "audio":  audio_status_indicator
            #
            # "pwm":    pwm_status_indicator
            #    note:  once in pwm, must power off or reboot to get normal
            #           functionality back
            #
            # "serial": serial_status_indicator, output is which file to play, and whether to loop
            #
            # "speech": speech_status_indicator, output is text for espeak or whatever
            #
        }
        self.outputs = []
        output_configs = {
                connection: output_config
                for connection, output_config in interlock_config.items()
                if (type(output_config) == dict and
                    output_config.get('mode') == "output" ) }
        for connection, output_config in output_configs.items():
            try:
                output = output_mapping[output_config['type']](
                        output_config, connection )
                self.outputs.append(output)
                log.info("output " + connection + " added")
            except:
                log.error("output " + connection + " could not be added ")

        #
        # set up the tasks that read rfid badges
        #
        rfid_reader_mapping = {
            "serial":       serial_rfid_reader,
            "stdio":        keyboard_rfid_reader,
            "input_event":  input_event_rfid_reader,
        }
        self.rfid_readers = []
        rfid_configs = { 
                connection: rfid_config 
                for connection, rfid_config in interlock_config.items()
                if type(rfid_config) == dict and 
                    rfid_config.get('mode') == "rfid_reader" }
        for connection, rfid_config in rfid_configs.items():
            try:
                reader = rfid_reader_mapping[rfid_config['type']](
                        rfid_config, connection, self.tool_id, self.action_queue)
                reader.start()
                self.rfid_readers.append(reader)
                log.info("rfid_reader " + connection + " added")
            except:
                log.error("rfid_reader " + connection + " could not be added")

        #
        # set up the tasks that monitors input lines
        #
        monitor_mapping = {
            #
            # "serial":  serial_monitor,
            # "stdio":   stdio_monitor,
            #
            "adc":     adc_monitor,
            "digital": digital_monitor,
        }
        self.monitors = []
        monitor_configs = { 
                connection: monitor_config 
                for connection, monitor_config in interlock_config.items()
                if type(monitor_config) == dict and
                    monitor_config.get("mode") == "monitor" }
        for connection, monitor_config in monitor_configs.items():
            try:
                monitor = monitor_mapping[monitor_config['type']](
                        monitor_config, connection, self.action_queue)
                monitor.start()
                self.monitors.append(monitor)
                log.info("monitor " + connection + " added")
            except KeyError, e:
                log.error("monitor " + connection + " could not be added " + str(e))

        self.need_status_updates = self.outputs + self.rfid_readers

    def run(self):
        log = logging.getLogger("interlock.run")
        log.debug("starting")
        #
        # equipment is not active, monitor the rfid reader and see if 
        # authorized to use this tool
        #

        status_update_actions = {
            ACTIVE:            self.active_mode,
            INACTIVE_SOON:     self.warning_mode,
            INACTIVE:          self.inactive_mode,
            RESET_TIMER:       self.reset_timers,
            ERROR:             self.error,

            POWER_UP:          self.nothing,
            ERROR_CONFIG:      self.nothing,
            ERROR_NETWORK:     self.nothing,
            ERROR_MAINTENANCE: self.nothing,

            TESTING_NETWORK:   self.nothing,
            CHECKING_BADGE:    self.nothing,
            LOGIN_DENIED:      self.nothing,
        }

        self.action_queue.put((INACTIVE, "interlock.run() initial power up"))

        while True:
            log.debug("waiting on action_queue.get()")
            new_status, queued_from = self.action_queue.get()

            log.debug("setting status to {0} because {1} said so".format(
                    new_status, queued_from))

            status_update_actions[new_status]()
            for update_me in self.need_status_updates:
                update_me.update(new_status)

        log.debug("ending")

    def nothing(self):
        pass

    def locked_out(self):
        for update_me in self.need_status_updates:
            update_me.update(ERROR_CONFIG)

    def active_mode(self):
        log = logging.getLogger("interlock.run")
        log.debug("active_mode start")

        self.clear_all_timers()

        self.timer_to_warning = threading.Timer(
                self.timeout - self.warning_seconds,
                lambda: self.action_queue.put(
                    (INACTIVE_SOON, "interlock.active_mode()") ) )

        # self.timer_to_deactivate = threading.Timer(
        #         self.timeout,
        #         lambda: self.action_queue.put(
        #             (INACTIVE, "interlock.active_mode()") ) )

        log.debug("active_mode starting timers")
        self.timer_to_warning.start()
        # self.timer_to_deactivate.start()
        log.debug("active_mode end")


    def warning_mode(self):
        log = logging.getLogger("interlock.run")
        log.debug("warning_mode")

        if self.timer_to_deactivate <> None and self.timer_to_warning == None:
            # 
            # already in warning mode
            # 
            pass
        else:
            self.clear_all_timers()
            self.timer_to_deactivate = threading.Timer(
                    self.warning_seconds,
                    lambda: self.action_queue.put(
                        (INACTIVE, "interlock.active_mode()") ) )
            self.timer_to_deactivate.start()

    def inactive_mode(self):
        log = logging.getLogger("interlock.run")
        log.debug("inactive_mode() called")

        self.clear_all_timers()

    def reset_timers(self):
        log = logging.getLogger("interlock.run")
        log.debug("reset_timers called")

        if self.timer_to_warning <> None or self.timer_to_deactivate <> None:
            self.action_queue.put((ACTIVE, "interlock.reset_timers()"))

    def error(self):
        log = logging.getLogger("interlock.run")
        log.debug("errors called")
        self.clear_all_timers()

    def clear_all_timers(self):
        if self.timer_to_warning <> None:
            self.timer_to_warning.cancel()
            self.timer_to_warning = None
        if self.timer_to_deactivate <> None:
            self.timer_to_deactivate.cancel()
            self.timer_to_deactivate = None


################################################################################
#
#  command line initiation
#
################################################################################

if __name__ == "__main__":
    lock_filename = "/var/lock/mother"
    fp = open(lock_filename, "w+")
    try:
        fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fp.truncate(0)
        fp.write(str(os.getpid()))
    except IOError:
        print "Another instance is still running"
        sys.exit(0)

    config = configuration.read()

    #
    # set up logging
    #
    error_log = ErrorArrayHandler()
    error_log.setLevel(logging.ERROR)

    logging.config.dictConfig(config.get('logging', {}))
    logger = logging.getLogger()
    logger.addHandler(error_log)
    logger.setLevel(logging.DEBUG)

    #
    # let's do this thing
    #
    interlock = interlock(config, error_log)
    if error_log.get_errors():
        print "here are the errors"
        for init_error in error_log.get_errors():
            print init_error.levelname + ":      " + init_error.name + ":     " + init_error.message
        time.sleep(2)
        interlock.locked_out()
    else:
        time.sleep(2)
        interlock.start()
        heartbeat = heartbeat()
        heartbeat.run()
