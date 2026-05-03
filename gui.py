import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import json
import os
import time
import random
from pathlib import Path

# ─── Paths & Config ────────────────────────────────────────────────────────────
CONFIG_FILE = Path.home() / ".netraptor" / "config.json"
CONFIG_FILE.parent.mkdir(exist_ok=True)

APP_NAME    = "NETRAPTOR"
APP_AUTHOR  = "Rayyan Umair"
APP_TAGLINE = "Technology evolves quickly. Responsibility does not."
APP_VERSION = "2.0"

def load_config() -> dict:
    try:
        return json.loads(CONFIG_FILE.read_text())
    except Exception:
        return {}

def save_config(cfg: dict):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


# ─── Color Palette ─────────────────────────────────────────────────────────────
BG        = "#0a0e14"
BG2       = "#0f141c"
BG3       = "#161d28"
BG4       = "#1c2535"
BORDER    = "#1e2d42"
BORDER2   = "#243348"
TEXT      = "#cdd9e5"
TEXT_DIM  = "#6a8099"
TEXT_MUTE = "#3d5166"
ACCENT    = "#4fa3e0"
ACCENT2   = "#2d7fc1"
GREEN     = "#39d353"
GREEN_DIM = "#1a6b28"
YELLOW    = "#e3b341"
ORANGE    = "#f0883e"
RED       = "#f85149"
CRITICAL  = "#ff3333"
PURPLE    = "#bc8cff"
TEAL      = "#39c5c8"

RISK_COLORS = {
    "CRITICAL":   CRITICAL,
    "HIGH":       RED,
    "MEDIUM":     ORANGE,
    "LOW":        YELLOW,
    "INFO":       TEXT_DIM,
    "CLEAN":      GREEN,
    "UNKNOWN":    TEXT_DIM,
    "SAFE":       GREEN,
    "MONITOR":    YELLOW,
    "CONCERNING": ORANGE,
    "DANGEROUS":  CRITICAL,
}

RISK_EMOJI = {
    "CRITICAL":   "🔴",
    "HIGH":       "🟠",
    "MEDIUM":     "🟡",
    "LOW":        "🟢",
    "CLEAN":      "✅",
    "SAFE":       "✅",
    "MONITOR":    "👁",
    "CONCERNING": "⚠️",
    "DANGEROUS":  "💀",
    "UNKNOWN":    "❓",
    "INFO":       "ℹ️",
}


# ─── Demo / Hardcoded Results ──────────────────────────────────────────────────
# Newbies can explore without scanning a real network

