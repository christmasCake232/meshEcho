import logging
from datetime import timedelta
from logging import Logger
from typing import List

from meshtastic import BROADCAST_NUM
from meshtastic.mesh_interface import MeshInterface

from config_check import ConfigCheck
from interface_utils import get_long_name
from interface_utils import get_short_name


class BaseCmd:

    def __init__(self, key: str, config: dict):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._key = key

        config_check = ConfigCheck(
            config,
            self.__class__.__name__,
            None,
            self.logger
        )

        self._blacklist = config_check.get("blacklist", [], list).copy()
        self._whitelist = config_check.get("whitelist", [], list).copy()
        if self._blacklist and self._whitelist:
            self.logger.error(f"config error: 'blacklist' and 'whitelist' are mutually exclusive")
            exit(1)

        self._config = config_check

    def check_access(self, from_id: str) -> bool:
        if not self._blacklist and not self._whitelist:
            return True
        elif from_id not in self._blacklist:
            return True
        elif from_id in self._whitelist:
            return True
        else:
            return False

    def __call__(self, escape: str, packet: dict, interface: MeshInterface):
        raise NotImplementedError()

    @property
    def logger(self) -> Logger:
        return self._logger

    @property
    def key(self) -> str:
        return self._key

    def help_line(self, escape: str) -> str:
        return f"{escape}{self.key}"

    @staticmethod
    def is_packet_dm(packet: dict, interface: MeshInterface) -> bool:
        return packet["to"] == interface.localNode.nodeNum

    @staticmethod
    def send_reply_dm(replies: List[str], packet: dict, interface: MeshInterface):
        from_id = packet["fromId"]
        for reply in replies:
            interface.sendText(reply, destinationId=from_id, wantAck=False)

    @staticmethod
    def send_reply_channel(replies: List[str], packet: dict, interface: MeshInterface):
        channel_index = packet.get("channel", 0)

        for reply in replies:
            interface.sendText(
                reply, channelIndex=channel_index, destinationId=BROADCAST_NUM, wantAck=False)

    def log_reply(self, replies: List[str], packet: dict, interface: MeshInterface):
        from_id = packet["fromId"]
        name = get_long_name(interface, from_id)
        reply = " ".join(" ".join(r.split()) for r in replies)
        self.logger.info(f"from {name}: '{self.get_text(packet)}' -> '{reply}'")

    def send_reply(self, replies: List[str], packet: dict, interface: MeshInterface):

        if self.is_packet_dm(packet=packet, interface=interface):
            self.send_reply_dm(
                replies,
                interface=interface,
                packet=packet
            )
        else:
            self.send_reply_channel(
                replies,
                interface=interface,
                packet=packet
            )

        self.log_reply(replies, packet, interface)

    def apply_channel_prefix(self, packet: dict, interface: MeshInterface, text: str) -> str:
        if self.is_packet_dm(packet, interface):
            return text

        else:
            return f"{self.reply_prefix(packet, interface)}\n{text}"

    def reply_prefix(self, packet: dict, interface: MeshInterface) -> str:
        name = get_short_name(interface, packet["fromId"])
        return f"{self.key}({name})"

    # def format_age(self, time_: int, now: int = None) -> str:
    #     now = now or int(time.time())
    #     return self.format_time_delta(timedelta(seconds=now - time_))

    @staticmethod
    def format_time_delta(td: timedelta) -> str:
        total_seconds = td.total_seconds()
        if total_seconds >= (60 * 60):
            h = total_seconds / (60 * 60)
            return f"{h:.0f}h"
        elif total_seconds >= 60:
            m = total_seconds / 60
            return f"{m:.0f}m"
        else:
            return f"{total_seconds:.0f}s"

    @staticmethod
    def get_text(packet: dict, ) -> str:
        return packet["decoded"]["text"]
