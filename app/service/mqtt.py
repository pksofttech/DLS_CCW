import json
from fastapi_mqtt import FastMQTT, MQTTConfig
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
    try:
        print_success("Received message: ", client, topic, payload.decode(), qos, properties)
        data = payload.decode()
        sn = "NoSN"
        if data == "ESP32_2":
            sn = "002"

        # url = f"http://127.0.0.1:8000/heartbeat?sn={sn}"
        # print_success(f"httpx : {url}")
        # requests.get(url)
    except Exception as e:
        print_error(e)


@fast_mqtt.on_disconnect()
def disconnect(client, packet, exc=None):
    print_success("Disconnected")


@fast_mqtt.on_subscribe()
def subscribe(client, mid, qos, properties):
    print_success("subscribed", client, mid, qos, properties)


print_success("Set MQTT MODULE IN FASTAPI")