DEMO_DEVICES = [
    {
        "ip": "192.168.1.1",
        "hostname": "gateway.local",
        "mac": "A4:3E:51:2B:8F:1C",
        "vendor": "Netgear",
        "device_type": "Router/Gateway",
        "risk_score": 72,
        "risk_label": "HIGH",
        "ai_summary": {
            "headline": "Your router has two dangerous ports open — Telnet must be disabled immediately.",
            "summary": "This is your network gateway, meaning all traffic flows through it. It's running Telnet (a protocol with zero encryption) alongside the admin web panel. Anyone on your network could intercept credentials or attempt to take control.",
            "top_priority": "Disable Telnet (port 23) in your router's admin panel right now.",
            "overall_verdict": "CONCERNING",
        },
        "open_ports": [
            {
                "port": 23, "service": "Telnet", "version": "BusyBox v1.26.2",
                "risk_level": "CRITICAL", "cve_ids": ["CVE-2019-9081", "CVE-2018-5767"],
                "ai_explanation": {
                    "what_is_it": "Telnet is a remote control protocol from the 1970s. It lets someone log into this router and issue commands — like having a keyboard plugged directly into it over the network.",
                    "why_it_matters": "Telnet sends everything — including your router's admin password — in plain text. If anyone on your network runs a free tool called Wireshark, they can read every character you type.",
                    "real_risk": "An attacker on your WiFi (like a neighbor or someone at a coffee shop on the same network) can capture your router admin password and reconfigure your entire network, redirect all your traffic, or install malware on every connected device.",
                    "how_to_fix": "Log into your router admin panel (usually at 192.168.1.1 in your browser). Go to Administration → Remote Management or Services. Find 'Telnet' and switch it OFF. Save and reboot. Use SSH instead if you need remote access.",
                    "severity_reason": "CRITICAL because the admin password for your entire network travels unencrypted through the air.",
                }
            },
            {
                "port": 80, "service": "HTTP", "version": "lighttpd 1.4.53",
                "risk_level": "MEDIUM", "cve_ids": [],
                "ai_explanation": {
                    "what_is_it": "Port 80 is the standard web port — this is how your router serves its admin web interface when you type 192.168.1.1 in your browser.",
                    "why_it_matters": "HTTP (without the S) means data between your browser and the router isn't encrypted. Your admin session could be intercepted by someone on the same network.",
                    "real_risk": "Session hijacking: an attacker captures your session cookie and takes over your logged-in admin session without needing your password.",
                    "how_to_fix": "Enable HTTPS for the admin panel in your router settings. Most modern routers support this under Administration → Access. After enabling, always use https://192.168.1.1 to log in.",
                    "severity_reason": "MEDIUM because it's internal-only, but unencrypted admin access is still a risk on shared networks.",
                }
            },
            {
                "port": 443, "service": "HTTPS", "version": "lighttpd 1.4.53",
                "risk_level": "LOW", "cve_ids": [],
                "ai_explanation": {
                    "what_is_it": "Port 443 is the encrypted web port (HTTPS). Your router uses this to serve a secure version of its admin panel.",
                    "why_it_matters": "Unlike port 80, traffic on port 443 is encrypted, so intercepting it yields only gibberish. This is the correct way to access your router's admin interface.",
                    "real_risk": "Low risk in isolation — the main concern would be an outdated TLS version or weak cipher suite, but this requires specific tools to exploit.",
                    "how_to_fix": "Ensure you're using HTTPS for all router admin access. Consider disabling the plain HTTP admin panel (port 80) so all access is forced through HTTPS.",
                    "severity_reason": "LOW because encrypted access is expected and correct — just ensure the HTTP version is disabled.",
                }
            },
        ]
    },
    {
        "ip": "192.168.1.42",
        "hostname": "DESKTOP-RAYYAN",
        "mac": "B8:27:EB:4D:A1:55",
        "vendor": "Dell",
        "device_type": "Windows Workstation",
        "risk_score": 85,
        "risk_label": "CRITICAL",
        "ai_summary": {
            "headline": "This Windows PC has SMB exposed — it's vulnerable to the same attack that spread WannaCry ransomware.",
            "summary": "This workstation has three ports open that are commonly targeted in ransomware campaigns. The combination of SMB, RDP, and NetBIOS on one machine is a red flag — attackers actively scan for exactly this profile.",
            "top_priority": "Patch Windows immediately and disable SMBv1 — run 'Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol' in PowerShell as Administrator.",
            "overall_verdict": "DANGEROUS",
        },
        "open_ports": [
            {
                "port": 445, "service": "SMB", "version": "Windows SMBv1",
                "risk_level": "CRITICAL", "cve_ids": ["CVE-2017-0144", "CVE-2017-0145", "CVE-2020-0796"],
                "ai_explanation": {
                    "what_is_it": "SMB (Server Message Block) is Windows' file sharing protocol — it's how Windows PCs share files and printers. Port 445 is the modern SMB port.",
                    "why_it_matters": "SMBv1 is the exact vulnerability exploited by WannaCry in 2017, which infected 230,000 computers in 150 countries in a single day. Microsoft patched it, but only if Windows Update has been run.",
                    "real_risk": "A device on the same network running EternalBlue (a freely available exploit) can take complete control of this machine within seconds — no password required. From there, ransomware can spread to every other device on the network automatically.",
                    "how_to_fix": "1) Open PowerShell as Administrator. 2) Run: Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol. 3) Run Windows Update and install all patches. 4) Reboot. 5) If you don't share files, also disable SMBv2: Set-SmbServerConfiguration -EnableSMB2Protocol $false.",
                    "severity_reason": "CRITICAL because this is the exact exploit used in the largest ransomware attack in history, and it requires zero user interaction.",
                }
            },
            {
                "port": 3389, "service": "RDP", "version": "Microsoft Terminal Services",
                "risk_level": "CRITICAL", "cve_ids": ["CVE-2019-0708", "CVE-2021-34535"],
                "ai_explanation": {
                    "what_is_it": "RDP (Remote Desktop Protocol) lets you control this Windows computer from another machine — you see the full desktop remotely, as if you were sitting in front of it.",
                    "why_it_matters": "RDP is one of the top three ways ransomware gangs break into company networks. Automated scanners hit port 3389 millions of times per day across the internet.",
                    "real_risk": "BlueKeep (CVE-2019-0708) allows remote code execution with no authentication. Even a patched RDP can be brute-forced — attackers use wordlists of common passwords and can try thousands per minute.",
                    "how_to_fix": "If RDP is not needed, disable it: System → Remote Desktop → Off. If needed: 1) Enable Network Level Authentication (NLA). 2) Set account lockout after 5 failed attempts (Local Security Policy). 3) Use a VPN — never expose RDP directly to the internet. 4) Change the port from 3389 to a non-standard port.",
                    "severity_reason": "CRITICAL because BlueKeep allows unauthenticated remote takeover, and brute-force tools are freely available.",
                }
            },
            {
                "port": 139, "service": "NetBIOS", "version": "",
                "risk_level": "HIGH", "cve_ids": ["CVE-2008-4250"],
                "ai_explanation": {
                    "what_is_it": "NetBIOS is a legacy Windows networking protocol from the 1980s. Port 139 provides file and printer sharing through the older NetBIOS interface — it's essentially the ancestor of SMB.",
                    "why_it_matters": "NetBIOS leaks information about the computer (its name, domain, user) to anyone who asks — no credentials required. It's also exploitable in combination with other attacks.",
                    "real_risk": "Attackers use NetBIOS to map your network silently — learning what machines exist, what they're named, and what users are logged in. This recon information is used to plan targeted attacks.",
                    "how_to_fix": "Disable NetBIOS over TCP/IP: Network Connections → Adapter Properties → IPv4 Properties → Advanced → WINS tab → 'Disable NetBIOS over TCP/IP'. If file sharing isn't needed, also disable the 'File and Printer Sharing' feature entirely.",
                    "severity_reason": "HIGH because it leaks network intelligence and has a long history of direct exploits on unpatched systems.",
                }
            },
        ]
    },
    {
        "ip": "192.168.1.77",
        "hostname": "raspberrypi.local",
        "mac": "DC:A6:32:11:F4:B2",
        "vendor": "Raspberry Pi Foundation",
        "device_type": "Linux/Unix Host",
        "risk_score": 28,
        "risk_label": "MEDIUM",
        "ai_summary": {
            "headline": "Raspberry Pi with SSH open — safe if the default password has been changed.",
            "summary": "This Pi has SSH enabled, which is normal and expected. The risk is entirely dependent on whether the default 'raspberry' password has been changed. Many Pi owners never change it.",
            "top_priority": "Run 'passwd' on the Pi right now and set a strong, unique password if you haven't already.",
            "overall_verdict": "MONITOR",
        },
        "open_ports": [
            {
                "port": 22, "service": "SSH", "version": "OpenSSH 8.9p1",
                "risk_level": "LOW", "cve_ids": [],
                "ai_explanation": {
                    "what_is_it": "SSH (Secure Shell) is an encrypted remote access protocol — it lets you control this Raspberry Pi from a terminal window on another computer. It's the secure, modern replacement for Telnet.",
                    "why_it_matters": "SSH itself is secure. The risk is entirely in the password (or key) used to authenticate. Raspberry Pi devices ship with the username 'pi' and password 'raspberry' — and millions of Pi owners never change this.",
                    "real_risk": "If the default credentials haven't been changed, any device on your network can log into this Pi instantly with 'ssh pi@192.168.1.77' and the default password. From there, an attacker controls a Linux machine on your network.",
                    "how_to_fix": "1) SSH in: ssh pi@192.168.1.77. 2) Run: passwd — set a strong password (12+ characters, mix of letters, numbers, symbols). 3) Better yet, switch to SSH key authentication and disable password login: edit /etc/ssh/sshd_config, set 'PasswordAuthentication no'. 4) Consider changing the default 'pi' username.",
                    "severity_reason": "LOW because SSH is encrypted — but the default password situation makes this a MEDIUM risk until confirmed changed.",
                }
            },
            {
                "port": 80, "service": "HTTP", "version": "nginx 1.18.0",
                "risk_level": "MEDIUM", "cve_ids": [],
                "ai_explanation": {
                    "what_is_it": "This Pi is running a web server on port 80 — likely Pi-hole (a network ad blocker), Home Assistant, or a personal project.",
                    "why_it_matters": "If this web app has no login or a weak one, anyone on the network can access it. Depending on what it controls (smart home devices, DNS settings), this could have wide impact.",
                    "real_risk": "If it's Pi-hole: an attacker could modify your DNS settings to redirect traffic. If it's Home Assistant: full control of smart home devices. If it's a personal project: depends on what data it exposes.",
                    "how_to_fix": "Enable authentication on whatever app is running here. Keep the software updated (sudo apt update && sudo apt upgrade). If this service isn't intentional, find what's running with: sudo systemctl list-units --type=service.",
                    "severity_reason": "MEDIUM because the risk depends entirely on what application is exposed and whether it has authentication.",
                }
            },
        ]
    },
    {
        "ip": "192.168.1.112",
        "hostname": "Unknown",
        "mac": "50:C7:BF:3A:9E:20",
        "vendor": "Espressif",
        "device_type": "IoT Device",
        "risk_score": 45,
        "risk_label": "MEDIUM",
        "ai_summary": {
            "headline": "Unknown Espressif IoT device with an open admin panel — identify this before trusting it.",
            "summary": "Espressif makes the ESP8266/ESP32 chips used in millions of cheap smart home devices — bulbs, plugs, sensors. This device has a web admin panel open with no hostname, which means it may be using default credentials.",
            "top_priority": "Identify what this device is, log into its web panel, and change the default password.",
            "overall_verdict": "MONITOR",
        },
        "open_ports": [
            {
                "port": 80, "service": "HTTP", "version": "ESP-IDF httpd",
                "risk_level": "MEDIUM", "cve_ids": [],
                "ai_explanation": {
                    "what_is_it": "This is a web admin interface built into an IoT device — likely a smart plug, smart bulb, or DIY sensor running on an Espressif ESP chip.",
                    "why_it_matters": "IoT devices are infamous for shipping with default passwords like 'admin/admin' that users never change. They're often poorly maintained with no security updates.",
                    "real_risk": "Mirai botnet (which knocked major websites offline in 2016) spread by scanning for exactly this type of device with default credentials. A compromised IoT device can be used to attack other devices or flood networks with traffic.",
                    "how_to_fix": "1) Open 192.168.1.112 in your browser and log in. 2) Change the default password immediately. 3) Check if the device has firmware updates — apply them. 4) Consider putting all IoT devices on a separate WiFi network (VLAN or guest network) so they can't reach your main devices.",
                    "severity_reason": "MEDIUM because IoT devices with default credentials are trivially compromised and frequently targeted by automated botnets.",
                }
            },
        ]
    },
    {
        "ip": "192.168.1.200",
        "hostname": "iphone-rayyan.local",
        "mac": "3C:22:FB:D1:7A:44",
        "vendor": "Apple",
        "device_type": "Mobile/Consumer Device",
        "risk_score": 0,
        "risk_label": "CLEAN",
        "ai_summary": {
            "headline": "iPhone with no open ports — this device looks secure.",
            "summary": "Apple devices are designed with security in mind. No open ports means no exposed services. This is the expected profile for a well-maintained iPhone.",
            "top_priority": "Keep iOS updated — Apple regularly patches security vulnerabilities.",
            "overall_verdict": "SAFE",
        },
        "open_ports": []
    },
]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def make_demo_device_objects():
    """Convert demo dicts into simple namespace objects for compatibility."""
    class PortObj:
        def __init__(self, d):
            self.port = d["port"]
            self.service = d["service"]
            self.version = d["version"]
            self.risk_level = d["risk_level"]
            self.cve_ids = d["cve_ids"]
            self.ai_explanation = d.get("ai_explanation", {})

    class DevObj:
        def __init__(self, d):
            self.ip = d["ip"]
            self.hostname = d["hostname"]
            self.mac = d["mac"]
            self.vendor = d["vendor"]
            self.device_type = d["device_type"]
            self.risk_score = d["risk_score"]
            self.risk_label = d["risk_label"]
            self.ai_summary = d.get("ai_summary", {})
            self.open_ports = [PortObj(p) for p in d["open_ports"]]
        def to_dict(self):
            return {"ip": self.ip, "hostname": self.hostname}

    return [DevObj(d) for d in DEMO_DEVICES]


