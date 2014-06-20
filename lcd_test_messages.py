#! /usr/bin/python

from lcd_i2c_p018 import lcd_i2c_p018 as lcd_class
import time

dwait = .1

lcd_display = lcd_class(1)
lcd_display.reset()
lcd_display.cursor(False)
time.sleep(dwait)

messages = [
    [ "powerup",         (  0, 255, 256), [ "DMS Interlock:  ", " Powering Up    " ]],
    [ "testing_network", (  0, 255, 256), [ "DMS Interlock:  ", " Testing Network" ]],

    [ "maintenance",     (255,   0,   0), [ "Down for        ", "     Maintenance" ]],

    [ "asleep",          (255, 255,   0), [ "Swipe Badge     ", "     to Activate" ]],

    [ "checking",        (  0, 255, 255), [ "Permission      ", " Checking Server" ]],
    [ "failed",          (255,   0,   0), [ "Permission      ", "    Badge Denied" ]],
    [ "succeeded",       (  0, 255,   0), [ "Permission      ", "      is Granted" ]],

    [ "inactive_soon",   (255, 255,   0), [ "Auto-logoff     ", " in 10 minutes  " ]],
]

# try:
while True:
	for type, color, text in messages:
		lcd_display.show_rgb(text, color)
		time.sleep(2.1)

while True:
	for type, color, text in messages:
		lcd_display.set_rgb(0, 0, 0) # set lcd backlight to green (half bright)
		lcd_display.show(["                ", "                "])
		lcd_display.show(text)
		lcd_display.set_rgb(color[0], color[1], color[2]) # set lcd backlight to green (half bright)
		time.sleep(2.1)

# except KeyboardInterrupt:
# 	lcd_display.clear()
# 	lcd_display.show(["Damn it!"])

