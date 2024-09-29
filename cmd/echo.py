from meshtastic.stream_interface import StreamInterface

from interface_utils import get_long_name
from .base import BaseCmd


class EchoCmd(BaseCmd):

    def __init__(self, config: dict):
        super().__init__(key="echo", config=config)

        self.logger.info(f"cmd enabled: {self.__class__.__name__}")

    def help_line(self, escape: str) -> str:
        return f"{super().help_line(escape)}: display a line of text"

    @staticmethod
    def _sanitize_text(text: str) -> str:
        return " ".join(text.split())

    def __call__(self, escape: str, packet: dict, interface: StreamInterface):
        text = self.get_text(packet).strip().lstrip(f"{escape}{self.key}").strip()
        if text:
            text = self.apply_channel_prefix(packet, interface, text)
            self.send_reply([text], packet, interface)

        else:
            from_id = packet["fromId"]
            from_name = get_long_name(interface, from_id)
            self.logger.info(f"from {from_name}: '{text}' -> empty body, dropping")
