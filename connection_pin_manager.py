#! /usr/bin/python

################################################################################
#
# connection to pin mapper
#
################################################################################

class connection_pin_mapper():
	def __init__(self):

		#
		# USR0 GPIO1_21
		# USR1 GPIO2_22
		# USR2 GPIO2_23
		# USR3 GPIO2_24
		#

		#
		# see /home/greiter/Documents/Beaglebone Black/
		#   /Beaglebone Black System Reference Manual.pdf
		#   page: 70 for pinouts
		#
		self.connections = {
				#
				# from 
				#    http://www.alexanderhiam.com/wp-content/uploads/
				#    2013/06/beaglebone_pinout.png
				#
				# connector 9
				#
				"GPIO0_30": {"type": "digital", "pins": ["P9_11"], "init": GPIO.HIGH, "read": "to_gnd", "led": True},
				"GPIO1_28": {"type": "digital", "pins": ["P9_12"], "init": GPIO.HIGH, "read": "to_gnd", "led": "blinks, but resets to high"},
				"GPIO0_31": {"type": "digital", "pins": ["P9_13"], "init": GPIO.HIGH, "read": "to_gnd", "led": True},
				"GPIO1_18": {"type": "digital", "pins": ["P9_14"], "init": GPIO.LOW,  "read": "to_3v3", "led": False},
				"GPIO1_16": {"type": "digital", "pins": ["P9_15"], "init": GPIO.HIGH, "read": "to_gnd", "led": True},
				"GPIO1_19": {"type": "digital", "pins": ["P9_16"], "init": GPIO.LOW,  "read": "to_3v3", "led": True},
				"GPIO0_5":  {"type": "digital", "pins": ["P9_17"], "init": GPIO.LOW,  "read": "nope",   "led": False},
				"GPIO0_4":  {"type": "digital", "pins": ["P9_18"], "init": GPIO.LOW,  "read": "nope",   "led": False},
				"GPIO0_13": {"type": "digital", "pins": ["P9_19"], "init": GPIO.HIGH, "read": "nope",   "led": False},
				"GPIO0_12": {"type": "digital", "pins": ["P9_20"], "init": GPIO.HIGH, "read": "nope",   "led": False},
				"GPIO0_3":  {"type": "digital", "pins": ["P9_21"], "init": GPIO.HIGH, "read": "to_gnd", "led": False},
				"GPIO0_2":  {"type": "digital", "pins": ["P9_22"], "init": GPIO.HIGH, "read": "to_gnd", "led": True},
				"GPIO1_17": {"type": "digital", "pins": ["P9_23"], "init": GPIO.LOW,  "read": "to_3v3", "led": False},
				"GPIO0_15": {"type": "digital", "pins": ["P9_24"], "init": GPIO.HIGH, "read": "to_gnd", "led": True},
				"GPIO3_21": {"type": "digital", "pins": ["P9_25"], "init": GPIO.HIGH, "read": "nope",   "led": False},
				"GPIO0_14": {"type": "digital", "pins": ["P9_26"], "init": GPIO.HIGH, "read": "to_gnd", "led": True},
				"GPIO3_19": {"type": "digital", "pins": ["P9_27"], "init": GPIO.LOW,  "read": "nope",   "led": False},
				"GPIO3_17": {"type": "digital", "pins": ["P9_28"], "init": GPIO.LOW,  "read": "to_gnd", "led": False},
				"GPIO3_15": {"type": "digital", "pins": ["P9_29"], "init": GPIO.LOW,  "read": "to_3v3", "led": False},
				"GPIO3_16": {"type": "digital", "pins": ["P9_30"], "init": GPIO.LOW,  "read": "to_3v3", "led": True},
				"GPIO3_14": {"type": "digital", "pins": ["P9_31"], "init": GPIO.HIGH, "read": "nope",   "led": False},
				# adc lives here
				"GPIO0_20": {"type": "digital", "pins": ["P9_41"], "init": GPIO.LOW,  "read": "to_3v3", "led": True},
				"GPIO0_7":  {"type": "digital", "pins": ["P9_42"], "init": GPIO.LOW,  "read": "to_3v3", "led": True},

				#
				# connector 8
				#
				"GPIO1_6":  {"type": "digital", "pins": ["P8_3"], "init": GPIO.HIGH},
				"GPIO1_7":  {"type": "digital", "pins": ["P8_4"], "init": GPIO.HIGH},
				"GPIO1_2":  {"type": "digital", "pins": ["P8_5"], "init": GPIO.HIGH},
				"GPIO1_3":  {"type": "digital", "pins": ["P8_6"], "init": GPIO.HIGH},

				"GPIO2_2":  {"type": "digital", "pins": ["P8_7"], "init": GPIO.HIGH,  "read": "to_gnd", "led": "blinks, but resets to high"},
				"GPIO2_3":  {"type": "digital", "pins": ["P8_8"], "init": GPIO.HIGH,  "read": "to_gnd", "led": "blinks, but resets to high"},
				"GPIO2_5":  {"type": "digital", "pins": ["P8_9"], "init": GPIO.HIGH,  "read": "to_gnd", "led": "blinks, but resets to high"},
				"GPIO2_4":  {"type": "digital", "pins": ["P8_10"], "init": GPIO.HIGH, "read": "to_gnd", "led": "blinks, but resets to high"},
				"GPIO1_13": {"type": "digital", "pins": ["P8_11"], "init": GPIO.LOW,  "read": "to_3v3", "led": True},
				"GPIO1_12": {"type": "digital", "pins": ["P8_12"], "init": GPIO.LOW,  "read": "to_3v3", "led": True},
				"GPIO0_23": {"type": "digital", "pins": ["P8_13"], "init": GPIO.LOW,  "read": "to_3v3", "led": True},
				"GPIO0_26": {"type": "digital", "pins": ["P8_14"], "init": GPIO.LOW,  "read": "to_3v3", "led": True},
				"GPIO1_15": {"type": "digital", "pins": ["P8_15"], "init": GPIO.LOW,  "read": "to_3v3", "led": True},
				"GPIO1_14": {"type": "digital", "pins": ["P8_16"], "init": GPIO.LOW,  "read": "to_3v3", "led": True},
				"GPIO0_27": {"type": "digital", "pins": ["P8_17"], "init": GPIO.LOW,  "read": "to_3v3", "led": True},
				"GPIO2_1":  {"type": "digital", "pins": ["P8_18"], "init": GPIO.LOW,  "read": "to_3v3", "led": True},
				"GPIO0_22": {"type": "digital", "pins": ["P8_19"], "init": GPIO.LOW,  "read": "to_3v3", "led": True},

				"GPIO1_31": {"type": "digital", "pins": ["P8_20"], "init": GPIO.HIGH},
				"GPIO1_30": {"type": "digital", "pins": ["P8_21"], "init": GPIO.LOW},
				"GPIO1_5":  {"type": "digital", "pins": ["P8_22"], "init": GPIO.HIGH},
				"GPIO1_4":  {"type": "digital", "pins": ["P8_23"], "init": GPIO.HIGH},
				"GPIO1_1":  {"type": "digital", "pins": ["P8_24"], "init": GPIO.HIGH},
				"GPIO1_0":  {"type": "digital", "pins": ["P8_25"], "init": GPIO.HIGH},
				"GPIO1_29": {"type": "digital", "pins": ["P8_26"], "init": GPIO.HIGH},
				"GPIO2_22": {"type": "digital", "pins": ["P8_27"], "init": GPIO.HIGH},
				"GPIO2_24": {"type": "digital", "pins": ["P8_28"], "init": GPIO.HIGH},
				"GPIO2_23": {"type": "digital", "pins": ["P8_29"], "init": GPIO.LOW},
				"GPIO2_25": {"type": "digital", "pins": ["P8_30"], "init": GPIO.LOW},
				"GPIO0_10": {"type": "digital", "pins": ["P8_31"], "init": GPIO.HIGH},
				"GPIO0_11": {"type": "digital", "pins": ["P8_32"], "init": GPIO.LOW},
				"GPIO0_9":  {"type": "digital", "pins": ["P8_33"], "init": GPIO.LOW},
				"GPIO2_17": {"type": "digital", "pins": ["P8_34"], "init": GPIO.LOW},
				"GPIO0_8":  {"type": "digital", "pins": ["P8_35"], "init": GPIO.LOW},
				"GPIO2_16": {"type": "digital", "pins": ["P8_36"], "init": GPIO.LOW},
				"GPIO2_14": {"type": "digital", "pins": ["P8_37"], "init": GPIO.LOW},
				"GPIO2_15": {"type": "digital", "pins": ["P8_38"], "init": GPIO.LOW},
				"GPIO2_12": {"type": "digital", "pins": ["P8_39"], "init": GPIO.LOW},
				"GPIO2_13": {"type": "digital", "pins": ["P8_40"], "init": GPIO.LOW},
				"GPIO2_10": {"type": "digital", "pins": ["P8_41"], "init": GPIO.HIGH},
				"GPIO2_11": {"type": "digital", "pins": ["P8_42"], "init": GPIO.HIGH},
				"GPIO2_8":  {"type": "digital", "pins": ["P8_43"], "init": GPIO.HIGH},
				"GPIO2_9":  {"type": "digital", "pins": ["P8_44"], "init": GPIO.HIGH},
				"GPIO2_6":  {"type": "digital", "pins": ["P8_45"], "init": GPIO.LOW},
				"GPIO2_27": {"type": "digital", "pins": ["P8_46"], "init": GPIO.LOW},
				
				#
				# from http://learn.adafruit.com/
				#   setting-up-io-python-library-on-beaglebone-black/i2c
				#
				# "I2C1": {
				# 		"type": "i2c", 
				# 		"pins": ["P9_28", "P9_29", "P9_31"]},
				"I2C": {
						"type": "i2c", 
						"pins": ["P9_19", "P9_20"]},

				#
				# from http://learn.adafruit.com/
				#   setting-up-io-python-library-on-beaglebone-black/spi
				#
				"spi0": {
						"type": "i2c", 
						"pins": ["P9_17", "P9_21", "P9_18", "P9_22"]},
				"spi1": {
						"type": "i2c", 
						"pins": ["P9_28", "P9_29", "P9_30", "P9_31"]},

				#
				# from http://learn.adafruit.com/
				#   setting-up-io-python-library-on-beaglebone-black/adc
				#
				"AIN0": {"type": "adc", "pins": ["P9_39"]},
				"AIN1": {"type": "adc", "pins": ["P9_40"]},
				"AIN2": {"type": "adc", "pins": ["P9_37"]},
				"AIN3": {"type": "adc", "pins": ["P9_38"]},
				"AIN4": {"type": "adc", "pins": ["P9_33"]},
				"AIN5": {"type": "adc", "pins": ["P9_36"]},
				"AIN6": {"type": "adc", "pins": ["P9_35"]},

				#
				# from http://learn.adafruit.com/
				#   setting-up-io-python-library-on-beaglebone-black/pwm
				#
				"PWM1A": {"type": "pwm", "pins": ["P9_14"]},
				"PWM1B": {"type": "pwm", "pins": ["P9_16"]},
				"PWM2A": {"type": "pwm", "pins": ["P8_19"]},
				"PWM2B": {"type": "pwm", "pins": ["P8_13"]},

				#
				# from http://learn.adafruit.com/
				#   setting-up-io-python-library-on-beaglebone-black/uart
				#
				"/dev/ttyO1": {
						"type": "serial", 
						"uart": "UART1", 
						"read": True,
						"write": True,
						"pins": ['P9_26', 'P9_24', 'P9_20', 'P9_19']},
				"/dev/ttyO2": {
						"type": "serial", 
						"uart": "UART2", 
						"read": True,
						"write": True,
						"pins": ['P9_22', 'P9_21']},
				"/dev/ttyO3": {
						"type": "serial", 
						"uart": "UART3", 
						"read": False,
						"write": True,
						"pins": ['P9_42', 'P8_36', 'P8_34']},
				"/dev/ttyO4": {
						"type": "serial", 
						"uart": "UART4", 
						"read": True,
						"write": True,
						"pins": ['P9_11', 'P9_13', 'P8_35', 'P8_33']},
				"/dev/ttyO5": {
						"type": "serial", 
						"uart": "UART5", 
						"read": True,
						"write": True,
						"pins": ['P8_38', 'P8_37', 'P8_31', 'P8_32']},

				#
				# from 
				#   http://elinux.org/images/8/8c/Black_eMMC_and_HDMI_pins.PNG
				#
				"MMC1": {
						"type": "mmc", 
						"pins": [
							"P8_3", "P8_4", "P8_5", "P8_6", "P8_20", "P8_21", 
							"P8_22", "P8_23", "P8_24", "P8_25" ]},

				"HDMI": {
						"type": "hdmi", 
						"pins": [ 
							"P8_27", "P8_28", "P8_29", "P8_30", "P8_31", 
							"P8_32", "P8_33", "P8_34", "P8_35", "P8_36", 
							"P8_37", "P8_38", "P8_39", "P8_40", "P8_41", 
							"P8_42", "P8_43", "P8_44", "P8_45", "P8_46" ]},

				"stdin": {
						"type": "stdio", 
						"read": True,
						"write": False},

				"stdout": {
						"type": "stdio", 
						"read": False,
						"write": True},
		}

		for connection in self.connections.keys():
			self.connections[connection]["used"] = False
			for pin in self.connections[connection]['pins']:
				if pin not in self.connections:
					if debug.get('connection_pin_mapper.__init__'):
						print "adding " + pin
					self.connections[pin] = {
							"type": "digital", 
							"used": False, 
							"pins": [pin]}

	def use(self, connection):
		if connection not in self.connections:
			return False

		desired_pins = self.connections[connection]['pins']

		conflicting_connections = { 
				connection: conflict for 
				connection, conflict in self.connections.items()
				if set(conflict['pins']).intersection(set(desired_pins)) and 
				   conflict["used"] == True }

		if len(conflicting_connections) == 0:
			self.connections[connection]['used'] = True
			return True
		else:
			return("conflicts with: " + 
					", ".join(conflicting_connections.keys()))

	def get_type(self, connection):
		try:
			return self.connections[connection]['type']
		except KeyError:
			return None

	def get_header_pins(self, connection):
		try:
			return self.connections[connection]['pins']
		except KeyError:
			return []
