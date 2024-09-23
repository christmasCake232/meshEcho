from logging import Logger
from sys import exit


class ConfigCheck:

    def __init__(self, config_name: str, required: list):
        self._config_name = config_name
        self._required = required.copy()

    @property
    def config_name(self):
        return self._config_name

    @property
    def required(self):
        return self._required.copy()

    def validate_config(self, config: dict, logger: Logger):
        sub_config = config.get(self.config_name, None)
        if sub_config is None:
            logger.error(f"{self.config_name} is not defined in config file")
            exit(1)
        else:
            for k in self.required:
                if k not in sub_config:
                    logger.error(f"{self.config_name}[{k}] is not defined in config file")
                    exit(1)

        return self.get_sub_config(config)

    def get_sub_config(self, config: dict):
        return config[self.config_name]
