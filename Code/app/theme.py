"""greendash · Streamlit theme and HTML building blocks.

Design reference: brand guidelines v1.0 (app/brand guidelines/).
Rules carried over from the prototype:
  * the three verdicts (Likelihood, Eligibility, Impact quality) are always separate components;
  * every status shows an icon + a word + a colour, never colour alone;
  * every impact number is a labelled range with formula, baseline, horizon and source;
  * CO2e, energy, paper and digital adoption are never summed;
  * never white text on Verdant (#19C37D).
Security: every value that comes from data is passed through `esc()` before it is put in HTML.
"""
from __future__ import annotations

import html
from pathlib import Path

import streamlit as st

ASSETS = Path(__file__).resolve().parent / "assets"
LOGO_LIGHT = str(ASSETS / "greendash-logo-on-light-transparent.png")
LOGO_DARK = str(ASSETS / "greendash-logo-dark-transparent.png")

CORE_RULE = "ML predicts. Rules decide eligibility. The carbon engine calculates. The LLM only explains. Claim-Check verifies."
SYNTHETIC = "Synthetic data."

# Brand tokens (brand guidelines section 04). Plotly charts read these too.
C = {
    "verdant": "#19C37D", "canopy": "#0F7A55", "deep_forest": "#0A3B2C", "mint": "#7BE5B5", "dew": "#DDF8EA",
    "amber": "#F5B53D", "aqua": "#22B8CF", "iris": "#8B7CF6", "slate_sage": "#8AA79A",
    "success": "#22A06B", "warning": "#F59E0B", "error": "#E5484D", "info": "#4C8DFF",
    "abyss": "#06110D", "mist": "#F1F8F4", "pure": "#FFFFFF", "fog": "#E3EFE9", "ink": "#0B1F18", "ink_soft": "#4A6358",
    "warning_tx": "#8A5A00", "info_tx": "#2A5DB0", "success_tx": "#157A4F", "error_tx": "#B42318",
}
FAMILY = {"emissions": C["verdant"], "co2": C["verdant"], "energy": C["amber"], "paper": C["aqua"], "digital": C["iris"], "neutral": C["slate_sage"]}

STATUS = {
    "RECOMMEND": ("recommend", "Worth exploring", "check"),
    "REVIEW": ("review", "Mixed signals", "compare"),
    "ABSTAIN": ("abstain", "Need one thing", "help"),
    "SOFT_SURFACE": ("soft", "Good to know", "bulb"),
    "RULED_OUT": ("ruledout", "Not for you, and here's why", "shield"),
}
LIKELIHOOD = {"HIGH": ("high", "High"), "MEDIUM": ("medium", "Medium"), "LOW": ("low", "Low")}
ELIGIBILITY = {"ELIGIBLE": ("pass", "Passed"), "NEEDS_VERIFICATION": ("needs", "Needs verification"), "NOT_ELIGIBLE": ("no", "Not eligible")}
QUALITY_STEPS = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
PATHWAY_ICON = {"GP01": "car", "GP02": "home", "GP03": "sun", "GP04": "sheet"}

_P = 'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"'
ICONS = {
    "check": f'<svg viewBox="0 0 24 24" {_P}><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>',
    "compare": f'<svg viewBox="0 0 24 24" {_P}><circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M13 6h3a2 2 0 0 1 2 2v7"/><path d="M11 18H8a2 2 0 0 1-2-2V9"/></svg>',
    "help": f'<svg viewBox="0 0 24 24" {_P}><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/></svg>',
    "bulb": f'<svg viewBox="0 0 24 24" {_P}><path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/></svg>',
    "shield": f'<svg viewBox="0 0 24 24" {_P}><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/></svg>',
    "target": f'<svg viewBox="0 0 24 24" {_P}><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
    "clipboard": f'<svg viewBox="0 0 24 24" {_P}><rect width="8" height="4" x="8" y="2" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="m9 14 2 2 4-4"/></svg>',
    "gauge": f'<svg viewBox="0 0 24 24" {_P}><path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/></svg>',
    "clock": f'<svg viewBox="0 0 24 24" {_P}><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>',
    "user": f'<svg viewBox="0 0 24 24" {_P}><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
    "receipt": f'<svg viewBox="0 0 24 24" {_P}><path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z"/><path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8"/></svg>',
    "lock": f'<svg viewBox="0 0 24 24" {_P}><rect width="18" height="11" x="3" y="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
    "car": f'<svg viewBox="0 0 24 24" {_P}><path d="m21 8-2 2-1.5-3.7A2 2 0 0 0 15.646 5H8.4a2 2 0 0 0-1.903 1.257L5 10 3 8"/><rect width="18" height="8" x="3" y="10" rx="2"/><path d="M7 14h.01"/><path d="M17 14h.01"/><path d="M5 18v2"/><path d="M19 18v2"/></svg>',
    "home": f'<svg viewBox="0 0 24 24" {_P}><path d="M3 10.5 12 3l9 7.5"/><path d="M5 9v11a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V9"/><path d="M9 21v-5a3 3 0 0 1 6 0v5"/></svg>',
    "sun": f'<svg viewBox="0 0 24 24" {_P}><path d="M3 21 12 14l9 7"/><circle cx="12" cy="7.5" r="2.75"/><path d="M12 2v1"/><path d="M6.5 7.5h-1"/><path d="M18.5 7.5h-1"/></svg>',
    "sheet": f'<svg viewBox="0 0 24 24" {_P}><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="m9 15 2 2 4-4"/></svg>',
    "info": f'<svg viewBox="0 0 24 24" {_P}><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>',
    "eye_off": f'<svg viewBox="0 0 24 24" {_P}><path d="M10.733 5.076a10.744 10.744 0 0 1 11.205 6.575 1 1 0 0 1 0 .696 10.747 10.747 0 0 1-1.444 2.49"/><path d="M14.084 14.158a3 3 0 0 1-4.242-4.242"/><path d="M17.479 17.499a10.75 10.75 0 0 1-15.417-5.151 1 1 0 0 1 0-.696 10.75 10.75 0 0 1 4.446-5.143"/><path d="m2 2 20 20"/></svg>',
}