# ─── Tooltip ─────────────────────────────────────────────────────────────────

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=self.text, font=("Courier", 8),
                 fg=TEXT, bg=BG4, relief="flat", padx=8, pady=4,
                 borderwidth=1).pack()

    def hide(self, event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


# ─── API Setup Dialog ─────────────────────────────────────────────────────────

class APISetupDialog(tk.Toplevel):
    def __init__(self, parent, on_complete):
        super().__init__(parent)
        self.on_complete = on_complete

        self.title(f"{APP_NAME} — AI Setup")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()
        self.focus_force()

        w, h = 560, 480
        self.update_idletasks()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        self._build()

    def _build(self):
        # Top accent bar
        tk.Frame(self, bg=ACCENT, height=3).pack(fill="x")

        # Header
        hdr = tk.Frame(self, bg=BG, pady=20)
        hdr.pack(fill="x", padx=30)
        tk.Label(hdr, text=f"◈ {APP_NAME}", font=("Courier", 20, "bold"),
                 fg=ACCENT, bg=BG).pack(anchor="w")
        tk.Label(hdr, text="Unlock AI-Powered Security Explanations",
                 font=("Helvetica", 11, "bold"), fg=TEXT, bg=BG).pack(anchor="w", pady=(4, 0))
        tk.Label(hdr, text=APP_TAGLINE,
                 font=("Helvetica", 9, "italic"), fg=TEXT_DIM, bg=BG).pack(anchor="w")

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=30)

        # Info
        info = tk.Frame(self, bg=BG, pady=12)
        info.pack(fill="x", padx=30)
        tk.Label(info,
                 text="Your API key is stored locally in ~/.netraptor/config.json\n"
                      "It is never shared, transmitted, or uploaded anywhere.",
                 font=("Helvetica", 9), fg=TEXT_DIM, bg=BG,
                 justify="left").pack(anchor="w")

        # Provider
        pf = tk.Frame(self, bg=BG)
        pf.pack(fill="x", padx=30, pady=(8, 4))
        tk.Label(pf, text="AI Provider:", font=("Helvetica", 10),
                 fg=TEXT_DIM, bg=BG, width=12, anchor="w").pack(side="left")

        # Import PROVIDERS here explicitly to avoid NameError
        from ai import PROVIDER_NAMES
        self.provider_var = tk.StringVar(value=PROVIDER_NAMES[0])
        cb = ttk.Combobox(pf, textvariable=self.provider_var,
                          values=PROVIDER_NAMES, state="readonly",
                          width=24, font=("Helvetica", 10))
        cb.pack(side="left", padx=(8, 0))

        # API Key
        kf = tk.Frame(self, bg=BG)
        kf.pack(fill="x", padx=30, pady=4)
        tk.Label(kf, text="API Key:", font=("Helvetica", 10),
                 fg=TEXT_DIM, bg=BG, width=12, anchor="w").pack(side="left")
        self.key_var = tk.StringVar()
        self.key_entry = tk.Entry(
            kf, textvariable=self.key_var,
            font=("Courier", 10), bg=BG3, fg=TEXT,
            insertbackground=ACCENT, relief="flat",
            highlightthickness=1, highlightbackground=BORDER,
            highlightcolor=ACCENT, show="•", width=32
        )
        self.key_entry.pack(side="left", padx=(8, 6), ipady=5)
        self.show_var = tk.BooleanVar()

        def toggle_show():
            self.key_entry.config(show="" if self.show_var.get() else "•")

        tk.Checkbutton(kf, text="show", variable=self.show_var,
                       command=toggle_show, bg=BG, fg=TEXT_DIM,
                       selectcolor=BG3, activebackground=BG,
                       font=("Helvetica", 9)).pack(side="left")

        # Where to get keys
        lf = tk.Frame(self, bg=BG)
        lf.pack(fill="x", padx=30, pady=(2, 10))
        tk.Label(lf, text="Get a free key →", font=("Helvetica", 8),
                 fg=TEXT_DIM, bg=BG).pack(side="left")
        for txt in ["console.anthropic.com", "platform.openai.com", "aistudio.google.com"]:
            tk.Label(lf, text=f"  {txt}", font=("Helvetica", 8),
                     fg=ACCENT, bg=BG).pack(side="left")

        # Status
        self.status_lbl = tk.Label(self, text="", font=("Helvetica", 9),
                                   fg=GREEN, bg=BG)
        self.status_lbl.pack(pady=4)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=30)

        # Buttons
        bf = tk.Frame(self, bg=BG, pady=20)
        bf.pack()

        tk.Button(bf, text="Skip for now", font=("Helvetica", 10),
                  fg=TEXT_DIM, bg=BG3, activebackground=BORDER,
                  activeforeground=TEXT, relief="flat",
                  padx=20, pady=8, cursor="hand2",
                  command=self._skip).pack(side="left", padx=8)

        tk.Button(bf, text="  Connect AI  ", font=("Helvetica", 10, "bold"),
                  fg=BG, bg=ACCENT, activebackground=ACCENT2,
                  activeforeground=BG, relief="flat",
                  padx=20, pady=8, cursor="hand2",
                  command=self._connect).pack(side="left", padx=8)

        # Author footer
        tk.Label(self, text=f"Built by {APP_AUTHOR}",
                 font=("Helvetica", 8), fg=TEXT_MUTE, bg=BG).pack(pady=(0, 10))

    def _connect(self):
        key = self.key_var.get().strip()
        if not key:
            self.status_lbl.config(text="⚠  Enter your API key first", fg=ORANGE)
            return
        provider = self.provider_var.get()
        self.status_lbl.config(text="Testing connection...", fg=TEXT_DIM)
        self.update()

        from ai import AIClient
        client = AIClient(provider, key)
        ok, msg = client.test_connection()
        if ok:
            self.status_lbl.config(text=f"✓  {msg}", fg=GREEN)
            cfg = load_config()
            cfg["provider"] = provider
            cfg["api_key"] = key
            save_config(cfg)
            self.after(800, lambda: self.on_complete(provider, key))
            self.after(850, self.destroy)
        else:
            self.status_lbl.config(text=f"✗  {msg}", fg=RED)

    def _skip(self):
        self.on_complete(None, None)
        self.destroy()


