# core_deception.py - High-Interaction Deception Layer (Ghost Ship Listener)
# Creates fake services that trap, interact with, and log attacker behavior

import asyncio      # Async framework - handles thousands of connections without threads
import json         # For logging structured data to JSON file
import datetime     # Adds timestamps to all log entries
import os           # Checks if log files exist before writing

def log_event(event_type, attacker_ip, details=""):
    """
    Appends threat intelligence data to the central JSON log.
    Acts as the telemetry feed for the Aegis Command Center.
    """
    # All components write to the SAME file for unified intelligence feed
    log_file = 'mutation_logs.json'
    
    # Create a structured log entry with timestamp, event type, attacker IP, and details
    new_entry = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event": event_type,
        "ip": attacker_ip,
        "details": details
    }

    # Check if log file already exists on disk
    if os.path.exists(log_file):
        try:
            # Try to read existing JSON data into a list
            with open(log_file, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            # If file is corrupted or empty, start fresh with empty list
            data = []
    else:
        # No file exists yet, start with empty list
        data = []

    # Add the new entry to the end of the list
    data.append(new_entry)

    # Write the entire list back to file with pretty formatting (4 spaces indent)
    with open(log_file, 'w') as f:
        json.dump(data, f, indent=4)

async def handle_attacker(reader, writer):
    """
    Routes the adversary to a specific high-interaction deception module.
    Personality routing is determined mathematically to ensure consistency.
    """
    # Get attacker's address and port (e.g., ('192.168.1.100', 54321))
    addr = writer.get_extra_info('peername')
    # Get the local address and port the attacker connected TO (e.g., ('0.0.0.0', 1001))
    sock = writer.get_extra_info('sockname')
    
    # Extract just the IP address from the tuple
    attacker_ip = addr[0]
    # Extract just the destination port number
    port = sock[1]

    # MATHEMATICAL ROUTING: port modulo 5 gives consistent profile per port
    # Port 1000 → 0, 1001 → 1, 1002 → 2, 1003 → 3, 1004 → 4, 1005 → 0, etc.
    personality_seed = port % 5

    # Log to console for operator visibility
    print(f"[ALERT] Scanner detected from IP {attacker_ip} on port {port} (Profile {personality_seed})")
    # Write to JSON log file
    log_event("GHOST_SHIP_DETECTION", attacker_ip, f"Targeting Profile {personality_seed} on port {port}")

    try:
        # PROFILE 0: Simulated Data Leak (ports 1000, 1005, 1010...)
        if personality_seed == 0:
            # Fake HTTP response with "leaked" environment variables and credentials
            fake_env = (
                "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n"
                "# DEBUG MODE ENABLED\nDB_HOST=127.0.0.1\nDB_USER=root\n"
                "DB_PASS=AegisSecret2026!\nAPI_KEY=sk_live_51MzXjHG92kd...\n"
            )
            # Convert string to bytes and send to attacker
            writer.write(fake_env.encode())
            # Wait until all data is actually transmitted
            await writer.drain()
            # Hold connection open for 10 seconds to waste attacker's time
            await asyncio.sleep(10)

        # PROFILE 1: Interactive Shell Mimicry (ports 1001, 1006, 1011...)
        elif personality_seed == 1:
            # Send fake Linux shell prompt
            writer.write(b"ubuntu@sirpt-victim:~$ ")
            await writer.drain()

            # Infinite loop - keep connection alive until attacker disconnects or times out
            while True:
                # Wait up to 30 seconds for attacker to send a command
                data = await asyncio.wait_for(reader.read(1024), timeout=30.0)
                if not data:
                    # Connection closed, exit loop
                    break

                # Decode bytes to string, ignoring any invalid UTF-8, and remove whitespace
                command = data.decode('utf-8', errors='ignore').strip()

                # Simulate processing latency to look like a real system
                await asyncio.sleep(2.5)
                # Reject every command with permission denied, then show prompt again
                writer.write(f"sh: 1: {command}: Permission denied\nubuntu@sirpt-victim:~$ ".encode())
                await writer.drain()

                # Log every command the attacker attempts
                log_event("SHELL_MIMICRY", attacker_ip, f"Command attempted: {command}")

        # PROFILE 2: Credential Harvesting Module (ports 1002, 1007, 1012...)
        elif personality_seed == 2:
            # Fake FTP server banner asking for username
            writer.write(b"220-Development Backup Server\r\nLogin: ")
            await writer.drain()

            # Wait up to 10 seconds for username input
            creds = await asyncio.wait_for(reader.read(1024), timeout=10.0)
            if creds:
                # Ask for password
                writer.write(b"331 Password required\r\nPassword: ")
                await writer.drain()

                # Wait up to 10 seconds for password input
                passwd = await asyncio.wait_for(reader.read(1024), timeout=10.0)

                # Decode and clean up the captured credentials
                decoded_user = creds.decode('utf-8', errors='ignore').strip()
                decoded_pass = passwd.decode('utf-8', errors='ignore').strip()
                
                # LOG THE CAPTURED CREDENTIALS - this is the payoff!
                log_event("CREDENTIAL_HARVEST", attacker_ip, f"Captured: {decoded_user} / {decoded_pass}")

        # PROFILE 3: Standard SSH Decoy with Latency (ports 1003, 1008, 1013...)
        elif personality_seed == 3:
            # Send fake SSH version banner (real SSH servers do this)
            writer.write(b"SSH-2.0-OpenSSH_8.2p1\r\n")
            await writer.drain()
            # Hold connection open for 15 seconds doing nothing
            # Wastes attacker time and bypasses fast scanners
            await asyncio.sleep(15)

        # PROFILE 4: Tool-Breaker Infinite Payload (ports 1004, 1009, 1014...)
        elif personality_seed == 4:
            # Send HTTP header indicating JSON response is coming
            writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n")
            await writer.drain()
            log_event("TOOL_SABOTAGE", attacker_ip, "Deploying infinite recursion payload")

            # Infinite loop that never ends
            while True:
                # Send chunks of incomplete JSON (no closing brackets)
                # Repeated 50 times per chunk to overwhelm parsers
                writer.write(b'{"aegis_morph_data_leak":' * 50)
                await writer.drain()
                # Sleep 0.5 seconds to avoid overloading our own server
                # while keeping attacker's connection open
                await asyncio.sleep(0.5)

    except asyncio.TimeoutError:
        # Attacker didn't respond in time - ignore and continue
        pass
    except Exception:
        # Any other error (connection reset, broken pipe) - ignore to prevent crash
        pass
    finally:
        # ALWAYS close the connection properly, no matter what happened
        writer.close()
        await writer.wait_closed()

async def deploy_phantom_network(start_port, end_port):
    """
    Initializes the asynchronous listeners to create the deception surface.
    """
    # List to store all server objects (so we can control them)
    servers = []
    print("[*] Initializing Aegis Morph Deception Layer...")

    # Loop through every port in the specified range (1000 to 1100 inclusive)
    for port in range(start_port, end_port + 1):
        try:
            # Create a TCP server that listens on ALL interfaces ('0.0.0.0')
            # Each connection calls handle_attacker()
            server = await asyncio.start_server(handle_attacker, '0.0.0.0', port)
            servers.append(server)
        except Exception:
            # Port is already in use (by another service) - skip it silently
            continue

    # Show how many ports we successfully opened
    print(f"[+] Ghost Ship active. Listening on {len(servers)} high-interaction polymorphic ports.")
    
    # Run all servers forever - this line NEVER returns (runs until killed)
    # The * unpacks the list of servers into individual arguments
    await asyncio.gather(*[s.serve_forever() for s in servers])

# Main execution - only runs if script is executed directly (not imported)
if __name__ == "__main__":
    # Start the deception network on ports 1000 through 1100
    asyncio.run(deploy_phantom_network(1000, 1100))
