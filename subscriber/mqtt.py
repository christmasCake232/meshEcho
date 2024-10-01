import json
import sys

import paho.mqtt.client as mqtt
from meshtastic.mesh_interface import MeshInterface

from config_check import ConfigCheck
from .base import BaseSubscriber


class MqttSubscriber(BaseSubscriber):

    def __init__(self, config: dict, mqtt_client: mqtt.Client):
        super().__init__(default_topic="meshtastic.receive")

        if not mqtt_client or not mqtt_client.is_connected():
            self.logger.error("mqtt client is not connected")
            sys.exit(1)
        else:
            self._mqtt_client = mqtt_client

        mqtt_config = ConfigCheck(config, self.__class__.__name__, ["node_ids"], self.logger)
        self._node_ids = [id_.lower() for id_ in mqtt_config["node_ids"]]

    @property
    def node_ids(self):
        return self._node_ids.copy()

    def _telemetry(self, packet: dict, interface: MeshInterface):

        telemetry = self.dict_get(packet, ["decoded", "telemetry"])
        if telemetry:
            from_id = f'{packet["from"]:x}'
            long_name = self.get_long_name(packet["fromId"], interface)

            device_metrics = self.dict_get(telemetry, "deviceMetrics")
            if device_metrics:
                state_topic = f"homeassistant/sensor/{from_id}_device_metrics/state"
                payload = json.dumps(device_metrics, sort_keys=True)
                self._mqtt_client.publish(state_topic, payload)

                self.logger.info(f"{long_name} updating {state_topic}")

            environment_metrics = self.dict_get(telemetry, "environmentMetrics")
            if environment_metrics:
                state_topic = f"homeassistant/sensor/{from_id}_environment_metrics/state"
                payload = json.dumps(environment_metrics, sort_keys=True)
                self._mqtt_client.publish(state_topic, payload)

                self.logger.info(f"{long_name} updating {state_topic}")

            local_stats = self.dict_get(telemetry, "localStats")
            if local_stats:
                state_topic = f"homeassistant/sensor/{from_id}_local_stats/state"
                payload = json.dumps(local_stats, sort_keys=True)
                self._mqtt_client.publish(state_topic, payload)

                self.logger.info(f"{long_name} updating {state_topic}")

    @staticmethod
    def _precision_to_meter(precision_bits: int) -> float:
        # 10 14.5 mi 23335.49
        # 11 7.3 mi 11748.2
        # 12 3.6 mi 5793.64
        # 13 1.8 mi 2896.82
        # 14 4787 ft 1459.078
        # 15 2382 ft 726.0336
        # 16 1194 ft 363.9312
        # 17 597 ft 181.966
        # 18 299 ft 91.1352
        # 19 148 ft 45.1104

        # y = 2103253 - 641854 * x  + 78792.7 * x ^ 2 - 4852.927 * x ^ 3 + 149.7082 * x ^ 4 - 1.848088 * x ^ 5I
        meter = 2103253
        meter -= 641854 * precision_bits
        meter += 78792.7 * (precision_bits ** 2)
        meter -= 4852.927 * (precision_bits ** 3)
        meter += 149.7082 * (precision_bits ** 4)
        meter -= 1.848088 * (precision_bits ** 5)
        return meter

    def _position(self, packet: dict, interface: MeshInterface):
        # https://www.home-assistant.io/integrations/device_tracker.mqtt/
        from_id = f'{packet["from"]:x}'
        long_name = self.get_long_name(packet["fromId"], interface)
        position = self.dict_get(packet, ["decoded", "position"])
        if position and all(k in position for k in ["precisionBits", "latitude", "longitude"]):
            state_topic = f"homeassistant/device_tracker/{from_id}_position/attributes"

            precision_bits = position["precisionBits"]
            gps_accuracy = self._precision_to_meter(precision_bits)
            payload = {
                "latitude": position["latitude"],
                "longitude": position["longitude"],
                "gps_accuracy": gps_accuracy
            }
            self.logger.info(f"{long_name} updating {state_topic}")
            self._mqtt_client.publish(state_topic, json.dumps(payload, sort_keys=True))

    @staticmethod
    def get_long_name(from_id: str, interface: MeshInterface):
        return interface.nodes.get(from_id, {}).get("user", {}).get("longName", from_id)

    def __call__(self, packet: dict, interface: MeshInterface):

        from_id = packet["fromId"]

        if from_id in self._node_ids:
            port_num = packet.get("decoded", {}).get("portnum", None)

            match port_num:
                case "TELEMETRY_APP":
                    self._telemetry(packet, interface)

                case "POSITION_APP":
                    self._position(packet, interface)
