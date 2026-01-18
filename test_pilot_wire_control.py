#!/usr/bin/env python3
"""
Test script for controlling NodOn Pilot Wire Module (D2-01-0C).

Usage:
    python3 test_pilot_wire_control.py /dev/tty.usbserial-FT4TVD76

Commands:
    0 - Off
    1 - Comfort
    2 - Eco
    3 - Frost Protection
    4 - Comfort -1°C
    5 - Comfort -2°C
    t - Teach-in
    q - Quit
"""
import sys
import time

print("🔌 NodOn Pilot Wire Controller", flush=True)
print("=" * 50, flush=True)

# Add the custom_components to path
sys.path.insert(0, 'custom_components/enocean_custom')

from enocean_library.communicators import SerialCommunicator
from enocean_library.protocol.packet import Packet, RadioPacket

# Configuration - Update these for your setup
DONGLE_BASE_ID = [0xFF, 0xB2, 0x99, 0x00]  # Your dongle's base ID
SENDER_ID = [0xFF, 0xB2, 0x99, 0x00]       # Sender ID - using base ID (offset 0) like Jeedom
SENDER_OFFSET = 0  # Current offset from base ID

# NodOn device ID (the device we're sending TO)
NODON_DEVICE_ID = [0x05, 0x87, 0x98, 0xD1]  # Your NodOn's ID from received packets

# Pilot Wire modes
MODES = {
    0: ("Off", "Heater completely off"),
    1: ("Comfort", "Full heating"),
    2: ("Eco", "Reduced heating (~comfort - 3.5°C)"),
    3: ("Frost Protection", "Minimum heating"),
    4: ("Comfort -1°C", "Comfort minus 1°C"),
    5: ("Comfort -2°C", "Comfort minus 2°C"),
}

# Global communicator
comm = None


def packet_callback(packet):
    """Handle received packets."""
    if not isinstance(packet, RadioPacket):
        return
    
    if packet.rorg == 0xD2:  # VLD packet
        cmd = (packet.data[1] >> 4) & 0x0F
        if cmd == 0x0A:  # Pilot Wire Mode Response
            mode = packet.data[2] & 0x0F
            mode_name = MODES.get(mode, ("Unknown", ""))[0]
            print(f"\n📥 Response from device:", flush=True)
            print(f"   Sender: {hex(packet.sender_int)}", flush=True)
            print(f"   Mode: {mode} ({mode_name})", flush=True)
        else:
            print(f"\n📥 VLD packet (CMD={hex(cmd)}): {[hex(b) for b in packet.data]}", flush=True)
    else:
        print(f"\n📥 Packet (RORG={hex(packet.rorg)}): {[hex(b) for b in packet.data]}", flush=True)


def send_pilot_wire_mode(mode: int):
    """Send a pilot wire mode command."""
    global comm, SENDER_ID
    
    # Build VLD packet for D2-01-0C
    # CMD 0x08 = Set Pilot Wire Mode
    # Note: Pilot wire commands (0x08-0x0A) use CMD as full byte, NOT shifted!
    # Jeedom sends: [0xD2, 0x08, 0x01, sender_id..., 0x00]
    
    data = [0xD2]  # RORG = VLD
    data.append(0x08)  # CMD = 8 (Set Pilot Wire Mode) - NOT shifted!
    data.append(mode & 0x0F)  # Mode value (1=comfort, 2=eco, etc.)
    data.extend(SENDER_ID)
    data.append(0x00)  # Status
    
    # Optional data: SubTelNum + Destination ID + dBm + Security
    optional = [0x03]  # SubTelNum
    optional.extend(NODON_DEVICE_ID)  # Destination = NodOn device
    optional.append(0xFF)  # dBm
    optional.append(0x00)  # Security level
    
    packet = Packet(0x01, data=data, optional=optional)
    
    mode_info = MODES.get(mode, ("Unknown", ""))
    print(f"\n📤 Sending: Mode {mode} ({mode_info[0]})", flush=True)
    print(f"   {mode_info[1]}", flush=True)
    print(f"   To: {[hex(b) for b in NODON_DEVICE_ID]}", flush=True)
    print(f"   From: {[hex(b) for b in SENDER_ID]}", flush=True)
    print(f"   Packet: {[hex(b) for b in data]}", flush=True)
    
    comm.send(packet)
    print("   ✅ Sent!", flush=True)


def send_teach_in():
    """Send UTE teach-in packet for D2-01-0C."""
    global comm, SENDER_ID
    
    # UTE teach-in packet
    data = [0xD4]  # UTE RORG
    data.append(0x20)  # Bidirectional teach-in request
    data.append(0xD2)  # EEP RORG
    data.append(0x01)  # EEP FUNC
    data.append(0x0C)  # EEP TYPE
    data.append(0x00)  # Manufacturer ID high (NodOn = 0x0046)
    data.append(0x46)  # Manufacturer ID low
    data.extend(SENDER_ID)
    data.append(0x00)  # Status
    
    # Optional data with destination
    optional = [0x03]
    optional.extend(NODON_DEVICE_ID)
    optional.append(0xFF)
    optional.append(0x00)
    
    packet = Packet(0x01, data=data, optional=optional)
    
    print(f"\n📤 Sending TEACH-IN packet", flush=True)
    print(f"   EEP: D2-01-0C (Pilot Wire)", flush=True)
    print(f"   Sender ID: {[hex(b) for b in SENDER_ID]}", flush=True)
    print(f"   To device: {[hex(b) for b in NODON_DEVICE_ID]}", flush=True)
    
    comm.send(packet)
    print("   ✅ Sent! Put your NodOn in learn mode to pair.", flush=True)


