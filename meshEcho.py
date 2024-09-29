#!/usr/bin/env python

import logging
import os.path
import time
import tomllib
from argparse import ArgumentParser
from argparse import ArgumentTypeError
from logging import Logger
from sys import exit
from typing import Optional

import meshtastic
import meshtastic.serial_interface
import paho.mqtt.client as mqtt

from config_check import ConfigCheck
from subscriber import CmdSubscriber
from subscriber import MqttSubscriber


def load_config() -> dict:
    def is_file(s):
        if not os.path.isfile(s):
            raise ArgumentTypeError(f"{s} is not a file")

        return s

    parser = ArgumentParser()
    parser.add_argument(
        "-c", "--config",
        default="meshEcho.toml",
        required=False,
        type=is_file
    )
    args = parser.parse_args()
    with open(args.config, "rb") as fd:
        config = tomllib.load(fd)

    return config


def get_mqtt_client(config: dict, logger: Logger) -> Optional[mqtt.Client]:
    mqtt_config = ConfigCheck(
        config,
        "mqtt",
        ["username", "password", "host"],
        logger
    )
    # mqtt_config = config_check.validate_config(config, logger)

    if mqtt_config.get("enabled", False, bool):

        logger.info("setting up mqtt client")

        mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        mqtt_client.username_pw_set(
            username=mqtt_config["username"],
            password=mqtt_config["password"]
        )
        try:
            mqtt_client.connect(
                host=mqtt_config["host"],
                port=mqtt_config.get("port", 1883, int),
                keepalive=mqtt_config.get("keepalive", 60, int)
            )
            mqtt_client.loop_start()
        except ConnectionRefusedError:
            logger.error(f"failed to setup mqtt client: Connection refused")
            exit(1)

        for index in range(3):
            time.sleep(1)
            if mqtt_client.is_connected():
                break
            else:
                logger.info("trying to connect to mqtt broker...")

        if not mqtt_client.is_connected():
            logger.error("failed to connect to mqtt broker")
            exit(1)

        return mqtt_client

    else:
        logger.info("mqtt client disabled")
        return None


def connect_to_node(config: dict, logger: Logger):
    mesh_config = ConfigCheck(config, "meshtastic", ["port"], logger)
    port = mesh_config["port"]

    exit_flag = False
    while not exit_flag:
        logger.info(f"trying to connect to {port}...")
        try:
            iface = meshtastic.serial_interface.SerialInterface(devPath=port)
            logger.info(f"connected to {port}")

            logger.info(f"{iface.getShortName()} {iface.getLongName()}")

            while iface.isConnected.is_set():
                try:
                    time.sleep(5)

                except KeyboardInterrupt:
                    exit_flag = True
                    iface.close()
                    break

            if not exit_flag:
                logger.info("trying to reconnect...")
                time.sleep(5)
        except FileNotFoundError:
            logger.info(f"port not found {port}...")
            exit_flag = True


def print_banner(logger: Logger):
    banner_path = "banner.txt"
    if os.path.isfile(banner_path):
        with open(banner_path, "r") as fd:
            for line in fd:
                logger.info(line.strip("\n"))


def get_logger() -> Logger:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname).1s %(name)-20s:%(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )
    logger = logging.getLogger("meshEcho")
    return logger


def main():
    logger = get_logger()
    config = load_config()

    print_banner(logger)

    mqtt_client = get_mqtt_client(config, logger)

    mqtt_sub = MqttSubscriber(config, mqtt_client)
    mqtt_sub.pubsub_subscribe()

    cmd_sub = CmdSubscriber(config)
    cmd_sub.pubsub_subscribe()

    connect_to_node(config, logger)

    logger.info("exiting")


if __name__ == '__main__':
    main()