def esc(value) -> str:
    """Escape any data value before it is placed in HTML."""
    return html.escape("" if value is None else str(value), quote=True)


def icon(name: str, size: int = 18) -> str:
    return f'<span class="gd-ic" style="width:{size}px;height:{size}px">{ICONS[name]}</span>'


def num(n) -> str:
    return "–" if n is None else f"{n:,}"


def render(html_str: str) -> None:
    """Render trusted layout HTML. Data inside it must already be escaped with esc()."""
    st.markdown(html_str, unsafe_allow_html=True)


# --------------------------------------------------------------------------- CSS
CSS = """
:root{
  --verdant:#19C37D;--canopy:#0F7A55;--dew:#DDF8EA;--mint:#7BE5B5;--amber:#F5B53D;--aqua:#22B8CF;--iris:#8B7CF6;--sage:#8AA79A;
  --success:#22A06B;--warning:#F59E0B;--error:#E5484D;--info:#4C8DFF;--mist:#F1F8F4;--fog:#E3EFE9;--ink:#0B1F18;--ink-soft:#4A6358;
  --warning-tx:#8A5A00;--info-tx:#2A5DB0;--success-tx:#157A4F;--error-tx:#B42318;--abyss:#06110D;
  --divider:rgba(11,31,24,.08);--border:rgba(11,31,24,.12);--elev-1:0 2px 8px rgba(11,31,24,.06);--elev-2:0 8px 24px rgba(11,31,24,.10);
  --font-display:"Plus Jakarta Sans","SF Pro Display",system-ui,sans-serif;--font-body:"Inter","SF Pro Text",system-ui,sans-serif;--font-mono:"JetBrains Mono","SF Mono",ui-monospace,monospace;
}
.stApp, .stMarkdown, .stMarkdown p, .stButton button p, input, select, textarea { font-family: var(--font-body); }
/* never override Streamlit's icon font (Material Symbols) */
.stApp { background:
  radial-gradient(520px 520px at 0% 0%, rgba(15,122,85,.16), transparent 70%),
  radial-gradient(420px 420px at 100% 100%, rgba(25,195,125,.10), transparent 70%),
  radial-gradient(360px 360px at 100% 40%, rgba(34,184,207,.08), transparent 70%), var(--mist); }
h1, h2, h3, h4 { font-family: var(--font-display) !important; letter-spacing:-.01em; color:var(--ink); }
.block-container { padding-top: 4.5rem; max-width: 1280px; }  /* clears Streamlit's fixed header */
.gd-ic { display:inline-flex; flex:none; vertical-align:middle; }
.gd-ic svg { width:100%; height:100%; }
/* Buttons: primary is a full pill, Canopy fill so white text passes contrast */
.stButton > button, .stDownloadButton > button, .stLinkButton > a { border-radius:14px; min-height:44px; font-weight:600; }
.stButton > button[kind="primary"] { border-radius:999px; background:var(--canopy); border-color:var(--canopy); }
.stButton > button:focus-visible { outline:2px solid var(--canopy); outline-offset:2px; }
[data-testid="stExpander"] { border-radius:16px; background:#fff; border:1px solid var(--divider); }
[data-testid="stMetric"] { background:rgba(255,255,255,.8); border-radius:20px; padding:12px 16px; box-shadow:var(--elev-1); }

.gd-banner{display:flex;align-items:center;gap:10px;padding:8px 14px;border-radius:14px;background:var(--fog);color:var(--ink-soft);font-size:13px;font-weight:500;margin-bottom:8px}
.gd-banner--warn{background:rgba(245,158,11,.16);color:var(--warning-tx)} .gd-banner--info{background:rgba(76,141,255,.12);color:var(--info-tx)}
.gd-banner--ok{background:rgba(34,160,107,.12);color:var(--success-tx)} .gd-banner--err{background:rgba(229,72,77,.10);color:var(--error-tx)}
.gd-tag{display:inline-flex;align-items:center;gap:4px;padding:2px 8px;border-radius:999px;font-family:var(--font-mono);font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-soft);background:#fff;border:1px solid var(--divider);white-space:nowrap}
.gd-tag--code{text-transform:none;letter-spacing:.02em}
.gd-core{font-size:12px;color:var(--ink-soft);text-align:center;padding:24px 0 8px}
.gd-core b{color:var(--ink)}
.gd-card{position:relative;background:linear-gradient(135deg,rgba(255,255,255,.92),rgba(255,255,255,.80));border-radius:24px;padding:20px;box-shadow:inset 0 1px 0 rgba(255,255,255,.85),0 0 0 1px rgba(11,31,24,.06),var(--elev-2);margin-bottom:12px}
.gd-card--flat{background:rgba(255,255,255,.66);box-shadow:0 0 0 1px rgba(11,31,24,.06),var(--elev-1)}
.gd-card--accent::after{content:"";position:absolute;left:24px;right:24px;top:0;height:2px;border-radius:0 0 2px 2px;background:var(--accent)}
[class*="st-key-gd-proof"]{position:relative;background:linear-gradient(135deg,rgba(255,255,255,.94),rgba(255,255,255,.82));border-radius:24px;padding:20px 20px 12px;box-shadow:inset 0 1px 0 rgba(255,255,255,.9),0 0 0 1px rgba(11,31,24,.06),var(--elev-2)}
[class*="st-key-gd-panel"]{background:rgba(255,255,255,.72);border-radius:24px;padding:20px;box-shadow:0 0 0 1px rgba(11,31,24,.06),var(--elev-1)}
.gd-accent{position:absolute;left:24px;right:24px;top:-20px;height:2px;border-radius:0 0 2px 2px}
.gd-row{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.gd-between{justify-content:space-between}
.gd-pathway{display:flex;align-items:center;gap:8px;font-weight:600;font-size:13px;color:var(--ink-soft);margin:10px 0 6px}
.gd-pathway .gd-ic{color:var(--canopy)}
.gd-headline{font-family:var(--font-display) !important;font-weight:600;font-size:20px !important;line-height:28px !important;padding:0 !important;color:var(--ink);margin:0 0 10px}
.gd-muted{color:var(--ink-soft)} .gd-small{font-size:12px !important;line-height:16px !important}
.gd-disc{font-family:var(--font-mono);font-size:11px !important;line-height:16px !important;letter-spacing:.04em;color:var(--ink-soft);text-transform:uppercase}

.gd-status{display:inline-flex;align-items:center;gap:6px;min-height:28px;padding:0 12px 0 8px;border-radius:999px;font-size:12px;font-weight:600;white-space:nowrap}
.gd-status--recommend{background:var(--dew);color:var(--canopy)} .gd-status--soft{background:var(--fog);color:var(--ink-soft)}
.gd-status--abstain{background:rgba(245,158,11,.16);color:var(--warning-tx)} .gd-status--review{background:rgba(76,141,255,.12);color:var(--info-tx)}
.gd-status--ruledout{background:var(--fog);color:var(--ink-soft)}
.gd-chip{display:inline-flex;align-items:center;gap:8px;min-height:32px;padding:0 12px;border-radius:999px;font-size:12px;font-weight:600;background:var(--fog);color:var(--ink)}
.gd-chip--why{background:rgba(34,184,207,.12)} .gd-chip--why .gd-ic{color:#0E7C8C}

.gd-verdicts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:12px 0}
.gd-verdict{display:flex;flex-direction:column;gap:2px;min-height:44px;padding:8px 10px 8px 12px;border-radius:14px;border:1px solid var(--edge);background:var(--bg)}
.gd-verdict__h{display:flex;align-items:center;gap:6px;font-size:11px;font-weight:600;color:var(--ink-soft)}
.gd-verdict__h .gd-ic{color:var(--tx)}
.gd-verdict__v{font-weight:700;font-size:14px;color:var(--tx)}
.gd-verdict__s{font-family:var(--font-mono);font-size:10px;color:#5F756B}
.gd-v-high{--bg:var(--dew);--edge:var(--verdant);--tx:var(--canopy)} .gd-v-medium{--bg:rgba(245,158,11,.14);--edge:var(--amber);--tx:var(--warning-tx)}
.gd-v-low{--bg:var(--fog);--edge:var(--sage);--tx:var(--ink-soft)} .gd-v-pass{--bg:rgba(34,160,107,.12);--edge:var(--success);--tx:var(--success-tx)}
.gd-v-needs{--bg:rgba(245,158,11,.16);--edge:var(--warning);--tx:var(--warning-tx)} .gd-v-no{--bg:var(--fog);--edge:var(--sage);--tx:var(--ink-soft)}
.gd-v-impact{--bg:#fff;--edge:var(--border);--tx:var(--ink)} .gd-v-impact .gd-verdict__h .gd-ic{color:var(--aqua)}
.gd-v-na{--bg:var(--fog);--edge:var(--divider);--tx:var(--ink-soft)}
.gd-meter{display:inline-flex;gap:3px;margin-left:6px;vertical-align:middle}
.gd-meter i{width:10px;height:6px;border-radius:3px;background:rgba(11,31,24,.12)} .gd-meter i.on{background:var(--aqua)}

.gd-impact{background:var(--fog);border-radius:16px;padding:16px;margin:12px 0}
.gd-impact__l{display:flex;justify-content:space-between;align-items:center;font-size:13px;font-weight:600;color:var(--ink-soft)}
.stMarkdown .gd-impact__kpi,.gd-impact__kpi{font-family:var(--font-display);font-weight:800;font-size:34px !important;line-height:40px !important;letter-spacing:-.02em;color:var(--canopy);margin:6px 0 2px;font-feature-settings:"tnum" 1}
.gd-impact__kpi small{font-size:14px !important;font-weight:700;letter-spacing:0}
.gd-range{margin-top:8px}
.gd-range__t{position:relative;height:8px;border-radius:999px;background:rgba(11,31,24,.12)}
.gd-range__b{position:absolute;top:0;bottom:0;border-radius:999px;opacity:.55}
.gd-range__m{position:absolute;top:-4px;width:4px;height:16px;margin-left:-2px;border-radius:2px}
.gd-range__lbl{display:flex;justify-content:space-between;font-size:11px;color:var(--ink-soft);margin-top:6px;font-feature-settings:"tnum" 1}
.gd-metrics{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px}
.gd-metric{background:#fff;border-radius:14px;padding:12px}
.gd-metric__v{font-family:var(--font-display);font-weight:800;font-size:26px}
.gd-dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;vertical-align:middle}

.gd-ev{list-style:none;padding:0;margin:0}
.gd-ev li{padding:10px 0;border-top:1px solid var(--divider)} .gd-ev li:first-child{border-top:0}
.gd-prov{display:inline-flex;align-items:center;gap:6px;padding:2px 8px 2px 6px;border-radius:999px;font-size:11px;font-weight:600;background:var(--fog);color:var(--ink-soft);margin-right:6px}
.gd-prov--declared .gd-ic{color:var(--iris)} .gd-prov--inferred .gd-ic{color:var(--canopy)}
.gd-date{font-family:var(--font-mono);font-size:11px;color:#5F756B;letter-spacing:.04em}

.gd-stamp{display:flex;align-items:center;gap:12px;padding:12px 16px;border-radius:16px;background:rgba(34,160,107,.12);font-size:13px;margin:12px 0}
.gd-stamp .gd-ic{color:var(--success-tx)} .gd-stamp--tpl{background:var(--fog)} .gd-stamp--tpl .gd-ic{color:var(--ink-soft)}
.gd-stamp__n{margin-left:auto;font-family:var(--font-mono);font-size:11px;color:var(--success-tx);white-space:nowrap}
.gd-whynot{background:#fff;border:1px solid var(--divider);border-radius:16px;padding:16px;margin:12px 0}
.gd-ladder{display:flex;align-items:center;gap:10px;padding:12px 16px;border-radius:16px;border:1px dashed rgba(11,31,24,.25);font-size:13px;margin:8px 0}

.gd-tile{border-radius:24px;padding:16px;min-height:150px;display:flex;flex-direction:column;gap:10px;background:rgba(255,255,255,.72);box-shadow:0 0 0 1px rgba(11,31,24,.06),var(--elev-1)}
.gd-tile.is-on{background:rgba(255,255,255,.94);box-shadow:0 0 0 2px var(--canopy),var(--elev-2)}
.gd-tile__i{width:40px;height:40px;border-radius:50%;display:grid;place-items:center;background:var(--dew);color:var(--canopy)}
.gd-tile__i.q{background:var(--fog);color:var(--ink-soft)}
.gd-tile__n{font-family:var(--font-display);font-weight:700;font-size:16px}

.gd-kpi{position:relative;overflow:hidden;border-radius:28px;padding:18px 20px;background:rgba(255,255,255,.88);box-shadow:0 0 0 1px rgba(11,31,24,.06),var(--elev-2);height:100%}
.gd-kpi::after{content:"";position:absolute;left:0;right:0;top:0;height:3px;background:var(--fam)}
.gd-kpi.est::after{opacity:.55;background:repeating-linear-gradient(90deg,var(--fam) 0 8px,transparent 8px 12px)}
.gd-kpi__v{font-family:var(--font-display);font-weight:800;font-size:26px;line-height:34px;margin-top:6px;font-feature-settings:"tnum" 1}
.gd-kpi__v .gd-small{display:block;font-family:var(--font-body);font-weight:500}

.gd-viol{background:rgba(229,72,77,.10);border-bottom:1px solid var(--error);border-radius:3px;padding:0 2px}
.gd-viol sup{font-family:var(--font-mono);font-size:10px;color:var(--error-tx);margin-left:3px}
.gd-crumbs{font-size:12px;color:var(--ink-soft);margin-bottom:8px}
.gd-crumbs b{color:var(--ink)}
/* ---- Cockpit dark mode (brand guidelines 4.3): any page that renders st.container(key="gd-dark") ---- */
.st-key-gd-dark{display:none}
.stApp:has(.st-key-gd-dark){background:
  radial-gradient(560px 560px at 0% 0%, rgba(15,122,85,.28), transparent 70%),
  radial-gradient(420px 420px at 100% 30%, rgba(34,184,207,.10), transparent 70%), #06110D}
.stApp:has(.st-key-gd-dark) [data-testid="stHeader"]{background:#06110D}
.stApp:has(.st-key-gd-dark) [data-testid="stMain"]{
  --ink:rgba(255,255,255,.94);--ink-soft:rgba(255,255,255,.68);--mist:#06110D;--fog:#122A21;--dew:rgba(25,195,125,.18);
  --canopy:#7BE5B5;--divider:rgba(255,255,255,.12);--border:rgba(255,255,255,.16);
  --warning-tx:#F5B53D;--info-tx:#8FB8FF;--success-tx:#7BE5B5;--error-tx:#FF8A8E;
  --elev-1:0 2px 8px rgba(0,0,0,.35);--elev-2:0 8px 24px rgba(0,0,0,.45);color:var(--ink)}
.stApp:has(.st-key-gd-dark) [data-testid="stMain"] :is([data-testid="stMarkdownContainer"],[data-testid="stMarkdownContainer"] :is(p,li,b,strong),
  [data-testid="stWidgetLabel"] p,[data-testid="stMetricValue"],[data-testid="stMetricLabel"] p,[data-baseweb="tab"] p,th,td){color:var(--ink)}
.stApp:has(.st-key-gd-dark) [data-testid="stMain"] :is([data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p,.gd-muted,.gd-verdict__s,.gd-crumbs){color:var(--ink-soft)}
.stApp:has(.st-key-gd-dark) [data-testid="stMain"] :is(.gd-card,.gd-card--flat,.gd-kpi,.gd-metric,.gd-whynot,[class*="st-key-gd-panel"],[data-testid="stMetric"],[data-testid="stExpander"]){
  background:#0C1D16;box-shadow:0 0 0 1px rgba(255,255,255,.10),var(--elev-1);border-color:rgba(255,255,255,.12)}
.stApp:has(.st-key-gd-dark) [data-testid="stMain"] .gd-verdict{--bg:rgba(255,255,255,.05);--edge:rgba(255,255,255,.16);--tx:var(--ink)}
.stApp:has(.st-key-gd-dark) [data-testid="stMain"] :is(.gd-range__t,.gd-meter i:not(.on)){background:rgba(255,255,255,.16)}
.stApp:has(.st-key-gd-dark) [data-testid="stMain"] hr{border-color:var(--divider);background:var(--divider)}
.stApp:has(.st-key-gd-dark) [data-testid="stMain"] [data-testid="stTable"] :is(th,td){border-color:var(--divider);background:transparent}
.stApp:has(.st-key-gd-dark) [data-testid="stMain"] [data-testid="stTable"] thead th{color:var(--ink-soft)}
/* buttons and segmented controls: dark surface, light label; primary is Verdant with Abyss text (never white on Verdant) */
.stApp:has(.st-key-gd-dark) [data-testid="stMain"] .stButton > button,
.stApp:has(.st-key-gd-dark) [data-testid="stMain"] button[data-testid^="stBaseButton-segmented_control"]{background:#0C1D16;border-color:rgba(255,255,255,.24);color:var(--ink)}
.stApp:has(.st-key-gd-dark) [data-testid="stMain"] button[data-testid="stBaseButton-segmented_controlActive"]{border-color:#19C37D;background:rgba(25,195,125,.18)}
.stApp:has(.st-key-gd-dark) [data-testid="stMain"] .gd-tag{background:rgba(255,255,255,.08);color:var(--ink-soft)}
.stApp:has(.st-key-gd-dark) [data-testid="stMain"] .stButton > button[kind="primary"]{background:#19C37D;border-color:#19C37D;color:#06110D}
.stApp:has(.st-key-gd-dark) [data-testid="stMain"] .stButton > button[kind="primary"] p{color:#06110D}
.stApp:has(.st-key-gd-dark) [data-testid="stMain"] .stButton > button:disabled{opacity:.45}
@media (max-width: 640px){ .gd-verdicts{grid-template-columns:1fr} .stMarkdown .gd-impact__kpi,.gd-impact__kpi{font-size:28px} }
"""


