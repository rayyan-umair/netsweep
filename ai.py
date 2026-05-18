"""
NetSweep - Network Discovery & Security Assessment
ai.py - AI Explanation Layer

Author  : Rayyan Umair
Date    : 4 May, 2026
Purpose : Handles all AI provider integrations (Anthropic, OpenAI, Google, Groq).
          Generates four-layer security explanations for every scan finding.
          Also provides hardcoded fallback explanations when no API key is set.
Contact : rayyanxumair@gmail.com
GitHub  : github.com/rayyan-umair

"Technology evolves quickly. Responsibility does not."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  This file is part of NetSweep, a network security scanner built for learners.
  Written and maintained by Rayyan Umair. All logic, structure, and design
  decisions in this file reflect the author's original work.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import threading
import requests
from dataclasses import dataclass
from typing import Optional, Callable

# ─── Provider Config ───────────────────────────────────────────────────────────

PROVIDERS = {
    "Anthropic (Claude)": {
        "key_prefix": "sk-ant",
        "model": "claude-sonnet-4-20250514",
    },
    "OpenAI (GPT-4o)": {
        "key_prefix": "sk-",
        "model": "gpt-4o",
    },
    "Google (Gemini)": {
        "key_prefix": "AIza",
        "model": "gemini-2.0-flash-lite",
    },
    "Groq (Llama 3)": {
    "key_prefix": "gsk_",
    "model": "llama-3.1-8b-instant",
    },
}

PROVIDER_NAMES = list(PROVIDERS.keys())

# ─── Prompt Templates ─────────────────────────────────────────────────────────

PORT_EXPLANATION_PROMPT = """You are a cybersecurity educator explaining a network finding to a beginner or student.

Device found: {ip} ({hostname}) - classified as {device_type}
Finding: Port {port} open - Service: {service} - Version: {version}
Risk level: {risk_level}
CVEs found: {cves}
Network context: {context}

Respond ONLY with a JSON object (no markdown, no preamble) with exactly these keys:
{{
  "what_is_it": "Plain English: what is this service and why does it exist? (2-3 sentences)",
  "why_it_matters": "The security implication - what an attacker could do with this. (2-3 sentences)",
  "real_risk": "Concrete worst-case scenario specific to this finding. Be specific, not vague. (2-3 sentences)",
  "how_to_fix": "Exact actionable steps to remediate this - not vague advice, real instructions. (3-5 sentences)",
  "severity_reason": "One sentence explaining why this is rated {risk_level}"
}}"""

DEVICE_SUMMARY_PROMPT = """You are a cybersecurity educator summarizing a full device scan for a beginner.

Device: {ip} ({hostname})
Type: {device_type}
Vendor: {vendor}
Risk Score: {risk_score}/100 - {risk_label}
Open ports: {ports_summary}
CVEs found: {cve_count} total

