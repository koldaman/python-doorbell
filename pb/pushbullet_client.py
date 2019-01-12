from pushbullet import Pushbullet
import logging

logger = logging.getLogger(__name__)


class PushbulletClient:

	def __init__(self, api_key):
		self.pb = Pushbullet(api_key)

	def send(self, title, text):
		try:
			return self.pb.push_note(title, text)
		except Exception as ex:
			logger.exception('Error sending Pushbullet notification')

if __name__ == "__main__":

	PUSHBULLET_API_KEY = 'fill_in_your_API_key'

	pushbullet_client = PushbulletClient(PUSHBULLET_API_KEY)
	push = pushbullet_client.send("This is the title", "This is the body")
	print push

