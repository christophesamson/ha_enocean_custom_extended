#!/usr/bin/env python3
"""
Simple test script for EnOcean USB 300 dongle.

Usage:
    1. Plug in your USB 300 dongle
    2. Find the device path (usually /dev/tty.usbserial-* on macOS)
    3. Run: python3 test_dongle.py /dev/tty.usbserial-XXXXX

This script will:
    - Connect to the dongle
    - Read the base ID
    - Listen for incoming EnOcean packets
    - Optionally send a pilot wire command
"""
import sys
import time

# Add the custom_components to path
sys.path.insert(0, 'custom_components/enocean_custom')

from enocean_library.communicators import SerialCommunicator
from enocean_library.protocol.packet import Packet, RadioPacket
from enocean_library.protocol.constants import PACKET


def packet_callback(packet):
    """Callback for received packets."""
    print(f"\n📥 Received packet:")
    print(f"   Type: {type(packet).__name__}")
    print(f"   Data: {[hex(b) for b in packet.data]}")
    if hasattr(packet, 'sender_int'):
        print(f"   Sender ID: {hex(packet.sender_int)}")
    if hasattr(packet, 'rorg'):
        print(f"   RORG: {hex(packet.rorg)}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 test_dongle.py <device_path>")
        print("\nTo find your device path, run:")
        print("  ls /dev/tty.usbserial* /dev/tty.USB* /dev/cu.* 2>/dev/null | grep -i usb")
        print("\nExample:")
        print("  python3 test_dongle.py /dev/tty.usbserial-FT123456")
        sys.exit(1)

    device_path = sys.argv[1]
    print(f"🔌 Connecting to EnOcean dongle at {device_path}...")

    try:
        communicator = SerialCommunicator(port=device_path, callback=packet_callback)
        communicator.start()
        print("✅ Connected!")

        # Wait a moment for connection to establish
        time.sleep(1)

        # Try to get the base ID
        print("\n📋 Dongle information:")
        if communicator.base_id:
            base_id_hex = [hex(b) for b in communicator.base_id]
            print(f"   Base ID: {base_id_hex}")
        else:
            print("   Base ID: (querying...)")

        print("\n👂 Listening for EnOcean packets...")
        print("   Press Ctrl+C to stop\n")
        print("   Try pressing an EnOcean switch or trigger a sensor!")
        print("-" * 50)

        # Keep running until Ctrl+C
        while True:
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\n🛑 Stopping...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  - Is the dongle plugged in?")
        print("  - Is the device path correct?")
        print("  - Do you have permission to access the serial port?")
        sys.exit(1)
    finally:
        if 'communicator' in locals():
            communicator.stop()
            print("👋 Disconnected")


if __name__ == "__main__":
    main()

