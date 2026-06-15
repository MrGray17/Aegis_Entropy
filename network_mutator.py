# network_mutator.py - Moving Target Defense (MTD) Engine
# Modifies outgoing TCP packets to spoof OS fingerprints and confuse reconnaissance

import os           # File operations
import json         # JSON logging
import random       # Random selection of OS profiles per packet
import datetime     # Timestamps for logs
from scapy.all import IP, TCP      # Packet manipulation library - only import needed layers
from netfilterqueue import NetfilterQueue  # Hooks into Linux iptables to intercept packets

# Hardcoded path to log file - note: should match other components for unified logging
LOG_FILE = "/home/admin-sirpt/aegis_morph/mutation_logs.json"

def log_event(event_type, src_port, new_ttl):
    """
    Appends packet mutation data to the central intelligence feed.
    Synchronized with the JSON array structure used by the Dashboard.
    """
    # Create log entry - note IP is "LOCAL_OUTBOUND" because this is OUR traffic
    new_entry = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event": event_type,
        "ip": "LOCAL_OUTBOUND",
        "details": f"Port: {src_port} | Mutated TTL: {new_ttl}"
    }

    # Read existing log file (same logic as core_deception.py)
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = []
    else:
        data = []

    # Append and write back
    data.append(new_entry)
    with open(LOG_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def mutate_packet(packet):
    """
    Intercepts and modifies outgoing TCP/IP packets at Layer 3/4.
    Alters Time-To-Live (TTL) and TCP Window sizes to spoof OS fingerprints,
    creating a Moving Target Defense (MTD) effect against reconnaissance.
    """
    try:
        # Extract raw packet bytes and parse into Scapy packet object
        scapy_pkt = IP(packet.get_payload())

        # Only modify TCP packets (ignore UDP, ICMP, etc.)
        if scapy_pkt.haslayer(TCP):
            # Define realistic OS fingerprint profiles
            # Each OS has characteristic starting TTL and TCP window ranges
            os_profiles = [
                {"os": "Windows", "ttl": 128, "window": random.randint(8000, 8192)},
                {"os": "Cisco",   "ttl": 255, "window": random.randint(4000, 4128)},
                {"os": "Linux",   "ttl": 64,  "window": random.randint(5800, 5840)},
                {"os": "Solaris", "ttl": 254, "window": random.randint(8100, 8192)}
            ]

            # Pick a RANDOM profile for THIS packet only
            # Next packet might get a different OS
            profile = random.choice(os_profiles)
            
            # Modify the packet fields to match the chosen OS
            scapy_pkt.ttl = profile["ttl"]
            scapy_pkt[TCP].window = profile["window"]

            # Delete existing checksums - they become invalid when we change fields
            # Deleting forces Scapy to recalculate correct ones automatically
            del scapy_pkt[IP].chksum
            del scapy_pkt[TCP].chksum

            # Replace original packet payload with our modified version
            packet.set_payload(bytes(scapy_pkt))

            # Console output for operator
            print(f"[*] Polymorphic Shift: Spoofing {profile['os']} (TTL: {profile['ttl']}, Win: {profile['window']})")
            # Log the mutation
            log_event("MTD_MUTATION", scapy_pkt[TCP].sport, profile['ttl'])

    except Exception as e:
        # Any error - fail silently. Don't crash, don't disrupt network traffic
        # The mutation is skipped, packet continues unchanged
        pass
    finally:
        # CRITICAL: Must release the packet back to the kernel
        # Without this, the packet is dropped and network breaks
        packet.accept()

# Main execution
if __name__ == "__main__":
    print("[*] Initializing Aegis Morph Polymorphic Engine (MTD)...")
    print("[*] Hooking into Netfilter Queue 1 for dynamic OS signature spoofing.")

    try:
        # Create NetfilterQueue object to interface with iptables
        nfqueue = NetfilterQueue()
        
        # Bind to queue number 1 (must match iptables --queue-num)
        # When iptables sends packets to queue 1, mutate_packet processes them
        nfqueue.bind(1, mutate_packet)
        
        # Start the loop - this blocks forever, processing packets as they arrive
        nfqueue.run()
        
    except KeyboardInterrupt:
        # Graceful shutdown on Ctrl+C
        print("\n[*] Terminating Polymorphic Engine.")
    except Exception as e:
        # Show helpful error if something goes wrong (wrong queue, no permissions)
        print(f"[CRITICAL] Engine failure: {e}")
        print("[!] Ensure iptables rules are configured and running as root.")
