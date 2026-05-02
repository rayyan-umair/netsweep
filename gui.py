"""
NetSweep GUI — Polished Dark Interface
Built with tkinter + ttk. Runs on Windows / macOS / Linux.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import json
import os
import sys
import time
from pathlib import Path

# ─── Paths & Config ────────────────────────────────────────────────────────────
CONFIG_FILE = Path.home() / ".netsweep" / "config.json"
CONFIG_FILE.parent.mkdir(exist_ok=True)

def load_config() -> dict:
    try:
        return json.loads(CONFIG_FILE.read_text())
    except Exception:
        return {}

def save_config(cfg: dict):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


# ─── Color Palette ─────────────────────────────────────────────────────────────
BG        = "#0d1117"
BG2       = "#161b22"
BG3       = "#21262d"
BORDER    = "#30363d"
TEXT      = "#e6edf3"
TEXT_DIM  = "#8b949e"
ACCENT    = "#58a6ff"
GREEN     = "#3fb950"
YELLOW    = "#d29922"
ORANGE    = "#f0883e"
RED       = "#f85149"
CRITICAL  = "#ff4444"

RISK_COLORS = {
    "CRITICAL": CRITICAL,
    "HIGH":     RED,
    "MEDIUM":   ORANGE,
    "LOW":      YELLOW,
    "INFO":     TEXT_DIM,
    "CLEAN":    GREEN,
    "UNKNOWN":  TEXT_DIM,
    "SAFE":     GREEN,
    "MONITOR":  YELLOW,
    "CONCERNING": ORANGE,
    "DANGEROUS": CRITICAL,
}


# ─── API Key Setup Dialog ──────────────────────────────────────────────────────

class APISetupDialog(tk.Toplevel):
    def __init__(self, parent, on_complete):
        super().__init__(parent)
        self.on_complete = on_complete
        self.result = None

        self.title("NetSweep — AI Setup")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()

        # Center on screen
        self.update_idletasks()
        w, h = 520, 420
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        self._build()

    def _build(self):
        pad = dict(padx=30, pady=10)

        # Logo / header
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=30, pady=(30, 10))

        tk.Label(header, text="◈ NETSWEEP", font=("Courier", 22, "bold"),
                 fg=ACCENT, bg=BG).pack(anchor="w")
        tk.Label(header, text="Network Discovery & Security Assessment",
                 font=("Helvetica", 11), fg=TEXT_DIM, bg=BG).pack(anchor="w")

        # Separator
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=30, pady=10)

        # Intro text
        tk.Label(self,
                 text="Enable AI-powered explanations for every finding.",
                 font=("Helvetica", 12, "bold"), fg=TEXT, bg=BG).pack(**pad, anchor="w")
        tk.Label(self,
                 text="Your key is stored locally only — never shared, never uploaded.",
                 font=("Helvetica", 10), fg=TEXT_DIM, bg=BG, wraplength=460,
                 justify="left").pack(padx=30, anchor="w")

        # Provider selector
        prov_frame = tk.Frame(self, bg=BG)
        prov_frame.pack(fill="x", padx=30, pady=(15, 5))
        tk.Label(prov_frame, text="Provider:", font=("Helvetica", 10),
                 fg=TEXT_DIM, bg=BG).pack(side="left")

        from ai import PROVIDERS
        self.provider_var = tk.StringVar(value="Anthropic (Claude)")
        provider_menu = ttk.Combobox(
            prov_frame, textvariable=self.provider_var,
            values=list(PROVIDERS.keys()), state="readonly", width=22,
            font=("Helvetica", 10)
        )
        provider_menu.pack(side="left", padx=(10, 0))

        # API Key input
        key_frame = tk.Frame(self, bg=BG)
        key_frame.pack(fill="x", padx=30, pady=5)
        tk.Label(key_frame, text="API Key:", font=("Helvetica", 10),
                 fg=TEXT_DIM, bg=BG).pack(side="left")
        self.key_var = tk.StringVar()
        key_entry = tk.Entry(
            key_frame, textvariable=self.key_var,
            font=("Courier", 10), bg=BG3, fg=TEXT,
            insertbackground=ACCENT, relief="flat",
            bd=1, highlightthickness=1, highlightbackground=BORDER,
            highlightcolor=ACCENT, show="•", width=36
        )
        key_entry.pack(side="left", padx=(10, 5), ipady=4)
        self.show_var = tk.BooleanVar()
        def toggle_show():
            key_entry.config(show="" if self.show_var.get() else "•")
        tk.Checkbutton(key_frame, text="show", variable=self.show_var,
                       command=toggle_show, bg=BG, fg=TEXT_DIM,
                       selectcolor=BG3, activebackground=BG,
                       font=("Helvetica", 9)).pack(side="left")

        # Helper link
        link_frame = tk.Frame(self, bg=BG)
        link_frame.pack(fill="x", padx=30)
        tk.Label(link_frame, text="Get a free key: ", font=("Helvetica", 9),
                 fg=TEXT_DIM, bg=BG).pack(side="left")
        for text, url in [
            ("console.anthropic.com", "https://console.anthropic.com"),
            ("  platform.openai.com", "https://platform.openai.com"),
            ("  aistudio.google.com", "https://aistudio.google.com"),
        ]:
            lbl = tk.Label(link_frame, text=text, font=("Helvetica", 9),
                           fg=ACCENT, bg=BG, cursor="hand2")
            lbl.pack(side="left")

        # Status label
        self.status_lbl = tk.Label(self, text="", font=("Helvetica", 9),
                                   fg=GREEN, bg=BG)
        self.status_lbl.pack(pady=5)

        # Buttons
        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.pack(pady=(10, 20))

        skip_btn = tk.Button(
            btn_frame, text="Skip for now",
            font=("Helvetica", 10), fg=TEXT_DIM, bg=BG3,
            activebackground=BORDER, activeforeground=TEXT,
            relief="flat", padx=18, pady=8, cursor="hand2",
            command=self._skip
        )
        skip_btn.pack(side="left", padx=8)

        unlock_btn = tk.Button(
            btn_frame, text="  Unlock AI  ",
            font=("Helvetica", 10, "bold"), fg=BG, bg=ACCENT,
            activebackground="#79b8ff", activeforeground=BG,
            relief="flat", padx=18, pady=8, cursor="hand2",
            command=self._unlock
        )
        unlock_btn.pack(side="left", padx=8)

    def _unlock(self):
        key = self.key_var.get().strip()
        if not key:
            self.status_lbl.config(text="⚠  Please enter an API key", fg=ORANGE)
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


# ─── Scan Result Panel ─────────────────────────────────────────────────────────

class DeviceCard(tk.Frame):
    """A single device's result card in the results panel."""

    def __init__(self, parent, device, ai_client, mode_var, **kwargs):
        super().__init__(parent, bg=BG2, relief="flat", bd=0, **kwargs)
        self.device = device
        self.ai_client = ai_client
        self.mode_var = mode_var
        self._port_frames = {}
        self._build()

    def _build(self):
        d = self.device

        # Card border accent
        risk_color = RISK_COLORS.get(d.risk_label, TEXT_DIM)
        accent_bar = tk.Frame(self, bg=risk_color, width=4)
        accent_bar.pack(side="left", fill="y")

        content = tk.Frame(self, bg=BG2)
        content.pack(side="left", fill="both", expand=True, padx=12, pady=10)

        # Header row
        header = tk.Frame(content, bg=BG2)
        header.pack(fill="x")

        tk.Label(header, text=d.ip, font=("Courier", 13, "bold"),
                 fg=ACCENT, bg=BG2).pack(side="left")
        tk.Label(header, text=f"  {d.hostname}", font=("Courier", 11),
                 fg=TEXT_DIM, bg=BG2).pack(side="left")

        risk_badge = tk.Label(
            header,
            text=f"  {d.risk_label}  ",
            font=("Helvetica", 9, "bold"),
            fg=BG, bg=risk_color
        )
        risk_badge.pack(side="right")

        score_lbl = tk.Label(
            header, text=f"Risk Score: {d.risk_score}/100",
            font=("Helvetica", 9), fg=TEXT_DIM, bg=BG2
        )
        score_lbl.pack(side="right", padx=10)

        # Metadata row
        meta = tk.Frame(content, bg=BG2)
        meta.pack(fill="x", pady=(2, 6))
        for label, val in [("Type", d.device_type), ("Vendor", d.vendor), ("MAC", d.mac)]:
            tk.Label(meta, text=f"{label}: ", font=("Helvetica", 9),
                     fg=TEXT_DIM, bg=BG2).pack(side="left")
            tk.Label(meta, text=val + "   ", font=("Helvetica", 9, "bold"),
                     fg=TEXT, bg=BG2).pack(side="left")

        # AI Summary area (Learning mode)
        self.summary_frame = tk.Frame(content, bg=BG3)
        self.summary_lbl = tk.Label(
            self.summary_frame,
            text="⟳  Generating AI summary...",
            font=("Helvetica", 9, "italic"),
            fg=TEXT_DIM, bg=BG3, wraplength=560, justify="left"
        )
        self.summary_lbl.pack(padx=10, pady=6, anchor="w")

        # Open ports
        if d.open_ports:
            tk.Label(content,
                     text=f"Open Ports ({len(d.open_ports)} found):",
                     font=("Helvetica", 9, "bold"), fg=TEXT_DIM, bg=BG2).pack(anchor="w", pady=(4, 2))
            for port_info in d.open_ports:
                self._add_port_row(content, port_info)
        else:
            tk.Label(content, text="✓  No open ports detected",
                     font=("Helvetica", 9), fg=GREEN, bg=BG2).pack(anchor="w", pady=4)

        # Separator
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", side="bottom")

        self._refresh_mode()

    def _add_port_row(self, parent, port_info):
        risk_color = RISK_COLORS.get(port_info.risk_level, TEXT_DIM)

        row = tk.Frame(parent, bg=BG2)
        row.pack(fill="x", pady=1)

        # Port badge
        tk.Label(row, text=f":{port_info.port}", font=("Courier", 10, "bold"),
                 fg=risk_color, bg=BG2, width=7, anchor="w").pack(side="left")
        tk.Label(row, text=port_info.service, font=("Helvetica", 9, "bold"),
                 fg=TEXT, bg=BG2, width=14, anchor="w").pack(side="left")
        tk.Label(row,
                 text=f"[{port_info.risk_level}]",
                 font=("Helvetica", 8, "bold"),
                 fg=risk_color, bg=BG2, width=10, anchor="w").pack(side="left")
        if port_info.version:
            tk.Label(row, text=port_info.version[:50], font=("Courier", 8),
                     fg=TEXT_DIM, bg=BG2).pack(side="left")
        if port_info.cve_ids:
            tk.Label(row, text=f"  ⚠ {len(port_info.cve_ids)} CVE(s)",
                     font=("Helvetica", 8), fg=RED, bg=BG2).pack(side="left")

        # Toggle button for explanation
        toggle_btn = tk.Label(row, text="▸ Explain", font=("Helvetica", 8),
                              fg=ACCENT, bg=BG2, cursor="hand2")
        toggle_btn.pack(side="right", padx=4)

        # Explanation panel (hidden by default)
        explain_frame = tk.Frame(parent, bg=BG3)
        explain_frame.pack(fill="x", pady=1)
        explain_frame.pack_forget()

        self._port_frames[port_info.port] = {
            "frame": explain_frame,
            "visible": False,
            "btn": toggle_btn,
            "port_info": port_info,
            "loaded": False,
        }

        def toggle(evt, port=port_info.port):
            state = self._port_frames[port]
            if state["visible"]:
                state["frame"].pack_forget()
                state["btn"].config(text="▸ Explain")
                state["visible"] = False
            else:
                state["frame"].pack(fill="x", pady=1)
                state["btn"].config(text="▾ Hide")
                state["visible"] = True
                if not state["loaded"]:
                    self._render_explanation(port, state)

        toggle_btn.bind("<Button-1>", toggle)

    def _render_explanation(self, port, state):
        frame = state["frame"]
        port_info = state["port_info"]

        # Clear frame
        for w in frame.winfo_children():
            w.destroy()

        expl = port_info.ai_explanation
        if not expl:
            from ai import get_fallback_explanation
            expl = get_fallback_explanation(port_info.service)

        if "error" in expl:
            tk.Label(frame, text=f"⚠ AI unavailable: {expl['error']}",
                     font=("Helvetica", 9, "italic"), fg=ORANGE,
                     bg=BG3, wraplength=500, justify="left").pack(padx=10, pady=4, anchor="w")
            state["loaded"] = True
            return

        LABELS = {
            "what_is_it":     ("🔍 WHAT IS IT",   TEXT_DIM),
            "why_it_matters": ("⚡ WHY IT MATTERS", ORANGE),
            "real_risk":      ("💀 REAL RISK",      RED),
            "how_to_fix":     ("🛡  HOW TO FIX IT", GREEN),
        }

        for key, (label, color) in LABELS.items():
            val = expl.get(key)
            if not val:
                continue
            row = tk.Frame(frame, bg=BG3)
            row.pack(fill="x", padx=10, pady=2)
            tk.Label(row, text=label + "  ", font=("Helvetica", 8, "bold"),
                     fg=color, bg=BG3, width=16, anchor="w").pack(side="left", anchor="n")
            tk.Label(row, text=val, font=("Helvetica", 9),
                     fg=TEXT, bg=BG3, wraplength=440, justify="left").pack(side="left", fill="x", expand=True)

        if port_info.cve_ids:
            cve_row = tk.Frame(frame, bg=BG3)
            cve_row.pack(fill="x", padx=10, pady=(0, 4))
            tk.Label(cve_row, text="📋 CVEs", font=("Helvetica", 8, "bold"),
                     fg=RED, bg=BG3, width=16, anchor="w").pack(side="left")
            tk.Label(cve_row, text=" · ".join(port_info.cve_ids),
                     font=("Courier", 8), fg=RED, bg=BG3).pack(side="left")

        state["loaded"] = True

    def update_ai_summary(self, summary: dict):
        """Called when AI summary arrives."""
        headline = summary.get("headline", "")
        verdict = summary.get("overall_verdict", "")
        color = RISK_COLORS.get(verdict, TEXT_DIM)
        text = f"[{verdict}]  {headline}" if headline else "AI summary unavailable."
        self.summary_lbl.config(text=text, fg=color)

    def update_port_explanation(self, port: int, explanation: dict):
        """Called when AI port explanation arrives."""
        state = self._port_frames.get(port)
        if not state:
            return
        state["port_info"].ai_explanation = explanation
        state["loaded"] = False  # Force re-render next time opened
        if state["visible"]:
            self._render_explanation(port, state)

    def _refresh_mode(self):
        mode = self.mode_var.get() if self.mode_var else "learning"
        if mode == "learning":
            self.summary_frame.pack(fill="x", pady=(0, 6))
        else:
            self.summary_frame.pack_forget()


