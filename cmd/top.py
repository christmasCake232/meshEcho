import subprocess
import time

import psutil
from meshtastic.stream_interface import StreamInterface

from .base import BaseCmd


class TopCmd(BaseCmd):
    def __init__(self, config: dict):
        super().__init__(key="top", config=config)

        self.logger.info(f"cmd enabled: {self.__class__.__name__}")

    def help_line(self, escape: str) -> str:
        return f"{super().help_line(escape)}: reports host status"

    @staticmethod
    def host_uptime():
        uptime = time.time() - psutil.boot_time()
        return f"{uptime}s"
        # return FormatUtils.format_td(uptime)

    @staticmethod
    def get_rpi_status():
        try:
            result = subprocess.run(["vcgencmd", "get_throttled"], stdout=subprocess.PIPE)
            # https://www.raspberrypi.com/documentation/computers/os.html#get_throttled
            return result.stdout.decode()
        except FileNotFoundError:
            pass

        return "not found"

    def __call__(self, escape: str, packet: dict, interface: StreamInterface):
        buf = []
        if not self.is_packet_dm(packet, interface):
            buf.append(self.reply_prefix(packet, interface))

        load1, load5, load15 = psutil.getloadavg()
        buf.extend([
            f"load avg: {load1:.2f}, {load5:.2f}, {load15:.2f}",
            f"ram:{psutil.virtual_memory().percent}%, swap:{psutil.swap_memory().percent}%",
            f"uptime:{self.host_uptime()}"
        ])

        rpi_status = self.get_rpi_status()
        if rpi_status:
            buf.append(rpi_status)

        replies = ["\n".join(buf)]
        self.send_reply(replies, packet, interface)
