import re
from typing import List

from meshtastic.stream_interface import StreamInterface

from .base import BaseCmd


class ManCmd(BaseCmd):
    def __init__(self, config: dict, escape: str, cmds: List[BaseCmd]):
        super().__init__(key="man", config=config)

        self._cmd_mapping = {cmd.key: cmd.help_line(escape) for cmd in cmds}
        self._cmd_mapping[self.key] = self.help_line(escape)

        self.logger.info(f"cmd enabled: {self.__class__.__name__}")

    def help_line(self, escape: str) -> str:
        cmds = " ".join(sorted(self._cmd_mapping.keys()))
        return f"{super().help_line(escape)}: list available cmd: {cmds}"

    def __call__(self, escape: str, packet: dict, interface: StreamInterface):
        text = self.get_text(packet)

        man_text = None
        for cmd, help_line in self._cmd_mapping.items():
            if re.match(rf"^\s*{escape}{self.key}\s+({escape})?{cmd}.*", text):
                man_text = help_line
                break

        if not man_text:
            man_text = self.help_line(escape)

        man_text = self.apply_channel_prefix(packet, interface, man_text)
        self.send_reply([man_text], packet, interface)
