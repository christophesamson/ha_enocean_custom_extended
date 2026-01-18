#!/usr/bin/env python3
"""Simple test script for EnOcean USB 300 dongle."""
import sys
import time

print("🔌 Starting EnOcean dongle test...", flush=True)

# Add the custom_components to path
sys.path.insert(0, 'custom_components/enocean_custom')

print("📦 Importing libraries...", flush=True)
from enocean_library.communicators import SerialCommunicator
from enocean_library.protocol.packet import RadioPacket

def packet_callback(packet):
    """Callback for received packets."""
    print(f"\n📥 PACKET RECEIVED!", flush=True)
    print(f"   Data: {[hex(b) for b in packet.data]}", flush=True)
    if isinstance(packet, RadioPacket):
        print(f"   Sender: {hex(packet.sender_int)}", flush=True)
        print(f"   RORG: {hex(packet.rorg)}", flush=True)

if len(sys.argv) < 2:
    print("Usage: python3 test_dongle_simple.py <device_path>")
    sys.exit(1)

device_path = sys.argv[1]
print(f"🔗 Connecting to {device_path}...", flush=True)

try:
    comm = SerialCommunicator(port=device_path, callback=packet_callback)
    comm.start()
    print("✅ Connected!", flush=True)
    
    time.sleep(0.5)
    
    if comm.base_id:
        print(f"📋 Base ID: {[hex(b) for b in comm.base_id]}", flush=True)
    
    print("\n👂 Listening for packets... Press Ctrl+C to stop", flush=True)
    print("   (Try pressing an EnOcean switch!)", flush=True)
    print("-" * 50, flush=True)
    
    while True:
        time.sleep(0.1)
        
except KeyboardInterrupt:
    print("\n🛑 Stopping...", flush=True)
except Exception as e:
    print(f"❌ Error: {e}", flush=True)
    import traceback
    traceback.print_exc()
finally:
    if 'comm' in dir():
        comm.stop()
    print("👋 Done", flush=True)

