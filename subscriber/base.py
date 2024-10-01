import logging
from logging import Logger
from typing import List

from meshtastic.mesh_interface import MeshInterface
from pubsub import pub


class BaseSubscriber:

    def __init__(self, default_topic: str, logger: Logger = None):
        self._default_topic = default_topic
        self._logger = logger or logging.getLogger(self.__class__.__name__)

    def __call__(self, packet: dict, interface: MeshInterface):
        raise NotImplementedError()

    def pubsub_subscribe(self, topic: str = None):
        topic = topic or self.default_topic
        self.logger.info(f"subscribing to {topic}")
        pub.subscribe(self, topic)

    @property
    def logger(self) -> Logger:
        return self._logger

    @property
    def default_topic(self) -> str:
        return self._default_topic

    @staticmethod
    def dict_get(d: dict, path: List[str] | str, default=None):

        if isinstance(path, list):
            working = d
            for key in path:
                working = working.get(key, None)
                if working is None:
                    return default

            return working

        elif isinstance(path, str):
            return d.get(path, default)

        else:
            raise TypeError()