def setup(page_title: str, layout: str = "wide", dark: bool = False) -> None:
    """Call first on every page: page config, logo, CSS.

    dark=True (Cockpit; brand guidelines 4.3) drops a keyed marker that the CSS
    uses to switch the main area to the dark tokens. The sidebar stays light.
    """
    st.set_page_config(page_title=f"greendash · {page_title}", page_icon=LOGO_LIGHT, layout=layout)
    # sidebar is light on every page; icon_image shows in the header when the sidebar is closed
    st.logo(LOGO_LIGHT, size="large", icon_image=LOGO_DARK if dark else LOGO_LIGHT)
    render(f"<style>{CSS}</style>")
    if dark:
        st.container(key="gd-dark").markdown("")  # marker only; styled via :has()


def footer() -> None:
    render(f'<div class="gd-core"><b>{esc(CORE_RULE)}</b><br>{esc(SYNTHETIC)} Not a credit decision. '
           'Every impact figure is an estimate, not a guarantee.</div>')


# Plotly colours for charts on the dark Cockpit (charts do not read CSS variables).
DARK = {"text": "rgba(255,255,255,0.94)", "muted": "rgba(255,255,255,0.68)", "grid": "rgba(255,255,255,0.12)",
        "plot": "#0C1D16", "background": "#06110D"}


