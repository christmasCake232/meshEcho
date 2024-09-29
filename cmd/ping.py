from datetime import datetime

from meshtastic.stream_interface import StreamInterface

from .base import BaseCmd


class PingCmd(BaseCmd):
    def __init__(self, config: dict):
        super().__init__(key="ping", config=config)

        self.logger.info(f"cmd enabled: {self.__class__.__name__}")

    def help_line(self, escape: str) -> str:
        return f"{super().help_line(escape)}: reports packet received time"

    def __call__(self, escape: str, packet: dict, interface: StreamInterface):
        print(sorted(packet.keys()))
        now = datetime.now()
        buf = ["pong"]

        if "rxTime" in packet:
            dt = datetime.fromtimestamp(packet["rxTime"])
            buf.append(f'node time: {dt.strftime("%H:%M:%S")}')

        buf.append(f'host time: {now.strftime("%H:%M:%S")}')
        buf.append(f'hops: {packet.get("hopLimit", "*")}/{packet.get("hopStart", "*")}')

        text = self.apply_channel_prefix(packet, interface, "\n".join(buf))
        self.send_reply([text], packet, interface)