# ─── Port Explanation Card ────────────────────────────────────────────────────

class PortExplainPanel(tk.Frame):
    def __init__(self, parent, port_info, **kw):
        super().__init__(parent, bg=BG3, **kw)
        self.port_info = port_info
        self._build()

    def _build(self):
        expl = self.port_info.ai_explanation
        if not expl:
            from ai import get_fallback_explanation
            expl = get_fallback_explanation(self.port_info.service)

        if "error" in expl:
            tk.Label(self, text=f"⚠  AI unavailable: {expl['error']}",
                     font=("Helvetica", 9, "italic"), fg=ORANGE,
                     bg=BG3, wraplength=520, justify="left").pack(padx=14, pady=8, anchor="w")
            return

        sections = [
            ("what_is_it",     "🔍  WHAT IS IT",    TEXT_DIM),
            ("why_it_matters", "⚡  WHY IT MATTERS", YELLOW),
            ("real_risk",      "💀  REAL RISK",      RED),
            ("how_to_fix",     "🛡  HOW TO FIX",     GREEN),
        ]

        for key, label, color in sections:
            val = expl.get(key)
            if not val:
                continue
            row = tk.Frame(self, bg=BG3)
            row.pack(fill="x", padx=14, pady=3)
            tk.Label(row, text=label, font=("Courier", 8, "bold"),
                     fg=color, bg=BG3, width=18, anchor="nw").pack(side="left", anchor="n")
            tk.Label(row, text=val, font=("Helvetica", 9),
                     fg=TEXT, bg=BG3, wraplength=420,
                     justify="left").pack(side="left", fill="x", expand=True)

        if self.port_info.cve_ids:
            cve_row = tk.Frame(self, bg=BG3)
            cve_row.pack(fill="x", padx=14, pady=(0, 6))
            tk.Label(cve_row, text="📋  CVEs FOUND", font=("Courier", 8, "bold"),
                     fg=RED, bg=BG3, width=18, anchor="w").pack(side="left")
            tk.Label(cve_row, text=" · ".join(self.port_info.cve_ids),
                     font=("Courier", 8), fg=RED, bg=BG3).pack(side="left")

        sr = expl.get("severity_reason", "")
        if sr:
            tk.Label(self, text=f"ℹ  {sr}", font=("Helvetica", 8, "italic"),
                     fg=TEXT_DIM, bg=BG3, wraplength=540,
                     justify="left").pack(padx=14, pady=(0, 8), anchor="w")


# ─── Device Card ─────────────────────────────────────────────────────────────

