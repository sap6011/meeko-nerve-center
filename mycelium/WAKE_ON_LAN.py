import socket
import struct
import json
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

def wake_machine(mac_address):
    # The 'Magic Packet' that wakes up a computer over Wi-Fi
    add_octets = mac_address.split(':')
    hwa = struct.pack('BBBBBB', *[int(x, 16) for x in add_octets])
    msg = b'\xff' * 6 + hwa * 16
    
    soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    soc.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    soc.sendto(msg, ('255.255.255.255', 9))
    print(f"⚡ Energy Sent: Waking {mac_address} for heavy tasking.")

if __name__ == "__main__":
    # Add your secondary machine's MAC address here
    # wake_machine('AA:BB:CC:DD:EE:FF')
    pass


# -- LIVE_WIRE topology connector --
def _wire_state():
    _r = json.loads((DATA / "known_devices.json").read_text()) if (DATA / "known_devices.json").exists() else {}
    (DATA / "wake_on_lan_state.json").write_text(json.dumps({"last_run": __import__("datetime").datetime.now().isoformat(), "status": "wired"}, indent=2))