Respond ONLY with a JSON object (no markdown) with exactly these keys:
{{
  "headline": "One punchy sentence summarizing this device's security posture",
  "summary": "2-3 sentences describing the overall risk picture for this device in plain English",
  "top_priority": "The single most important thing to fix or check on this device",
  "overall_verdict": "SAFE / MONITOR / CONCERNING / DANGEROUS"
}}"""


# ─── API Callers ───────────────────────────────────────────────────────────────

def _call_groq(api_key: str, model: str, prompt: str) -> str:
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": 600,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def _call_anthropic(api_key: str, model: str, prompt: str) -> str:
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": 600,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["content"][0]["text"]

def _call_openai(api_key: str, model: str, prompt: str) -> str:
    r = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": 600,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def _call_gemini(api_key: str, model: str, prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    r = requests.post(
        url,
        params={"key": api_key},
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


# ─── AI Client ────────────────────────────────────────────────────────────────

class AIClient:
    def __init__(self, provider: str, api_key: str):
        self.provider = provider
        self.api_key = api_key
        self.available = bool(api_key)

    def _call(self, prompt: str) -> str:
        if not self.available:
            raise RuntimeError("No API key configured")
        cfg = PROVIDERS.get(self.provider)
        if not cfg:
            raise ValueError(f"Unknown provider: {self.provider}")
        if self.provider == "Anthropic (Claude)":
            return _call_anthropic(self.api_key, cfg["model"], prompt)
        elif self.provider == "OpenAI (GPT-4o)":
            return _call_openai(self.api_key, cfg["model"], prompt)
        elif self.provider == "Google (Gemini)":
            return _call_gemini(self.api_key, cfg["model"], prompt)
        elif self.provider == "Groq (Llama 3)":
            return _call_groq(self.api_key, cfg["model"], prompt)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def _parse_json(self, text: str) -> dict:
        text = text.strip()
        if text.startswith("```"):
            parts = text.split("```")
            if len(parts) >= 2:
                text = parts[1]
                if text.startswith("json"):
                    text = text[4:]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            import re
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except Exception:
                    pass
            return {}

    def explain_port(self, device, port_info, context: str = "") -> dict:
        prompt = PORT_EXPLANATION_PROMPT.format(
            ip=device.ip,
            hostname=device.hostname,
            device_type=device.device_type,
            port=port_info.port,
            service=port_info.service,
            version=port_info.version or "unknown",
            risk_level=port_info.risk_level,
            cves=", ".join(port_info.cve_ids) if port_info.cve_ids else "None found",
            context=context or "Home or office network",
        )
        raw = self._call(prompt)
        return self._parse_json(raw)

    def summarize_device(self, device) -> dict:
        ports_summary = ", ".join(
            f"{p.port}/{p.service}[{p.risk_level}]"
            for p in device.open_ports
        ) or "No open ports found"
        cve_count = sum(len(p.cve_ids) for p in device.open_ports)
        prompt = DEVICE_SUMMARY_PROMPT.format(
            ip=device.ip,
            hostname=device.hostname,
            device_type=device.device_type,
            vendor=device.vendor,
            risk_score=device.risk_score,
            risk_label=device.risk_label,
            ports_summary=ports_summary,
            cve_count=cve_count,
        )
        raw = self._call(prompt)
        return self._parse_json(raw)

    def explain_all_async(self, devices: list, on_update: Callable, context: str = ""):
        def _worker():
            for device in devices:
                try:
                    summary = self.summarize_device(device)
                    device.ai_summary = summary
                    on_update(device.ip, None, summary)
                except Exception as e:
                    on_update(device.ip, None, {"error": str(e)})
                for port_info in device.open_ports:
                    try:
                        explanation = self.explain_port(device, port_info, context)
                        port_info.ai_explanation = explanation
                        on_update(device.ip, port_info.port, explanation)
                    except Exception as e:
                        on_update(device.ip, port_info.port, {"error": str(e)})
        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        return t

    def test_connection(self) -> tuple:
        try:
            result = self._call("Reply with the single word: connected")
            if result:
                return True, f"Connected via {self.provider}"
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                return False, "Invalid API key - check and try again"
            return False, f"API error {e.response.status_code}: {e.response.text[:100]}"
        except Exception as e:
            return False, str(e)
        return False, "No response received"


# ─── Fallback Explanations ────────────────────────────────────────────────────

FALLBACK_EXPLANATIONS = {
    "Telnet": {
        "what_is_it": "Telnet is a decades-old remote access protocol that lets someone control a device over the network.",
        "why_it_matters": "All data sent over Telnet - including passwords - travels in plain text. Anyone on the same network can intercept and read it instantly.",
        "real_risk": "An attacker on your network could capture the login credentials for this device and take full control of it.",
        "how_to_fix": "Disable Telnet immediately. Enable SSH instead - it does the same job but encrypts all traffic. Find this setting in the device's admin panel under Services or Remote Access.",
        "severity_reason": "CRITICAL because credentials are fully exposed to anyone on the network.",
    },
    "SMB": {
        "what_is_it": "SMB (Server Message Block) is the Windows file and printer sharing protocol.",
        "why_it_matters": "SMB vulnerabilities have enabled some of history's worst ransomware attacks - WannaCry and NotPetya both used SMB to spread across networks in minutes.",
        "real_risk": "An unpatched SMB service can allow an attacker to take full control of this machine and use it to spread ransomware to every device on your network.",
        "how_to_fix": "Ensure Windows is fully patched. Disable SMBv1 in Windows Features. Block port 445 at your firewall from external access. Run 'sc stop lanmanserver' if not needed.",
        "severity_reason": "CRITICAL due to history of catastrophic exploits targeting this exact service.",
    },
    "RDP": {
        "what_is_it": "RDP (Remote Desktop Protocol) gives full graphical control of a Windows machine over the network.",
        "why_it_matters": "RDP exposed to the internet is one of the most common entry points for ransomware gangs. Attackers scan for it constantly.",
        "real_risk": "A brute-forced or stolen RDP password gives an attacker a full desktop session - they can install ransomware, steal data, or use your machine as a pivot point.",
        "how_to_fix": "Never expose RDP directly to the internet. Use a VPN or RDP gateway. Enable Network Level Authentication (NLA). Enable account lockout after failed attempts.",
        "severity_reason": "CRITICAL because of constant automated scanning and active exploitation in the wild.",
    },
    "VNC": {
        "what_is_it": "VNC (Virtual Network Computing) provides remote graphical desktop access, similar to RDP but cross-platform.",
        "why_it_matters": "Many VNC installations are deployed without passwords or with weak ones, giving anyone who finds it full control of the desktop.",
        "real_risk": "An attacker could take full control of this machine - viewing the screen, moving the mouse, typing commands - without ever needing a password.",
        "how_to_fix": "Set a strong VNC password immediately. Restrict VNC access by IP address. Consider replacing with a VPN + SSH tunnel. Never expose VNC to the internet.",
        "severity_reason": "CRITICAL because authentication is frequently absent or weak on VNC installations.",
    },
    "FTP": {
        "what_is_it": "FTP (File Transfer Protocol) is used to transfer files between computers over a network.",
        "why_it_matters": "Like Telnet, FTP sends usernames and passwords in plain text - anyone sniffing network traffic can capture credentials instantly.",
        "real_risk": "Attackers can intercept FTP credentials and gain access to all files on the server, or use anonymous FTP to exfiltrate data without any credentials.",
        "how_to_fix": "Replace FTP with SFTP (SSH File Transfer Protocol) or FTPS (FTP over TLS). Disable anonymous FTP login. Restrict access by IP address in your FTP server config.",
        "severity_reason": "HIGH because credentials and data are transmitted unencrypted.",
    },
    "Redis": {
        "what_is_it": "Redis is an in-memory data store used for caching, session management, and real-time data.",
        "why_it_matters": "Redis was designed to run inside trusted networks - it has no authentication by default, so any connection is treated as trusted.",
        "real_risk": "An attacker can read all cached data (including session tokens), write arbitrary data, or use Redis's config commands to write files to the server and achieve code execution.",
        "how_to_fix": "Add a strong password via 'requirepass' in redis.conf. Bind Redis to 127.0.0.1 only. Never expose port 6379 to the internet. Upgrade to Redis 7+ which has ACL support.",
        "severity_reason": "CRITICAL because unauthenticated Redis instances lead directly to data breach and remote code execution.",
    },
}

def get_fallback_explanation(service: str) -> dict:
    for key, val in FALLBACK_EXPLANATIONS.items():
        if key.lower() in service.lower():
            return val
    return {
        "what_is_it": f"This port is running a service called {service}.",
        "why_it_matters": "Any open port is a potential entry point. This service should be reviewed to ensure it's necessary and properly secured.",
        "real_risk": "Without knowing the specific version and configuration, the exact risk is unclear - but unnecessary open ports increase your attack surface.",
        "how_to_fix": "If you don't need this service, disable it. If you do, ensure it's patched to the latest version and access is restricted to only those who need it.",
        "severity_reason": "Connect your AI provider in Settings for a detailed explanation of this specific finding.",
    }


if __name__ == "__main__":
    import os
    key = os.getenv("ANTHROPIC_API_KEY", "")
    client = AIClient("Anthropic (Claude)", key)
    ok, msg = client.test_connection()
    print(f"Connection test: {ok} - {msg}")