class DeviceCard(tk.Frame):
    def __init__(self, parent, device, mode_var, **kw):
        super().__init__(parent, bg=BG2, **kw)
        self.device = device
        self.mode_var = mode_var
        self._port_states = {}
        self._collapsed = False
        self._build()

    def _build(self):
        d = self.device
        risk_color = RISK_COLORS.get(d.risk_label, TEXT_DIM)
        emoji = RISK_EMOJI.get(d.risk_label, "❓")

        # Left accent bar
        tk.Frame(self, bg=risk_color, width=5).pack(side="left", fill="y")

        self._main = tk.Frame(self, bg=BG2)
        self._main.pack(side="left", fill="both", expand=True, padx=14, pady=10)

        # ── Header row ──────────────────────────────────────────────────────
        hdr = tk.Frame(self._main, bg=BG2)
        hdr.pack(fill="x")

        # Collapse toggle
        self._toggle_lbl = tk.Label(hdr, text="▼", font=("Courier", 10),
                                    fg=TEXT_DIM, bg=BG2, cursor="hand2")
        self._toggle_lbl.pack(side="left", padx=(0, 6))
        self._toggle_lbl.bind("<Button-1>", self._toggle_collapse)

        # IP + hostname
        tk.Label(hdr, text=d.ip, font=("Courier", 14, "bold"),
                 fg=ACCENT, bg=BG2).pack(side="left")
        tk.Label(hdr, text=f"  {d.hostname}", font=("Courier", 10),
                 fg=TEXT_DIM, bg=BG2).pack(side="left")

        # Risk badge
        tk.Label(hdr, text=f" {emoji} {d.risk_label} ",
                 font=("Courier", 9, "bold"),
                 fg=BG, bg=risk_color, padx=4).pack(side="right")

        # Score bar
        score_frame = tk.Frame(hdr, bg=BG2)
        score_frame.pack(side="right", padx=12)
        tk.Label(score_frame, text=f"Risk: {d.risk_score}/100",
                 font=("Helvetica", 8), fg=TEXT_DIM, bg=BG2).pack(anchor="e")
        bar_bg = tk.Frame(score_frame, bg=BG4, height=4, width=100)
        bar_bg.pack(anchor="e")
        bar_bg.pack_propagate(False)
        fill_w = max(2, int(d.risk_score))
        bar_fill = tk.Frame(bar_bg, bg=risk_color, height=4, width=fill_w)
        bar_fill.place(x=0, y=0)

        # ── Meta row ─────────────────────────────────────────────────────────
        meta = tk.Frame(self._main, bg=BG2)
        meta.pack(fill="x", pady=(3, 4))
        for label, val in [("Type", d.device_type), ("Vendor", d.vendor), ("MAC", d.mac)]:
            tk.Label(meta, text=f"{label}: ", font=("Helvetica", 8),
                     fg=TEXT_MUTE, bg=BG2).pack(side="left")
            tk.Label(meta, text=val + "   ", font=("Helvetica", 8, "bold"),
                     fg=TEXT_DIM, bg=BG2).pack(side="left")

        # ── Collapsible body ─────────────────────────────────────────────────
        self._body = tk.Frame(self._main, bg=BG2)
        self._body.pack(fill="x")

        # AI Summary panel
        self._summary_frame = tk.Frame(self._body, bg=BG4)
        self._summary_frame.pack(fill="x", pady=(0, 6))
        self._summary_lbl = tk.Label(
            self._summary_frame,
            text="⟳  AI summary loading..." if self.device.ai_summary else "⟳  Connect AI for explanations",
            font=("Helvetica", 9, "italic"),
            fg=TEXT_DIM, bg=BG4, wraplength=580, justify="left"
        )
        self._summary_lbl.pack(padx=10, pady=6, anchor="w")

        if self.device.ai_summary:
            self._render_summary(self.device.ai_summary)

        # ── Ports ────────────────────────────────────────────────────────────
        if d.open_ports:
            ports_hdr = tk.Frame(self._body, bg=BG2)
            ports_hdr.pack(fill="x", pady=(2, 4))
            tk.Label(ports_hdr,
                     text=f"OPEN PORTS  ({len(d.open_ports)} found)",
                     font=("Courier", 8, "bold"), fg=TEXT_DIM, bg=BG2).pack(side="left")

            for port_info in d.open_ports:
                self._add_port_row(port_info)
        else:
            tk.Label(self._body, text="✅  No open ports detected — this device looks clean",
                     font=("Helvetica", 9), fg=GREEN, bg=BG2).pack(anchor="w", pady=4)

        # Bottom separator
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", side="bottom")

        self._apply_mode()

    def _add_port_row(self, port_info):
        risk_color = RISK_COLORS.get(port_info.risk_level, TEXT_DIM)

        port_container = tk.Frame(self._body, bg=BG2)
        port_container.pack(fill="x", pady=1)

        row = tk.Frame(port_container, bg=BG2)
        row.pack(fill="x")

        # Port number
        tk.Label(row, text=f":{port_info.port}",
                 font=("Courier", 10, "bold"),
                 fg=risk_color, bg=BG2, width=8, anchor="w").pack(side="left")

        # Service name
        tk.Label(row, text=port_info.service,
                 font=("Helvetica", 9, "bold"),
                 fg=TEXT, bg=BG2, width=14, anchor="w").pack(side="left")

        # Risk badge
        tk.Label(row, text=f"[{port_info.risk_level}]",
                 font=("Courier", 8, "bold"),
                 fg=risk_color, bg=BG2, width=11, anchor="w").pack(side="left")

        # Version
        if port_info.version:
            tk.Label(row, text=port_info.version[:48],
                     font=("Courier", 8), fg=TEXT_DIM, bg=BG2).pack(side="left")

        # CVE count
        if port_info.cve_ids:
            tk.Label(row, text=f"  ⚠ {len(port_info.cve_ids)} CVE(s)",
                     font=("Helvetica", 8, "bold"), fg=RED, bg=BG2).pack(side="left")

        # Explain toggle
        toggle = tk.Label(row, text="▸ Learn more",
                          font=("Helvetica", 8), fg=TEAL, bg=BG2, cursor="hand2")
        toggle.pack(side="right", padx=6)
        Tooltip(toggle, "Click to see what this means and how to fix it")

        # Explanation panel (hidden by default)
        explain_panel_wrapper = tk.Frame(port_container, bg=BG3)
        self._port_states[port_info.port] = {
            "wrapper": explain_panel_wrapper,
            "toggle": toggle,
            "visible": False,
            "loaded": False,
            "port_info": port_info,
        }

        def on_toggle(evt, p=port_info.port):
            state = self._port_states[p]
            if state["visible"]:
                state["wrapper"].pack_forget()
                state["toggle"].config(text="▸ Learn more")
                state["visible"] = False
            else:
                state["wrapper"].pack(fill="x", pady=2)
                state["toggle"].config(text="▾ Close")
                state["visible"] = True
                if not state["loaded"]:
                    panel = PortExplainPanel(state["wrapper"], state["port_info"])
                    panel.pack(fill="x", pady=(4, 4))
                    state["loaded"] = True

        toggle.bind("<Button-1>", on_toggle)

    def _render_summary(self, summary: dict):
        for w in self._summary_frame.winfo_children():
            w.destroy()

        verdict = summary.get("overall_verdict", "")
        headline = summary.get("headline", "")
        priority = summary.get("top_priority", "")
        color = RISK_COLORS.get(verdict, TEXT_DIM)
        emoji = RISK_EMOJI.get(verdict, "")

        if headline:
            tk.Label(self._summary_frame,
                     text=f"{emoji}  {headline}",
                     font=("Helvetica", 9, "bold"),
                     fg=color, bg=BG4, wraplength=560,
                     justify="left").pack(padx=10, pady=(6, 2), anchor="w")

        summary_text = summary.get("summary", "")
        if summary_text:
            tk.Label(self._summary_frame, text=summary_text,
                     font=("Helvetica", 9), fg=TEXT, bg=BG4,
                     wraplength=560, justify="left").pack(padx=10, pady=2, anchor="w")

        if priority:
            pf = tk.Frame(self._summary_frame, bg=BG4)
            pf.pack(fill="x", padx=10, pady=(2, 6))
            tk.Label(pf, text="Priority: ", font=("Helvetica", 8, "bold"),
                     fg=YELLOW, bg=BG4).pack(side="left")
            tk.Label(pf, text=priority, font=("Helvetica", 8),
                     fg=TEXT, bg=BG4, wraplength=480, justify="left").pack(side="left")

    def update_ai_summary(self, summary: dict):
        self.device.ai_summary = summary
        self._render_summary(summary)

    def update_port_explanation(self, port: int, explanation: dict):
        state = self._port_states.get(port)
        if not state:
            return
        state["port_info"].ai_explanation = explanation
        state["loaded"] = False
        if state["visible"]:
            for w in state["wrapper"].winfo_children():
                w.destroy()
            panel = PortExplainPanel(state["wrapper"], state["port_info"])
            panel.pack(fill="x", pady=4)
            state["loaded"] = True

    def _toggle_collapse(self, evt=None):
        self._collapsed = not self._collapsed
        if self._collapsed:
            self._body.pack_forget()
            self._toggle_lbl.config(text="▶")
        else:
            self._body.pack(fill="x")
            self._toggle_lbl.config(text="▼")

    def _apply_mode(self):
        mode = self.mode_var.get() if self.mode_var else "learning"
        if mode == "learning":
            self._summary_frame.pack(fill="x", pady=(0, 6))
        else:
            self._summary_frame.pack_forget()


