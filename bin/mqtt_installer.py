#!/usr/bin/env python

import json
import re
import sys
import time
from argparse import ArgumentParser
from argparse import ArgumentTypeError
from argparse import Namespace

import paho.mqtt.client as mqtt


def validate_node_id(s: str):
    if not re.match(r"^!?[a-f\d]+$", s):
        raise ArgumentTypeError(f"invalid node id '{s}'")

    if not s.startswith("!"):
        s = f"!{s}"

    return s.lower()


def read_arg() -> Namespace:
    parser = ArgumentParser()

    parser.add_argument(
        "--mqtt_host",
        required=True
    )

    parser.add_argument(
        "--mqtt_port",
        required=False,
        default=1883,
        type=int
    )

    parser.add_argument(
        "--mqtt_user",
        required=True
    )
    parser.add_argument(
        "--mqtt_pass",
        required=True
    )

    parser.add_argument(
        "--retain",
        action="store_true",
        help="sets the retain flag for when installing topics"
    )

    parser.add_argument(
        "-u", "--uninstall",
        action="store_true",
        help="removed mqtt discovery topics"
    )

    parser.add_argument(
        "--device_metrics",
        action="store_true",
        help="enables the installation of device metrics discovery topics"
    )
    parser.add_argument(
        "--environment_metrics",
        action="store_true",
        help="enables the installation of environment metrics discovery topics"
    )
    parser.add_argument(
        "--local_stats",
        action="store_true",
        help="enables the installation of local stats discovery topics"
    )
    parser.add_argument(
        "--position",
        action="store_true",
        help="enables the installation of position discovery topics"
    )

    parser.add_argument(
        "--node",
        dest="node_id",
        required=True,
        type=validate_node_id,
        help="node id(hex) with or without the leading '!'"
    )

    args = parser.parse_args()
    return args


def device_metrics_discovery(node_id: str):
    if node_id.startswith("!"):
        node_id = node_id.lstrip("!")

    state_topic = f"homeassistant/sensor/{node_id}_device_metrics/state"
    payloads = [
        {
            "expire_after": 2400,
            "min": 0,
            "max": 101,
            "device_class": "battery",
            "state_topic": state_topic,
            "unit_of_measurement": "%",
            "value_template": "{{ value_json.batteryLevel | round(0) }}",
            "name": f"{node_id}_batteryLevel",
            "object_id": f"{node_id}_batteryLevel",
            "unique_id": f"{node_id}_batteryLevel",
            "device": {
                "identifiers": [f"{node_id}"],
                "name": f"{node_id}",
            }
        },
        {
            "expire_after": 2400,
            "min": 0,
            "max": 4.40,
            "device_class": "voltage",
            "state_topic": state_topic,
            "unit_of_measurement": "V",
            "value_template": "{{ value_json.voltage | round(2) }}",
            "name": f"{node_id}_voltage",
            "object_id": f"{node_id}_voltage",
            "unique_id": f"{node_id}_voltage",
            "device": {
                "identifiers": [f"{node_id}"],
                "name": f"{node_id}",
            }
        },
        {
            "expire_after": 2400,
            "icon": "mdi:radio-tower",
            "state_topic": state_topic,
            "unit_of_measurement": "%",
            "value_template": "{{ value_json.airUtilTx | round(2) }}",
            "name": f"{node_id}_airUtilTx",
            "object_id": f"{node_id}_airUtilTx",
            "unique_id": f"{node_id}_airUtilTx",
            "device": {
                "identifiers": [f"{node_id}"],
                "name": f"{node_id}",
            }
        },
        {
            "expire_after": 2400,
            "icon": "mdi:radio-tower",
            "state_topic": state_topic,
            "unit_of_measurement": "%",
            "value_template": "{{ value_json.channelUtilization | round(2) }}",
            "name": f"{node_id}_channelUtilization",
            "object_id": f"{node_id}_channelUtilization",
            "unique_id": f"{node_id}_channelUtilization",
            "device": {
                "identifiers": [f"{node_id}"],
                "name": f"{node_id}",
            }
        },
    ]

    for payload in payloads:
        topic_path = [
            "homeassistant",
            "sensor",
            payload["unique_id"],
            "config"
        ]
        discovery_topic = "/".join(topic_path)
        yield discovery_topic, payload


def environment_metrics_discovery(node_id: str):
    if node_id.startswith("!"):
        node_id = node_id.lstrip("!")

    state_topic = f"homeassistant/sensor/{node_id}_environment_metrics/state"
    payloads = [
        {
            "expire_after": 2400,
            "device_class": "temperature",
            "state_topic": state_topic,
            "unit_of_measurement": "°C",
            "value_template": "{{ value_json.temperature | round(1) }}",
            "name": f"{node_id}_temperature",
            "object_id": f"{node_id}_temperature",
            "unique_id": f"{node_id}_temperature",
            "device": {
                "identifiers": [f"{node_id}"],
                "name": f"{node_id}",
            }
        },
        {
            "expire_after": 2400,
            "device_class": "humidity",
            "state_topic": state_topic,
            "unit_of_measurement": "%",
            "value_template": "{{ value_json.relativeHumidity | round(0) }}",
            "name": f"{node_id}_relativeHumidity",
            "object_id": f"{node_id}_relativeHumidity",
            "unique_id": f"{node_id}_relativeHumidity",
            "device": {
                "identifiers": [f"{node_id}"],
                "name": f"{node_id}",
            }
        },
        {
            "expire_after": 2400,
            "device_class": "humidity",
            "state_topic": state_topic,
            "unit_of_measurement": "hPa",
            "value_template": "{{ value_json.barometricPressure | round(1) }}",
            "name": f"{node_id}_barometricPressure",
            "object_id": f"{node_id}_barometricPressure",
            "unique_id": f"{node_id}_barometricPressure",
            "device": {
                "identifiers": [f"{node_id}"],
                "name": f"{node_id}",
            }
        },
    ]

    for payload in payloads:
        topic_path = [
            "homeassistant",
            "sensor",
            payload["unique_id"],
            "config"
        ]
        discovery_topic = "/".join(topic_path)
        yield discovery_topic, payload


