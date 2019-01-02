#!/usr/bin/python
import RPi.GPIO as GPIO
import time
import threading


class Blinker:
	HEARTBEAT = [0.1, 0.2, 0.1, 1]
	ERROR = [0.1, 0.05, 0.1, 0.05, 0.1, 0.3]
	QUICK = [0.02, 0.08]
	SLOW = [0.5, 1]
	ALWAYS_ON = [1]

	def __init__(self, pinNumber, init=True, inverted=False):
		self.pinNumber = pinNumber
		self.index = 0
		self.pattern = []
		self.inverted = inverted
		self.timer = None
		if init:
			self.init_pin()

	def init_pin(self):
		GPIO.setup(self.pinNumber, GPIO.OUT)

	def start(self, pattern):
		self.stop()
		self.pattern = pattern
		self.index = 0
		if self.pattern:
			self.blink()

	def blink(self):
		if self.index >= len(self.pattern):
			self.index = 0
		duration = self.pattern[self.index]
		self.timer = threading.Timer(duration, self.blink)
		value = (self.index % 2) == 0
		if self.inverted:
			value = not value
		# print(self.pattern)
		# if value:
		# 	print('Blink')
		GPIO.output(self.pinNumber, value)
		self.index += 1
		self.timer.start()

	def stop(self):
		GPIO.output(self.pinNumber, not self.inverted)
		if self.timer:
			self.timer.cancel()


if __name__ == "__main__":
	try:
		print('Starting up')
		GPIO.setmode(GPIO.BCM)
		while True:
			blink = Blinker(18)
			blink.start(Blinker.HEARTBEAT)
			time.sleep(3.2)
			print('Done 1')
			blink.start(Blinker.SLOW)
			time.sleep(3)
			print('Done 2')
			blink.start(Blinker.QUICK)
			time.sleep(3)
			print('Done 3')
			blink.stop()

			blink = Blinker(18, inverted=True)
			blink.start(Blinker.HEARTBEAT)
			time.sleep(3)
			print('Done 4')
			blink.stop()
	except (KeyboardInterrupt, SystemExit):
		print('Finished')
		raise
	finally:
		blink.stop()
		GPIO.cleanup()

"""
GPIO.setwarnings(False)
# doing this first, since we're using a while True.
GPIO.cleanup()

GPIO.setmode(GPIO.BCM)
BLINK_PIN = 18

GPIO.setup(BLINK_PIN,  GPIO.OUT)

def b(duration):
   print('Blink')
   GPIO.output(BLINK_PIN, True)
   time.sleep(duration)
   GPIO.output(BLINK_PIN, False)

def b_heart():
   b(0.1)
   time.sleep(0.3)
   b(0.1)
   time.sleep(2)

print(__name__)

def blink():
   t = threading.currentThread()
   while getattr(t, "do_run", True):
      b_heart()
   print('Blink thread stoped')

def print_state(state):
   print('State: {}'.format(state))

t = threading.Thread(target=blink)
t.start()

try:
   while True:
      pass
except (KeyboardInterrupt, SystemExit):
   print('Finished')
   raise
finally:
   t.do_run = False
"""
