# ◈ NetSweep

**Network Discovery & Security Assessment**  
The first security scanner that teaches you while it scans.

---

## What it does

NetSweep finds every device on your network, scans their open ports, detects services and versions, checks for known CVEs, and — if you provide an AI key — explains every single finding in plain English with four layers:

- 🔍 **What is it** — plain English description
- ⚡ **Why it matters** — security implication
- 💀 **Real risk** — concrete worst-case scenario
- 🛡 **How to fix it** — exact actionable steps

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

On first launch, a setup screen will ask for your AI API key (optional — you can skip it).

### 3. Scan
Enter your network range (e.g. `192.168.1.0/24`) and click **Start Scan**.

---

## AI Providers

NetSweep supports any of these providers — you bring your own key:

| Provider | Model | Get key at |
|---|---|---|
| Anthropic (Claude) | claude-sonnet-4-20250514 | console.anthropic.com |
| OpenAI (GPT-4o) | gpt-4o | platform.openai.com |
| Google (Gemini) | gemini-1.5-pro | aistudio.google.com |

Your key is stored locally in `~/.netsweep/config.json`. Never shared. Never uploaded.

---

## Modes

| Mode | Description |
|---|---|
| **Learning Mode** | AI summaries visible, every finding explained, beginner-friendly |
| **Analyst Mode** | Raw data first, explanations available on click, no noise |

Toggle in the top-right corner.

---

## Files

```
netsweep/
├── gui.py           # Main application — run this
├── engine.py        # Scanning logic
├── ai.py            # AI explanation layer
├── requirements.txt # Dependencies
├── .env.example     # API key template
└── README.md        # This file
```

---

## Requirements

- Python 3.8+
- `requests` library
- `arp-scan` (optional, for better device discovery on Linux/macOS)
- Network access to the target range
- Root/admin privileges recommended for ARP scanning

---

## Legal

Only scan networks you own or have explicit permission to scan.  
NetSweep is an educational and defensive security tool.
