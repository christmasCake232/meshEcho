import subprocess
import time
from datetime import timedelta

import psutil
from meshtastic.mesh_interface import MeshInterface

from .base import BaseCmd


class TopCmd(BaseCmd):
    def __init__(self, config: dict):
        super().__init__(key="top", config=config)

        self.logger.info(f"cmd enabled: {self.__class__.__name__}")

    def help_line(self, escape: str) -> str:
        return f"{super().help_line(escape)}: reports host status"

    def host_uptime(self):
        uptime = time.time() - psutil.boot_time()
        return self.format_time_delta(timedelta(seconds=uptime))

    @staticmethod
    def get_rpi_status():
        try:
            result = subprocess.run(["vcgencmd", "get_throttled"], stdout=subprocess.PIPE)
            # https://www.raspberrypi.com/documentation/computers/os.html#get_throttled
            throttled = int(result.stdout.decode().strip().split("=")[-1], 0)
            status = []
            if (1 << 0) & throttled != 0:
                status.append("Undervoltage detected")
            if (1 << 1) & throttled != 0:
                status.append("Arm frequency capped")
            if (1 << 2) & throttled != 0:
                status.append("Currently throttled")
            if (1 << 3) & throttled != 0:
                status.append("Soft temperature limit active")
            if (1 << 16) & throttled != 0:
                status.append("Undervoltage has occurred")
            if (1 << 17) & throttled != 0:
                status.append("Arm frequency capping has occurred")
            if (1 << 18) & throttled != 0:
                status.append("Throttling has occurred")
            if (1 << 19) & throttled != 0:
                status.append("Soft temperature limit has occurred")

            if status:
                return ",".join(status)

        except FileNotFoundError:
            return None

    def __call__(self, escape: str, packet: dict, interface: MeshInterface):
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
