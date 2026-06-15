# traffic_shaper.py - Protocol Sabotage & Tarpitting Engine
# Responds to incoming scanner probes with weaponized TCP responses

from scapy.all import sniff, IP, TCP, send   # Packet capture, crafting, and sending
import json          # JSON logging
import datetime      # Timestamps
import os            # File operations
import random        # Random window jitter and MSS selection

def log_event(event_type, attacker_ip, details=""):
    """
    Appends Layer 4 entrapment telemetry to the central intelligence feed.
    Synchronized with the JSON array structure utilized by the Dashboard.
    """
    # Same logging logic as other components - writes to mutation_logs.json
    log_file = 'mutation_logs.json'
    new_entry = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event": event_type,
        "ip": attacker_ip,
        "details": details
    }

    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = []
    else:
        data = []

    data.append(new_entry)
    with open(log_file, 'w') as f:
        json.dump(data, f, indent=4)

def process_packet(pkt):
    """
    Intercepts TCP probes and crafts a deceptive, weaponized SYN-ACK response.
    Implements 'Window Jitter' to induce a Persist Timer state, alongside
    TCP Option Sabotage (MSS constraint) to cripple adversary stack buffers.
    Neutralizes SYN, FIN, NULL, and XMAS scanning techniques.
    """
    # Only process TCP packets (ignore UDP, ICMP, etc.)
    if pkt.haslayer(TCP):
        # Extract attacker information from the probe packet
        attacker_ip = pkt[IP].src          # Attacker's IP address
        target_port = pkt[TCP].dport       # Port they're scanning on our server
        tcp_flags = pkt[TCP].flags         # TCP flags (S=SYN, F=FIN, etc.)

        # Detect various scanning techniques:
        # "S"   - Normal SYN scan (most common)
        # "F"   - FIN scan (stealth, bypasses some firewalls)
        # "FPU" - XMAS scan (FIN+PUSH+URGENT - all flags set)
        # ""    - NULL scan (no flags set)
        if tcp_flags == "S" or tcp_flags == "F" or tcp_flags == "FPU" or tcp_flags == "":

            # WINDOW JITTER: Weaponize the TCP window field
            # 85% of the time: window = 0 (FREEZE - enter Persist Timer state)
            # 15% of the time: window = 5 or 10 (THROTTLE - crippled throughput)
            # random.random() returns 0.0 to 1.0, >0.15 is ~85% probability
            fake_window = 0 if random.random() > 0.15 else random.choice([5, 10])

            # TCP OPTION SABOTAGE: Craft malicious TCP options
            # ('MSS', tiny_value) - Maximum Segment Size (normal=1460)
            #   Setting to 48/128/256 forces attacker to use tiny packets
            # ('WScale', 0) - Disables window scaling, prevents high-speed transfers
            sabotage_options = [('MSS', random.choice([48, 128, 256])), ('WScale', 0)]

            # Craft the IP layer for our response
            # dst = attacker's IP (send it back to them)
            # src = original destination IP (spoofed to appear from the probed server)
            ip_layer = IP(dst=attacker_ip, src=pkt[IP].dst)

            # Craft the weaponized TCP layer
            tcp_layer = TCP(
                sport=target_port,                    # Source port matches what they probed
                dport=pkt[TCP].sport,                 # Send to attacker's source port
                flags="SA",                           # SYN-ACK (standard response to SYN)
                seq=random.getrandbits(32),           # Random 32-bit sequence number
                ack=pkt[TCP].seq + 1 if tcp_flags == "S" else 0,  # ACK number (if SYN)
                window=fake_window,                   # Our weaponized window (0, 5, or 10)
                options=sabotage_options              # Crippling TCP options
            )

            # Send the crafted packet (IP layer + TCP layer combined with /)
            # verbose=False suppresses Scapy's output
            send(ip_layer/tcp_layer, verbose=False)

            # Prepare log messages
            scan_type = "SYN" if tcp_flags == "S" else "STEALTH"
            status = f"FROZEN (Win=0, MSS={sabotage_options[0][1]})" if fake_window == 0 else f"THROTTLED (Win={fake_window})"

            # Console output for operator
            print(f"[ACTION] {scan_type} Scan Entrapped: {attacker_ip} -> {status} on port {target_port}")
            # Log to JSON file
            log_event("TARPIT_ENTRAPMENT", attacker_ip, f"Type: {scan_type} | State: {status} | Port: {target_port}")

# Main execution
if __name__ == "__main__":
    print("[*] Initializing Aegis Morph Supreme Protocol Tarpit...")
    print("[*] Active Modules: Window Jitter | TCP Option Sabotage | Multi-Vector Defense")

    # Start packet capture
    try:
        # sniff() captures packets matching the filter
        # filter="tcp" - BPF filter, only capture TCP packets (like tcpdump)
        # prn=process_packet - call this function for every captured packet
        # This blocks forever, processing packets as they arrive
        sniff(filter="tcp", prn=process_packet)
    except KeyboardInterrupt:
        # Graceful shutdown on Ctrl+C
        print("\n[*] Terminating Protocol Tarpit.")
    except Exception as e:
        print(f"[CRITICAL] Tarpit failure: {e}")
