import json
import time
from fastapi_mqtt import FastMQTT, MQTTConfig

from app.core.database import seve_to_log_mqtt
from ..stdio import *
import httpx as requests

_mqtt_host = "47.254.250.76"
# _mqtt_host = "mqtt.dollysolution.com"
_mqtt_port = 1883
fast_mqtt = FastMQTT(
    config=MQTTConfig(
        host=_mqtt_host,
        username="admin",
        password="dls@1234",
        # port=_mqtt_port,
    )
)


@fast_mqtt.on_connect()
def connect(client, flags, rc, properties):
    # fast_mqtt.client.subscribe("DLS/HB")  # subscribing mqtt topic
    fast_mqtt.client.subscribe("/time_stamp")  # subscribing mqtt topic
    print_success("Connected: ", flags, rc, properties)


@fast_mqtt.on_message()
async def message(client, topic, payload, qos, properties):
    start_time = time.perf_counter()
    try:
        mqtt_msg = payload.decode()
        # print_success("Received message: ", topic, mqtt_msg, "qos:", qos)
        json_msg = json.loads(mqtt_msg)
        sn = json_msg.get("sn", "")
        mqtt_data = {"topic": topic, "sn": sn, "message": mqtt_msg}
        await seve_to_log_mqtt(mqtt_data)
        if topic == "/heartbeat":
            print_success("Received heartbeat message: ", topic, mqtt_msg, "qos:", qos)
        elif topic == "/time_stamp":
            print_success("Received time_stamp message: ", topic, mqtt_msg, "qos:", qos)

        else:
            print_warning("Received message: ", topic, mqtt_msg, "qos:", qos)

    except Exception as e:
        print_error(e)

    end_time = time.perf_counter()
    total_time = (end_time - start_time) * 1000
    print(f"Function @fast_mqtt.on_message() Took {total_time:.4f} ms")


@fast_mqtt.on_disconnect()
def disconnect(client, packet, exc=None):
    print_success("Disconnected")


@fast_mqtt.on_subscribe()
def subscribe(client, mid, qos, properties):
    print_success("subscribed", client, mid, qos, properties)


print_success("Set MQTT MODULE IN FASTAPI")
