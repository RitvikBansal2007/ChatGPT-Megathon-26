"""greendash design tokens for the Streamlit app.

Constants only. Source of truth: greendash brand guidelines v1.0 (§04, §05,
§08, §09). Light mode is the customer default; DARK holds the Cockpit tokens.

Every status and badge carries icon + text + colour. Colour is never the only
signal. Text colours (`fg`) are AA-checked against their own `bg` (>= 4.5:1);
borders and chart marks are >= 3:1 against the surface they sit on.

`icon` is a Material Symbols Rounded name (use as ":material/<icon>:" in
st.markdown / st.badge). `glyph` is a plain-text fallback for raw HTML.
Any text placed in HTML next to these tokens must be html.escape()'d first.
"""

from typing import Final

# --------------------------------------------------------------------------
# Core palette (light mode, customer apps)
# --------------------------------------------------------------------------
COLORS: Final[dict[str, str]] = {
    # brand / action
    "primary": "#19C37D",          # Verdant: CTA fill, verified state, CO2e series on dark
    "on_primary": "#06110D",       # Abyss: the ONLY text colour allowed on Verdant
    "primary_text": "#0F7A55",     # Canopy: green text/icons on light surfaces, links
    "primary_tint": "#DDF8EA",     # Dew: selected rows, RECOMMEND badge fill
    "brand_dark": "#0A3B2C",       # Deep Forest
    # surfaces
    "background": "#F1F8F4",       # Mist
    "surface": "#FFFFFF",          # Pure: opaque cards
    "surface_inset": "#E3EFE9",    # Fog: inset wells, zebra rows
    # text
    "text": "#0B1F18",             # Ink
    "muted": "#4A6358",            # Ink Soft
    # lines
    "border": "rgba(11,31,24,0.08)",
    "border_strong": "#6B8A7C",    # 3.5:1 on Mist, for inputs/meaningful outlines
    "focus": "#0F7A55",            # Canopy focus ring
    # semantic (text-safe shades; brand hue noted)
    "success": "#17744D",          # from #22A06B
    "warning": "#8A5A00",          # from #F59E0B
    "error": "#B4232A",            # from #E5484D; Claim-Check BLOCKED only, never a refusal
    "info": "#2F5FBF",             # from #4C8DFF
}

# Cockpit (dark mode) tokens. Brand hues are used as-is here: all pass on Abyss.
DARK: Final[dict[str, str]] = {
    "background": "#06110D",       # Abyss
    "surface": "#0C1D16",          # Night Moss
    "surface_inset": "#122A21",    # Deep Glass
    "text": "rgba(255,255,255,0.94)",
    "muted": "rgba(255,255,255,0.68)",
    "border": "rgba(255,255,255,0.16)",
    "primary": "#19C37D",
    "on_primary": "#06110D",
    "focus": "#7BE5B5",            # Mint Glow
}

# --------------------------------------------------------------------------
# Card statuses (§4.5). RULED_OUT is calm slate, never red.
# --------------------------------------------------------------------------
STATUS: Final[dict[str, dict[str, str]]] = {
    "RECOMMEND": {
        "label": "Worth exploring",
        "icon": "check_circle", "glyph": "✓",
        "bg": "#DDF8EA", "fg": "#0F7A55", "border": "#0F7A55",
        "css_class": "gd-status--recommend",
    },
    "SOFT_SURFACE": {
        "label": "Good to know",
        "icon": "lightbulb", "glyph": "💡",
        "bg": "#EEF3F0", "fg": "#4A6358", "border": "#6B8A7C",
        "css_class": "gd-status--soft",
    },
    "ABSTAIN": {
        "label": "Need one thing",
        "icon": "help", "glyph": "?",
        "bg": "#FEF3DC", "fg": "#8A5A00", "border": "#8A5A00",
        "css_class": "gd-status--abstain",
    },
    "REVIEW": {
        "label": "Mixed signals",
        "icon": "compare_arrows", "glyph": "⇄",
        "bg": "#EAF1FF", "fg": "#2F5FBF", "border": "#2F5FBF",
        "css_class": "gd-status--review",
    },
    "RULED_OUT": {
        "label": "Not for you, and here's why",
        "icon": "verified_user", "glyph": "🛡",
        "bg": "#F4F7F5", "fg": "#4E6B5E", "border": "#6B8A7C",
        "css_class": "gd-status--ruled-out",
    },
}