def banner(text: str, kind: str = "") -> None:
    cls = {"warn": " gd-banner--warn", "info": " gd-banner--info", "ok": " gd-banner--ok", "err": " gd-banner--err"}.get(kind, "")
    render(f'<div class="gd-banner{cls}">{icon("info", 16)}<span>{esc(text)}</span></div>')


# --------------------------------------------------------------------------- building blocks
def status_badge(status: str) -> str:
    cls, label, ic = STATUS[status]
    return f'<span class="gd-status gd-status--{cls}">{icon(ic, 16)}{esc(label)}</span>'


def meter(quality: str | None) -> str:
    on = QUALITY_STEPS.get(quality or "", 0)
    return '<span class="gd-meter" aria-hidden="true">' + "".join(f'<i class="{"on" if on >= i else ""}"></i>' for i in (1, 2, 3)) + "</span>"


def verdicts(opp: dict) -> str:
    """Three separate verdict badges. No combined score exists anywhere."""
    lk_cls, lk = LIKELIHOOD[opp["likelihood_band"]]
    el_cls, el = ELIGIBILITY[opp["eligibility"]["result"]]
    q = opp["impact"].get("quality")
    h = '<div class="gd-verdicts" role="group" aria-label="Three separate verdicts">'
    h += f'<div class="gd-verdict gd-v-{lk_cls}"><span class="gd-verdict__h">{icon("target", 14)}Likelihood</span><span class="gd-verdict__v">{lk}</span><span class="gd-verdict__s">ML model</span></div>'
    h += f'<div class="gd-verdict gd-v-{el_cls}"><span class="gd-verdict__h">{icon("clipboard", 14)}Eligibility</span><span class="gd-verdict__v">{el}</span><span class="gd-verdict__s">{esc(opp["eligibility"]["rules_version"])}</span></div>'
    if q:
        h += f'<div class="gd-verdict gd-v-impact"><span class="gd-verdict__h">{icon("gauge", 14)}Impact quality</span><span class="gd-verdict__v">{q.title()}{meter(q)}</span><span class="gd-verdict__s">carbon engine</span></div>'
    else:
        h += f'<div class="gd-verdict gd-v-na"><span class="gd-verdict__h">{icon("gauge", 14)}Impact quality</span><span class="gd-verdict__v">Not estimated</span><span class="gd-verdict__s">carbon engine</span></div>'
    return h + "</div>"


