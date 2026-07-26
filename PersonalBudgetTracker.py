"""
Personal Budget Tracker  — Dark Theme Edition
"""

import json
import csv
import os
import hashlib
from tkinter import ttk, messagebox, filedialog
import tkinter as tk
from datetime import datetime, date
from collections import defaultdict

# ════════════════════════════════════════════════════════
#  DARK PALETTE
# ════════════════════════════════════════════════════════
BG          = "#0f1117"
SIDEBAR     = "#13171f"
TOPBAR      = "#161b25"
CARD        = "#1a2030"
CARD2       = "#1f2638"
CARD3       = "#252d42"
BORDER      = "#2a3347"
BORDER2     = "#364060"

EM          = "#22c55e"
EM_DK       = "#16a34a"
EM_DEEP     = "#14532d"
EM_DIM      = "#1a3a26"
EM_GLOW     = "#4ade80"

RED         = "#f87171"
RED_DIM     = "#3b1515"
AMBER       = "#fbbf24"
AMBER_DIM   = "#3b2a07"
BLUE        = "#60a5fa"
BLUE_DIM    = "#0f2044"
PURPLE      = "#a78bfa"
PURPLE_DIM  = "#2a1d4a"
CYAN        = "#22d3ee"
CYAN_DIM    = "#0a2a32"
ROSE        = "#fb7185"
ROSE_DIM    = "#3b0f1a"
ORANGE      = "#fb923c"
ORANGE_DIM  = "#3b1a06"
LIME        = "#84cc16"
LIME_DIM    = "#1c2e06"

TEXT        = "#e2e8f4"
TEXT2       = "#8896b0"
TEXT3       = "#4a5568"
WHITE       = "#ffffff"

ACCENT_PAL = [EM, BLUE, AMBER, PURPLE, RED,
              CYAN, ROSE, ORANGE, LIME, "#e879f9"]
ACCENT_DIM = [EM_DIM, BLUE_DIM, AMBER_DIM, PURPLE_DIM, RED_DIM,
              CYAN_DIM, ROSE_DIM, ORANGE_DIM, LIME_DIM, "#2a0a3b"]

# ─── Fonts ───────────────────────────────────────────────
FB  = ("Segoe UI", 15, "bold")
FH1 = ("Segoe UI", 18, "bold")
FH2 = ("Segoe UI", 12, "bold")
FH3 = ("Segoe UI", 10, "bold")
FBD = ("Segoe UI", 10)
FSM = ("Segoe UI", 9)
FXS = ("Segoe UI", 8)
FNV = ("Segoe UI", 10, "bold")
FMN = ("Courier New", 14, "bold")
FMS = ("Courier New", 11, "bold")
FMX = ("Courier New", 9)

# ─── Nav icons ───────────────────────────────────────────
NAV_ICONS = {
    "dashboard":  "\u2b21",   # ⬡ hexagon outline
    "analytics":  "\u2b22",   # ⬢ hexagon filled
    "history":    "\u2630",   # ☰ hamburger
    "add":        "\u2295",   # ⊕ plus-circle
    "cat_budget": "\u2299",   # ⊙ target
    "mon_budget": "\u25eb",   # ◫ calendar box
    "reports":    "\u21d3",   # ⇓ download arrow
}

# ─── Categories with emoji icons ─────────────────────────
CATEGORIES = [
    "\U0001f354  Food & Dining",
    "\U0001f697  Transport",
    "\U0001f3e0  Housing & Rent",
    "\U0001f48a  Health & Medical",
    "\U0001f3ae  Entertainment",
    "\U0001f455  Shopping",
    "\U0001f4da  Education",
    "\u2708\ufe0f  Travel",
    "\U0001f4a1  Utilities",
    "\U0001f4e6  Miscellaneous",
]

DATA_FILE = os.path.join(os.path.expanduser("~"), "pbt_dark.json")


# ════════════════════════════════════════════════════════
#  PERSISTENCE
# ════════════════════════════════════════════════════════
def load_db():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"users": {}, "expenses": [],
            "cat_budgets": {}, "mon_budgets": {}}


def save_db(db):
    with open(DATA_FILE, "w") as f:
        json.dump(db, f, indent=2)


def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def _dk(h, a=18):
    h = h.lstrip("#")
    r, g, b = [max(0, int(h[i:i + 2], 16) - a) for i in (0, 2, 4)]
    return f"#{r:02x}{g:02x}{b:02x}"


def _lt(h, a=18):
    h = h.lstrip("#")
    r, g, b = [min(255, int(h[i:i + 2], 16) + a) for i in (0, 2, 4)]
    return f"#{r:02x}{g:02x}{b:02x}"


# ════════════════════════════════════════════════════════
#  WIDGET FACTORY
# ════════════════════════════════════════════════════════
def L(parent, text="", font=None, fg=None, bg=None, **kw):
    return tk.Label(parent, text=text,
                    font=font or FBD,
                    fg=fg or TEXT,
                    bg=bg or parent["bg"], **kw)


def inp(parent, var=None, width=30, show=None):
    """Dark entry — returns a Frame wrapper so .pack()/.grid() work correctly."""
    wrapper = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
    e = tk.Entry(wrapper, textvariable=var, width=width,
                 show=show or "",
                 bg=CARD2, fg=TEXT,
                 insertbackground=EM,
                 disabledbackground=CARD2,
                 readonlybackground=CARD2,
                 relief="flat", font=FBD,
                 highlightthickness=0, bd=0)
    e.pack(fill="x", ipady=6, padx=0, pady=0)
    e.bind("<FocusIn>",
           lambda _: (wrapper.config(bg=EM), e.config(bg=CARD3)))
    e.bind("<FocusOut>",
           lambda _: (wrapper.config(bg=BORDER), e.config(bg=CARD2)))
    # Stash the real Entry on the wrapper for callers that need it
    wrapper.entry = e
    return wrapper