# --------------------------------------------------------------------------
# Verdict badges (§4.6). Three separate components; never merged or summed.
# Each family has its own glyph so they differ without colour.
# --------------------------------------------------------------------------
BADGES: Final[dict[str, dict]] = {
    "LIKELIHOOD": {
        "title": "Likelihood",
        "icon": "target", "glyph": "◎",
        "footnote": "Likelihood is not creditworthiness.",
        "values": {
            "HIGH":   {"label": "High",   "bg": "#DDF8EA", "fg": "#0F7A55", "border": "#0F7A55"},
            "MEDIUM": {"label": "Medium", "bg": "#FEF3DC", "fg": "#8A5A00", "border": "#8A5A00"},
            "LOW":    {"label": "Low",    "bg": "#EEF3F0", "fg": "#4A6358", "border": "#6B8A7C"},
        },
    },
    "ELIGIBILITY": {
        "title": "Eligibility",
        "icon": "assignment_turned_in", "glyph": "☑",
        "values": {
            "ELIGIBLE":           {"label": "Passed",             "bg": "#E3F5EC", "fg": "#17744D", "border": "#17744D"},
            "NEEDS_VERIFICATION": {"label": "Needs verification", "bg": "#FEF3DC", "fg": "#8A5A00", "border": "#8A5A00"},
            "NOT_ELIGIBLE":       {"label": "Not eligible",       "bg": "#EEF3F0", "fg": "#4A6358", "border": "#6B8A7C"},
        },
    },
    "IMPACT_QUALITY": {
        "title": "Impact quality",
        "icon": "speed", "glyph": "◔",
        # Same Aqua for all levels; the level is carried by the label and a
        # 3-step meter (`steps` lit), not by hue.
        "values": {
            "HIGH":   {"label": "High",   "steps": "3", "bg": "#E3F6F9", "fg": "#0E6B7A", "border": "#0E6B7A"},
            "MEDIUM": {"label": "Medium", "steps": "2", "bg": "#E3F6F9", "fg": "#0E6B7A", "border": "#0E6B7A"},
            "LOW":    {"label": "Low",    "steps": "1", "bg": "#E3F6F9", "fg": "#0E6B7A", "border": "#0E6B7A"},
        },
    },
}

# --------------------------------------------------------------------------
# Metric families (§4.2). Always shown separately, never summed or netted.
# chart = mark colour on light (>= 3:1 on Mist), text = label colour on light
# (>= 4.5:1), dark = brand hue for the Cockpit.
# --------------------------------------------------------------------------
METRICS: Final[dict[str, dict[str, str]]] = {
    "CO2E":    {"label": "CO₂e",             "unit": "kg CO₂e", "icon": "co2",
                "chart": "#0F7A55", "text": "#0F7A55", "dark": "#19C37D"},
    "ENERGY":  {"label": "Energy",           "unit": "kWh",     "icon": "bolt",
                "chart": "#B26F00", "text": "#8A5A00", "dark": "#F5B53D"},
    "PAPER":   {"label": "Paper",            "unit": "sheets",  "icon": "description",
                "chart": "#0E8A9C", "text": "#0E6B7A", "dark": "#22B8CF"},
    "DIGITAL": {"label": "Digital adoption", "unit": "%",       "icon": "smartphone",
                "chart": "#7462E8", "text": "#5B4BC4", "dark": "#8B7CF6"},
}
# Estimate vs realised is marked by pattern + label, not colour (§4.2).
ESTIMATE_STYLE: Final[dict[str, str]] = {"opacity": "0.55", "dash": "dash", "label": "Estimate"}
REALISED_STYLE: Final[dict[str, str]] = {"opacity": "1.0", "dash": "solid", "label": "Realised"}

