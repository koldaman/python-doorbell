import paho.mqtt.client as mqtt
import time
import json
import logging

logger = logging.getLogger(__name__)


class MqttClient:

	def __init__(self, host, port, channel):
		self.channel = channel
		self.mqttc = mqtt.Client()
		self.mqttc.on_connect = self._on_connect
		self.mqttc.on_publish = self._on_publish
		self.mqttc.connect(host, port, 60)

	def _on_connect(mqttc, obj, flags, rc):
		logger.debug("MQTT connect result: " + str(rc))

	def _on_publish(mqttc, obj, mid):
		logger.debug("MQTT message published: " + str(mid))

	def send(self, channelPostfix, topic, meter, device, value):
		channel_final = self.channel + "/" + channelPostfix
		msg = json.dumps({"topic": topic, "meter": meter, "dev": device, "value": value})
		self.mqttc.publish(channel_final, msg)
		logger.debug(channel_final + ": " + msg)
		time.sleep(0.05)

	def close(self):
		self.mqttc.disconnect()
		logger.debug("MQTT disconnected")

if __name__ == "__main__":

	mqtt_client = MqttClient("10.10.10.20", 1883, "influx")
	mqtt_client.send("home/door", "door", "home", "rpiZero", 0)
	mqtt_client.close()