def send_simple_teach_in():
    """Send a simple teach-in by sending comfort command (some devices learn from this)."""
    global comm, SENDER_ID
    
    # Some devices learn from a regular command while in learn mode
    # Send comfort mode as teach-in
    data = [0xD2]  # RORG = VLD
    data.append(0x08)  # CMD 0x08 (NOT shifted, matching Jeedom format)
    data.append(0x01)  # Mode = Comfort
    data.extend(SENDER_ID)
    data.append(0x00)
    
    # Optional data with destination
    optional = [0x03]
    optional.extend(NODON_DEVICE_ID)
    optional.append(0xFF)
    optional.append(0x00)
    
    packet = Packet(0x01, data=data, optional=optional)
    
    print(f"\n📤 Sending SIMPLE TEACH-IN (Comfort command)", flush=True)
    print(f"   Some devices learn from regular commands", flush=True)
    print(f"   Sender ID: {[hex(b) for b in SENDER_ID]}", flush=True)
    print(f"   To device: {[hex(b) for b in NODON_DEVICE_ID]}", flush=True)
    
    # Send it 3 times for better chance of pairing
    for i in range(3):
        comm.send(packet)
        time.sleep(0.3)
    
    print("   ✅ Sent 3x! Check if NodOn confirms pairing.", flush=True)


def change_sender_id(offset: int):
    """Change the sender ID offset from base ID."""
    global SENDER_ID, SENDER_OFFSET
    
    if offset < 0 or offset > 127:
        print("❌ Offset must be between 0 and 127", flush=True)
        return
    
    SENDER_OFFSET = offset
    SENDER_ID = DONGLE_BASE_ID.copy()
    SENDER_ID[3] = (DONGLE_BASE_ID[3] + offset) & 0xFF
    
    print(f"\n✅ Sender ID changed to: {[hex(b) for b in SENDER_ID]} (offset +{offset})", flush=True)


def print_menu():
    """Print the command menu."""
    print("\n" + "=" * 50, flush=True)
    print(f"📋 Current Sender ID: {[hex(b) for b in SENDER_ID]} (offset +{SENDER_OFFSET})", flush=True)
    print("=" * 50, flush=True)
    print("Mode commands:", flush=True)
    for mode, (name, desc) in MODES.items():
        print(f"   {mode} - {name}: {desc}", flush=True)
    print("-" * 50, flush=True)
    print("Other commands:", flush=True)
    print("   t - Send UTE TEACH-IN", flush=True)
    print("   s - Send SIMPLE teach-in", flush=True)
    print("   c - Change sender ID offset (try 1-10 to find Jeedom's ID)", flush=True)
    print("   m - Show this menu", flush=True)
    print("   q - Quit", flush=True)
    print("=" * 50, flush=True)


def main():
    global comm
    
    if len(sys.argv) < 2:
        print("Usage: python3 test_pilot_wire_control.py <device_path>")
        print("Example: python3 test_pilot_wire_control.py /dev/tty.usbserial-FT4TVD76")
        sys.exit(1)
    
    device_path = sys.argv[1]
    
    print(f"\n🔗 Connecting to {device_path}...", flush=True)
    
    try:
        comm = SerialCommunicator(port=device_path, callback=packet_callback)
        comm.start()
        print("✅ Connected!", flush=True)
        
        time.sleep(0.5)
        
        if comm.base_id:
            print(f"📋 Dongle Base ID: {[hex(b) for b in comm.base_id]}", flush=True)
        
        print(f"📋 Using Sender ID: {[hex(b) for b in SENDER_ID]}", flush=True)
        
        print_menu()
        
        while True:
            try:
                cmd = input("\n🎮 Enter command: ").strip().lower()
                
                if cmd == 'q':
                    break
                elif cmd == 't':
                    send_teach_in()
                elif cmd == 's':
                    send_simple_teach_in()
                elif cmd == 'm':
                    print_menu()
                elif cmd == 'c':
                    try:
                        offset_str = input("   Enter offset (1-127): ").strip()
                        change_sender_id(int(offset_str))
                    except ValueError:
                        print("❌ Invalid offset", flush=True)
                elif cmd in ['0', '1', '2', '3', '4', '5']:
                    send_pilot_wire_mode(int(cmd))
                else:
                    print("❌ Invalid command. Enter 0-5, t, s, c, m, or q", flush=True)
                    
            except EOFError:
                break
                
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted", flush=True)
    except Exception as e:
        print(f"\n❌ Error: {e}", flush=True)
        import traceback
        traceback.print_exc()
    finally:
        if comm:
            comm.stop()
        print("👋 Goodbye!", flush=True)


if __name__ == "__main__":
    main()