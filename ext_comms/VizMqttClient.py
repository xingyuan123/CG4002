import json
import paho.mqtt.client as mqtt
from queue import Queue
from Helper import ice_print_m as print

# HiveMQ broker run via Docker (on relay laptop)
broker = 'localhost'

def on_log(client, userdata, level, buf):
    print(f'{buf}')

def on_connect(client, userdata, flags, rc, prop):
    if rc==0:
        print('Connected to broker successfully')
    else:
        print(f'Failed connection to broker. Return code: {rc}')

def on_disconnect(client, userdata, flags, rc, prop):
    print(f'Disconnected with RC {rc}. Attempting reconnect')
    client.connect(broker)

class VizMqttClient:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id='Ultra96')
    client.on_connect    = on_connect
    client.on_log        = on_log
    client.on_disconnect = on_disconnect
    client.connect(broker)
    client.loop_start()

    def send_to_broker(self, data_q: Queue):    
        while True:
            data = data_q.get()
            topic = data[0]
            msg = data[1]
            result = self.client.publish(topic, json.dumps(msg))
            status = result[0]
            if status != 0:
                print(f'Failed to send message to topic {topic}')