# ─── Main Application Window ───────────────────────────────────────────────────

class NetSweepApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NetSweep — Network Security Scanner")
        self.configure(bg=BG)
        self.minsize(900, 600)

        cfg = load_config()
        self.provider = cfg.get("provider")
        self.api_key  = cfg.get("api_key")
        self.ai_client = None
        self.mode_var = tk.StringVar(value="learning")
        self._device_cards = {}
        self._scanning = False

        # Screen sizing
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = min(1200, sw - 80), min(800, sh - 80)
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        self._build_ui()

        # Show API setup if no key stored
        if not self.api_key:
            self.after(200, self._show_api_setup)
        else:
            self._init_ai_client()

    # ── UI Construction ─────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_topbar()
        self._build_toolbar()
        self._build_main()
        self._build_statusbar()

    def _build_topbar(self):
        bar = tk.Frame(self, bg=BG2, height=52)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        tk.Label(bar, text="◈ NETSWEEP", font=("Courier", 18, "bold"),
                 fg=ACCENT, bg=BG2).pack(side="left", padx=20, pady=10)
        tk.Label(bar, text="Network Discovery & Security Assessment",
                 font=("Helvetica", 10), fg=TEXT_DIM, bg=BG2).pack(side="left", pady=10)

        # Mode toggle
        mode_frame = tk.Frame(bar, bg=BG2)
        mode_frame.pack(side="right", padx=20)
        tk.Label(mode_frame, text="Mode:", font=("Helvetica", 9),
                 fg=TEXT_DIM, bg=BG2).pack(side="left", padx=(0, 6))

        for label, val in [("Learning", "learning"), ("Analyst", "analyst")]:
            rb = tk.Radiobutton(
                mode_frame, text=label, variable=self.mode_var, value=val,
                font=("Helvetica", 9), fg=TEXT, bg=BG2,
                selectcolor=BG3, activebackground=BG2,
                command=self._on_mode_change
            )
            rb.pack(side="left")

        # AI status indicator
        self.ai_status_lbl = tk.Label(
            bar, text="⬤ AI: OFF", font=("Helvetica", 9),
            fg=TEXT_DIM, bg=BG2
        )
        self.ai_status_lbl.pack(side="right", padx=(0, 20))

        # Settings link
        tk.Label(bar, text="⚙ Settings", font=("Helvetica", 9),
                 fg=ACCENT, bg=BG2, cursor="hand2").pack(side="right", padx=(0, 10))

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

    def _build_toolbar(self):
        bar = tk.Frame(self, bg=BG, pady=10)
        bar.pack(fill="x", padx=20)

        tk.Label(bar, text="Target:", font=("Helvetica", 10),
                 fg=TEXT_DIM, bg=BG).pack(side="left")

        self.target_var = tk.StringVar(value="192.168.1.0/24")
        target_entry = tk.Entry(
            bar, textvariable=self.target_var,
            font=("Courier", 11), bg=BG3, fg=TEXT,
            insertbackground=ACCENT, relief="flat",
            bd=0, highlightthickness=1,
            highlightbackground=BORDER, highlightcolor=ACCENT,
            width=22
        )
        target_entry.pack(side="left", padx=(8, 16), ipady=5)

        # Scan button
        self.scan_btn = tk.Button(
            bar, text="▶  Start Scan",
            font=("Helvetica", 10, "bold"),
            fg=BG, bg=GREEN,
            activebackground="#56d364", activeforeground=BG,
            relief="flat", padx=16, pady=6, cursor="hand2",
            command=self._start_scan
        )
        self.scan_btn.pack(side="left", padx=(0, 10))

        self.stop_btn = tk.Button(
            bar, text="■  Stop",
            font=("Helvetica", 10),
            fg=TEXT_DIM, bg=BG3,
            activebackground=BORDER,
            relief="flat", padx=12, pady=6, cursor="hand2",
            command=self._stop_scan, state="disabled"
        )
        self.stop_btn.pack(side="left")

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(
            bar, variable=self.progress_var,
            maximum=100, length=200, mode="determinate"
        )
        self.progress.pack(side="left", padx=20)
        self.progress_lbl = tk.Label(bar, text="", font=("Helvetica", 9),
                                     fg=TEXT_DIM, bg=BG)
        self.progress_lbl.pack(side="left")

        # Export
        tk.Button(
            bar, text="⬇ Export JSON",
            font=("Helvetica", 9),
            fg=TEXT_DIM, bg=BG3,
            relief="flat", padx=10, pady=4, cursor="hand2",
            command=self._export_json
        ).pack(side="right")

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=0)

    def _build_main(self):
        paned = tk.PanedWindow(self, orient="horizontal", bg=BORDER,
                               sashwidth=1, sashrelief="flat")
        paned.pack(fill="both", expand=True)

        # Results panel
        results_container = tk.Frame(paned, bg=BG)
        paned.add(results_container, minsize=580)

        header = tk.Frame(results_container, bg=BG)
        header.pack(fill="x", padx=14, pady=(8, 4))
        self.results_header = tk.Label(
            header, text="No scan results yet — enter a target and click Start Scan",
            font=("Helvetica", 10), fg=TEXT_DIM, bg=BG
        )
        self.results_header.pack(side="left")

        # Scrollable results
        canvas = tk.Canvas(results_container, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(results_container, orient="vertical",
                                  command=canvas.yview)
        self.results_frame = tk.Frame(canvas, bg=BG)
        self.results_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.results_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        # Log / detail panel
        log_container = tk.Frame(paned, bg=BG2)
        paned.add(log_container, minsize=260)

        tk.Label(log_container, text="SCAN LOG", font=("Courier", 9, "bold"),
                 fg=TEXT_DIM, bg=BG2).pack(anchor="w", padx=10, pady=(8, 2))
        tk.Frame(log_container, bg=BORDER, height=1).pack(fill="x")

        self.log_text = scrolledtext.ScrolledText(
            log_container, bg=BG2, fg=TEXT_DIM,
            font=("Courier", 9), relief="flat",
            state="disabled", wrap="word"
        )
        self.log_text.pack(fill="both", expand=True, padx=4, pady=4)

        # Tag colours for log
        self.log_text.tag_config("info",     foreground=TEXT_DIM)
        self.log_text.tag_config("good",     foreground=GREEN)
        self.log_text.tag_config("warn",     foreground=ORANGE)
        self.log_text.tag_config("critical", foreground=RED)
        self.log_text.tag_config("accent",   foreground=ACCENT)

        self._stored_canvas = canvas

    def _build_statusbar(self):
        bar = tk.Frame(self, bg=BG3, height=24)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        self.status_lbl = tk.Label(bar, text="Ready",
                                   font=("Helvetica", 8), fg=TEXT_DIM, bg=BG3)
        self.status_lbl.pack(side="left", padx=10)

    # ── AI Setup ────────────────────────────────────────────────────────────

    def _show_api_setup(self):
        APISetupDialog(self, self._on_api_configured)

    def _on_api_configured(self, provider, api_key):
        self.provider = provider
        self.api_key  = api_key
        self._init_ai_client()

    def _init_ai_client(self):
        if self.api_key:
            from ai import AIClient
            self.ai_client = AIClient(self.provider, self.api_key)
            self.ai_status_lbl.config(
                text=f"⬤ AI: {self.provider.split(' ')[0]}", fg=GREEN)
        else:
            self.ai_client = None
            self.ai_status_lbl.config(text="⬤ AI: OFF", fg=TEXT_DIM)

    # ── Scan Logic ───────────────────────────────────────────────────────────

    def _start_scan(self):
        if self._scanning:
            return
        target = self.target_var.get().strip()
        if not target:
            messagebox.showwarning("NetSweep", "Please enter a network range (e.g. 192.168.1.0/24)")
            return

        self._scanning = True
        self._scan_stop = False
        self._scan_devices = []

        # Reset UI
        for w in self.results_frame.winfo_children():
            w.destroy()
        self._device_cards.clear()
        self._log_clear()
        self.progress_var.set(0)
        self.scan_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.results_header.config(text="Scanning in progress...")
        self._status(f"Starting scan: {target}")
        self._log(f"NetSweep started — target: {target}\n", "accent")

        def run():
            try:
                from engine import scan_network
                def prog(stage, cur, tot):
                    if self._scan_stop:
                        raise InterruptedError("Scan stopped by user")
                    pct = (cur / max(tot, 1)) * 100
                    self.after(0, self.progress_var.set, pct)
                    self.after(0, self.progress_lbl.config,
                               {"text": f"{stage} {cur}/{tot}"})
                    if stage == "scanning" and cur < tot:
                        self.after(0, self._log,
                                   f"Scanning device {cur+1}/{tot}...\n", "info")

                devices = scan_network(target, progress_cb=prog)
                self._scan_devices = devices
                self.after(0, self._on_scan_complete, devices)
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

    def _on_scan_complete(self, devices):
        self._scanning = False
        self.scan_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.progress_var.set(100)

        count = len(devices)
        crit  = sum(1 for d in devices if d.risk_label in ("CRITICAL", "HIGH"))
        self.results_header.config(
            text=f"Scan complete — {count} devices found, {crit} high-risk"
        )
        self._log(f"\n✓ Scan complete — {count} devices\n", "good")

        for d in devices:
            self._add_device_card(d)
            risk_tag = "critical" if d.risk_label in ("CRITICAL", "HIGH") else "info"
            self._log(f"  {d.ip} ({d.hostname}) — {d.risk_label} [{d.risk_score}]\n", risk_tag)

        self._status(f"Scan complete — {count} devices found")

        # Start AI explanations
        if self.ai_client and devices:
            self._log("\n⟳ Generating AI explanations...\n", "accent")
            def on_ai_update(ip, port, explanation):
                self.after(0, self._handle_ai_update, ip, port, explanation)
            self.ai_client.explain_all_async(devices, on_ai_update)

    def _on_scan_stopped(self):
        self._log("\n■ Scan stopped by user\n", "warn")
        self.results_header.config(text="Scan stopped")
        self._status("Scan stopped")

    def _on_scan_error(self, err):
        self._scanning = False
        self.scan_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self._log(f"\n✗ Scan error: {err}\n", "critical")
        self.results_header.config(text=f"Scan error: {err}")
        self._status("Scan error — check log")
        messagebox.showerror("NetSweep Scan Error", err)

    def _add_device_card(self, device):
        card = DeviceCard(
            self.results_frame, device,
            self.ai_client, self.mode_var
        )
        card.pack(fill="x", padx=10, pady=4)
        self._device_cards[device.ip] = card
        self._stored_canvas.yview_moveto(1.0)

    def _handle_ai_update(self, ip, port, explanation):
        card = self._device_cards.get(ip)
        if not card:
            return
        if port is None:
            card.update_ai_summary(explanation)
        else:
            card.update_port_explanation(port, explanation)

    # ── Mode ────────────────────────────────────────────────────────────────

    def _on_mode_change(self):
        for card in self._device_cards.values():
            card._refresh_mode()

    # ── Export ───────────────────────────────────────────────────────────────

    def _export_json(self):
        if not self._scan_devices:
            messagebox.showinfo("NetSweep", "No scan data to export yet.")
            return
        from tkinter.filedialog import asksaveasfilename
        path = asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="netsweep_results.json"
        )
        if path:
            data = [d.to_dict() for d in self._scan_devices]
            Path(path).write_text(json.dumps(data, indent=2))
            self._log(f"✓ Exported to {path}\n", "good")
            messagebox.showinfo("NetSweep", f"Results exported to:\n{path}")

    # ── Log helpers ──────────────────────────────────────────────────────────

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
        self.status_lbl.config(text=msg)


# ─── Entry Point ───────────────────────────────────────────────────────────────

def main():
    # Apply ttk theme
    app = NetSweepApp()
    style = ttk.Style(app)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("TCombobox",
                    fieldbackground=BG3, background=BG3,
                    foreground=TEXT, bordercolor=BORDER)
    style.configure("Horizontal.TProgressbar",
                    background=ACCENT, troughcolor=BG3)
    app.mainloop()

if __name__ == "__main__":
    main()