def position_discovery(node_id: str):
    if node_id.startswith("!"):
        node_id = node_id.lstrip("!")

    topic = f"homeassistant/device_tracker/{node_id}_position/config"
    payload = {
        "json_attributes_topic": f"homeassistant/device_tracker/{node_id}_position/attributes",
        "name": f"{node_id}_position",
        "object_id": f"{node_id}_position",
        "unique_id": f"{node_id}_position",
        "device": {
            "identifiers": [f"{node_id}"],
            "name": f"{node_id}",
        }
    }
    yield topic, payload


def local_stats_discovery(node_id: str):
    _ = {
        "numPacketsTx",
        "numTotalNodes",
        "uptimeSeconds"
    }

    if node_id.startswith("!"):
        node_id = node_id.lstrip("!")

    state_topic = f"homeassistant/sensor/{node_id}_local_stats/state"

    payloads = []

    names = [
        "numOnlineNodes",
        "numTotalNodes",
    ]
    for name in names:
        payloads.append(
            {
                "expire_after": 1200,
                "state_topic": state_topic,
                "unit_of_measurement": "node",
                "value_template": f"{{{{ value_json.{name} }}}}",
                "name": f"{node_id}_{name}",
                "object_id": f"{node_id}_{name}",
                "unique_id": f"{node_id}_{name}",
                "device": {
                    "identifiers": [f"{node_id}"],
                    "name": f"{node_id}",
                }
            }
        )
    names = [
        "numPacketsRx",
        "numPacketsRxBad",
        "numPacketsTx",
    ]
    for name in names:
        payloads.append(
            {
                "expire_after": 1200,
                "state_topic": state_topic,
                "unit_of_measurement": "packet",
                "value_template": f"{{{{ value_json.{name} }}}}",
                "name": f"{node_id}_{name}",
                "object_id": f"{node_id}_{name}",
                "unique_id": f"{node_id}_{name}",
                "device": {
                    "identifiers": [f"{node_id}"],
                    "name": f"{node_id}",
                }
            }
        )

    for payload in payloads:
        topic_path = [
            "homeassistant",
            "sensor",
            payload["unique_id"],
            "config"
        ]
        discovery_topic = "/".join(topic_path)
        yield discovery_topic, payload


def install_topic(args: Namespace, mqtt_client: mqtt.Client, topic: str, payload: dict):
    if args.uninstall:
        print(f"uninstalling {topic}")
        mqtt_client.publish(topic, "", qos=1)
        time.sleep(2)

    else:
        print(f"installing {topic}")
        json_payload = json.dumps(payload, sort_keys=True)
        print(json.dumps(payload, sort_keys=True, indent=0))
        mqtt_client.publish(topic, json_payload, retain=args.retain, qos=1)
        time.sleep(2)


def main():
    args = read_arg()

    mqtt_client = None
    try:
        mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        mqtt_client.username_pw_set(
            # username="mesht_mqtt",
            # password="4s8PcqG1S@Ps"
            username=args.mqtt_user,
            password=args.mqtt_pass
        )
        # mqtt_client.connect("10.3.0.51", args.mqtt_port, 60)
        mqtt_client.connect(args.mqtt_host, args.mqtt_port, 60)
        mqtt_client.loop_start()

        for i in range(5):
            print(f"{i + 1}/5: connecting to mqtt broker: {args.mqtt_host}:{args.mqtt_port}")
            time.sleep(1)
            if mqtt_client.is_connected():
                break

        if not mqtt_client.is_connected():
            print(f"filed to connect to mqtt broker: {args.mqtt_host}:{args.mqtt_port}")
            sys.exit(1)

        print(f"connected to mqtt broker")

        node_id = args.node_id

        if args.device_metrics:
            print(f"{node_id} device metrics")
            for topic, payload in device_metrics_discovery(node_id):
                install_topic(args, mqtt_client, topic, payload)

        if args.environment_metrics:
            print(f"{node_id} environment metrics")
            for topic, payload in environment_metrics_discovery(node_id):
                install_topic(args, mqtt_client, topic, payload)

        if args.local_stats:
            print(f"{node_id} local stats")
            for topic, payload in local_stats_discovery(node_id):
                install_topic(args, mqtt_client, topic, payload)

        if args.position:
            print(f"{node_id} position")
            for topic, payload in position_discovery(node_id):
                install_topic(args, mqtt_client, topic, payload)

    except Exception as e:
        raise e
    finally:
        if mqtt_client:
            mqtt_client.disconnect()


if __name__ == '__main__':
    main()
