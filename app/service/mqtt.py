import json
import time
from fastapi_mqtt import FastMQTT, MQTTConfig

from app.core.database import process_mqtt_data
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
    fast_mqtt.client.subscribe("/info/#")
    fast_mqtt.client.subscribe("/getmoney/#")
    fast_mqtt.client.subscribe("/heartbeat/#")
    fast_mqtt.client.subscribe("/stats/#")
    print_success("Connected: ", flags, rc, properties)


@fast_mqtt.on_message()
async def message(client, topic: str, payload, qos, properties):
    start_time = time.perf_counter()
    try:
        mqtt_msg = payload.decode()
        json_msg = json.loads(mqtt_msg)

        if topic.startswith("/"):
            topic = topic[1:]
        # print_success("Received message: ", topic, mqtt_msg, "qos:", qos)
        topics = topic.split("/")
        # print(topics)
        topic = topics[0]
        sn = ""
        if len(topics) > 1:
            sn = topics[1]
        else:
            sn = json_msg.get("sn", "")

        if sn is None:
            return None

        mqtt_data = {"topic": topic, "sn": sn, "message": mqtt_msg}
        # print(mqtt_data)
        r = await process_mqtt_data(mqtt_data)

    except Exception as e:
        print_error("Received message: ", topic, payload, "qos:", qos)
        print_error(e)

    end_time = time.perf_counter()
    total_time = (end_time - start_time) * 1000
    # print(f"Function @fast_mqtt.on_message() Took {total_time:.4f} ms")


@fast_mqtt.on_disconnect()
def disconnect(client, packet, exc=None):
    print_success("Disconnected")


@fast_mqtt.on_subscribe()
def subscribe(client, mid, qos, properties):
    print_success("subscribed", client, mid, qos, properties)


print_success("Set MQTT MODULE IN FASTAPI")