def range_bar(low, central, high, colour: str) -> str:
    lo_lim = max(0, low - (high - low) * 0.6)
    hi_lim = high * 1.15

    def pct(v):
        return (v - lo_lim) / (hi_lim - lo_lim) * 100

    return (f'<div class="gd-range" role="img" aria-label="Range {num(low)} to {num(high)}, central {num(central)}">'
            f'<div class="gd-range__t"><span class="gd-range__b" style="left:{pct(low):.1f}%;width:{pct(high) - pct(low):.1f}%;background:{colour}"></span>'
            f'<span class="gd-range__m" style="left:{pct(central):.1f}%;background:{colour}"></span></div>'
            f'<div class="gd-range__lbl"><span>Low {num(low)}</span><span>Central {num(central)}</span><span>High {num(high)}</span></div></div>')


def impact_block(opp: dict) -> str:
    im = opp["impact"]
    status = im["status"]
    if status == "ESTIMATED" and im.get("metric_family") == "paper":
        p, d = im.get("paper") or {}, im.get("digital_adoption") or {}
        return (f'<div class="gd-impact"><div class="gd-impact__l"><span>Paper and digital, reported separately</span><span class="gd-tag">Estimate</span></div>'
                f'<div class="gd-metrics"><div class="gd-metric"><span class="gd-small gd-muted"><i class="gd-dot" style="background:{C["aqua"]}"></i>Paper</span><div class="gd-metric__v">{num(p.get("sheets_per_year"))}</div><span class="gd-small gd-muted">sheets a year</span></div>'
                f'<div class="gd-metric"><span class="gd-small gd-muted"><i class="gd-dot" style="background:{C["iris"]}"></i>Digital adoption</span><div class="gd-metric__v">{esc(d.get("display"))}</div><span class="gd-small gd-muted">{esc(d.get("unit"))}</span></div></div>'
                '<p class="gd-small gd-muted" style="margin:8px 0 0">Digital adoption is tracked separately. No CO₂e figure is claimed for paperless.</p></div>')
    if status == "ESTIMATED" and im.get("low") is not None:
        h = (f'<div class="gd-impact"><div class="gd-impact__l"><span>Estimated yearly impact</span><span class="gd-tag">Estimate</span></div>'
             f'<p class="gd-impact__kpi">{num(im["low"])} to {num(im["high"])} <small>kg CO₂e a year</small></p>'
             f'<p class="gd-muted" style="margin:0">{esc(im.get("bills"))}</p>' + range_bar(im["low"], im["central"], im["high"], C["verdant"]))
        sec = im.get("secondary")
        if sec:
            h += (f'<p class="gd-small gd-muted" style="margin:12px 0 0;font-weight:600">Energy, reported separately</p>'
                  f'<p style="margin:2px 0;font-weight:600">{num(sec["low"])} to {num(sec["high"])} {esc(sec["unit"])}</p>' + range_bar(sec["low"], sec["central"], sec["high"], C["amber"]))
        if im.get("first_step"):
            h += f'<p style="margin:10px 0 0">{esc(im["first_step"])}</p>'
        return h + "</div>"
    if status == "INSUFFICIENT_DATA":
        missing = ", ".join(m.replace("_", " ") for m in im.get("missing_inputs") or [])
        return (f'<div class="gd-impact"><div class="gd-impact__l"><span>{icon("lock", 16)} Not enough information to estimate</span></div>'
                f'<p class="gd-muted" style="margin:8px 0 0">We need {esc(missing)} before we show a number. We never fill the gap with a made-up value.</p></div>')
    if status == "HIDDEN":
        return (f'<div class="gd-impact"><div class="gd-impact__l"><span>{icon("eye_off", 16)} Impact hidden for now</span></div>'
                '<p class="gd-muted" style="margin:8px 0 0">We\'ll show an estimate once the mixed signals are cleared up.</p></div>')
    return ""