# ─── Main Application ─────────────────────────────────────────────────────────

class NetRaptorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} — Network Security Scanner  //  {APP_AUTHOR}")
        self.configure(bg=BG)

        cfg = load_config()
        self.provider  = cfg.get("provider")
        self.api_key   = cfg.get("api_key")
        self.ai_client = None
        self.mode_var  = tk.StringVar(value="learning")
        self._cards    = {}
        self._scanning = False
        self._scan_stop = False
        self._scan_devices = []

        # Window size: 70% of screen, minimum 1000x700
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w = max(1000, int(sw * 0.72))
        h = max(700,  int(sh * 0.78))
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(1000, 680)

        self._build_ui()
        self._apply_ttk_style()

        if not self.api_key:
            self.after(300, self._show_api_setup)
        else:
            self._init_ai()

    # ── TTK Style ──────────────────────────────────────────────────────────

    def _apply_ttk_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TCombobox",
                         fieldbackground=BG3, background=BG3,
                         foreground=TEXT, bordercolor=BORDER,
                         selectbackground=BG4, selectforeground=TEXT)
        style.configure("Horizontal.TProgressbar",
                         background=ACCENT, troughcolor=BG3, bordercolor=BG3)
        style.configure("Vertical.TScrollbar",
                         background=BG3, troughcolor=BG2,
                         bordercolor=BG2, arrowcolor=TEXT_DIM)

    # ── UI Construction ────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_topbar()
        self._build_toolbar()
        self._build_main()
        self._build_statusbar()

    def _build_topbar(self):
        bar = tk.Frame(self, bg=BG2, height=56)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        # Left: brand
        left = tk.Frame(bar, bg=BG2)
        left.pack(side="left", padx=20, pady=8)
        tk.Label(left, text=f"◈ {APP_NAME}", font=("Courier", 20, "bold"),
                 fg=ACCENT, bg=BG2).pack(side="left")
        tk.Label(left, text="  //  Network Discovery & Security Assessment",
                 font=("Helvetica", 9), fg=TEXT_DIM, bg=BG2).pack(side="left")

        # Right: controls
        right = tk.Frame(bar, bg=BG2)
        right.pack(side="right", padx=20)

        # AI status
        self.ai_status_lbl = tk.Label(right, text="⬤ AI: OFF",
                                       font=("Courier", 8), fg=TEXT_DIM, bg=BG2)
        self.ai_status_lbl.pack(side="left", padx=(0, 16))

        # Mode toggle
        tk.Label(right, text="Mode:", font=("Helvetica", 8),
                 fg=TEXT_DIM, bg=BG2).pack(side="left")
        for label, val in [("Learning", "learning"), ("Analyst", "analyst")]:
            rb = tk.Radiobutton(right, text=label, variable=self.mode_var, value=val,
                                font=("Helvetica", 8), fg=TEXT, bg=BG2,
                                selectcolor=BG3, activebackground=BG2,
                                command=self._on_mode_change)
            rb.pack(side="left", padx=2)

        # Settings
        settings_lbl = tk.Label(right, text="  ⚙ AI Settings",
                                  font=("Helvetica", 8), fg=ACCENT, bg=BG2,
                                  cursor="hand2")
        settings_lbl.pack(side="left", padx=(10, 0))
        settings_lbl.bind("<Button-1>", lambda e: self._show_api_setup())

        # Author credit
        tk.Label(right, text=f"  //  {APP_AUTHOR}",
                 font=("Helvetica", 7, "italic"), fg=TEXT_MUTE, bg=BG2).pack(side="left")

        tk.Frame(self, bg=ACCENT, height=2).pack(fill="x")

    def _build_toolbar(self):
        bar = tk.Frame(self, bg=BG, pady=8)
        bar.pack(fill="x", padx=16)

        # Demo mode button
        demo_btn = tk.Button(bar, text="🎓  Demo Mode",
                              font=("Helvetica", 9, "bold"),
                              fg=PURPLE, bg=BG3,
                              activebackground=BG4, activeforeground=PURPLE,
                              relief="flat", padx=12, pady=5, cursor="hand2",
                              command=self._run_demo)
        demo_btn.pack(side="left", padx=(0, 12))
        Tooltip(demo_btn, "Load example results — no network needed. Great for learning!")

        tk.Frame(bar, bg=BORDER, width=1).pack(side="left", fill="y", pady=2, padx=4)

        # Target entry
        tk.Label(bar, text="Target:", font=("Helvetica", 9),
                 fg=TEXT_DIM, bg=BG).pack(side="left", padx=(8, 4))
        self.target_var = tk.StringVar(value="192.168.1.0/24")
        tk.Entry(bar, textvariable=self.target_var,
                 font=("Courier", 10), bg=BG3, fg=TEXT,
                 insertbackground=ACCENT, relief="flat",
                 highlightthickness=1, highlightbackground=BORDER,
                 highlightcolor=ACCENT, width=20).pack(side="left", ipady=4, padx=(0, 10))

        # Scan button
        self.scan_btn = tk.Button(bar, text="▶  Scan Network",
                                   font=("Helvetica", 9, "bold"),
                                   fg=BG, bg=GREEN,
                                   activebackground="#56d364",
                                   relief="flat", padx=14, pady=5,
                                   cursor="hand2", command=self._start_scan)
        self.scan_btn.pack(side="left", padx=(0, 6))

        self.stop_btn = tk.Button(bar, text="■  Stop",
                                   font=("Helvetica", 9),
                                   fg=TEXT_DIM, bg=BG3,
                                   activebackground=BORDER,
                                   relief="flat", padx=10, pady=5,
                                   cursor="hand2", command=self._stop_scan,
                                   state="disabled")
        self.stop_btn.pack(side="left")

        # Progress
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(bar, variable=self.progress_var,
                                         maximum=100, length=180,
                                         mode="determinate")
        self.progress.pack(side="left", padx=14)
        self.progress_lbl = tk.Label(bar, text="", font=("Courier", 8),
                                      fg=TEXT_DIM, bg=BG)
        self.progress_lbl.pack(side="left")

        # Export
        tk.Button(bar, text="⬇  Export JSON",
                  font=("Helvetica", 8), fg=TEXT_DIM, bg=BG3,
                  relief="flat", padx=10, pady=4, cursor="hand2",
                  command=self._export).pack(side="right")

        # Clear
        tk.Button(bar, text="✕  Clear",
                  font=("Helvetica", 8), fg=TEXT_DIM, bg=BG3,
                  relief="flat", padx=10, pady=4, cursor="hand2",
                  command=self._clear).pack(side="right", padx=4)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

    def _build_main(self):
        paned = tk.PanedWindow(self, orient="horizontal",
                               bg=BORDER, sashwidth=2, sashrelief="flat")
        paned.pack(fill="both", expand=True)

        # ── Results panel ──────────────────────────────────────────────────
        rc = tk.Frame(paned, bg=BG)
        paned.add(rc, minsize=620)

        # Results header
        rh = tk.Frame(rc, bg=BG, pady=6)
        rh.pack(fill="x", padx=14)
        self.results_header = tk.Label(rh,
            text="Click  🎓 Demo Mode  to explore example results, or enter a target and scan.",
            font=("Helvetica", 9), fg=TEXT_DIM, bg=BG)
        self.results_header.pack(side="left")

        # Scrollable results area
        canvas = tk.Canvas(rc, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(rc, orient="vertical", command=canvas.yview)
        self.results_frame = tk.Frame(canvas, bg=BG)
        self.results_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.results_frame, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        def _scroll(e):
            canvas.yview_scroll(-1 * (e.delta // 120), "units")
        canvas.bind_all("<MouseWheel>", _scroll)
        canvas.bind_all("<Button-4>",
            lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>",
            lambda e: canvas.yview_scroll(1, "units"))
        self._canvas = canvas

        # ── Log panel ──────────────────────────────────────────────────────
        lc = tk.Frame(paned, bg=BG2)
        paned.add(lc, minsize=240)

        # Log header
        lh = tk.Frame(lc, bg=BG2, pady=6)
        lh.pack(fill="x", padx=10)
        tk.Label(lh, text="SCAN LOG", font=("Courier", 8, "bold"),
                 fg=TEXT_DIM, bg=BG2).pack(side="left")

        # Legend
        lg = tk.Frame(lc, bg=BG2)
        lg.pack(fill="x", padx=10, pady=(0, 4))
        for label, color in [("CRIT", CRITICAL), ("HIGH", RED),
                               ("MED", ORANGE), ("LOW", YELLOW), ("OK", GREEN)]:
            tk.Label(lg, text=f"■{label} ", font=("Courier", 7),
                     fg=color, bg=BG2).pack(side="left")

        tk.Frame(lc, bg=BORDER, height=1).pack(fill="x")

        self.log_text = scrolledtext.ScrolledText(
            lc, bg=BG2, fg=TEXT_DIM,
            font=("Courier", 8), relief="flat",
            state="disabled", wrap="word",
            insertbackground=ACCENT
        )
        self.log_text.pack(fill="both", expand=True, padx=4, pady=4)

        for tag, color in [
            ("info",     TEXT_DIM),
            ("good",     GREEN),
            ("warn",     ORANGE),
            ("critical", RED),
            ("accent",   ACCENT),
            ("purple",   PURPLE),
            ("teal",     TEAL),
        ]:
            self.log_text.tag_config(tag, foreground=color)

        # Glossary / cheat sheet at bottom of log
        self._build_glossary(lc)

    def _build_glossary(self, parent):
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=(4, 0))
        gloss_hdr = tk.Frame(parent, bg=BG2)
        gloss_hdr.pack(fill="x", padx=10, pady=(4, 2))
        tk.Label(gloss_hdr, text="QUICK GLOSSARY", font=("Courier", 7, "bold"),
                 fg=TEXT_DIM, bg=BG2).pack(side="left")

        glossary = [
            ("Port",    "A numbered door on a device — services listen here"),
            ("CVE",     "A known, named vulnerability with a public ID"),
            ("SSH",     "Secure remote terminal access — encrypted"),
            ("SMB",     "Windows file sharing — dangerous if unpatched"),
            ("RDP",     "Remote desktop for Windows — high attack target"),
            ("Telnet",  "Old remote access — sends passwords in plain text"),
            ("ARP",     "Protocol that maps IPs to physical MAC addresses"),
            ("Banner",  "Service version info sent when you connect"),
        ]

        for term, definition in glossary:
            row = tk.Frame(parent, bg=BG2)
            row.pack(fill="x", padx=10, pady=1)
            tk.Label(row, text=f"{term}:", font=("Courier", 7, "bold"),
                     fg=TEAL, bg=BG2, width=9, anchor="w").pack(side="left")
            tk.Label(row, text=definition, font=("Helvetica", 7),
                     fg=TEXT_DIM, bg=BG2, wraplength=160,
                     justify="left").pack(side="left")

    def _build_statusbar(self):
        bar = tk.Frame(self, bg=BG3, height=22)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        self.status_lbl = tk.Label(bar, text=f"Ready  //  {APP_AUTHOR}  //  {APP_TAGLINE}",
                                    font=("Helvetica", 7), fg=TEXT_MUTE, bg=BG3)
        self.status_lbl.pack(side="left", padx=10)
        tk.Label(bar, text=f"v{APP_VERSION}",
                 font=("Courier", 7), fg=TEXT_MUTE, bg=BG3).pack(side="right", padx=10)

    # ── AI ──────────────────────────────────────────────────────────────────

    def _show_api_setup(self):
        APISetupDialog(self, self._on_api_configured)

    def _on_api_configured(self, provider, api_key):
        self.provider = provider
        self.api_key  = api_key
        self._init_ai()

    def _init_ai(self):
        if self.api_key:
            from ai import AIClient
            self.ai_client = AIClient(self.provider, self.api_key)
            short = self.provider.split(" ")[0]
            self.ai_status_lbl.config(text=f"⬤ AI: {short}", fg=GREEN)
            self._log(f"✓ AI connected via {self.provider}\n", "good")
        else:
            self.ai_client = None
            self.ai_status_lbl.config(text="⬤ AI: OFF", fg=TEXT_DIM)

    # ── Demo Mode ──────────────────────────────────────────────────────────

    def _run_demo(self):
        self._clear()
        self._log(f"◈ {APP_NAME} — Demo Mode\n", "accent")
        self._log(f"Built by {APP_AUTHOR}\n", "purple")
        self._log("─" * 38 + "\n", "info")
        self._log("Loading example network results...\n", "info")
        self._log("These are realistic findings you'd\n", "info")
        self._log("see on a typical home network.\n\n", "info")

        devices = make_demo_device_objects()
        self._scan_devices = devices
        self.results_header.config(
            text=f"Demo Network — {len(devices)} devices  //  Click '▸ Learn more' on any port to understand it")
        self._status("Demo mode — exploring example results")

        def load_with_delay():
            for i, d in enumerate(devices):
                time.sleep(0.25)
                self.after(0, self._add_card, d)
                tag = "critical" if d.risk_label in ("CRITICAL", "HIGH", "DANGEROUS") else \
                      "warn" if d.risk_label in ("MEDIUM", "CONCERNING") else "good"
                self.after(0, self._log,
                           f"  {d.ip}  {d.hostname}\n"
                           f"  └─ {d.risk_label} [{d.risk_score}/100]  "
                           f"{len(d.open_ports)} port(s)\n\n", tag)

            self.after(len(devices) * 260, lambda: self._log(
                "✓ Demo loaded — click 'Learn more' on\n"
                "  any port to see what it means.\n", "teal"))
            self.after(len(devices) * 260, lambda: self.progress_var.set(100))

        threading.Thread(target=load_with_delay, daemon=True).start()
        self.progress_var.set(0)

        def animate_progress():
            v = self.progress_var.get()
            if v < 95:
                self.progress_var.set(v + 3)
                self.after(60, animate_progress)
        self.after(60, animate_progress)

    # ── Scan ───────────────────────────────────────────────────────────────

    def _start_scan(self):
        if self._scanning:
            return
        target = self.target_var.get().strip()
        if not target:
            messagebox.showwarning(APP_NAME, "Enter a network range — e.g. 192.168.1.0/24")
            return
        self._clear()
        self._scanning = True
        self._scan_stop = False
        self.scan_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.progress_var.set(0)
        self.results_header.config(text="Scanning...")
        self._log(f"◈ {APP_NAME} — Live Scan\n", "accent")
        self._log(f"Built by {APP_AUTHOR}\n", "purple")
        self._log("─" * 38 + "\n", "info")
        self._log(f"Target: {target}\n\n", "info")
        self._status(f"Scanning {target}...")

        def run():
            try:
                from engine import scan_network
                def prog(stage, cur, tot):
                    if self._scan_stop:
                        raise InterruptedError("Stopped")
                    pct = (cur / max(tot, 1)) * 100
                    self.after(0, self.progress_var.set, pct)
                    self.after(0, self.progress_lbl.config,
                               {"text": f"{stage} {cur}/{tot}"})
                devices = scan_network(target, progress_cb=prog)
                self._scan_devices = devices
                self.after(0, self._on_scan_done, devices)
            except InterruptedError:
                self.after(0, self._on_scan_stopped)
            except Exception as e:
                self.after(0, self._on_scan_error, str(e))

        threading.Thread(target=run, daemon=True).start()

    def _stop_scan(self):
        self._scan_stop = True
        self._scanning = False
        self.scan_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

    def _on_scan_done(self, devices):
        self._scanning = False
        self.scan_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.progress_var.set(100)
        count = len(devices)
        crit  = sum(1 for d in devices if d.risk_label in ("CRITICAL", "HIGH", "DANGEROUS"))
        self.results_header.config(
            text=f"Scan complete — {count} device(s), {crit} high-risk  //  Click '▸ Learn more' on any port")
        self._log(f"✓ Done — {count} device(s) found, {crit} high-risk\n\n", "good")
        for d in devices:
            self._add_card(d)
            tag = "critical" if d.risk_label in ("CRITICAL", "HIGH", "DANGEROUS") else \
                  "warn" if d.risk_label in ("MEDIUM",) else "good"
            self._log(f"  {d.ip}  {d.hostname}\n"
                      f"  └─ {d.risk_label}  {len(d.open_ports)} port(s)\n\n", tag)
        self._status(f"Scan complete — {count} device(s)")
        if self.ai_client and devices:
            self._log("⟳ Generating AI explanations...\n", "teal")
            def on_update(ip, port, expl):
                self.after(0, self._handle_ai, ip, port, expl)
            self.ai_client.explain_all_async(devices, on_update)

    def _on_scan_stopped(self):
        self._scanning = False
        self.scan_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self._log("■ Scan stopped\n", "warn")
        self.results_header.config(text="Scan stopped")
        self._status("Stopped")

    def _on_scan_error(self, err):
        self._scanning = False
        self.scan_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self._log(f"✗ Error: {err}\n", "critical")
        self.results_header.config(text=f"Error: {err}")
        self._status("Error")
        messagebox.showerror(APP_NAME, f"Scan error:\n{err}")

    def _add_card(self, device):
        card = DeviceCard(self.results_frame, device, self.mode_var)
        card.pack(fill="x", padx=10, pady=4)
        self._cards[device.ip] = card
        self._canvas.yview_moveto(1.0)

    def _handle_ai(self, ip, port, expl):
        card = self._cards.get(ip)
        if not card:
            return
        if port is None:
            card.update_ai_summary(expl)
        else:
            card.update_port_explanation(port, expl)

    # ── Mode ──────────────────────────────────────────────────────────────

    def _on_mode_change(self):
        for card in self._cards.values():
            card._apply_mode()

    # ── Utilities ─────────────────────────────────────────────────────────

    def _clear(self):
        for w in self.results_frame.winfo_children():
            w.destroy()
        self._cards.clear()
        self._scan_devices = []
        self._log_clear()
        self.progress_var.set(0)
        self.progress_lbl.config(text="")
        self.results_header.config(
            text="Click  🎓 Demo Mode  to explore example results, or enter a target and scan.")

    def _export(self):
        if not self._scan_devices:
            messagebox.showinfo(APP_NAME, "No data to export yet.")
            return
        from tkinter.filedialog import asksaveasfilename
        path = asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="netraptor_results.json"
        )
        if path:
            try:
                data = [d.to_dict() for d in self._scan_devices]
                Path(path).write_text(json.dumps(data, indent=2))
                self._log(f"✓ Exported to {path}\n", "good")
                messagebox.showinfo(APP_NAME, f"Exported to:\n{path}")
            except Exception as e:
                messagebox.showerror(APP_NAME, f"Export failed: {e}")

    def _log(self, msg: str, tag: str = "info"):
        self.log_text.config(state="normal")
        self.log_text.insert("end", msg, tag)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _log_clear(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")

    def _status(self, msg: str):
        self.status_lbl.config(
            text=f"{msg}  //  {APP_AUTHOR}  //  {APP_TAGLINE}")


# ─── Entry Point ───────────────────────────────────────────────────────────────

def main():
    app = NetRaptorApp()
    app.mainloop()

if __name__ == "__main__":
    main()
