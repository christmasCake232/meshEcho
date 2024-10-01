import re

from meshtastic.mesh_interface import MeshInterface

from cmd import EchoCmd
from cmd import ManCmd
from cmd import NoaaCmd
from cmd import PingCmd
from cmd import RollCmd
from cmd import TopCmd
from config_check import ConfigCheck
from interface_utils import get_long_name
from .base import BaseSubscriber


class CmdSubscriber(BaseSubscriber):
    _cmds = [
        EchoCmd,
        NoaaCmd,
        PingCmd,
        RollCmd,
        TopCmd,
    ]

    def __init__(self, config: dict):
        super().__init__(default_topic="meshtastic.receive.text")

        config_check = ConfigCheck(
            config,
            self.__class__.__name__,
            ["escape"],
            self.logger
        )

        self._escape = config_check["escape"]
        self._blacklist = config_check.get("blacklist", [], list).copy()
        self._whitelist = config_check.get("whitelist", [], list).copy()
        if self._blacklist and self._whitelist:
            self.logger.error(f"config error: 'blacklist' and 'whitelist' are mutually exclusive")
            exit(1)

        self._cmd_list = []
        for cmd in self._cmds:
            if cmd.__name__ in config:
                self._cmd_list.append(cmd(config=config))
            else:
                self.logger.info(f"cmd disabled: {cmd.__name__}")

        if ManCmd.__name__ in config:
            man_cmd = ManCmd(config=config, cmds=self._cmd_list, escape=self.escape)
            self._cmd_list.append(man_cmd)

        else:
            self.logger.info(f"cmd disabled: {ManCmd.__name__}")

    def check_access(self, from_id: str) -> bool:
        if not self._blacklist and not self._whitelist:
            return True
        elif from_id not in self._blacklist:
            return True
        elif from_id in self._whitelist:
            return True
        else:
            return False

    @property
    def escape(self) -> str:
        return self._escape

    def __call__(self, packet: dict, interface: MeshInterface):
        from_id = packet["fromId"]
        from_name = get_long_name(interface, from_id)
        text = packet["decoded"]["text"]

        if self.check_access(from_id):
            for cmd in self._cmd_list:
                if re.match(rf"^\s*{self.escape}{cmd.key}.*", text):
                    if cmd.check_access(from_id):
                        cmd(self.escape, packet, interface)

                    else:
                        cmd.logger.info(f"access denied for {from_name}({from_id})")

                    break
        else:
            self.logger.info(f"access denied for {from_name}({from_id})")