def evidence(opp: dict) -> str:
    rows = opp.get("reason_codes") or []
    if not rows:
        return '<p class="gd-muted">No evidence rows for this card.</p>'
    out = '<ul class="gd-ev">'
    for r in rows:
        declared = r["source"] == "customer_declared"
        prov = (f'<span class="gd-prov gd-prov--declared">{icon("user", 14)}You told us</span>' if declared
                else f'<span class="gd-prov gd-prov--inferred">{icon("receipt", 14)}From your transactions</span>')
        out += (f'<li>{prov}<span class="gd-tag gd-tag--code">{esc(r["code"])}</span>'
                f'<div style="margin:6px 0 2px">{esc(r["display"])}</div><span class="gd-date">DATA AS OF {esc(r["observed_at"]).upper()}</span></li>')
    return out + "</ul>"


def claim_stamp(opp: dict) -> str:
    ex = opp["explanation"]
    n = len(ex["sentences"])
    if ex["source"] == "llm":
        return (f'<div class="gd-stamp">{icon("shield", 20)}<span>Every statement above was checked against our calculation engine.</span>'
                f'<span class="gd-stamp__n">{n} OF {n} VERIFIED</span></div>')
    return (f'<div class="gd-stamp gd-stamp--tpl">{icon("shield", 20)}<span>Standard summary: same facts, fixed wording, checked against our calculation engine.</span>'
            '<span class="gd-stamp__n" style="color:var(--ink-soft)">STANDARD</span></div>')


