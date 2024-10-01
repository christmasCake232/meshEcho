import random
import re
from typing import List
from typing import Optional
from typing import Tuple

from meshtastic.mesh_interface import MeshInterface

from .base import BaseCmd


class RollCmd(BaseCmd):

    def __init__(self, config: dict):
        super().__init__(key="roll", config=config)

        self._default_rolls = self._config.get("default_rolls", 3, int)
        self._default_sides = self._config.get("default_sides", 6, int)

        self._max_rolls = self._config.get("max_rolls", 20, int)
        self._max_sides = self._config.get("max_sides", 100, int)
        self.logger.info(f"cmd enabled: {self.__class__.__name__}")

    def help_line(self, escape: str) -> str:
        return f"{super().help_line(escape)}: [N][dM]- generate random (N)umbers X where X in [1,M]"

    def get_numbers(self, text: str) -> Tuple[Optional[int], Optional[int], List[int]]:
        if text:

            rolls, sides = None, None
            if re.match(rf"^{self.key}$", text):
                # no args
                rolls, sides = self._default_rolls, self._default_sides

            elif re.match(rf"^{self.key}\d+$", text):
                # N
                args = re.findall(r"\d+", text)
                rolls, sides = int(args[0]), self._default_sides

            elif re.match(rf"^{self.key}\d+d\d+$", text):
                # NdM
                args = re.findall(r"\d+", text)
                rolls, sides = int(args[0]), int(args[1])

            elif re.match(rf"^{self.key}d\d+", text):
                # dM
                args = re.findall(r"\d+", text)
                rolls, sides = 3, int(args[0])

            if rolls is not None and sides is not None:
                rolls, sides = min(rolls, self._max_rolls), min(sides, self._max_sides)
                return rolls, sides, [random.randint(1, sides) for _ in range(rolls)]

            return None, None, []

    def __call__(self, escape: str, packet: dict, interface: MeshInterface):

        text = "".join(self.get_text(packet).lstrip(escape).split())
        count, upper_range, numbers = self.get_numbers(text)
        if numbers:
            reply = f'{count}d{upper_range} Σ({",".join(str(i) for i in numbers)})={sum(numbers)}'

            reply = self.apply_channel_prefix(packet, interface, reply)
            self.send_reply([reply], packet, interface)
