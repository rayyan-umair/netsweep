"""
NetSweep - Network Discovery & Security Assessment
engine.py - Scanning Engine

Author  : Rayyan Umair
Date    : 4 May, 2026
Purpose : Core scanning logic. Handles host discovery, port scanning, banner
          grabbing, service detection, CVE lookup, risk scoring, and device
          profiling. Designed to be imported and driven by gui.py.
Contact : rayyanxumair@gmail.com
GitHub  : github.com/rayyan-umair

"Technology evolves quickly. Responsibility does not."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  This file is part of NetSweep, a network security scanner built for learners.
  Written and maintained by Rayyan Umair. All logic, structure, and design
  decisions in this file reflect the author's original work.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import subprocess
import socket
import json
import platform
import re
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from typing import Optional
import requests


# ─── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class PortInfo:
    port: int
    state: str          # open / closed / filtered
    service: str        # http, ssh, telnet, etc.
    version: str        # detected version string
    risk_level: str     # CRITICAL / HIGH / MEDIUM / LOW / INFO
    cve_ids: list       = field(default_factory=list)
    ai_explanation: dict = field(default_factory=dict)  # filled by ai.py

@dataclass
class DeviceInfo:
    ip: str
    mac: str            = "Unknown"
    hostname: str       = "Unknown"
    vendor: str         = "Unknown"
    os_guess: str       = "Unknown"
    device_type: str    = "Unknown"   # Router / Workstation / IoT / etc.
    open_ports: list    = field(default_factory=list)    # list[PortInfo]
    risk_score: int     = 0           # 0–100
    risk_label: str     = "Unknown"
    ai_summary: dict    = field(default_factory=dict)    # filled by ai.py

    def to_dict(self):
        d = asdict(self)
        return d


# ─── Risk Definitions ─────────────────────────────────────────────────────────

# Ports that carry inherent risk weight
PORT_RISK = {
    21:   ("FTP",            "HIGH",     "Unencrypted file transfer - credentials sent in plaintext"),
    22:   ("SSH",            "LOW",      "Encrypted remote access - generally safe, watch for old versions"),
    23:   ("Telnet",         "CRITICAL", "Unencrypted remote access - credentials fully exposed"),
    25:   ("SMTP",           "MEDIUM",   "Mail server - check for open relay"),
    53:   ("DNS",            "MEDIUM",   "DNS service - check for zone transfer"),
    80:   ("HTTP",           "MEDIUM",   "Unencrypted web server - data visible in transit"),
    110:  ("POP3",           "HIGH",     "Unencrypted email retrieval"),
    135:  ("RPC",            "HIGH",     "Windows RPC - common attack surface"),
    139:  ("NetBIOS",        "HIGH",     "Windows file sharing - legacy, frequently exploited"),
    143:  ("IMAP",           "HIGH",     "Unencrypted email - credentials exposed"),
    443:  ("HTTPS",          "LOW",      "Encrypted web server - generally safe"),
    445:  ("SMB",            "CRITICAL", "Windows file sharing - EternalBlue, ransomware vector"),
    1433: ("MSSQL",          "HIGH",     "Microsoft SQL Server - database exposure"),
    1521: ("Oracle DB",      "HIGH",     "Oracle database - sensitive data exposure"),
    3306: ("MySQL",          "HIGH",     "MySQL database - check for public exposure"),
    3389: ("RDP",            "CRITICAL", "Remote Desktop - brute force & BlueKeep target"),
    4444: ("Metasploit",     "CRITICAL", "Known exploit framework port - active compromise likely"),
    5432: ("PostgreSQL",     "HIGH",     "PostgreSQL database"),
    5900: ("VNC",            "CRITICAL", "Remote desktop - often password-less, full access"),
    6379: ("Redis",          "CRITICAL", "Redis cache - often unauthenticated, data exposure"),
    7547: ("TR-069",         "CRITICAL", "Router management - Mirai botnet target"),
    8080: ("HTTP-Alt",       "MEDIUM",   "Alternate web server or proxy"),
    8443: ("HTTPS-Alt",      "LOW",      "Alternate HTTPS"),
    9200: ("Elasticsearch",  "CRITICAL", "Search engine - often unauthenticated, data breach risk"),
    27017:("MongoDB",        "CRITICAL", "Database - frequently exposed without authentication"),
}

RISK_WEIGHTS = {"CRITICAL": 40, "HIGH": 20, "MEDIUM": 10, "LOW": 3, "INFO": 0}

def risk_label_from_score(score: int) -> str:
    if score >= 80: return "CRITICAL"
    if score >= 50: return "HIGH"
    if score >= 25: return "MEDIUM"
    if score >= 10: return "LOW"
    return "CLEAN"


# ─── Host Discovery ────────────────────────────────────────────────────────────

def ping_host(ip: str) -> bool:
    """Returns True if host responds to ping."""
    param = "-n" if platform.system().lower() == "windows" else "-c"
    try:
        result = subprocess.run(
            ["ping", param, "1", "-W", "1", str(ip)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3
        )
        return result.returncode == 0
    except Exception:
        return False

def arp_scan(network: str) -> dict:
    """
    Returns {ip: mac} for all hosts found via ARP.
    Falls back to ping sweep if arp-scan isn't available.
    """
    hosts = {}
    try:
        result = subprocess.run(
            ["arp-scan", "--localnet", "--quiet"],
            capture_output=True, text=True, timeout=30
        )
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2 and is_ip(parts[0]):
                hosts[parts[0]] = parts[1]
    except FileNotFoundError:
        # arp-scan not available - use ARP cache + ping sweep
        hosts = ping_sweep(network)
    return hosts

def ping_sweep(network: str) -> dict:
    """Ping sweep fallback - returns {ip: 'Unknown'} for alive hosts."""
    hosts = {}
    try:
        net = ipaddress.ip_network(network, strict=False)
        ips = list(net.hosts())
        # Limit to /24 for speed
        if len(ips) > 254:
            ips = ips[:254]
        with ThreadPoolExecutor(max_workers=50) as ex:
            futures = {ex.submit(ping_host, str(ip)): str(ip) for ip in ips}
            for f in as_completed(futures):
                ip = futures[f]
                if f.result():
                    hosts[ip] = lookup_mac_from_arp(ip)
    except Exception as e:
        print(f"[Engine] Ping sweep error: {e}")
    return hosts

def lookup_mac_from_arp(ip: str) -> str:
    """Pull MAC from system ARP cache."""
    try:
        result = subprocess.run(["arp", "-n", ip], capture_output=True, text=True, timeout=3)
        for line in result.stdout.splitlines():
            parts = line.split()
            if ip in parts:
                for p in parts:
                    if ":" in p or "-" in p:
                        return p.upper()
    except Exception:
        pass
    return "Unknown"

def is_ip(s: str) -> bool:
    try:
        ipaddress.ip_address(s)
        return True
    except ValueError:
        return False


# ─── Hostname & Vendor Resolution ─────────────────────────────────────────────

def resolve_hostname(ip: str) -> str:
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return "Unknown"

def lookup_vendor(mac: str) -> str:
    """OUI lookup via macvendors.com API (free, no key needed)."""
    if mac in ("Unknown", ""):
        return "Unknown"
    try:
        oui = mac.replace("-", ":").upper()[:8]
        r = requests.get(f"https://api.macvendors.com/{oui}", timeout=3)
        if r.status_code == 200:
            return r.text.strip()
    except Exception:
        pass
    return "Unknown"

def guess_device_type(hostname: str, vendor: str, open_ports: list) -> str:
    h = hostname.lower()
    v = vendor.lower()
    ports = [p.port for p in open_ports]

    if any(x in h for x in ["router", "gateway", "gw", "ap", "access"]):
        return "Router/Gateway"
    if any(x in v for x in ["cisco", "netgear", "ubiquiti", "tp-link", "asus", "linksys"]):
        return "Router/Gateway"
    if any(x in h for x in ["phone", "android", "iphone", "pixel"]):
        return "Mobile Device"
    if any(x in v for x in ["apple", "samsung", "huawei", "xiaomi", "lg electronics"]):
        return "Mobile/Consumer Device"
    if 80 in ports or 443 in ports:
        return "Web Server / IoT"
    if 3389 in ports or 445 in ports:
        return "Windows Workstation"
    if 22 in ports:
        return "Linux/Unix Host"
    return "Unknown Device"


# ─── Port Scanning ─────────────────────────────────────────────────────────────

COMMON_PORTS = sorted(PORT_RISK.keys()) + [
    8000, 8888, 9090, 10000, 49152
]

def scan_port(ip: str, port: int, timeout: float = 1.0) -> Optional[PortInfo]:
    """Returns PortInfo if port is open, None otherwise."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        if result == 0:
            service, risk_level, _ = PORT_RISK.get(port, (guess_service(port), "INFO", ""))
            version = grab_banner(ip, port)
            return PortInfo(
                port=port,
                state="open",
                service=service,
                version=version,
                risk_level=risk_level,
                cve_ids=lookup_cves(service, version)
            )
    except Exception:
        pass
    return None