def why_not(opp: dict) -> str:
    w = opp.get("why_not")
    if not w:
        return ""
    return (f'<div class="gd-whynot"><b>{icon("shield", 18)} Why not?</b><p style="margin:6px 0">{esc(w["text"])}</p>'
            f'<p class="gd-small gd-muted" style="margin:0 0 6px">What would change this: {esc(w["change"])}</p>'
            f'<span class="gd-disc">Rule {esc(w["rule"])} · rules-1.0</span></div>')


def card_header(opp: dict, as_of: str = "30 JUN") -> str:
    icon_name = PATHWAY_ICON[opp["opportunity_id"]]
    h = f'<div class="gd-row gd-between">{status_badge(opp["status"])}<span class="gd-tag">As of {esc(as_of)}</span></div>'
    h += f'<div class="gd-pathway">{icon(icon_name, 18)}{esc(opp["opportunity_name"])}</div>'
    headline = opp["headline"] if opp["status"] != "RULED_OUT" else "Not for you right now."
    h += f'<h3 class="gd-headline">{esc(headline)}</h3>'
    if opp.get("why_now"):
        h += f'<span class="gd-chip gd-chip--why">{icon("clock", 16)}Why now: {esc(opp["why_now"]["display"])}</span>'
    return h


def accent_for(status: str) -> str:
    return {"RECOMMEND": C["verdant"], "ABSTAIN": C["warning"], "REVIEW": C["info"]}.get(status, "transparent")