# --------------------------------------------------------------------------
# Layout (§8.3, §9). 4px base grid.
# --------------------------------------------------------------------------
SPACING: Final[dict[str, int]] = {
    "xxs": 4, "xs": 8, "sm": 12, "md": 16, "lg": 24,
    "xl": 32, "xxl": 48, "page": 64, "hero": 80,
    "card_pad_mobile": 16, "card_pad_desktop": 24, "proof_card_pad": 20,
}

RADIUS: Final[dict[str, int]] = {
    "widget": 28, "card": 24, "modal": 28, "sheet": 32,
    "button": 14, "input": 14, "pill": 999, "table": 20,
    "tooltip": 12, "inset": 16,
}

FONT_SIZES: Final[dict[str, int]] = {   # mobile-first (§5.3); desktop in css()
    "display": 36, "h1": 28, "h2": 22, "h3": 18,
    "body_l": 16, "body": 14, "kpi": 36,
    "label": 12, "tag": 11,            # tag is mono uppercase; 11px is brand spec
    "input": 16,                       # prevents iOS zoom
}

TAP_TARGET: Final[int] = 44
MOBILE_WIDTH: Final[int] = 390


def css() -> str:
    """Return the one static <style> block. No arguments, no interpolation."""
    return """<style>
:root{
  --gd-primary:#19C37D;--gd-on-primary:#06110D;--gd-primary-text:#0F7A55;--gd-dew:#DDF8EA;
  --gd-bg:#F1F8F4;--gd-surface:#FFFFFF;--gd-inset:#E3EFE9;
  --gd-text:#0B1F18;--gd-muted:#4A6358;--gd-border:rgba(11,31,24,0.08);--gd-border-strong:#6B8A7C;
  --gd-focus:#0F7A55;
  --gd-font-body:Inter,"SF Pro Text",Roboto,system-ui,sans-serif;
  --gd-font-display:"Plus Jakarta Sans","SF Pro Display",system-ui,sans-serif;
  --gd-font-mono:"JetBrains Mono","SF Mono","Roboto Mono",ui-monospace,monospace;
  --gd-ease:cubic-bezier(0.2,0,0,1);
}

/* ---- page: mobile first (390px), 16px gutters ---- */
.block-container{padding:16px 16px 96px;max-width:1280px;}
body,.stApp{font-family:var(--gd-font-body);font-feature-settings:"tnum" 1,"cv11" 1;}

/* ---- focus + tap targets ---- */
a:focus-visible,button:focus-visible,[tabindex]:focus-visible,summary:focus-visible{
  outline:2px solid var(--gd-focus);outline-offset:2px;}
.stButton>button,.gd-tap,.gd-card summary{min-height:44px;min-width:44px;}
input,select,textarea{font-size:16px !important;}

/* ---- primary CTA: Verdant fill, Abyss text (never white) ---- */
.stButton>button[kind="primary"],[data-testid="stBaseButton-primary"]{
  background:var(--gd-primary);color:var(--gd-on-primary);border:0;border-radius:999px;
  font-weight:600;min-height:56px;width:100%;
  box-shadow:0 2px 8px rgba(11,31,24,0.06),0 0 16px rgba(25,195,125,0.25);}
.stButton>button[kind="primary"]:hover,[data-testid="stBaseButton-primary"]:hover{
  background:#0F7A55;color:#FFFFFF;}
.stButton>button[kind="secondary"],[data-testid="stBaseButton-secondary"]{
  border-radius:999px;border:1px solid var(--gd-border-strong);background:transparent;color:var(--gd-text);}

/* ---- cards (opaque first; glass only where supported) ---- */
.gd-card{position:relative;background:var(--gd-surface);color:var(--gd-text);
  border:1px solid var(--gd-border);border-radius:24px;padding:20px;margin:0 0 16px;
  box-shadow:0 8px 24px rgba(11,31,24,0.10);}
@supports ((backdrop-filter:blur(1px)) or (-webkit-backdrop-filter:blur(1px))){
  .gd-card{background:rgba(255,255,255,0.80);
    -webkit-backdrop-filter:blur(24px) saturate(160%);backdrop-filter:blur(24px) saturate(160%);
    border-color:#FFFFFF;box-shadow:inset 0 1px 0 rgba(255,255,255,0.30),0 0 0 1px rgba(11,31,24,0.06),0 8px 24px rgba(11,31,24,0.10);}
}
@media (prefers-reduced-transparency:reduce){
  .gd-card{background:var(--gd-surface);-webkit-backdrop-filter:none;backdrop-filter:none;}
}
.gd-card.gd-status--recommend{border-top:2px solid var(--gd-primary);}
.gd-card.gd-status--soft{box-shadow:0 2px 8px rgba(11,31,24,0.06);}
/* RULED_OUT: calm and quieter, but no opacity (opacity would break contrast) */
.gd-card.gd-status--ruled-out{background:#F4F7F5;box-shadow:none;border:1px solid var(--gd-border);}
.gd-card h3,.gd-headline{font-family:var(--gd-font-display);font-weight:600;font-size:18px;line-height:24px;margin:12px 0 8px;color:var(--gd-text);}
.gd-body{font-size:14px;line-height:20px;color:var(--gd-text);}
.gd-muted{color:var(--gd-muted);}
.gd-row{display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap;}

/* ---- status pill + badges: solid, never translucent ---- */
.gd-pill,.gd-badge{display:inline-flex;align-items:center;gap:8px;border-radius:999px;
  border:1px solid currentColor;font-size:12px;line-height:16px;font-weight:600;letter-spacing:.02em;padding:4px 12px;}
.gd-pill{min-height:28px;}
.gd-status--recommend .gd-pill,.gd-pill.gd-status--recommend{background:#DDF8EA;color:#0F7A55;}
.gd-status--soft .gd-pill,.gd-pill.gd-status--soft{background:#EEF3F0;color:#4A6358;border-color:#6B8A7C;}
.gd-status--abstain .gd-pill,.gd-pill.gd-status--abstain{background:#FEF3DC;color:#8A5A00;}
.gd-status--review .gd-pill,.gd-pill.gd-status--review{background:#EAF1FF;color:#2F5FBF;}
.gd-status--ruled-out .gd-pill,.gd-pill.gd-status--ruled-out{background:#EEF3F0;color:#4E6B5E;border-color:#6B8A7C;}

.gd-verdicts{display:grid;grid-template-columns:1fr;gap:8px;margin:16px 0;}
.gd-badge{min-height:44px;border-radius:14px;justify-content:flex-start;padding:8px 12px;}
.gd-badge .gd-badge-title{font-weight:500;}
.gd-badge--high{background:#DDF8EA;color:#0F7A55;}
.gd-badge--medium{background:#FEF3DC;color:#8A5A00;}
.gd-badge--low,.gd-badge--not-eligible{background:#EEF3F0;color:#4A6358;border-color:#6B8A7C;}
.gd-badge--eligible{background:#E3F5EC;color:#17744D;}
.gd-badge--needs-verification{background:#FEF3DC;color:#8A5A00;}
.gd-badge--impact{background:#E3F6F9;color:#0E6B7A;}
.gd-meter{display:inline-flex;gap:3px;margin-left:auto;}
.gd-meter i{display:block;width:10px;height:10px;border-radius:2px;border:1px solid #0E6B7A;}
.gd-meter i.on{background:#0E6B7A;}

/* ---- chips and tags ---- */
.gd-chip{display:inline-flex;align-items:center;gap:8px;border-radius:999px;padding:6px 12px;
  font-size:12px;line-height:16px;font-weight:600;background:#E3F6F9;color:#0E6B7A;}
.gd-tag{font-family:var(--gd-font-mono);font-weight:500;font-size:11px;line-height:16px;
  letter-spacing:.12em;text-transform:uppercase;color:var(--gd-muted);}
.gd-tag--boxed{border:1px solid var(--gd-border-strong);border-radius:999px;padding:2px 8px;}

/* ---- impact well + KPI ---- */
.gd-well{background:var(--gd-inset);border-radius:16px;padding:16px;margin:12px 0;}
.gd-kpi{font-family:var(--gd-font-display);font-weight:800;font-size:36px;line-height:40px;
  letter-spacing:-.02em;color:#0F7A55;font-variant-numeric:tabular-nums;}

/* ---- metric tiles: four families, always separate ---- */
.gd-metrics{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.gd-metric{background:var(--gd-surface);border:1px solid var(--gd-border);border-left:4px solid;border-radius:16px;padding:12px;}
.gd-metric .gd-metric-value{font-family:var(--gd-font-display);font-weight:800;font-size:24px;line-height:32px;font-variant-numeric:tabular-nums;color:var(--gd-text);}
.gd-metric--co2e{border-left-color:#0F7A55;}  .gd-metric--co2e .gd-metric-label{color:#0F7A55;}
.gd-metric--energy{border-left-color:#B26F00;}.gd-metric--energy .gd-metric-label{color:#8A5A00;}
.gd-metric--paper{border-left-color:#0E8A9C;} .gd-metric--paper .gd-metric-label{color:#0E6B7A;}
.gd-metric--digital{border-left-color:#7462E8;}.gd-metric--digital .gd-metric-label{color:#5B4BC4;}
.gd-metric--estimate{border-left-style:dashed;}

/* ---- Claim-Check stamp, disclaimers, banner ---- */
.gd-stamp{display:flex;gap:8px;align-items:flex-start;background:#E3F5EC;color:#17744D;
  border-radius:14px;padding:12px;font-size:12px;line-height:16px;font-weight:600;}
.gd-blocked{color:#B4232A;text-decoration:underline 1px;}
.gd-footnote{font-size:12px;line-height:16px;color:var(--gd-muted);margin-top:12px;}
.gd-banner{background:#0A3B2C;color:#FFFFFF;border-radius:14px;padding:8px 12px;
  font-size:12px;line-height:16px;font-weight:600;margin-bottom:16px;}
/* Clear Streamlit's fixed 60px top toolbar so the banner is visible.
   Higher specificity than the .block-container rules in the media queries. */
[data-testid="stMainBlockContainer"].block-container{padding-top:72px;}
/* Synthetic-data banner: a keyed st.container(key="gd_banner"), so the
   text is a normal widget and never sits inside raw HTML. Deep Forest pill. */
.st-key-gd_banner{display:inline-flex;width:auto !important;align-self:flex-start;
  background:#0A3B2C;border-radius:999px;padding:6px 16px;min-height:32px;justify-content:center;margin-bottom:8px;}
.st-key-gd_banner p,.st-key-gd_banner [data-testid="stMarkdownContainer"]{color:#FFFFFF;
  font-size:12px;line-height:16px;font-weight:600;letter-spacing:.02em;margin:0;}
.gd-link{color:#0F7A55;font-weight:600;text-decoration:underline;display:inline-flex;align-items:center;min-height:44px;}
.gd-actions{display:flex;flex-direction:column;gap:8px;margin-top:16px;}
.gd-feedback{display:flex;flex-wrap:wrap;gap:8px;}

/* ---- tablet and up ---- */
@media (min-width:600px){
  .block-container{padding:24px 24px 64px;}
  .gd-verdicts{grid-template-columns:repeat(3,1fr);}
  .gd-metrics{grid-template-columns:repeat(4,1fr);}
}
@media (min-width:1200px){
  .block-container{padding:32px;}
  .gd-card{padding:24px;}
  .gd-card h3,.gd-headline{font-size:20px;line-height:28px;}
  .gd-kpi{font-size:44px;line-height:48px;}
}

/* ---- motion ---- */
.gd-card,.gd-badge,.gd-pill,.stButton>button{transition:box-shadow 150ms var(--gd-ease),background-color 150ms var(--gd-ease);}
@media (prefers-reduced-motion:reduce){
  *{animation:none !important;transition-duration:0ms !important;scroll-behavior:auto !important;}
}
</style>"""