def grab_banner(ip: str, port: int) -> str:
    """Attempt to grab service banner for version info."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect((ip, port))
        sock.send(b"HEAD / HTTP/1.0\r\n\r\n")
        banner = sock.recv(256).decode(errors="ignore").strip()
        sock.close()
        # Extract meaningful version info
        for line in banner.splitlines():
            if any(kw in line.lower() for kw in ["server:", "version", "openssh", "apache", "nginx", "iis"]):
                return line.strip()[:80]
        return banner[:80] if banner else ""
    except Exception:
        return ""

def guess_service(port: int) -> str:
    try:
        return socket.getservbyport(port)
    except Exception:
        return f"port-{port}"

def scan_all_ports(ip: str, ports: list = None, progress_cb=None) -> list:
    """Scan multiple ports concurrently. Returns list of open PortInfo objects."""
    ports = ports or COMMON_PORTS
    open_ports = []
    with ThreadPoolExecutor(max_workers=30) as ex:
        futures = {ex.submit(scan_port, ip, p): p for p in ports}
        done = 0
        for f in as_completed(futures):
            done += 1
            if progress_cb:
                progress_cb(done, len(ports))
            result = f.result()
            if result:
                open_ports.append(result)
    return sorted(open_ports, key=lambda p: p.port)


# ─── CVE Lookup ───────────────────────────────────────────────────────────────

def lookup_cves(service: str, version: str) -> list:
    """
    Query NVD (NIST) free API for CVEs related to service/version.
    Returns list of CVE IDs (strings).
    """
    if not service or service.startswith("port-"):
        return []
    try:
        keyword = f"{service} {version}".strip()[:100]
        url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        params = {"keywordSearch": keyword, "resultsPerPage": 5}
        r = requests.get(url, params=params, timeout=5)
        if r.status_code == 200:
            data = r.json()
            vulns = data.get("vulnerabilities", [])
            return [v["cve"]["id"] for v in vulns[:5]]
    except Exception:
        pass
    return []


# ─── Risk Scoring ─────────────────────────────────────────────────────────────

def calculate_risk(open_ports: list) -> tuple:
    """Returns (score 0-100, label string)."""
    score = 0
    for port_info in open_ports:
        score += RISK_WEIGHTS.get(port_info.risk_level, 0)
        score += len(port_info.cve_ids) * 5
    score = min(score, 100)
    return score, risk_label_from_score(score)


# ─── Full Device Scan ──────────────────────────────────────────────────────────

def scan_device(ip: str, mac: str = "Unknown", progress_cb=None) -> DeviceInfo:
    """Complete scan of a single device. Returns populated DeviceInfo."""
    hostname = resolve_hostname(ip)
    vendor = lookup_vendor(mac)
    open_ports = scan_all_ports(ip, progress_cb=progress_cb)
    risk_score, risk_label = calculate_risk(open_ports)
    device_type = guess_device_type(hostname, vendor, open_ports)

    return DeviceInfo(
        ip=ip,
        mac=mac,
        hostname=hostname,
        vendor=vendor,
        os_guess="",        # populated optionally
        device_type=device_type,
        open_ports=open_ports,
        risk_score=risk_score,
        risk_label=risk_label,
    )


# ─── Network Scan Orchestrator ─────────────────────────────────────────────────

def scan_network(network: str, progress_cb=None) -> list:
    """
    Full network scan.
    progress_cb(stage: str, current: int, total: int)
    Returns list of DeviceInfo.
    """
    # Stage 1: Discovery
    if progress_cb:
        progress_cb("discovery", 0, 1)
    hosts = arp_scan(network)
    if not hosts:
        hosts = ping_sweep(network)
    total = len(hosts)
    if progress_cb:
        progress_cb("discovery", total, total)

    # Stage 2: Device scans
    devices = []
    for i, (ip, mac) in enumerate(hosts.items()):
        if progress_cb:
            progress_cb("scanning", i, total)
        device = scan_device(ip, mac)
        devices.append(device)

    if progress_cb:
        progress_cb("scanning", total, total)

    return sorted(devices, key=lambda d: d.risk_score, reverse=True)


# ─── Quick test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.0/24"
    print(f"[NetSweep Engine] Scanning {target}...")

    def prog(stage, cur, tot):
        print(f"  [{stage}] {cur}/{tot}")

    devices = scan_network(target, progress_cb=prog)
    for d in devices:
        print(f"\n{d.ip} ({d.hostname}) - Risk: {d.risk_label} ({d.risk_score})")
        for p in d.open_ports:
            print(f"  :{p.port} {p.service} [{p.risk_level}]")
