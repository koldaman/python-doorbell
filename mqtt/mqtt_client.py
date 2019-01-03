import paho.mqtt.client as mqtt
import time
import json
import logging

logger = logging.getLogger(__name__)


class MqttClient:

	def __init__(self, host, port, client, channel):
		self.channel = channel
		self.mqttc = mqtt.Client(client)
		self.mqttc.on_connect = self._on_connect
		self.mqttc.on_disconnect = self._on_disconnect
		self.mqttc.on_publish = self._on_publish
		self.mqttc.connect(host, port, 60)
		self.mqttc.loop_start()

	def _on_connect(self, mqttc, userdata, flags, rc):
		if rc == 0:
			logger.debug("Connected to MQTT OK. Returned code {}".format(str(rc)))
		else:
			logger.debug("Bad MQTT connection. Returned code {}".format(str(rc)))

	def _on_disconnect(self, client, userdata, rc):
		logging.info("MQTT disconnected. Reason {}".format(str(rc)))

	def _on_publish(self, mqttc, obj, mid):
		logger.debug("MQTT message published: " + str(mid))

	def send(self, channelPostfix, topic, meter, device, value):
		channel_final = self.channel + "/" + channelPostfix
		msg = json.dumps({"topic": topic, "meter": meter, "dev": device, "value": value})
		self.mqttc.publish(channel_final, msg)
		logger.debug(channel_final + ": " + msg)
		time.sleep(0.05)

	def close(self):
		self.mqttc.loop_stop()
		self.mqttc.disconnect()
		logger.debug("MQTT disconnected")

if __name__ == "__main__":

	mqtt_client = MqttClient("10.10.10.20", 1883, "influx")
	mqtt_client.send("home/door", "door", "home", "rpiZero", 0)
	mqtt_client.close()
