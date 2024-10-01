from meshtastic.mesh_interface import MeshInterface


def get_long_name(interface: MeshInterface, from_id: str):
    return interface.nodes.get(from_id, {}).get("user", {}).get("longName", from_id)


def get_short_name(interface: MeshInterface, from_id: str):
    return interface.nodes.get(from_id, {}).get("user", {}).get("shortName", from_id)
