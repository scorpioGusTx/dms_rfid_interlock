#! /usr/bin/python

import json

configuration_filename = "/etc/mother.ini"

def write(updated_config):
	""" 
	Write the configuration.  
	Pass in the entire configuration to be saved.
	"""
	original_config =  json.loads(open("/etc/mother.ini", "r").read())
	config = dict(updated_config.items() + original_config.items())
	open("/etc/mother.ini", "w").write(json.dumps(config, sort_keys=True, indent=4))

def read(field = None):
	""" 
	Read in the configuration.  
	Pass in the fieldname of interest, otherwise the entire configuarion will 
	be returned.
	"""
	config = json.loads(open(configuration_filename, "r").read())
	if field == None:
		return config
	else:
		return config[field] if field in config else None

