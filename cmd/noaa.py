import json
from typing import Optional
from urllib.parse import urlunsplit, urlencode
from urllib.request import urlopen

from meshtastic.stream_interface import StreamInterface

from .base import BaseCmd


class NoaaCmd(BaseCmd):
    def __init__(self, config: dict):
        super().__init__(key="noaa", config=config)

        self.logger.info(f"cmd enabled: {self.__class__.__name__}")

    def help_line(self, escape: str) -> str:
        return f"{super().help_line(escape)}: reports NOAA alerts around your QTH"

    @staticmethod
    def _get_alerts(latitude: float, longitude: float):
        path = "/alerts/active"
        query = urlencode({"point": f"{latitude},{longitude}"})
        url = urlunsplit(("https", "api.weather.gov", path, query, ""))

        with urlopen(url) as fd:
            data = json.load(fd)

        for feature in data.get("features", []):
            properties = feature.get("properties", {})
            headline = properties.get("headline")
            description = properties.get("description")

            yield headline, description

    @staticmethod
    def _get_position(interface: StreamInterface, node_id: str) -> Optional[dict]:
        keys = {"latitude", "longitude"}
        position = interface.nodes.get(node_id, {}).get("position", None)
        if position and all(k in position for k in keys):
            return position

        return None

    def __call__(self, escape: str, packet: dict, interface: StreamInterface):
        from_id = packet["fromId"]

        replies = []
        position = self._get_position(interface, from_id)
        if position:

            alerts = list(h for h, _ in self._get_alerts(position["latitude"], position["longitude"]))
            alert_count = len(alerts)
            if alert_count == 1:
                replies.append(f"{alerts[0].strip()}".strip())

            elif alert_count >= 2:
                for index, alert in enumerate(alerts):
                    replies.append(f"({index + 1}/{len(alerts)}){alert.strip()}".strip())

            else:
                replies.append(f"no active_alerts".strip())

        else:
            replies.append(f"no qth data".strip())

        replies[0] = self.apply_channel_prefix(packet, interface, replies[0])
        self.send_reply(replies, packet, interface)
