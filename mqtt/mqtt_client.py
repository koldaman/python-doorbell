import paho.mqtt.client as mqtt
import time
import json

class MqttClient:

	def __init__(self, host, port, channel):
		self.channel = channel
		self.mqttc = mqtt.Client()
		self.mqttc.on_connect = self._on_connect
		self.mqttc.on_publish = self._on_publish
		self.mqttc.connect(host, port, 60)

	def _on_connect(self, mqttc, obj, flags, rc):
		print("MQTT connect result: " + str(rc))

	def _on_publish(mqttc, obj, mid):
		print("MQTT message published: " + str(mid))

	def send(self, channelPostfix, topic, meter, device, value):
		channelFinal = self.channel + "/" + channelPostfix
		msg = json.dumps({"topic": topic, "meter": meter, "dev": device, "value": value})
		self.mqttc.publish(channelFinal, msg)
		print channelFinal + ": " + msg
		time.sleep(0.05)

	def close(self):
		self.mqttc.disconnect()

if __name__ == "__main__":

	mqtt_client = MqttClient("10.10.10.20", 1883, "influx")
	mqtt_client.send("home/bell", "bell", "home", "rpiZero", 1.234)
	mqtt_client.close()
