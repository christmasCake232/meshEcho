import logging
from logging import Logger
from sys import exit


class ConfigCheck:

    def __init__(self, root_config: dict, config_name: str, required: list = None, logger: Logger = None):
        self._config_name = config_name
        self._required = required.copy() if required else []

        self._logger = logger or logging.getLogger(self.__class__.__name__)

        self._config = self.validate_config(root_config)

    @property
    def config_name(self):
        return self._config_name

    @property
    def required(self):
        return self._required.copy()

    @property
    def logger(self) -> Logger:
        return self._logger

    def validate_config(self, config: dict):
        sub_config = config.get(self.config_name, None)
        if sub_config is None:
            self.logger.error(f"{self.config_name} is not defined in config file")
            exit(1)
        else:
            for k in self.required:
                if k not in sub_config:
                    self.logger.error(f"{self.config_name}[{k}] is not defined in config file")
                    exit(1)

        return self.get_sub_config(config)

    def get_sub_config(self, config: dict):
        return config[self.config_name]

    def get(self, key: str, default=None, type_=None):
        value = self._config.get(key, default)
        if value is not default and type_ is not None and not isinstance(value, type_):
            self.logger.error(f"{self.config_name}[{key}] is not type {type_}")
            exit(1)

        return value

    def __getitem__(self, item):
        return self._config[item]
