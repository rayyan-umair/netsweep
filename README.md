# NetSweep

**Network Discovery & Security Assessment**
The first security scanner that teaches you while it scans.

Built by Rayyan Umair — Technology evolves quickly. Responsibility does not.

---

## What it does

NetSweep finds every device on your network, scans their open ports, detects
services and versions, checks for known CVEs, and explains every single finding
in plain English with four layers:

- What is it — plain English description of the service
- Why it matters — the security implication
- Real risk — concrete worst-case scenario specific to your finding
- How to fix it — exact actionable steps, not vague advice

No Nmap. No command line experience required. No guessing what the output means.

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run

```bash
python gui.py
```

On first launch, a setup screen will ask for your AI API key.
This is optional — skip it and the tool still scans and reports findings.
AI just adds the explanations on top.

### 3. Try Demo Mode first

Click Demo Mode in the toolbar before scanning anything.
It loads a realistic set of example results — a router, a Windows PC, a Raspberry Pi,
an IoT device, and an iPhone — all with full explanations pre-loaded.
This is the fastest way to understand what NetSweep shows you and why it matters.

### 4. Scan your network

Enter your network range (e.g. 192.168.1.0/24) and click Start Scan.

---

## AI Providers

NetSweep supports multiple AI providers. You bring your own key.
It is stored locally in ~/.netsweep/config.json and never shared or uploaded.

| Provider | Model | Free Tier | Get Key |
|---|---|---|---|
| Google (Gemini) | gemini-2.0-flash | Yes — 1500 req/day | aistudio.google.com |
| Groq (Llama 3) | llama-3.1-8b-instant | Yes — 14400 req/day | console.groq.com |
| OpenAI (GPT-4o) | gpt-4o | No | platform.openai.com |
| Anthropic (Claude) | claude-sonnet-4-20250514 | No | console.anthropic.com |

Recommended for beginners: Groq. Sign up at console.groq.com, generate a key,
select Groq in the AI Setup dialog, paste the key, and click Connect.
No credit card required.

---

## Modes

| Mode | Description |
|---|---|
| Learning | AI summaries visible on every device card by default. Best for beginners. |
| Analyst | Raw data first, explanations on click. Best for experienced users. |

Toggle between modes in the top-right corner of the application.

---

## Files

netsweep/
├── gui.py           # Main application — run this
├── engine.py        # Scanning logic
├── ai.py            # AI explanation layer
├── requirements.txt # Dependencies
└── README.md        # This file

---

## Requirements

- Python 3.8+
- requests library
- arp-scan (optional, better device discovery on Linux and macOS)
- Network access to the target range
- Root or administrator privileges recommended for ARP scanning

---

## How Risk Scoring Works

Each device receives a score from 0 to 100 based on its open ports and CVEs found.

| Label | Score | Meaning |
|---|---|---|
| CLEAN | 0-9 | No significant exposure |
| LOW | 10-24 | Minor services open |
| MEDIUM | 25-49 | Services present that warrant review |
| HIGH | 50-79 | Dangerous services open, action recommended |
| CRITICAL | 80-100 | Severely exposed, act immediately |

A single open Telnet, SMB, or RDP port can push a device into CRITICAL on its own.
Each CVE found on a service adds 5 points to the score.

---

## Legal

Only scan networks you own or have explicit permission to scan.
NetSweep is an educational and defensive security tool.
Unauthorized network scanning may be illegal in your jurisdiction.
