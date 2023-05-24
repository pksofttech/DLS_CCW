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
    fast_mqtt.client.subscribe("/info/#")  # subscribing mqtt topic
    fast_mqtt.client.subscribe("/payment")  # subscribing mqtt topic
    fast_mqtt.client.subscribe("/heartbeat")  # subscribing mqtt topic
    print_success("Connected: ", flags, rc, properties)


@fast_mqtt.on_message()
async def message(client, topic: str, payload, qos, properties):
    start_time = time.perf_counter()
    try:
        mqtt_msg = payload.decode()
        if topic.startswith("/"):
            topic = topic[1:]
        # print_success("Received message: ", topic, mqtt_msg, "qos:", qos)
        # mqtt_data = {"topic": topic, "sn": sn, "message": mqtt_msg}
        # await seve_to_log_mqtt(mqtt_data)
        # print_warning("Received message: ", topic, mqtt_msg, "qos:", qos)
        topics = topic.split("/")
        sn = ""

        if len(topics) == 2:
            sn = topics[1]
        if topics[0] == "info":
            # info message
            if sn:
                pass

        elif topics[0] == "heartbeat":
            # heartbeat message
            pass
        elif topics[0] == "payments":
            # payments message
            pass
        else:
            pass
            # print_warning("Received message not subscribe : ", topic, mqtt_msg, "qos:", qos)

        mqtt_data = {"topic": topic, "sn": sn, "message": mqtt_msg}
        # print(mqtt_data)
        await seve_to_log_mqtt(mqtt_data)

        json_msg = json.loads(mqtt_msg)
        sn = json_msg.get("sn", "")
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