def cbox(parent, var, values, width=24):
    # Force dark colours for both the field AND the dropdown popup list
    root = parent.winfo_toplevel()
    root.option_add("*TCombobox*Listbox.background",  CARD2)
    root.option_add("*TCombobox*Listbox.foreground",  TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", EM_DEEP)
    root.option_add("*TCombobox*Listbox.selectForeground", EM_GLOW)
    root.option_add("*TCombobox*Listbox.font",        FBD)

    s = ttk.Style()
    s.theme_use("default")
    s.configure("PBT.TCombobox",
                fieldbackground=CARD2,
                background=CARD2,
                foreground=TEXT,
                selectbackground=EM_DEEP,
                selectforeground=EM_GLOW,
                arrowcolor=EM,
                arrowsize=14,
                borderwidth=0,
                relief="flat",
                padding=(6, 6))
    s.map("PBT.TCombobox",
          fieldbackground=[("readonly", CARD2),
                           ("disabled", CARD),
                           ("active",   CARD3)],
          foreground=[("readonly", TEXT)],
          selectbackground=[("readonly", EM_DEEP)],
          arrowcolor=[("pressed", EM_GLOW), ("active", EM_GLOW)])

    cb = ttk.Combobox(parent, textvariable=var, values=values,
                      state="readonly", font=FBD,
                      style="PBT.TCombobox", width=width)
    return cb


def Btn(parent, text, cmd, bg=None, fg=None, padx=14, pady=8):
    bg  = bg or EM
    fg  = fg or "#0a1a0f"
    hov = _lt(bg, 20)
    b = tk.Button(parent, text=text, command=cmd,
                  bg=bg, fg=fg, font=FH3,
                  relief="flat", bd=0, cursor="hand2",
                  padx=padx, pady=pady,
                  activebackground=hov, activeforeground=fg)
    b.bind("<Enter>", lambda e: b.config(bg=hov))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b


def SmBtn(parent, text, cmd, bg=None, fg=None):
    bg  = bg or CARD3
    fg  = fg or TEXT2
    hov = _lt(bg, 12)
    b = tk.Button(parent, text=text, command=cmd,
                  bg=bg, fg=fg, font=FSM,
                  relief="flat", bd=0, cursor="hand2",
                  padx=8, pady=4,
                  activebackground=hov, activeforeground=TEXT)
    b.bind("<Enter>", lambda e: b.config(bg=hov))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b


def Card(parent, padx=16, pady=14, bg=None, **kw):
    return tk.Frame(parent, bg=bg or CARD,
                    highlightthickness=1,
                    highlightbackground=BORDER,
                    padx=padx, pady=pady, **kw)


def Sep(parent, color=None, pady=10):
    tk.Frame(parent, bg=color or BORDER,
             height=1).pack(fill="x", pady=pady)


# ─── Progress bar ────────────────────────────────────────
def ProgBar(parent, pct, color=None, height=8, track=None):
    pct   = max(0.0, min(1.0, pct))
    color = color or EM
    track = track or BORDER
    outer = tk.Frame(parent, bg=track, height=height)
    outer.pack(fill="x", pady=(3, 2))
    outer.pack_propagate(False)

    def draw(e, o=outer, p=pct, c=color, h=height):
        w = max(0, int(o.winfo_width() * p))
        if w > 0:
            tk.Frame(o, bg=c, width=w,
                     height=h).place(x=0, y=0, relheight=1)

    outer.bind("<Configure>", draw)
    return outer


# ─── Toast ───────────────────────────────────────────────
def Toast(root, msg, kind="ok", dur=2400):
    cfg = {
        "ok":   (EM_DEEP,   EM_GLOW, "\u2713 "),
        "err":  (RED_DIM,   RED,     "\u2715 "),
        "warn": (AMBER_DIM, AMBER,   "\u26a0 "),
    }
    bg, fg, icon = cfg.get(kind, cfg["ok"])
    t = tk.Toplevel(root)
    t.overrideredirect(True)
    t.configure(bg=BORDER2)
    t.attributes("-topmost", True)
    inner = tk.Frame(t, bg=bg, padx=16, pady=10)
    inner.pack(padx=1, pady=1)
    L(inner, f"{icon}{msg}", FSM, fg, bg).pack(side="left")
    root.update_idletasks()
    t.update_idletasks()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    w  = t.winfo_width()
    h  = t.winfo_height()
    t.geometry(f"+{sw - w - 20}+{sh - h - 56}")
    root.after(dur, lambda: t.destroy() if t.winfo_exists() else None)


# ─── Empty state ─────────────────────────────────────────
def Empty(parent, icon="\u25cc", title="Nothing here",
          sub="", act=None, acmd=None):
    f = tk.Frame(parent, bg=parent["bg"])
    f.pack(fill="both", expand=True, pady=36)
    L(f, icon,  ("Segoe UI", 34),  TEXT3, f["bg"]).pack()
    L(f, title, FH2,               TEXT2, f["bg"]).pack(pady=(8, 2))
    if sub:
        L(f, sub, FSM, TEXT3, f["bg"]).pack()
    if act and acmd:
        Btn(f, f"  {act}  ", acmd, padx=16, pady=8).pack(pady=(14, 0))


# ─── Scrollable frame ─────────────────────────────────────
class Scroll(tk.Frame):
    def __init__(self, parent, bg=None, **kw):
        bg = bg or BG
        super().__init__(parent, bg=bg, **kw)
        cv = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        sb = tk.Scrollbar(self, orient="vertical", command=cv.yview,
                          bg=CARD, troughcolor=BG,
                          width=5, relief="flat", bd=0)
        cv.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        cv.pack(side="left",  fill="both", expand=True)
        self.inner = tk.Frame(cv, bg=bg)
        wid = cv.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind(
            "<Configure>",
            lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>",
                lambda e: cv.itemconfig(wid, width=e.width))
        cv.bind_all(
            "<MouseWheel>",
            lambda e: cv.yview_scroll(-1 * (e.delta // 120), "units"))


# ════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ════════════════════════════════════════════════════════
class BudgetTracker(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Personal Budget Tracker")
        self.geometry("1200x750")
        self.minsize(1020, 640)
        self.configure(bg=BG)
        self.db           = load_db()
        self.user         = None
        self._nav_active  = None
        self._flt_cat     = tk.StringVar(value="All")
        self._flt_sort    = tk.StringVar(value="Newest")
        self._flt_search  = tk.StringVar()
        self._build()
        self._go("dashboard")

    # ════════════════════════════════════════════════════
    #  SHELL
    # ════════════════════════════════════════════════════
    def _build(self):
        # TOP BAR
        top = tk.Frame(self, bg=TOPBAR, height=58)
        top.pack(fill="x")
        top.pack_propagate(False)
        tk.Frame(top, bg=BORDER, height=1).place(
            relx=0, rely=1.0, relwidth=1, anchor="sw")

        brand = tk.Frame(top, bg=TOPBAR, width=260)
        brand.pack(side="left", fill="y")
        brand.pack_propagate(False)
        tk.Frame(brand, bg=EM, width=3).pack(side="left", fill="y")
        bi = tk.Frame(brand, bg=TOPBAR)
        bi.pack(side="left", fill="both", expand=True, padx=14)
        cv = tk.Canvas(bi, width=26, height=26,
                       bg=TOPBAR, highlightthickness=0)
        cv.pack(side="left", pady=16)
        cv.create_oval(1, 1, 25, 25, fill=EM, outline="")
        cv.create_text(13, 13, text="\u20bf",
                       fill="#0a1a0f",
                       font=("Segoe UI", 11, "bold"))
        L(bi, "  Personal Budget Tracker", ("Segoe UI", 11, "bold"), EM_GLOW, TOPBAR).pack(side="left")

        rbar = tk.Frame(top, bg=TOPBAR)
        rbar.pack(side="right", fill="y", padx=20)

        date_pill = tk.Frame(rbar, bg=CARD2,
                             highlightthickness=1,
                             highlightbackground=BORDER)
        date_pill.pack(side="left", pady=18, padx=(0, 14))
        L(date_pill,
          f"  \U0001f4c5  {date.today().strftime('%d %b %Y')}  ",
          FXS, TEXT2, CARD2).pack()

        self._user_lbl = L(rbar, "\u25cb  Guest", FSM, TEXT3, TOPBAR)
        self._user_lbl.pack(side="left", padx=(0, 12))

        self._auth_btn = Btn(rbar, "  \u21a5  Login / Sign Up  ",
                             self._auth_dialog,
                             bg=EM_DIM, fg=EM_GLOW, padx=12, pady=7)
        self._auth_btn.pack(side="left")

        # BODY
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        # SIDEBAR
        sb = tk.Frame(body, bg=SIDEBAR, width=260)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        tk.Frame(sb, bg=SIDEBAR, height=10).pack()

        self._navb = {}
        for key, label in [
            ("dashboard",  "Dashboard"),
            ("analytics",  "Analytics"),
            ("history",    "History"),
            ("add",        "Add Expense"),
            ("cat_budget", "Category Budget"),
            ("mon_budget", "Monthly Budget"),
            ("reports",    "Reports"),
        ]:
            self._mk_nav(sb, key, NAV_ICONS[key], label)

        tk.Frame(sb, bg=SIDEBAR).pack(fill="both", expand=True)
        tk.Frame(sb, bg=BORDER, height=1).pack(fill="x", padx=16)

        for icon, txt, cmd, col in [
            ("\u21e3", "  Export CSV",    self._export_csv, TEXT2),
            ("\u2297", "  Clear My Data", self._nuke,       RED),
        ]:
            b = tk.Button(sb, text=f" {icon}  {txt}",
                          command=cmd,
                          bg=SIDEBAR, fg=col, font=FSM,
                          relief="flat", bd=0, cursor="hand2",
                          padx=16, pady=10, anchor="w")
            b.pack(fill="x")
            b.bind("<Enter>", lambda e, b=b: b.config(bg=CARD))
            b.bind("<Leave>", lambda e, b=b: b.config(bg=SIDEBAR))

        # WORKSPACE
        self.ws = tk.Frame(body, bg=BG)
        self.ws.pack(fill="both", expand=True)

    def _mk_nav(self, parent, key, icon, text):
        row   = tk.Frame(parent, bg=SIDEBAR, cursor="hand2")
        row.pack(fill="x")
        bar   = tk.Frame(row, bg=SIDEBAR, width=3)
        bar.pack(side="left", fill="y")
        inner = tk.Frame(row, bg=SIDEBAR, padx=14, pady=11)
        inner.pack(side="left", fill="both", expand=True)
        il = L(inner, icon, ("Courier New", 13, "bold"), TEXT3, SIDEBAR)
        il.pack(side="left", padx=(0, 10))
        tl = L(inner, text, FNV, TEXT3, SIDEBAR)
        tl.pack(side="left")

        for w in (row, inner, il, tl):
            w.bind("<Button-1>", lambda e, k=key: self._go(k))

        def on_enter(_):
            if key != self._nav_active:
                for w in (row, inner, il, tl):
                    w.config(bg=CARD2)

        def on_leave(_):
            if key != self._nav_active:
                for w in (row, inner, il, tl):
                    w.config(bg=SIDEBAR)

        for w in (row, inner, il, tl):
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)

        self._navb[key] = (row, bar, inner, il, tl)

    def _go(self, key):
        if self._nav_active and self._nav_active in self._navb:
            r, b, i, il, tl = self._navb[self._nav_active]
            for w in (r, i, il, tl):
                w.config(bg=SIDEBAR)
            b.config(bg=SIDEBAR)
            il.config(fg=TEXT3)
            tl.config(fg=TEXT3)

        self._nav_active = key
        r, b, i, il, tl = self._navb[key]
        for w in (r, i, il, tl):
            w.config(bg=CARD2)
        b.config(bg=EM)
        il.config(fg=EM_GLOW)
        tl.config(fg=TEXT)

        for w in self.ws.winfo_children():
            w.destroy()

        pages = {
            "dashboard":  self._pg_dashboard,
            "analytics":  self._pg_analytics,
            "history":    self._pg_history,
            "add":        self._pg_add,
            "cat_budget": self._pg_cat_budget,
            "mon_budget": self._pg_mon_budget,
            "reports":    self._pg_reports,
        }
        pages[key]()

    # ─── Page header wrapper ─────────────────────────────
    def _page(self, icon, title, subtitle="", scroll=False):
        outer = tk.Frame(self.ws, bg=BG)
        outer.pack(fill="both", expand=True)

        hdr = tk.Frame(outer, bg=TOPBAR)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=BORDER, height=1).pack(fill="x", side="bottom")
        hi = tk.Frame(hdr, bg=TOPBAR, padx=26, pady=14)
        hi.pack(fill="x")

        badge = tk.Frame(hi, bg=EM_DIM,
                         highlightthickness=1,
                         highlightbackground=EM_DEEP)
        badge.pack(side="left", padx=(0, 14))
        L(badge, f"  {icon}  ",
          ("Courier New", 14, "bold"), EM_GLOW, EM_DIM).pack()

        vc = tk.Frame(hi, bg=TOPBAR)
        vc.pack(side="left")
        L(vc, title,    FH1, TEXT,  TOPBAR).pack(anchor="w")
        if subtitle:
            L(vc, subtitle, FSM, TEXT3, TOPBAR).pack(anchor="w", pady=(1, 0))

        L(hi, date.today().strftime("%A, %d %B %Y"),
          FXS, TEXT3, TOPBAR).pack(side="right")

        if scroll:
            sf = Scroll(outer, bg=BG)
            sf.pack(fill="both", expand=True)
            c = tk.Frame(sf.inner, bg=BG, padx=26, pady=18)
            c.pack(fill="both", expand=True)
        else:
            c = tk.Frame(outer, bg=BG, padx=26, pady=18)
            c.pack(fill="both", expand=True)
        return c

    # ─── KPI card ────────────────────────────────────────
    def _kpi(self, parent, icon, label, value, accent, sub):
        c = tk.Frame(parent, bg=CARD,
                     highlightthickness=1,
                     highlightbackground=BORDER)
        c.pack(side="left", fill="both", expand=True, padx=(0, 10))
        tk.Frame(c, bg=accent, height=3).pack(fill="x")
        body = tk.Frame(c, bg=CARD, padx=16, pady=14)
        body.pack(fill="both", expand=True)
        top_row = tk.Frame(body, bg=CARD)
        top_row.pack(fill="x")
        ic_bg = tk.Frame(top_row, bg=_dk(accent, 60) or CARD3,
                         width=34, height=34)
        ic_bg.pack(side="right")
        ic_bg.pack_propagate(False)
        ic_cv = tk.Canvas(ic_bg, width=34, height=34,
                          bg=ic_bg["bg"], highlightthickness=0)
        ic_cv.pack()
        ic_cv.create_text(17, 17, text=icon,
                          fill=accent,
                          font=("Segoe UI Emoji", 14))
        L(top_row, label, FXS, TEXT3, CARD).pack(anchor="w", pady=(4, 0))
        L(body, value, FMN, accent, CARD).pack(anchor="w", pady=(6, 2))
        L(body, sub,   FXS, TEXT3,  CARD).pack(anchor="w")
        return c

    # ════════════════════════════════════════════════════
    #  DASHBOARD
    # ════════════════════════════════════════════════════
    def _pg_dashboard(self):
        p = self._page(NAV_ICONS["dashboard"],
                       "Dashboard", "Your financial overview")
        exps   = self._mine()
        uid    = self.user or "__guest__"
        month  = date.today().strftime("%Y-%m")
        m_exps = [e for e in exps if e["date"].startswith(month)]
        m_tot  = sum(e["amount"] for e in m_exps)
        a_tot  = sum(e["amount"] for e in exps)
        mb     = self.db.get("mon_budgets", {}).get(uid, {})
        m_bud  = mb.get(month, 0)
        avg    = a_tot / len(exps) if exps else 0
        remain = m_bud - m_tot if m_bud else 0

        # KPI strip
        krow = tk.Frame(p, bg=BG)
        krow.pack(fill="x", pady=(0, 16))
        rem_sub = (f"NPR {remain:,.0f} "
                   f"{'left' if remain >= 0 else 'over'}"
                   if m_bud else "Set a limit \u2192")
        self._kpi(krow, "\U0001f4b8", "This Month",
                  f"NPR {m_tot:,.2f}", EM,
                  f"{len(m_exps)} transactions")
        self._kpi(krow, "\U0001f4c5", "Monthly Budget",
                  f"NPR {m_bud:,.2f}" if m_bud else "Not set",
                  BLUE, rem_sub)
        self._kpi(krow, "\U0001f4ca", "Total Spent",
                  f"NPR {a_tot:,.2f}", PURPLE,
                  f"{len(exps)} records")
        self._kpi(krow, "\u2300", "Avg / Entry",
                  f"NPR {avg:,.2f}", AMBER,
                  "across all time")

        # Monthly budget progress
        if m_bud > 0:
            bp = Card(p, padx=20, pady=14)
            bp.pack(fill="x", pady=(0, 14))
            tr = tk.Frame(bp, bg=CARD)
            tr.pack(fill="x")
            pct_b = m_tot / m_bud
            clr_b = (EM if pct_b < 0.75
                     else AMBER if pct_b < 1.0 else RED)
            dim_b = (EM_DIM if pct_b < 0.75
                     else AMBER_DIM if pct_b < 1.0 else RED_DIM)
            btext = ("\u2713  On Track" if pct_b < 0.75
                     else "\u26a0  Watch Out" if pct_b < 1.0
                     else "\u2715  Over Budget")
            L(tr, f"\U0001f4c5   "
              f"{date.today().strftime('%B %Y')} \u2014 Budget",
              FH2, TEXT, CARD).pack(side="left")
            badge2 = tk.Frame(tr, bg=dim_b,
                              highlightthickness=1,
                              highlightbackground=clr_b)
            badge2.pack(side="right")
            L(badge2, f"  {btext}  ", FXS, clr_b, dim_b).pack()
            ProgBar(bp, min(pct_b, 1.0), clr_b, height=10)
            br = tk.Frame(bp, bg=CARD)
            br.pack(fill="x", pady=(2, 0))
            L(br, f"Spent  NPR {m_tot:,.2f}",
              FXS, TEXT2, CARD).pack(side="left")
            L(br, f"Limit  NPR {m_bud:,.2f}",
              FXS, TEXT2, CARD).pack(side="right")

        # Two-column lower section
        lower = tk.Frame(p, bg=BG)
        lower.pack(fill="both", expand=True)
        lower.columnconfigure(0, weight=5)
        lower.columnconfigure(1, weight=3)
        lower.rowconfigure(0, weight=1)

        # Recent transactions
        rc = Card(lower, padx=0, pady=0)
        rc.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        rh = tk.Frame(rc, bg=CARD, padx=18, pady=12)
        rh.pack(fill="x")
        L(rh, "\U0001f550  Recent Transactions",
          FH2, TEXT, CARD).pack(side="left")
        SmBtn(rh, "View All \u2192",
              lambda: self._go("history"),
              CARD3, EM_GLOW).pack(side="right")
        tk.Frame(rc, bg=BORDER, height=1).pack(fill="x")

        recent = sorted(exps, key=lambda x: x["date"], reverse=True)[:8]
        if recent:
            for i, e in enumerate(recent):
                rb  = CARD if i % 2 == 0 else CARD2
                ci  = next((j for j, c in enumerate(CATEGORIES)
                            if c == e["category"]), 0)
                acc = ACCENT_PAL[ci % len(ACCENT_PAL)]
                rw  = tk.Frame(rc, bg=rb, padx=18, pady=10)
                rw.pack(fill="x")
                cv2 = tk.Canvas(rw, width=10, height=10,
                                bg=rb, highlightthickness=0)
                cv2.create_oval(1, 1, 9, 9, fill=acc, outline="")
                cv2.pack(side="left", padx=(0, 10))
                mid = tk.Frame(rw, bg=rb)
                mid.pack(side="left", fill="both", expand=True)
                L(mid, e["category"],    FSM, TEXT2, rb).pack(anchor="w")
                L(mid, e["description"], FXS, TEXT3, rb).pack(anchor="w")
                rr2 = tk.Frame(rw, bg=rb)
                rr2.pack(side="right")
                L(rr2, f"NPR {e['amount']:,.2f}",
                  FMS, EM_GLOW, rb).pack(anchor="e")
                L(rr2, e["date"], FXS, TEXT3, rb).pack(anchor="e")
        else:
            Empty(rc, "\U0001f4b8", "No transactions yet",
                  "Add your first expense",
                  "\u2295  Add Expense", lambda: self._go("add"))

        # This-month category breakdown
        cc = Card(lower, padx=0, pady=0)
        cc.grid(row=0, column=1, sticky="nsew")
        L(cc, "  \U0001f4c6  This Month",
          FH2, TEXT, CARD).pack(anchor="w", padx=18, pady=(12, 6))
        tk.Frame(cc, bg=BORDER, height=1).pack(fill="x")

        cat_t = defaultdict(float)
        for e in m_exps:
            cat_t[e["category"]] += e["amount"]
        grand = sum(cat_t.values()) or 1

        if cat_t:
            for i, (cat, tot) in enumerate(
                    sorted(cat_t.items(), key=lambda x: -x[1])[:7]):
                ci  = next((j for j, c in enumerate(CATEGORIES)
                            if c == cat), i)
                acc = ACCENT_PAL[ci % len(ACCENT_PAL)]
                rr3 = tk.Frame(cc, bg=CARD, padx=18, pady=7)
                rr3.pack(fill="x")
                tr3 = tk.Frame(rr3, bg=CARD)
                tr3.pack(fill="x")
                L(tr3, cat, FXS, TEXT2, CARD).pack(side="left")
                L(tr3, f"NPR {tot:,.0f}",
                  FXS, acc, CARD).pack(side="right")
                ProgBar(rr3, tot / grand, acc, height=5)
        else:
            L(cc, "\n  No spending this month",
              FSM, TEXT3, CARD).pack(anchor="w", padx=18)

    # ════════════════════════════════════════════════════
    #  ANALYTICS
    # ════════════════════════════════════════════════════
    def _pg_analytics(self):
        p = self._page(NAV_ICONS["analytics"],
                       "Analytics",
                       "Visual breakdown of your spending",
                       scroll=True)
        exps = self._mine()
        if not exps:
            Empty(p, "\U0001f4ca", "No data to analyze",
                  "Add some expenses to see charts",
                  "\u2295  Add Expense", lambda: self._go("add"))
            return

        cat_t = defaultdict(float)
        for e in exps:
            cat_t[e["category"]] += e["amount"]
        grand       = sum(cat_t.values()) or 1
        sorted_cats = sorted(cat_t.items(), key=lambda x: -x[1])

        # Category bar chart
        L(p, "  \U0001f4ca  Spending by Category",
          FH2, TEXT, BG).pack(anchor="w", pady=(0, 8))
        bc = Card(p, padx=20, pady=16)
        bc.pack(fill="x", pady=(0, 20))

        for i, (cat, tot) in enumerate(sorted_cats):
            ci  = next((j for j, c in enumerate(CATEGORIES)
                        if c == cat), i)
            acc = ACCENT_PAL[ci % len(ACCENT_PAL)]
            dim = ACCENT_DIM[ci % len(ACCENT_DIM)]
            pct = tot / grand
            rr  = tk.Frame(bc, bg=CARD, pady=7)
            rr.pack(fill="x")
            tr  = tk.Frame(rr, bg=CARD)
            tr.pack(fill="x")
            pill = tk.Frame(tr, bg=dim,
                            highlightthickness=1,
                            highlightbackground=acc)
            pill.pack(side="left")
            L(pill, f"  {cat}  ", FXS, acc, dim).pack()
            L(tr, f"NPR {tot:,.2f}  \u00b7  {pct * 100:.1f}%",
              FXS, TEXT2, CARD).pack(side="right")
            bar_bg = tk.Frame(rr, bg=CARD3, height=14)
            bar_bg.pack(fill="x", pady=(4, 0))

            def draw_fill(e, bg=bar_bg, p=pct, c=acc, t=tot):
                w = max(4, int(bg.winfo_width() * p))
                fill = tk.Frame(bg, bg=c, width=w, height=14)
                fill.place(x=0, y=0, relheight=1)
                if w > 80:
                    L(fill, f"  NPR {t:,.0f}",
                      ("Segoe UI", 8, "bold"), BG, c).place(
                        x=2, y=0, relheight=1)

            bar_bg.bind("<Configure>", draw_fill)

        # Monthly trend
        L(p, "  \U0001f4c8  Monthly Trend",
          FH2, TEXT, BG).pack(anchor="w", pady=(0, 8))
        m_totals = defaultdict(float)
        for e in exps:
            m_totals[e["date"][:7]] += e["amount"]
        months = sorted(m_totals.keys())[-10:]
        vals   = [m_totals[m] for m in months]
        max_v  = max(vals) or 1
        uid    = self.user or "__guest__"
        mon_b  = self.db.get("mon_budgets", {}).get(uid, {})

        tc = Card(p, padx=20, pady=16)
        tc.pack(fill="x", pady=(0, 20))
        chart = tk.Frame(tc, bg=CARD)
        chart.pack(fill="x")
        BAR_H = 110

        for m, v in zip(months, vals):
            col = tk.Frame(chart, bg=CARD)
            col.pack(side="left", fill="y", expand=True, padx=3)
            bar_h = max(4, int(BAR_H * v / max_v))
            bud_v = mon_b.get(m, 0)
            bar_c = RED if (bud_v and v > bud_v) else EM
            tk.Frame(col, bg=CARD, height=BAR_H - bar_h).pack()
            tk.Frame(col, bg=bar_c, width=36, height=bar_h).pack()
            L(col, m[5:],             FXS, TEXT3, CARD).pack(pady=(4, 0))
            L(col, f"{v / 1000:.1f}k", FXS, TEXT2, CARD).pack()

        L(tc, "  \u25cf Green = under budget    \u25cf Red = over budget",
          FXS, TEXT3, CARD).pack(anchor="w", pady=(8, 0))

        # Donut + legend
        L(p, "  \U0001f535  Category Share",
          FH2, TEXT, BG).pack(anchor="w", pady=(0, 8))
        sc = Card(p, padx=20, pady=16)
        sc.pack(fill="x")
        si = tk.Frame(sc, bg=CARD)
        si.pack(fill="x")

        cv3 = tk.Canvas(si, width=180, height=180,
                        bg=CARD, highlightthickness=0)
        cv3.pack(side="left", padx=(0, 24))
        start = 0
        for i, (cat, tot) in enumerate(sorted_cats):
            ci  = next((j for j, c in enumerate(CATEGORIES)
                        if c == cat), i)
            acc = ACCENT_PAL[ci % len(ACCENT_PAL)]
            ext = (tot / grand) * 360
            cv3.create_arc(14, 14, 166, 166,
                           start=start, extent=ext,
                           fill=acc, outline=CARD, width=2)
            start += ext
        cv3.create_oval(52, 52, 128, 128, fill=CARD, outline=CARD)
        cv3.create_text(90, 86, text="Total", fill=TEXT3, font=FXS)
        cv3.create_text(90, 102,
                        text=f"NPR {grand:,.0f}",
                        fill=TEXT,
                        font=("Segoe UI", 8, "bold"))

        leg = tk.Frame(si, bg=CARD)
        leg.pack(side="left", fill="both", expand=True)
        for i, (cat, tot) in enumerate(sorted_cats[:8]):
            ci  = next((j for j, c in enumerate(CATEGORIES)
                        if c == cat), i)
            acc = ACCENT_PAL[ci % len(ACCENT_PAL)]
            rr4 = tk.Frame(leg, bg=CARD, pady=5)
            rr4.pack(fill="x")
            cv4 = tk.Canvas(rr4, width=10, height=10,
                            bg=CARD, highlightthickness=0)
            cv4.create_oval(1, 1, 9, 9, fill=acc, outline="")
            cv4.pack(side="left", padx=(0, 8))
            L(rr4, cat, FXS, TEXT2, CARD).pack(side="left")
            L(rr4, f"{tot / grand * 100:.1f}%",
              FXS, acc, CARD).pack(side="right")

    # ════════════════════════════════════════════════════
    #  HISTORY
    # ════════════════════════════════════════════════════
    def _pg_history(self):
        p = self._page(NAV_ICONS["history"],
                       "Transaction History",
                       "All recorded expenses")

        # Reset filters each time page loads so stale state doesn't hide data
        self._flt_cat.set("All")
        self._flt_search.set("")

        tb = Card(p, padx=16, pady=12)
        tb.pack(fill="x", pady=(0, 12))
        tbr = tk.Frame(tb, bg=CARD)
        tbr.pack(fill="x")

        for ltext, var, vals, w in [
            ("Category:", self._flt_cat,
             ["All"] + CATEGORIES, 18),
            ("Sort:", self._flt_sort,
             ["Newest", "Oldest", "Highest", "Lowest"], 10),
        ]:
            L(tbr, ltext, FXS, TEXT3, CARD).pack(side="left", padx=(0, 4))
            cb = cbox(tbr, var, vals, width=w)
            cb.pack(side="left", padx=(0, 14))
            cb.bind("<<ComboboxSelected>>",
                    lambda e: self._render_hist(tbl_f))

        L(tbr, "\U0001f50d", FSM, TEXT3, CARD).pack(
            side="left", padx=(0, 4))
        se = inp(tbr, var=self._flt_search, width=20)
        se.pack(side="left")
        self._flt_search.trace(
            "w", lambda *_: self._render_hist(tbl_f))

        SmBtn(tbr, "\u21e3  Export",
              self._export_csv, EM_DIM, EM_GLOW).pack(side="right")

        tbl_f = tk.Frame(p, bg=BG)
        tbl_f.pack(fill="both", expand=True)
        self._render_hist(tbl_f)

    def _render_hist(self, frame):
        for w in frame.winfo_children():
            w.destroy()

        cat  = self._flt_cat.get()
        srt  = self._flt_sort.get()
        srch = self._flt_search.get().lower().strip()

        all_expenses = self._mine()

        # Normalize: strip extra spaces for comparison
        def cat_match(e_cat):
            if cat == "All":
                return True
            return e_cat.strip() == cat.strip()

        rows = [
            e for e in all_expenses
            if cat_match(e["category"])
            and (not srch
                 or srch in e.get("description", "").lower()
                 or srch in e.get("category", "").lower()
                 or srch in e.get("date", ""))
        ]

        sort_key = {
            "Newest":  lambda x: x["date"],
            "Oldest":  lambda x: x["date"],
            "Highest": lambda x: x["amount"],
            "Lowest":  lambda x: x["amount"],
        }.get(srt, lambda x: x["date"])

        rows = sorted(rows, key=sort_key,
                      reverse=srt in ("Newest", "Highest"))

        if not all_expenses:
            Empty(frame, "\U0001f4b8",
                  "No expenses recorded yet",
                  "Go to 'Add Expense' to record your first entry",
                  "\u2295  Add Expense", lambda: self._go("add"))
            return

        if not rows:
            Empty(frame, "\U0001f50d",
                  "No matching records",
                  "Try 'All' in the category filter or clear the search")
            return

        hdr = tk.Frame(frame, bg=EM_DEEP, padx=16, pady=10)
        hdr.pack(fill="x")

        # Fixed columns
        for txt, w in [("#", 28), ("Date", 80), ("Category", 160)]:
            L(hdr, txt, ("Segoe UI", 9, "bold"),
              EM_GLOW, EM_DEEP).pack(side="left", padx=(0, 8))
            tk.Frame(hdr, bg=EM_DEEP, width=w).pack(side="left")

        # Flexible description column
        L(hdr, "Description", ("Segoe UI", 9, "bold"),
          EM_GLOW, EM_DEEP).pack(side="left", expand=True, fill="x")

        # Right-side fixed columns
        for txt in ["Amount", "Actions"]:
            L(hdr, txt, ("Segoe UI", 9, "bold"),
              EM_GLOW, EM_DEEP).pack(side="left", padx=(0, 14))

        sf = Scroll(frame, bg=BG)
        sf.pack(fill="both", expand=True)
        inner = sf.inner

        for i, e in enumerate(rows):
            rb  = CARD if i % 2 == 0 else CARD2
            ci  = next((j for j, c in enumerate(CATEGORIES)
                        if c == e["category"]), 0)
            acc = ACCENT_PAL[ci % len(ACCENT_PAL)]
            dim = ACCENT_DIM[ci % len(ACCENT_DIM)]

            try:
                r2 = int(acc[1:3], 16)
                g2 = int(acc[3:5], 16)
                b2 = int(acc[5:7], 16)
                pill_bg = (f"#{max(0, r2 - 140):02x}"
                           f"{max(0, g2 - 140):02x}"
                           f"{max(0, b2 - 140):02x}")
            except Exception:
                pill_bg = dim

            rw = tk.Frame(inner, bg=rb, padx=16, pady=10)
            rw.pack(fill="x", pady=1)

            # Use fixed-width Label with anchor so columns align
            L(rw, str(i + 1), FXS, TEXT3, rb).pack(side="left")
            tk.Frame(rw, bg=rb, width=20).pack(side="left")
            L(rw, e["date"],  FXS, TEXT3, rb).pack(side="left")
            tk.Frame(rw, bg=rb, width=12).pack(side="left")

            pill = tk.Frame(rw, bg=pill_bg,
                            highlightthickness=1,
                            highlightbackground=acc,
                            padx=6, pady=2)
            pill.pack(side="left")
            L(pill, e["category"],
              ("Segoe UI", 8, "bold"), acc, pill_bg).pack()
            tk.Frame(rw, bg=rb, width=8).pack(side="left")

            L(rw, e["description"],
              FSM, TEXT, rb).pack(side="left", fill="x", expand=True)
            L(rw, f"NPR {e['amount']:,.2f}",
              FMS, EM_GLOW, rb).pack(side="left", padx=(0, 8))

            def mk_del(eid, fr=frame):
                return lambda: self._del_exp(eid, fr)

            SmBtn(rw, "\u2715", mk_del(e["id"]),
                  RED_DIM, RED).pack(side="right", padx=(2, 0))

        total = sum(e["amount"] for e in rows)
        ft = tk.Frame(frame, bg=EM_DEEP, padx=16, pady=9)
        ft.pack(fill="x")
        L(ft, f"  {len(rows)} records",
          FXS, TEXT2, EM_DEEP).pack(side="left")
        L(ft, f"Total  NPR {total:,.2f}",
          FMS, EM_GLOW, EM_DEEP).pack(side="right")

    def _del_exp(self, eid, frame):
        if messagebox.askyesno(
                "Delete", "Delete this expense permanently?",
                icon="warning"):
            self.db["expenses"] = [
                e for e in self.db["expenses"] if e["id"] != eid]
            save_db(self.db)
            self._render_hist(frame)
            Toast(self, "Expense deleted", "err")

    def _edit_dlg(self, rec, frame):
        win = tk.Toplevel(self)
        win.title("Edit Expense")
        win.geometry("460x430")
        win.configure(bg=CARD)
        win.grab_set()
        win.resizable(False, False)

        tk.Frame(win, bg=EM, height=3).pack(fill="x")
        L(win, "  \u270f  Edit Expense",
          FH2, TEXT, CARD).pack(anchor="w", padx=22, pady=(14, 0))
        tk.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=22, pady=8)

        f = tk.Frame(win, bg=CARD, padx=22)
        f.pack(fill="x")
        av  = tk.StringVar(value=str(rec["amount"]))
        cv2 = tk.StringVar(value=rec["category"])
        dv  = tk.StringVar(value=rec["description"])
        dtv = tk.StringVar(value=rec["date"])

        for ltext, var, is_cb in [
            ("Amount (NPR)",       av,  False),
            ("Category",           cv2, True),
            ("Description",        dv,  False),
            ("Date (YYYY-MM-DD)",  dtv, False),
        ]:
            L(f, ltext, FSM, TEXT2, CARD).pack(anchor="w", pady=(10, 2))
            if is_cb:
                cbox(f, cv2, CATEGORIES).pack(fill="x")
            else:
                inp(f, var=var).pack(fill="x")

        msg = L(f, "", FSM, RED, CARD)
        msg.pack(pady=(8, 0))

        def save():
            try:
                amt = float(av.get())
                assert amt > 0
                datetime.strptime(dtv.get(), "%Y-%m-%d")
            except Exception:
                msg.config(text="\u26a0  Invalid amount or date")
                return
            for e in self.db["expenses"]:
                if e["id"] == rec["id"]:
                    e.update({
                        "amount":      round(amt, 2),
                        "category":    cv2.get(),
                        "description": dv.get() or "\u2014",
                        "date":        dtv.get(),
                    })
            save_db(self.db)
            win.destroy()
            self._render_hist(frame)
            Toast(self, "Expense updated \u2713")

        Btn(f, "  \U0001f4be  Save Changes  ",
            save).pack(fill="x", pady=(14, 0))

    # ════════════════════════════════════════════════════
    #  ADD EXPENSE
    # ════════════════════════════════════════════════════
    def _pg_add(self):
        p = self._page(NAV_ICONS["add"],
                       "Add Expense", "Record a new spending entry")
        outer = tk.Frame(p, bg=BG)
        outer.pack(fill="both", expand=True)

        # ── Left: scrollable form so button is always reachable ──
        left_wrap = tk.Frame(outer, bg=BG)
        left_wrap.pack(side="left", fill="both", anchor="nw")

        sf_form = Scroll(left_wrap, bg=BG)
        sf_form.pack(fill="both", expand=True)

        form = Card(sf_form.inner, padx=26, pady=22)
        form.pack(fill="x", anchor="nw", ipadx=4, pady=(0, 10))
        tk.Frame(form, bg=EM, height=3).place(x=0, y=0, relwidth=1)
        tk.Frame(form, bg=CARD, height=3).pack()
        L(form, "New Expense", FH2, TEXT, CARD).pack(
            anchor="w", pady=(4, 12))

        av  = tk.StringVar()
        cv2 = tk.StringVar(value=CATEGORIES[0])
        dv  = tk.StringVar()
        dtv = tk.StringVar(value=str(date.today()))
        nv  = tk.StringVar()

        for ltext, var, is_cb, hint in [
            ("\U0001f4b0  Amount (NPR) *",  av,  False, "e.g. 350.00"),
            ("\U0001f3f7\ufe0f  Category *", cv2, True,  ""),
            ("\U0001f4dd  Description",      dv,  False, "What was this for?"),
            ("\U0001f4c5  Date *",           dtv, False, "YYYY-MM-DD"),
            ("\U0001f516  Note / Tag",       nv,  False, "Optional memo"),
        ]:
            L(form, ltext, FSM, TEXT2, CARD).pack(anchor="w", pady=(10, 2))
            if is_cb:
                cbox(form, var, CATEGORIES).pack(fill="x", ipady=4)
            else:
                w = inp(form, var=var)
                w.pack(fill="x")
                if hint:
                    L(form, hint, FXS, TEXT3, CARD).pack(
                        anchor="w", pady=(1, 0))

        msg = L(form, "", FSM, RED, CARD)
        msg.pack(pady=(10, 0))

        def submit():
            try:
                amt = float(av.get().strip())
                assert amt > 0
            except Exception:
                msg.config(text="\u26a0  Enter a valid positive amount",
                           fg=RED)
                return
            try:
                datetime.strptime(dtv.get().strip(), "%Y-%m-%d")
            except ValueError:
                msg.config(text="\u26a0  Date must be YYYY-MM-DD",
                           fg=RED)
                return

            self.db["expenses"].append({
                "id":          str(datetime.now().timestamp()),
                "user":        self.user or "__guest__",
                "amount":      round(float(av.get()), 2),
                "category":    cv2.get(),
                "description": dv.get().strip() or "\u2014",
                "date":        dtv.get().strip(),
                "note":        nv.get().strip(),
            })
            save_db(self.db)
            av.set("")
            dv.set("")
            nv.set("")
            dtv.set(str(date.today()))
            cv2.set(CATEGORIES[0])
            msg.config(text="\u2705  Expense recorded!", fg=EM_GLOW)
            Toast(self, "Expense added \u2713")
            # Refresh both the recent list and the live budget status
            self._refresh_last(last_f)
            self._refresh_budget_status(bs_frame)

        Btn(form, "  \u2295  Add Expense  ",
            submit, padx=20, pady=11).pack(fill="x", pady=(18, 6))

        side = tk.Frame(outer, bg=BG)
        side.pack(side="left", fill="both", expand=True, padx=(14, 0))

        bs_frame = tk.Frame(side, bg=BG)
        bs_frame.pack(fill="x", pady=(0, 12))
        self._refresh_budget_status(bs_frame)

        last_f = Card(side, padx=16, pady=14)
        last_f.pack(fill="x")
        self._refresh_last(last_f)

    def _refresh_last(self, frame):
        for w in frame.winfo_children():
            w.destroy()
        L(frame, "\U0001f550  Recently Added",
          FH3, TEXT, CARD).pack(anchor="w", pady=(0, 8))
        tk.Frame(frame, bg=BORDER, height=1).pack(fill="x", pady=(0, 6))
        last = sorted(self._mine(),
                      key=lambda x: x["id"], reverse=True)[:5]
        if not last:
            L(frame, "Nothing yet", FXS, TEXT3, CARD).pack(anchor="w")
            return
        for e in last:
            ci  = next((j for j, c in enumerate(CATEGORIES)
                        if c == e["category"]), 0)
            acc = ACCENT_PAL[ci % len(ACCENT_PAL)]
            rr  = tk.Frame(frame, bg=CARD, pady=5)
            rr.pack(fill="x")
            cv5 = tk.Canvas(rr, width=8, height=8,
                            bg=CARD, highlightthickness=0)
            cv5.create_oval(0, 0, 8, 8, fill=acc, outline="")
            cv5.pack(side="left", padx=(0, 8))
            mid = tk.Frame(rr, bg=CARD)
            mid.pack(side="left", fill="both", expand=True)
            L(mid, e["category"],    FXS, TEXT2, CARD).pack(anchor="w")
            L(mid, e["description"], FXS, TEXT3, CARD).pack(anchor="w")
            L(rr, f"NPR {e['amount']:,.0f}",
              FMX, EM_GLOW, CARD).pack(side="right")

    def _refresh_budget_status(self, frame):
        """Rebuild the live monthly budget status widget."""
        for w in frame.winfo_children():
            w.destroy()
        uid   = self.user or "__guest__"
        month = date.today().strftime("%Y-%m")
        mb_v  = (self.db.get("mon_budgets", {})
                 .get(uid, {}).get(month, 0))
        m_tot = sum(
            e["amount"] for e in self._mine()
            if e["date"].startswith(month))
        if mb_v <= 0:
            return
        bs = Card(frame, padx=18, pady=14)
        bs.pack(fill="x")
        pct3 = m_tot / mb_v
        clr3 = (EM if pct3 < 0.75 else AMBER if pct3 < 1.0 else RED)
        L(bs, "\U0001f4c5  Monthly Budget Status",
          FH3, TEXT, CARD).pack(anchor="w")
        ProgBar(bs, min(pct3, 1.0), clr3, height=8)
        L(bs, (f"NPR {m_tot:,.2f}  /  NPR {mb_v:,.2f}"
               f"  ({pct3 * 100:.0f}% used)"),
          FXS, clr3, CARD).pack(anchor="w", pady=(4, 0))

    # ════════════════════════════════════════════════════
    #  CATEGORY BUDGET
    # ════════════════════════════════════════════════════
    def _pg_cat_budget(self):
        p = self._page(NAV_ICONS["cat_budget"],
                       "Category Budget",
                       "Set spending limits per category",
                       scroll=True)
        uid     = self.user or "__guest__"
        buds    = self.db["cat_budgets"].setdefault(uid, {})
        cat_exp = defaultdict(float)
        for e in self._mine():
            cat_exp[e["category"]] += e["amount"]

        cols = tk.Frame(p, bg=BG)
        cols.pack(fill="both", expand=True)

        lf = Card(cols, padx=22, pady=20)
        lf.pack(side="left", anchor="nw", ipadx=4)
        tk.Frame(lf, bg=EM, height=3).place(x=0, y=0, relwidth=1)
        tk.Frame(lf, bg=CARD, height=3).pack()
        L(lf, f"  {NAV_ICONS['cat_budget']}  Set Category Budget",
          FH2, TEXT, CARD).pack(anchor="w", pady=(4, 12))

        catv = tk.StringVar(value=CATEGORIES[0])
        amtv = tk.StringVar()
        L(lf, "Category", FSM, TEXT2, CARD).pack(anchor="w")
        cbox(lf, catv, CATEGORIES).pack(fill="x", pady=(2, 10))
        L(lf, "Monthly Limit (NPR)", FSM, TEXT2, CARD).pack(anchor="w")
        inp(lf, var=amtv, width=28).pack(fill="x")

        msg = L(lf, "", FSM, RED, CARD)
        msg.pack(pady=(8, 0))

        def save_bud():
            try:
                amt = float(amtv.get())
                assert amt > 0
            except Exception:
                msg.config(text="\u26a0  Enter a valid amount", fg=RED)
                return
            buds[catv.get()] = round(amt, 2)
            save_db(self.db)
            amtv.set("")
            msg.config(text="\u2705  Budget saved!", fg=EM_GLOW)
            Toast(self, "Budget saved \u2713")
            _refresh()

        Btn(lf, "  \U0001f4be  Save Budget  ",
            save_bud).pack(fill="x", pady=(12, 0))

        rf = Card(cols, padx=20, pady=18)
        rf.pack(side="left", anchor="nw", padx=(12, 0),
                fill="both", expand=True)
        L(rf, f"  {NAV_ICONS['cat_budget']}  Active Budgets",
          FH2, TEXT, CARD).pack(anchor="w", pady=(0, 8))
        tk.Frame(rf, bg=BORDER, height=1).pack(fill="x", pady=(0, 8))

        bi = tk.Frame(rf, bg=CARD)
        bi.pack(fill="both", expand=True)

        def _refresh():
            # Recompute spending totals live so new expenses are reflected
            live_cat_exp = defaultdict(float)
            for e in self._mine():
                live_cat_exp[e["category"]] += e["amount"]

            for w in bi.winfo_children():
                w.destroy()
            if not buds:
                Empty(bi, "\U0001f3af", "No budgets set",
                      "Add limits using the form")
                return
            for cat, bamt in sorted(buds.items()):
                spent = live_cat_exp.get(cat, 0)
                pct   = min(spent / bamt, 1.0) if bamt else 0
                over  = spent > bamt
                clr   = RED if over else (AMBER if pct > 0.75 else EM)

                rc2 = tk.Frame(
                    bi, bg=CARD2,
                    highlightthickness=1, highlightbackground=BORDER,
                    padx=14, pady=12)
                rc2.pack(fill="x", pady=(0, 8))
                tr2 = tk.Frame(rc2, bg=CARD2)
                tr2.pack(fill="x")
                L(tr2, cat, FBD, TEXT, CARD2).pack(side="left")
                if over:
                    ob = tk.Frame(tr2, bg=RED_DIM,
                                  highlightthickness=1,
                                  highlightbackground=RED)
                    ob.pack(side="left", padx=(8, 0))
                    L(ob, "  \u2715  Over Budget  ",
                      FXS, RED, RED_DIM).pack()

                def mk_del_cat(c):
                    return lambda: (
                        buds.pop(c, None),
                        save_db(self.db),
                        _refresh(),
                        Toast(self, "Budget removed", "err"))

                SmBtn(tr2, "\u2297  Remove",
                      mk_del_cat(cat), RED_DIM, RED).pack(side="right")

                ProgBar(rc2, pct, clr, height=8)
                br4 = tk.Frame(rc2, bg=CARD2)
                br4.pack(fill="x", pady=(2, 0))
                L(br4, f"Spent  NPR {spent:,.2f}",
                  FXS, clr,  CARD2).pack(side="left")
                L(br4, f"Limit  NPR {bamt:,.2f}",
                  FXS, TEXT3, CARD2).pack(side="right")

        _refresh()

    # ════════════════════════════════════════════════════
    #  MONTHLY BUDGET
    # ════════════════════════════════════════════════════
    def _pg_mon_budget(self):
        p = self._page(NAV_ICONS["mon_budget"],
                       "Monthly Budget",
                       "Set a total spending limit per month",
                       scroll=True)
        uid   = self.user or "__guest__"
        mb    = self.db.setdefault("mon_budgets", {}).setdefault(uid, {})
        exps  = self._mine()
        today = date.today()
        cur_m = today.strftime("%Y-%m")

        sf2 = Card(p, padx=22, pady=20)
        sf2.pack(fill="x", pady=(0, 18))
        tk.Frame(sf2, bg=EM, height=3).place(x=0, y=0, relwidth=1)
        tk.Frame(sf2, bg=CARD, height=3).pack()
        L(sf2, "  \U0001f4c5  Set Monthly Budget",
          FH2, TEXT, CARD).pack(anchor="w", pady=(4, 12))

        months_list = []
        y2, mo2 = today.year, today.month
        for _ in range(12):
            months_list.append(f"{y2}-{mo2:02d}")
            mo2 += 1
            if mo2 > 12:
                mo2 = 1
                y2 += 1

        fr2   = tk.Frame(sf2, bg=CARD)
        fr2.pack(fill="x")
        selm  = tk.StringVar(value=cur_m)
        amtv2 = tk.StringVar()

        L(fr2, "Month", FSM, TEXT2, CARD).pack(anchor="w")
        cbox(fr2, selm, months_list, width=14).pack(
            anchor="w", pady=(2, 10))
        L(fr2, "Budget Amount (NPR)", FSM, TEXT2, CARD).pack(anchor="w")
        inp(fr2, var=amtv2, width=28).pack(anchor="w")

        msg2 = L(fr2, "", FSM, RED, CARD)
        msg2.pack(anchor="w", pady=(6, 0))

        def save_mb():
            try:
                amt = float(amtv2.get())
                assert amt > 0
            except Exception:
                msg2.config(text="\u26a0  Enter a valid amount", fg=RED)
                return
            mb[selm.get()] = round(amt, 2)
            save_db(self.db)
            amtv2.set("")
            msg2.config(
                text=f"\u2705  Budget set for {selm.get()}!",
                fg=EM_GLOW)
            Toast(self, "Monthly budget saved \u2713")
            _refresh_hist()

        Btn(fr2, "  \U0001f4c5  Save Monthly Budget  ",
            save_mb).pack(anchor="w", pady=(12, 0))

        # Current month card
        cur_bud  = mb.get(cur_m, 0)
        m_exps_c = [e for e in exps if e["date"].startswith(cur_m)]
        m_tot_c  = sum(e["amount"] for e in m_exps_c)

        cc = Card(p, padx=22, pady=18)
        cc.pack(fill="x", pady=(0, 18))
        ch2 = tk.Frame(cc, bg=CARD)
        ch2.pack(fill="x")
        L(ch2, f"\U0001f4c5  {today.strftime('%B %Y')} \u2014 Current Month",
          FH2, TEXT, CARD).pack(side="left")

        if cur_bud:
            pct5  = m_tot_c / cur_bud
            clr5  = (EM if pct5 < 0.75
                     else AMBER if pct5 < 1.0 else RED)
            dim5  = (EM_DIM if pct5 < 0.75
                     else AMBER_DIM if pct5 < 1.0 else RED_DIM)
            btxt5 = ("\u2713  On Track" if pct5 < 0.75
                     else "\u26a0  Watch Out" if pct5 < 1.0
                     else "\u2715  Over Budget")
            b5 = tk.Frame(ch2, bg=dim5,
                          highlightthickness=1,
                          highlightbackground=clr5)
            b5.pack(side="right")
            L(b5, f"  {btxt5}  ", FXS, clr5, dim5).pack()
            ProgBar(cc, min(pct5, 1.0), clr5, height=12)

            sr = tk.Frame(cc, bg=CARD)
            sr.pack(fill="x", pady=(10, 0))
            for lbl2, val2, col2 in [
                ("Spent",     f"NPR {m_tot_c:,.2f}", clr5),
                ("Budget",    f"NPR {cur_bud:,.2f}", TEXT2),
                ("Remaining",
                 f"NPR {cur_bud - m_tot_c:,.2f}",
                 EM if cur_bud > m_tot_c else RED),
                ("Entries", str(len(m_exps_c)), BLUE),
            ]:
                sc2 = tk.Frame(
                    sr, bg=CARD2,
                    highlightthickness=1, highlightbackground=BORDER,
                    padx=14, pady=10)
                sc2.pack(side="left", padx=(0, 10))
                L(sc2, lbl2, FXS, TEXT3, CARD2).pack()
                L(sc2, val2, FMS, col2, CARD2).pack(pady=(4, 0))

            if m_exps_c:
                Sep(cc, BORDER, pady=10)
                L(cc, "Category breakdown",
                  FSM, TEXT2, CARD).pack(anchor="w", pady=(0, 6))
                cat_t2 = defaultdict(float)
                for e in m_exps_c:
                    cat_t2[e["category"]] += e["amount"]
                for cat, tot in sorted(
                        cat_t2.items(), key=lambda x: -x[1]):
                    ci2 = next((j for j, c in enumerate(CATEGORIES)
                                if c == cat), 0)
                    acc = ACCENT_PAL[ci2 % len(ACCENT_PAL)]
                    rr5 = tk.Frame(cc, bg=CARD, pady=4)
                    rr5.pack(fill="x")
                    L(rr5, cat, FXS, TEXT2, CARD).pack(side="left")
                    L(rr5,
                      f"NPR {tot:,.2f}  "
                      f"({tot / m_tot_c * 100:.0f}%)",
                      FXS, acc, CARD).pack(side="right")
        else:
            L(cc, "No budget set for this month yet.",
              FBD, TEXT3, CARD).pack(anchor="w", pady=8)
            SmBtn(cc, "Set Budget \u2192",
                  lambda: (selm.set(cur_m), amtv2.set("")),
                  EM_DIM, EM_GLOW).pack(anchor="w")

        # All monthly budgets table
        L(p, "  \U0001f4cb  All Monthly Budgets",
          FH2, TEXT, BG).pack(anchor="w", pady=(0, 8))
        ht = Card(p, padx=0, pady=0)
        ht.pack(fill="x")

        def _refresh_hist():
            for w in ht.winfo_children():
                w.destroy()
            if not mb:
                L(ht, "  No monthly budgets set yet.",
                  FBD, TEXT3, CARD).pack(anchor="w", padx=18, pady=14)
                return

            hdr2 = tk.Frame(ht, bg=EM_DEEP, padx=16, pady=10)
            hdr2.pack(fill="x")
            for txt in ["Month", "Budget", "Spent",
                        "Remaining", "Progress", ""]:
                L(hdr2, txt, ("Segoe UI", 9, "bold"),
                  EM_GLOW, EM_DEEP).pack(
                    side="left", expand=True, fill="x")

            for i, (mk, bamt) in enumerate(
                    sorted(mb.items(), reverse=True)):
                rb   = CARD if i % 2 == 0 else CARD2
                sp   = sum(
                    e["amount"] for e in self._mine()
                    if e["date"].startswith(mk))
                pct6 = min(sp / bamt, 1.0) if bamt else 0
                clr6 = RED if sp > bamt else (
                    AMBER if pct6 > 0.75 else EM)
                rem  = bamt - sp

                rw2 = tk.Frame(ht, bg=rb, padx=16, pady=10)
                rw2.pack(fill="x", pady=1)
                mf2 = tk.Frame(rw2, bg=rb)
                mf2.pack(side="left", expand=True, fill="x")
                L(mf2, mk, FBD, TEXT, rb).pack(side="left")
                if mk == cur_m:
                    cb3 = tk.Frame(
                        mf2, bg=EM_DIM,
                        highlightthickness=1,
                        highlightbackground=EM)
                    cb3.pack(side="left", padx=(6, 0))
                    L(cb3, "  NOW  ", FXS, EM_GLOW, EM_DIM).pack()

                L(rw2, f"NPR {bamt:,.0f}",
                  FMX, TEXT2, rb).pack(side="left", expand=True, fill="x")
                L(rw2, f"NPR {sp:,.0f}",
                  FMX, clr6, rb).pack(side="left", expand=True, fill="x")
                L(rw2, f"NPR {rem:+,.0f}",
                  FMX, EM_GLOW if rem >= 0 else RED,
                  rb).pack(side="left", expand=True, fill="x")

                mb_bg2 = tk.Frame(rw2, bg=BORDER, height=8)
                mb_bg2.pack(side="left", expand=True,
                            fill="x", padx=(0, 10))
                mb_bg2.pack_propagate(False)

                def draw_m(e, bg=mb_bg2, p=pct6, c=clr6):
                    w = max(2, int(bg.winfo_width() * p))
                    tk.Frame(bg, bg=c, width=w,
                             height=8).place(x=0, y=0, relheight=1)

                mb_bg2.bind("<Configure>", draw_m)

                def mk_del_mb(k):
                    return lambda: (
                        mb.pop(k, None),
                        save_db(self.db),
                        _refresh_hist(),
                        Toast(self, "Budget removed", "err"))

                SmBtn(rw2, "\u2297", mk_del_mb(mk),
                      RED_DIM, RED).pack(side="right")

        _refresh_hist()

    # ════════════════════════════════════════════════════
    #  REPORTS
    # ════════════════════════════════════════════════════
    def _pg_reports(self):
        p = self._page(NAV_ICONS["reports"],
                       "Reports & Export",
                       "Download data and review summaries",
                       scroll=True)
        exps   = self._mine()
        month  = date.today().strftime("%Y-%m")
        cat_t3 = defaultdict(float)
        for e in exps:
            cat_t3[e["category"]] += e["amount"]

        L(p, "  \u21d3  Export Options", FH2, TEXT, BG).pack(
            anchor="w", pady=(0, 8))
        er = tk.Frame(p, bg=BG)
        er.pack(fill="x", pady=(0, 18))

        for title, desc, cmd in [
            ("\U0001f4cb  All Expenses",
             "Every recorded transaction",
             self._export_csv),
            (f"\U0001f4c5  {month} Only",
             f"Transactions for {month} only",
             lambda: self._export_csv(month=month)),
        ]:
            ec = Card(er, padx=18, pady=16)
            ec.pack(side="left", padx=(0, 14), fill="y")
            tk.Frame(ec, bg=EM, height=3).place(x=0, y=0, relwidth=1)
            tk.Frame(ec, bg=CARD, height=3).pack()
            L(ec, title, FH2, TEXT,  CARD).pack(anchor="w", pady=(4, 0))
            L(ec, desc,  FXS, TEXT3, CARD).pack(anchor="w", pady=(2, 10))
            SmBtn(ec, "\u21e3  Download CSV",
                  cmd, EM_DIM, EM_GLOW).pack(anchor="w")

        if not cat_t3:
            Empty(p, "\U0001f4cb", "No data yet",
                  "Add expenses to generate reports")
            return

        L(p, "  \U0001f4ca  Category Summary",
          FH2, TEXT, BG).pack(anchor="w", pady=(0, 8))
        tb2 = Card(p, padx=0, pady=0)
        tb2.pack(fill="x")
        grand2 = sum(cat_t3.values())
        ec2    = defaultdict(int)
        for e in exps:
            ec2[e["category"]] += 1

        hdr3 = tk.Frame(tb2, bg=EM_DEEP, padx=16, pady=10)
        hdr3.pack(fill="x")
        for txt in ["Category", "Total Spent", "# Records",
                    "Avg / Entry", "Share"]:
            L(hdr3, txt, ("Segoe UI", 9, "bold"),
              EM_GLOW, EM_DEEP).pack(
                side="left", expand=True, fill="x")

        for i, (cat, tot) in enumerate(
                sorted(cat_t3.items(), key=lambda x: -x[1])):
            rb   = CARD if i % 2 == 0 else CARD2
            n    = ec2[cat]
            avg2 = tot / n if n else 0
            rw3  = tk.Frame(tb2, bg=rb, padx=16, pady=9)
            rw3.pack(fill="x")
            for txt, col in [
                (cat,                       TEXT),
                (f"NPR {tot:,.2f}",         EM_GLOW),
                (str(n),                    TEXT2),
                (f"NPR {avg2:,.2f}",        TEXT2),
                (f"{tot / grand2 * 100:.1f}%", EM),
            ]:
                L(rw3, txt, FSM, col, rb).pack(
                    side="left", expand=True, fill="x")

        ft2 = tk.Frame(tb2, bg=EM_DEEP, padx=16, pady=10)
        ft2.pack(fill="x")
        for txt, col in [
            ("GRAND TOTAL",         EM_GLOW),
            (f"NPR {grand2:,.2f}",  EM_GLOW),
            (str(len(exps)),         TEXT2),
            ("",                    TEXT2),
            ("100%",                EM_GLOW),
        ]:
            L(ft2, txt, ("Segoe UI", 9, "bold"),
              col, EM_DEEP).pack(
                side="left", expand=True, fill="x")

    # ════════════════════════════════════════════════════
    #  AUTH
    # ════════════════════════════════════════════════════
    def _auth_dialog(self):
        if self.user:
            if messagebox.askyesno(
                    "Logout", f"Log out of '{self.user}'?"):
                self.user = None
                self._auth_btn.config(
                    text="  \u21a5  Login / Sign Up  ",
                    bg=EM_DIM, fg=EM_GLOW)
                self._user_lbl.config(
                    text="\u25cb  Guest", fg=TEXT3)
                self._go("dashboard")
            return

        win = tk.Toplevel(self)
        win.title("Login")
        win.geometry("420x380")
        win.configure(bg=CARD)
        win.grab_set()
        win.resizable(False, False)

        tk.Frame(win, bg=EM, height=3).pack(fill="x")
        top_row = tk.Frame(win, bg=CARD, pady=16)
        top_row.pack(fill="x")
        cv6 = tk.Canvas(top_row, width=36, height=36,
                        bg=CARD, highlightthickness=0)
        cv6.pack(side="left", padx=(22, 10))
        cv6.create_oval(1, 1, 35, 35, fill=EM, outline="")
        cv6.create_text(18, 18, text="\u20bf",
                        fill="#0a1a0f",
                        font=("Segoe UI", 14, "bold"))
        L(top_row, "Personal Budget Tracker",
          FH2, TEXT, CARD).pack(side="left")

        tk.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=22)

        f2 = tk.Frame(win, bg=CARD, padx=24)
        f2.pack(fill="x", pady=(4, 0))
        uv2 = tk.StringVar()
        pv2 = tk.StringVar()

        L(f2, "\U0001f464  Username",
          FSM, TEXT2, CARD).pack(anchor="w", pady=(12, 2))
        inp(f2, var=uv2, width=36).pack(fill="x")
        L(f2, "\U0001f512  Password",
          FSM, TEXT2, CARD).pack(anchor="w", pady=(10, 2))
        inp(f2, var=pv2, width=36, show="\u25cf").pack(fill="x")

        msg3 = L(f2, "", FSM, RED, CARD)
        msg3.pack(pady=(8, 0))

        def do_login():
            u, pw = uv2.get().strip(), pv2.get().strip()
            if not u or not pw:
                msg3.config(text="\u26a0  Both fields required")
                return
            users = self.db.setdefault("users", {})
            h = hash_pw(pw)
            if u in users:
                if users[u] != h:
                    msg3.config(text="\u26a0  Incorrect password")
                    return
                act = f"Welcome back, {u}!"
            else:
                users[u] = h
                save_db(self.db)
                act = f"Account created!  Hi, {u}!"
            self.user = u
            # Migrate any guest expenses to this account
            migrated = 0
            for e in self.db["expenses"]:
                if e.get("user", "__guest__") == "__guest__":
                    e["user"] = u
                    migrated += 1
            if migrated:
                save_db(self.db)
            self._auth_btn.config(
                text=f"  \u23fb  Logout ({u})  ",
                bg=RED_DIM, fg=RED,
                activebackground=RED, activeforeground=WHITE)
            self._user_lbl.config(
                text=f"\u25cf  {u}", fg=EM_GLOW)
            win.destroy()
            Toast(self, act)
            self._go("dashboard")

        Btn(f2, "  \u21a5  Continue  ",
            do_login).pack(fill="x", pady=(14, 0))
        L(f2, "New username? An account is created automatically.",
          FXS, TEXT3, CARD).pack(pady=(8, 0))

    # ════════════════════════════════════════════════════
    #  UTILITIES
    # ════════════════════════════════════════════════════
    def _mine(self):
        uid = self.user or "__guest__"
        result = []
        for e in self.db["expenses"]:
            e_user = e.get("user", "__guest__")
            # Match exact uid OR expenses saved before login (no user key)
            if e_user == uid:
                result.append(e)
        return result

    def _export_csv(self, month=None):
        rows = self._mine()
        if month:
            rows = [e for e in rows if e["date"].startswith(month)]
        if not rows:
            messagebox.showinfo("No Data", "No expenses to export.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"budget_{month or 'all'}.csv")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow(["Date", "Category", "Description",
                             "Amount (NPR)", "Note"])
            # Write each row — strip emoji prefix from category for clean CSV
            for r in rows:
                cat = r.get("category", "")
                # Remove leading emoji + spaces e.g. "🍔  Food & Dining" → "Food & Dining"
                cat_clean = cat.strip()
                # Strip leading non-ASCII chars and spaces
                i = 0
                while i < len(cat_clean) and (ord(cat_clean[i]) > 127 or cat_clean[i] == " "):
                    i += 1
                cat_clean = cat_clean[i:].strip()
                writer.writerow([
                    r.get("date", ""),
                    cat_clean or cat,
                    r.get("description", ""),
                    r.get("amount", 0),
                    r.get("note", ""),
                ])
        Toast(self, f"Exported {len(rows)} records \u2713")

    def _nuke(self):
        if not self._mine():
            messagebox.showinfo("Empty", "No data to clear.")
            return
        if messagebox.askyesno(
                "Clear All",
                "Delete ALL your expenses?\nThis cannot be undone.",
                icon="warning"):
            uid = self.user or "__guest__"
            self.db["expenses"] = [
                e for e in self.db["expenses"]
                if e.get("user", "__guest__") != uid]
            save_db(self.db)
            Toast(self, "All data cleared", "err")
            self._go("dashboard")


# ════════════════════════════════════════════════════════
if __name__ == "__main__":
    BudgetTracker().mainloop()