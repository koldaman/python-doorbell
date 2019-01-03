#!/usr/bin/python
import RPi.GPIO as GPIO
import time
import json
import logging
import sys, getopt
from blink.blinker import Blinker
from mqtt.mqtt_client import MqttClient
from pb.pushbullet_client import PushbulletClient
from conn.connection_checker import ConnectionChecker


ONLINE_CHECK_INTERVAL = 20  # check for connectivity each 20 secs
RING_TIMEOUT = 5  # 5secs max ringing time
PUSHBULLET_SEND_DELAY = 2  # 2secs delay when sending pushbullet notification
DEBOUNCE_DELAY_MS = 0.05  # delay in secs

GPIO.setmode(GPIO.BCM)
BLINK_PIN = 18
DOOR_PIN = 21
RING_PIN = 13
RELAY_PIN = 15
GPIO.setup(BLINK_PIN,  GPIO.OUT)
GPIO.setup(RELAY_PIN,  GPIO.OUT)
GPIO.setup(DOOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(RING_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Doorbell:

	def __init__(self, argv):
		config_file_path = "/home/pi/projects/doorbell/config.json"
		try:
			opts, args = getopt.getopt(argv, "hc:", ["configfile="])
		except getopt.GetoptError:
			print 'doorbell.py -c <configfile>'
			sys.exit(2)
		for opt, arg in opts:
			if opt == '-h':
				print 'doorbell.py -c <configfile>'
				sys.exit()
			elif opt in ("-c", "--configfile"):
				config_file_path = arg
		logger.debug("Config file path: {}".format(config_file_path))

		self.door_state = False
		self.old_door_state = self.door_state
		self.door_debounce_state = self.door_state
		self.door_debounce_time = 0
		self.ring_state = True
		self.old_ring_state = self.ring_state
		self.ring_collector = []
		self.last_ring_event_start = 0
		self.last_ring_event_stop  = 0
		self.ring_timeout_notified = False
		self.blink = Blinker(BLINK_PIN)
		self.blink.start(Blinker.HEARTBEAT)
		self.config = self.load_config(config_file_path)
		self.mqtt_client = MqttClient(
			self.config["mqtt"]["host"],
			self.config["mqtt"]["port"],
			self.config["mqtt"]["client"],
			self.config["mqtt"]["channel"]
		)
		pushbullet_config_list = self.config["pushbullet"]
		self.pbs_ring = []
		self.pbs_door = []
		for pb_config in pushbullet_config_list:
			if pb_config["ring"]:
				self.pbs_ring.append(PushbulletClient(pb_config["apiKey"]))
			if pb_config["door"]:
				self.pbs_door.append(PushbulletClient(pb_config["apiKey"]))
		self.is_online = False
		self.connection_checker = ConnectionChecker().set_check_delay(ONLINE_CHECK_INTERVAL).set_change_fc(self.connection_state_changed)
		self.connection_checker.check_continously()

	@staticmethod
	def load_config(path):
		with open(path) as json_data_file:
			data = json.load(json_data_file)
		return data

	def connection_state_changed(self, state):
		self.is_online = state
		logger.debug('Connection state changed to: {}'.format(state))
		self.state_changed()

	@staticmethod
	def print_state(state, type):
		if type == 'Ring':
			logger.debug('Ringing started' if not state else 'Ringing stoped')
		elif type == 'Door':
			logger.debug('Door {}'.format('Open'if state else 'Closed'))

	def state_changed(self, door_state_changed=False, ring_state_changed=False):
		self.blink.stop()

		blink_style = Blinker.HEARTBEAT if self.is_online else Blinker.ERROR

		logger.debug('Online: {}'.format(self.is_online))

		if self.door_state:
			blink_style = Blinker.QUICK
		elif not self.ring_state:
			blink_style = Blinker.ALWAYS_ON

		if door_state_changed:
			self.old_door_state = self.door_state
			self.print_state(self.door_state, 'Door')
			self.mqtt_client.send("home/door", "door", "home", "rpiZero", 1 if self.door_state else 0)
			self.pushbullet_door_notify("Opened" if self.door_state else "Closed")

		if ring_state_changed:
			self.old_ring_state = self.ring_state
			self.set_relay_state(not self.ring_state)
			now = time.time()
			if not self.ring_state:
				self.last_ring_event_start = time.time()
			else:
				self.last_ring_event_stop = time.time()
				duration = now - self.last_ring_event_start
				if not self.ring_timeout_notified:
					if duration > DEBOUNCE_DELAY_MS:
						logger.debug('Ring duration {}'.format(duration))
						self.ring_collector.append(duration)
						self.mqtt_client.send("home/bell", "bell", "home", "rpiZero", duration)
				self.ring_timeout_notified = False

			self.print_state(self.ring_state, 'Ring')

		self.blink.start(blink_style)

	def check_for_change(self):
		now = time.time()

		# door debounce prevention
		if self.door_debounce_state != self.door_state:
			self.door_debounce_time = now
		if now - self.door_debounce_time > DEBOUNCE_DELAY_MS and self.old_door_state != self.door_state:
			self.state_changed(door_state_changed=True)
		self.door_debounce_state = self.door_state

		if self.old_ring_state != self.ring_state:
			self.state_changed(ring_state_changed=True)

		if not self.ring_state and now - self.last_ring_event_start >= RING_TIMEOUT and not self.ring_timeout_notified:
			logger.debug('Timeout, stop ringing dude!')
			self.set_relay_state(False)
			self.ring_timeout_notified = True
			self.ring_collector.append(now - self.last_ring_event_start)
			self.pushbullet_ring_notify()

		if self.ring_collector and now - self.last_ring_event_stop >= PUSHBULLET_SEND_DELAY and self.ring_state:
			self.pushbullet_ring_notify()

	def read(self):
		self.door_state = GPIO.input(DOOR_PIN)
		self.ring_state = GPIO.input(RING_PIN)
		self.check_for_change()

	def pushbullet_ring_notify(self):
		if self.ring_collector:
			count = len(self.ring_collector)
			logger.debug('Sending {} ring notification to pushbullet: {}'.format(count, self.ring_collector))
			for pb in self.pbs_ring:
				pb.send("Doorbell", "Ringing {} x".format(count))
		self.ring_collector = []

	def pushbullet_door_notify(self, state):
		logger.debug('Sending door notification to pushbullet: {}'.format(state))
		for pb in self.pbs_door:
			pb.send("Door", state)

	def set_relay_state(self, state):
		GPIO.output(RELAY_PIN, state)

	def stop(self):
		self.blink.stop()
		self.mqtt_client.close()
		self.connection_checker.stop()

if __name__ == "__main__":

	logger.debug('Starting up')

	doorbell = Doorbell(sys.argv[1:])
	logger.debug('Config {}'.format(doorbell.config))

	try:
		while True:
			doorbell.read()
	except (KeyboardInterrupt, SystemExit):
		logger.debug('Finished')
		raise
	finally:
		doorbell.stop()
		GPIO.cleanup()