def tile(opp: dict, selected: bool) -> str:
    quiet = opp["status"] in ("RULED_OUT", "SOFT_SURFACE")
    line = {"RECOMMEND": "Worth exploring: see the receipt", "REVIEW": "Mixed signals: one question", "ABSTAIN": "Need one detail to estimate",
            "SOFT_SURFACE": "Good to know", "RULED_OUT": "Not for you right now"}[opp["status"]]
    return (f'<div class="gd-tile{" is-on" if selected else ""}"><span class="gd-tile__i{" q" if quiet else ""}">{icon(PATHWAY_ICON[opp["opportunity_id"]], 22)}</span>'
            f'<span class="gd-tile__n">{esc(opp["opportunity_name"])}</span>{status_badge(opp["status"])}<span class="gd-small gd-muted">{line}</span></div>')


def kpi(tile_data: dict) -> str:
    fam = {"co2": C["verdant"], "energy": C["amber"], "paper": C["aqua"], "digital": C["iris"]}[tile_data["family"]]
    status = tile_data["status"]
    tag = {"estimate": '<span class="gd-tag">Estimate</span>', "realised": '<span class="gd-tag" style="color:var(--success-tx)">Realised</span>',
           "pending": '<span class="gd-tag">Pending</span>'}[status]
    if status == "pending":
        value = '<div class="gd-kpi__v" style="font-size:20px;color:#5F756B">Not yet measurable</div>'
    elif tile_data.get("low") is not None:
        value = (f'<div class="gd-kpi__v">{num(tile_data["central"])} <span class="gd-small gd-muted">{esc(tile_data["unit"])}</span></div>'
                 f'<div class="gd-small gd-muted">Range {num(tile_data["low"])} to {num(tile_data["high"])} · central estimate</div>')
    elif tile_data["family"] == "digital":
        value = f'<div class="gd-kpi__v">{tile_data["central"] * 100:.0f}% <span class="gd-small gd-muted">{esc(tile_data["unit"])}</span></div>'
    else:
        value = f'<div class="gd-kpi__v">{num(tile_data["central"])} <span class="gd-small gd-muted">{esc(tile_data["unit"])}</span></div>'
    return (f'<div class="gd-kpi{" est" if status == "estimate" else ""}" style="--fam:{fam}"><div class="gd-row gd-between">'
            f'<span style="font-weight:600;color:var(--ink-soft);font-size:13px"><i class="gd-dot" style="background:{fam}"></i>{esc(tile_data["name"])}</span>{tag}</div>'
            f'{value}<p class="gd-small gd-muted" style="margin:6px 0 0">{esc(tile_data["note"])}</p></div>')
