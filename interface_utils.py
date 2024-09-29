from meshtastic.stream_interface import StreamInterface


def get_long_name(interface: StreamInterface, from_id: str):
    return interface.nodes.get(from_id, {}).get("user", {}).get("longName", from_id)


def get_short_name(interface: StreamInterface, from_id: str):
    return interface.nodes.get(from_id, {}).get("user", {}).get("shortName", from_id)
