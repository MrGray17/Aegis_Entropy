# Aegis Entropy: Autonomous Active Defense & MTD Framework

Aegis Entropy is a proactive security framework designed to shift the burden of engagement from the defender to the adversary. By implementing **Moving Target Defense (MTD)** and **High-Interaction Deception**, this system transforms a static network surface into a polymorphic, adversarial environment.

This project was developed within the **SIRPT** (Systèmes Informatiques Répartis et Programmation Temps-réel) engineering module to demonstrate advanced distributed threat intelligence and real-time autonomous response.

---

## Technical Architecture

The framework is composed of four integrated subsystems designed for zero-trust environments:

### 1. Moving Target Defense (network_mutator.py)
Utilizes Layer 3/4 packet mutation to invalidate adversarial reconnaissance. 
* **OS Fingerprint Spoofing**: Intercepts outgoing traffic via `NetfilterQueue` to dynamically alter **Time-To-Live (TTL)** and **TCP Window** sizes.
* **Reconnaissance Sabotage**: Concurrently mimics Windows, Linux, Cisco IOS, and Solaris signatures, rendering automated OS detection (Nmap, ZMap) inaccurate.

### 2. High-Interaction Deception (core_deception.py)
A "Ghost Ship" listener surface that engages adversaries across a wide port range.
* **Deterministic Personality Routing**: Maps ports to specific deception profiles (e.g., Simulated Data Leaks, Shell Mimicry, FTP Decoys) using a mathematical seed (Port % N).
* **Tool-Breaker Payloads**: Deploys infinite JSON recursion payloads to exhaust the memory and parsing capabilities of automated scanning tools.

### 3. Protocol Sabotage & Tarpitting (traffic_shaper.py)
Weaponizes the TCP stack to neutralize threats at the handshake level.
* **Window Jitter**: Forces attacker connections into a "Persist Timer" state by manipulating the TCP Window to 0.
* **MSS Constraints**: Hard-limits Maximum Segment Size (MSS) to disrupt exploitation buffers and cripple data throughput.

### 4. Autonomous Command Center (monitor_interface.py)
The centralized SOC dashboard and enforcement engine.
* **Threat Velocity Heuristics**: Calculates real-time threat levels (DEFCON) based on event frequency.
* **Kernel-Level Blackholing**: Automatically executes `ip route add blackhole` for IPs exceeding the ban threshold, ensuring zero-CPU cost packet dropping.

---

## Deployment Configuration

### Prerequisites
* Linux Kernel 5.x+
* Root/Sudo privileges
* Python 3.9+
* Required libraries: `scapy`, `netfilterqueue`, `asyncio`

### Initializing the MTD Hook
Before execution, outgoing TCP traffic must be routed to the mutation queue:
```bash
sudo iptables -A OUTPUT -p tcp -j NFQUEUE --queue-num 1
