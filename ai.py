"""
NetSweep AI Layer — Multi-Provider Explanation Engine
Supports: Anthropic (Claude), OpenAI (GPT-4o), Google (Gemini)
Generates four-layer security explanations for every finding.
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
        "model": "gemini-1.5-pro",
    },
}

# ─── Prompt Templates ─────────────────────────────────────────────────────────

PORT_EXPLANATION_PROMPT = """You are a cybersecurity educator explaining a network finding to a beginner or student.

Device found: {ip} ({hostname}) — classified as {device_type}
Finding: Port {port} open — Service: {service} — Version: {version}
Risk level: {risk_level}
CVEs found: {cves}
Network context: {context}

Respond ONLY with a JSON object (no markdown, no preamble) with exactly these keys:
{{
  "what_is_it": "Plain English: what is this service and why does it exist? (2-3 sentences)",
  "why_it_matters": "The security implication — what an attacker could do with this. (2-3 sentences)",
  "real_risk": "Concrete worst-case scenario specific to this finding. Be specific, not vague. (2-3 sentences)",
  "how_to_fix": "Exact actionable steps to remediate this — not vague advice, real instructions. (3-5 sentences)",
  "severity_reason": "One sentence explaining why this is rated {risk_level}"
}}"""

DEVICE_SUMMARY_PROMPT = """You are a cybersecurity educator summarizing a full device scan for a beginner.

Device: {ip} ({hostname})
Type: {device_type}
Vendor: {vendor}
Risk Score: {risk_score}/100 — {risk_label}
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
        if self.provider == "Anthropic (Claude)":
            model = PROVIDERS["Anthropic (Claude)"]["model"]
            return _call_anthropic(self.api_key, model, prompt)
        elif self.provider == "OpenAI (GPT-4o)":
            model = PROVIDERS["OpenAI (GPT-4o)"]["model"]
            return _call_openai(self.api_key, model, prompt)
        elif self.provider == "Google (Gemini)":
            model = PROVIDERS["Google (Gemini)"]["model"]
            return _call_gemini(self.api_key, model, prompt)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def _parse_json(self, text: str) -> dict:
        # Strip markdown fences if present
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Attempt to extract first JSON object
            import re
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {}

    def explain_port(self, device, port_info, context: str = "") -> dict:
        """Generate four-layer explanation for a single open port."""
        prompt = PORT_EXPLANATION_PROMPT.format(
            ip=device.ip,
            hostname=device.hostname,
            device_type=device.device_type,
            port=port_info.port,
            service=port_info.service,
            version=port_info.version or "unknown",
            risk_level=port_info.risk_level,
            cves=", ".join(port_info.cve_ids) if port_info.cve_ids else "None found",
            context=context or f"Home/office network with {1} device scanned",
        )
        raw = self._call(prompt)
        return self._parse_json(raw)

    def summarize_device(self, device) -> dict:
        """Generate overall device security summary."""
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
        """
        Asynchronously generate AI explanations for all devices & ports.
        Calls on_update(device_ip, port_or_None, explanation_dict) as results come in.
        """
        def _worker():
            for device in devices:
                # Device summary
                try:
                    summary = self.summarize_device(device)
                    device.ai_summary = summary
                    on_update(device.ip, None, summary)
                except Exception as e:
                    on_update(device.ip, None, {"error": str(e)})

                # Per-port explanations
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
        """Returns (success: bool, message: str)"""
        try:
            result = self._call("Reply with the single word: connected")
            if result:
                return True, f"Connected via {self.provider}"
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                return False, "Invalid API key — check and try again"
            return False, f"API error {e.response.status_code}: {e.response.text[:100]}"
        except Exception as e:
            return False, str(e)
        return False, "No response received"


# ─── Fallback (no API key) ────────────────────────────────────────────────────

FALLBACK_EXPLANATIONS = {
    "Telnet": {
        "what_is_it": "Telnet is a decades-old remote access protocol that lets someone control this device over the network.",
        "why_it_matters": "All data sent over Telnet — including passwords — travels in plain text. Anyone on the same network can intercept and read it instantly.",
        "real_risk": "An attacker on your network could capture the login credentials for this device and take full control of it.",
        "how_to_fix": "Disable Telnet immediately. Enable SSH instead — it does the same job but encrypts all traffic. Find this setting in the device's admin panel under Services or Remote Access.",
        "severity_reason": "CRITICAL because credentials are fully exposed to anyone on the network.",
    },
    "SMB": {
        "what_is_it": "SMB (Server Message Block) is the Windows file and printer sharing protocol.",
        "why_it_matters": "SMB vulnerabilities have enabled some of history's worst ransomware attacks — WannaCry and NotPetya both used SMB to spread across entire networks in minutes.",
        "real_risk": "An unpatched SMB service can allow an attacker to take full control of this machine and use it to spread ransomware to every other device on your network.",
        "how_to_fix": "Ensure Windows is fully patched. Disable SMBv1 (legacy version) in Windows Features. Block port 445 at your firewall from external access.",
        "severity_reason": "CRITICAL due to history of catastrophic exploits targeting this exact service.",
    },
    "RDP": {
        "what_is_it": "RDP (Remote Desktop Protocol) gives full graphical control of a Windows machine over the network.",
        "why_it_matters": "RDP exposed to the internet is one of the most common entry points for ransomware gangs. Attackers scan for it constantly.",
        "real_risk": "A brute-forced or stolen RDP password gives an attacker a full desktop session — they can install ransomware, steal data, or use your machine as a pivot point.",
        "how_to_fix": "Never expose RDP directly to the internet. Use a VPN or RDP gateway. Enable Network Level Authentication (NLA). Use a non-standard port if internal use only. Enable account lockout after failed attempts.",
        "severity_reason": "CRITICAL because of constant automated scanning and active exploitation in the wild.",
    },
    "VNC": {
        "what_is_it": "VNC (Virtual Network Computing) provides remote graphical desktop access, similar to RDP but cross-platform.",
        "why_it_matters": "Many VNC installations are deployed without passwords or with weak ones, giving anyone who finds it full control of the desktop.",
        "real_risk": "An attacker could take full control of this machine — viewing the screen, moving the mouse, typing commands — without ever needing a password if VNC is misconfigured.",
        "how_to_fix": "Set a strong VNC password immediately. Restrict VNC access by IP address. Consider replacing with a VPN + SSH tunnel setup instead. Never expose VNC to the internet.",
        "severity_reason": "CRITICAL because authentication is frequently absent or weak on VNC installations.",
    },
}

def get_fallback_explanation(service: str) -> dict:
    """Return hardcoded explanation for known dangerous services when no AI key."""
    for key, val in FALLBACK_EXPLANATIONS.items():
        if key.lower() in service.lower():
            return val
    return {
        "what_is_it": f"This port is running a service called {service}.",
        "why_it_matters": "Any open port is a potential entry point. This service should be reviewed to ensure it's necessary and properly secured.",
        "real_risk": "Without knowing the specific version and configuration, the exact risk is unclear — but unnecessary open ports increase your attack surface.",
        "how_to_fix": "If you don't need this service, disable it. If you do, ensure it's patched to the latest version and access is restricted to only those who need it.",
        "severity_reason": "Connect your AI provider in Settings for a detailed explanation of this specific finding.",
    }


# ─── Quick test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os
    key = os.getenv("ANTHROPIC_API_KEY", "")
    client = AIClient("Anthropic (Claude)", key)
    ok, msg = client.test_connection()
    print(f"Connection test: {ok} — {msg}")
