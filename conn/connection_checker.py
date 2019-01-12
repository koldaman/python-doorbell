import socket
import time
import threading
import logging

logger = logging.getLogger(__name__)

class ConnectionChecker:

	def __init__(self, host="8.8.8.8", port=53, timeout=3):
		"""
		Host: 8.8.8.8 (google-public-dns-a.google.com)
		OpenPort: 53/tcp
		Service: domain (DNS/TCP)
		"""
		self.host = host
		self.port = port
		self.timeout = timeout
		self.timer = None
		self._state = False
		self._old_state = self._state
		self._change_fc = None
		self._delay = 10

	def is_online(self):
		try:
			socket.setdefaulttimeout(self.timeout)
			socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((self.host, self.port))
			return True
		except Exception as ex:
			logger.exception('Error checking online status')
			return False

	def set_check_delay(self, delay):
		self._delay = delay
		return self

	def set_change_fc(self, change_fc):
		self._change_fc = change_fc
		return self

	def check_continously(self):
		# print('Checking...')
		self._state = self.is_online()
		# print('Fc: {}'.format(self._change_fc))
		# print('Delay: {}'.format(self._delay))
		# print('State: {}'.format(self._state))
		if self._state != self._old_state:
			self._change_fc(self._state)
			self._old_state = self._state
		self.timer = threading.Timer(self._delay, self.check_continously)
		self.timer.start()

	def stop(self):
		if self.timer:
			self.timer.cancel()


if __name__ == "__main__":
	# print(ConnectionChecker().is_online())

	def changed(state):
		print('Connection state changed to: {}'.format(state))

	cc = ConnectionChecker().set_change_fc(changed).set_check_delay(1)
	cc.check_continously()
	time.sleep(10)
	cc.stop()
