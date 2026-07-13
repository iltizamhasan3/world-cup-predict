"""High-contrast Ferrari race-control styling for the Streamlit dashboard."""

from __future__ import annotations

import base64
from pathlib import Path


def _font_uri(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def dashboard_css(project_root: Path) -> str:
    font_root = project_root / "assets" / "fonts"
    sans = _font_uri(font_root / "UbuntuSans.ttf")
    mono = _font_uri(font_root / "UbuntuMono.ttf")
    return f"""
<style>
@font-face {{
  font-family: 'WC Sans';
  src: url(data:font/ttf;base64,{sans}) format('truetype');
  font-display: swap;
}}
@font-face {{
  font-family: 'WC Data';
  src: url(data:font/ttf;base64,{mono}) format('truetype');
  font-display: swap;
}}

:root {{
  --rosso: #da291c;
  --rosso-active: #b01e0a;
  --canvas-root: #101010;
  --canvas: #181818;
  --canvas-elevated: #262626;
  --canvas-raised: #303030;
  --ink: #f5f5f3;
  --body: #c7c7c5;
  --muted: #969694;
  --hairline: #3a3a38;
  --focus: #f6e500;
}}

/* Hard reset: Streamlit must never leak a light surface into race control. */
html, body, #root, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"] {{
  background: var(--canvas-root) !important;
  color: var(--ink) !important;
}}
html, body, [class*="css"] {{
  font-family: 'FerrariSans', 'WC Sans', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
}}
[data-testid="stMainBlockContainer"] {{
  max-width: 1440px !important;
  padding: 0 64px 96px !important;
}}
[data-testid="stHeader"] {{ height: 0 !important; background: transparent !important; }}
[data-testid="stToolbar"], [data-testid="stDecoration"], .stAppDeployButton,
[data-testid="manage-app-button"], #MainMenu, footer {{ display: none !important; }}
[data-testid="stSidebar"] {{ display: none; }}

h1, h2, h3 {{
  color: var(--ink) !important;
  font-family: 'FerrariSans', 'WC Sans', system-ui, sans-serif;
  font-weight: 500 !important;
  letter-spacing: -.015em;
}}
h1 {{ font-size: clamp(3.2rem, 7vw, 5.5rem) !important; line-height: .98 !important; }}
h2 {{ font-size: clamp(1.9rem, 4vw, 2.5rem) !important; margin-top: 72px !important; }}
h3 {{ font-size: 1.625rem !important; }}
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stCaptionContainer"],
[data-testid="stWidgetLabel"] p {{ color: var(--body) !important; line-height: 1.55; }}
[data-testid="stCaptionContainer"] {{ font-size: 13px; }}
code, .data-label, .spec-value, .telemetry-table {{ font-family: 'WC Data', monospace !important; }}
a {{ color: var(--ink); text-decoration-color: var(--rosso); text-underline-offset: 4px; }}
hr {{ border-color: var(--hairline) !important; }}

/* 64px control rail. */
.st-key-top-navigation {{
  min-height: 72px;
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: 32px;
  border-bottom: 1px solid var(--hairline);
  background: rgba(16,16,16,.97);
  position: sticky;
  top: 0;
  z-index: 999;
}}
.st-key-top-navigation > div {{ margin: 0 !important; }}
.st-key-top-navigation > [data-testid="stElementContainer"],
.st-key-match-selector > [data-testid="stElementContainer"] {{
  width: 100% !important;
  min-width: 0;
}}
.brand-lockup {{ display: flex; align-items: center; min-height: 72px; gap: 16px; }}
.brand-mark {{
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  background: var(--rosso);
  color: #fff;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: .08em;
}}
.brand-name, .brand-meta {{ color: var(--ink); font-size: 12px; font-weight: 700; letter-spacing: .1em; }}
.brand-meta {{ color: var(--muted); font-weight: 500; }}
.st-key-top-navigation [data-testid="stRadio"] {{ width: auto; }}
.st-key-top-navigation [role="radiogroup"] {{ flex-wrap: nowrap; gap: 0 !important; }}
.st-key-top-navigation [data-testid="stRadioOption"] > div > div > div:first-child {{
  display: none;
}}
.st-key-top-navigation [role="radiogroup"] label {{
  min-height: 72px;
  padding: 0 16px !important;
  border-bottom: 3px solid transparent;
  border-radius: 0 !important;
  color: var(--body) !important;
  text-transform: uppercase;
  letter-spacing: .065em;
  font-size: 13px;
  font-weight: 700;
}}
.st-key-top-navigation [role="radiogroup"] label p {{ color: inherit !important; }}
.st-key-top-navigation [role="radiogroup"] label:has(input:checked) {{
  border-bottom-color: var(--rosso);
  color: var(--ink) !important;
  background: #1b1b1b;
}}
.st-key-top-navigation [data-testid="stWidgetLabel"] {{ display: none; }}

/* Match selector is a segmented control, not a loose row of radio buttons. */
.st-key-match-selector {{ margin-top: 0; }}
.st-key-match-selector [data-testid="stRadio"] {{ width: 100%; }}
.st-key-match-selector [role="radiogroup"] {{
  display: grid !important;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 !important;
  width: 100%;
  border-bottom: 1px solid var(--hairline);
}}
.st-key-match-selector [data-testid="stRadioOption"] {{
  width: 100%;
  min-width: 0;
  min-height: 52px;
  justify-content: center;
  padding: 0 16px !important;
  border-right: 1px solid var(--hairline);
  border-radius: 0 !important;
  background: var(--canvas);
  color: var(--body) !important;
}}
.st-key-match-selector [data-testid="stRadioOption"]:last-child {{ border-right: 0; }}
.st-key-match-selector [data-testid="stRadioOption"] > div > div > div:first-child {{
  display: none;
}}
.st-key-match-selector [data-testid="stRadioOption"] p {{
  color: inherit !important;
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
}}
.st-key-match-selector [data-testid="stRadioOption"]:has(input:checked) {{
  box-shadow: inset 0 -4px 0 var(--rosso);
  background: var(--canvas-elevated);
  color: var(--ink) !important;
}}

/* Editorial opening. */
.broadcast-header {{
  position: relative;
  padding: 112px 0 72px;
  border-bottom: 1px solid var(--hairline);
  background:
    linear-gradient(105deg, rgba(218,41,28,.10), transparent 35%),
    repeating-linear-gradient(90deg, transparent 0, transparent 159px, rgba(255,255,255,.025) 160px);
  overflow: hidden;
}}
.broadcast-header::after {{
  content: '';
  position: absolute;
  right: 0;
  bottom: 0;
  width: 112px;
  height: 6px;
  background: var(--rosso);
}}
.broadcast-kicker {{
  color: var(--rosso) !important;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: .14em;
  text-transform: uppercase;
  margin-bottom: 24px;
}}
.broadcast-header h1 {{ max-width: 12ch; margin: 0; }}
.broadcast-header p {{ color: var(--body) !important; max-width: 68ch; margin: 28px 0 0; font-size: 17px; }}

/* Match timing board. */
.match-strip {{
  position: relative;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: end;
  gap: 32px;
  min-height: 240px;
  padding: 72px 0 36px;
  border-bottom: 1px solid var(--hairline);
  background: linear-gradient(115deg, rgba(255,255,255,.035), transparent 42%);
}}
.match-strip::before {{
  content: '';
  position: absolute;
  left: 50%;
  top: 32px;
  bottom: 32px;
  width: 2px;
  background: var(--rosso);
}}
.match-strip .team {{
  color: var(--ink);
  font-size: clamp(2.5rem, 6vw, 4.8rem);
  font-weight: 600;
  line-height: .95;
  letter-spacing: -.03em;
}}
.match-strip .team:last-child {{ text-align: right; }}
.match-strip .versus {{
  z-index: 1;
  padding: 9px 13px;
  background: var(--rosso);
  color: #fff;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: .1em;
  text-transform: uppercase;
}}
.match-meta {{
  color: var(--body);
  font-family: 'WC Data', monospace;
  font-size: 12px;
  letter-spacing: .04em;
  padding: 18px 0 48px;
  text-transform: uppercase;
}}

.team-panel {{
  min-height: 240px;
  padding: 32px 0;
  border-top: 1px solid var(--hairline);
  border-bottom: 1px solid var(--hairline);
}}
.team-panel.away {{ text-align: right; }}
.team-panel .name {{ color: var(--ink); font-size: 18px; font-weight: 800; }}
.team-panel .number {{
  color: var(--ink);
  font-family: 'WC Data', monospace;
  font-size: clamp(2.8rem, 5vw, 4.8rem);
  font-weight: 700;
  line-height: 1;
  margin-top: 24px;
}}
.team-panel.away .number {{ color: var(--rosso); }}
.team-panel .label {{
  color: var(--body);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .1em;
  margin-top: 8px;
  text-transform: uppercase;
}}
.score-chip {{
  display: inline-flex;
  flex-direction: column;
  min-width: 112px;
  padding: 16px;
  margin: 0 8px 8px 0;
  border: 1px solid var(--hairline);
  border-radius: 0;
  background: var(--canvas-elevated);
}}
.score-chip:first-child {{ border-left: 4px solid var(--rosso); }}
.score-chip strong {{ color: var(--ink); font-family: 'WC Data'; font-size: 18px; }}
.score-chip span {{ color: var(--body); font-size: 12px; margin-top: 4px; }}
.section-rule {{ border-top: 1px solid var(--hairline); margin: 72px 0 24px; }}
.confidence-low {{
  display: inline-block;
  color: #fff;
  background: var(--rosso);
  padding: 7px 12px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: .1em;
}}

/* Our own metric system: explicit contrast, no inherited Streamlit colors. */
.telemetry-spec-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  margin: 20px 0 32px;
  border-top: 1px solid var(--hairline);
  border-left: 1px solid var(--hairline);
  background: var(--canvas);
}}
.telemetry-spec {{
  min-width: 0;
  min-height: 150px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 12px;
  padding: 24px;
  border-right: 1px solid var(--hairline);
  border-bottom: 1px solid var(--hairline);
  background: linear-gradient(135deg, rgba(255,255,255,.022), transparent 58%);
}}
.telemetry-spec.is-accent {{ box-shadow: inset 0 4px 0 var(--rosso); }}
.spec-label {{
  color: var(--body);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: .11em;
  text-transform: uppercase;
}}
.spec-value {{
  display: block;
  color: var(--ink);
  font-size: clamp(1.65rem, 2.8vw, 2.65rem);
  font-weight: 700;
  line-height: 1;
  overflow-wrap: anywhere;
}}
.telemetry-spec.is-accent .spec-value {{ color: var(--rosso); }}
.spec-note {{ color: var(--muted); font-size: 12px; line-height: 1.35; }}

/* Controlled tables replace Streamlit's white canvas grid. */
.telemetry-table-wrap {{
  width: 100%;
  max-height: 560px;
  overflow: auto;
  border: 1px solid var(--hairline);
  background: var(--canvas);
  scrollbar-color: var(--rosso) var(--canvas-raised);
}}
.telemetry-table {{ width: 100%; border-collapse: collapse; font-size: 13px; white-space: nowrap; }}
.telemetry-table th {{
  position: sticky;
  top: 0;
  z-index: 2;
  padding: 15px 16px;
  border-right: 1px solid var(--hairline);
  border-bottom: 2px solid var(--rosso);
  background: var(--canvas-raised);
  color: var(--ink);
  text-align: left;
  font-family: 'WC Sans', sans-serif;
  font-size: 11px;
  letter-spacing: .09em;
  text-transform: uppercase;
}}
.telemetry-table td {{
  padding: 14px 16px;
  border-right: 1px solid #2d2d2b;
  border-bottom: 1px solid #2d2d2b;
  background: var(--canvas);
  color: var(--body);
}}
.telemetry-table tr:nth-child(even) td {{ background: #1d1d1d; }}
.telemetry-table tbody tr:hover td {{ background: #272727; color: var(--ink); }}
.table-overflow, .telemetry-empty {{
  padding: 12px 16px;
  border: 1px solid var(--hairline);
  border-top: 0;
  background: var(--canvas-elevated);
  color: var(--body);
  font-size: 12px;
}}

/* BaseWeb and residual Streamlit surfaces. */
[data-testid="stMetric"], [data-testid="stDataFrame"], [data-testid="stTable"] {{
  background: var(--canvas) !important;
  color: var(--ink) !important;
}}
[data-baseweb="select"] > div, [data-baseweb="input"] > div,
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {{
  min-height: 48px;
  border-color: var(--hairline) !important;
  border-radius: 0 !important;
  background: var(--canvas-elevated) !important;
  color: var(--ink) !important;
  caret-color: var(--rosso) !important;
  -webkit-text-fill-color: var(--ink) !important;
}}
input::placeholder, textarea::placeholder {{ color: var(--muted) !important; opacity: 1; }}
[data-baseweb="select"] *, [data-baseweb="input"] * {{ color: var(--ink) !important; }}

/* Multiselect owns its internal search input; never inflate it like a text field. */
[data-testid="stMultiSelect"] [data-baseweb="select"] > div {{
  min-height: 56px;
  height: auto;
  align-items: flex-start;
  padding: 7px 8px;
}}
[data-testid="stMultiSelect"] [data-baseweb="select"] > div > div:first-child {{
  min-width: 0;
  flex-wrap: wrap;
  gap: 4px;
  overflow: visible;
}}
[data-testid="stMultiSelect"] [data-baseweb="tag"] {{
  flex: 0 0 auto;
  max-width: 100%;
  margin: 0;
}}
[data-testid="stMultiSelect"] input[role="combobox"] {{
  width: 12px !important;
  min-width: 12px !important;
  min-height: 28px !important;
  height: 28px !important;
  padding: 0 !important;
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}}
[data-baseweb="popover"], [role="listbox"], [role="option"] {{
  background: var(--canvas-elevated) !important;
  color: var(--ink) !important;
}}
[role="option"]:hover, [aria-selected="true"][role="option"] {{ background: var(--canvas-raised) !important; }}
[data-testid="stRadio"] [role="radiogroup"] label {{ color: var(--body) !important; }}
[data-testid="stRadio"] [role="radiogroup"] label p {{ color: inherit !important; }}
[data-testid="stExpander"] {{
  border: 1px solid var(--hairline) !important;
  border-radius: 0 !important;
  background: var(--canvas) !important;
}}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary p {{ color: var(--ink) !important; }}
[data-testid="stAlert"] {{
  border-radius: 0 !important;
  border: 1px solid var(--hairline) !important;
  border-left: 4px solid var(--rosso) !important;
  background: var(--canvas-elevated) !important;
  color: var(--ink) !important;
}}
[data-testid="stAlert"] p, [data-testid="stAlert"] div {{ color: var(--ink) !important; }}
.stButton > button, .stDownloadButton > button {{
  min-height: 48px;
  border: 1px solid var(--ink);
  border-radius: 0;
  background: transparent;
  color: var(--ink);
  font-size: 13px;
  font-weight: 800;
  letter-spacing: .1em;
  text-transform: uppercase;
}}
.stButton > button:hover {{ border-color: var(--rosso); color: #fff; background: var(--rosso); }}
button:focus-visible, input:focus-visible, [role="radio"]:focus-visible,
[data-baseweb="select"]:focus-within, .telemetry-table-wrap:focus-visible {{
  outline: 3px solid var(--focus) !important;
  outline-offset: 2px;
}}
[data-testid="stRadioOption"]:has(input:focus-visible) {{
  outline: 3px solid var(--focus) !important;
  outline-offset: -3px;
}}

.site-footer {{
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 24px;
  align-items: center;
  margin-top: 112px;
  padding: 48px 0 64px;
  border-top: 1px solid var(--hairline);
  color: var(--body);
  font-size: 11px;
  letter-spacing: .08em;
  text-transform: uppercase;
}}
.site-footer span:nth-child(2) {{ text-align: center; }}
.site-footer span:last-child {{ text-align: right; }}

@media (max-width: 900px) {{
  [data-testid="stMainBlockContainer"] {{ padding: 0 24px 64px !important; }}
  .st-key-top-navigation {{ position: static; grid-template-columns: 1fr; gap: 0; }}
  .brand-lockup {{ border-bottom: 1px solid var(--hairline); }}
  .st-key-top-navigation [role="radiogroup"] {{ overflow-x: auto; }}
  .st-key-top-navigation [role="radiogroup"] label {{
    min-height: 52px;
    flex: 0 0 auto;
    padding: 0 12px !important;
    white-space: nowrap !important;
  }}
  .st-key-top-navigation [role="radiogroup"] label p {{ white-space: nowrap !important; }}
  .broadcast-header {{ padding: 72px 0 56px; }}
  .match-strip {{ min-height: 0; grid-template-columns: 1fr; align-items: start; padding: 56px 0 36px; }}
  .match-strip::before {{ left: 0; top: 24px; bottom: 24px; }}
  .match-strip .team, .match-strip .team:last-child {{ padding-left: 24px; text-align: left; }}
  .match-strip .versus {{ justify-self: start; margin-left: 24px; }}
  .team-panel, .team-panel.away {{ min-height: auto; text-align: left; }}
  .telemetry-spec-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
  .site-footer {{ grid-template-columns: 1fr; }}
  .site-footer span:nth-child(2), .site-footer span:last-child {{ text-align: left; }}
}}

@media (max-width: 520px) {{
  [data-testid="stMainBlockContainer"] {{ padding: 0 16px 48px !important; }}
  .brand-meta {{ display: none; }}
  .brand-name {{ font-size: 11px; }}
  .brand-lockup {{ min-height: 64px; }}
  .st-key-top-navigation [data-testid="stRadio"] {{ width: 100%; }}
  .st-key-top-navigation [role="radiogroup"] {{
    display: grid !important;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    width: 100%;
    overflow: visible;
  }}
  .st-key-top-navigation [role="radiogroup"] label {{
    width: 100%;
    min-width: 0;
    min-height: 44px;
    justify-content: center;
    padding: 0 10px !important;
    border-right: 1px solid var(--hairline);
    font-size: 11px;
    letter-spacing: .05em;
  }}
  .st-key-top-navigation [role="radiogroup"] label:nth-child(even) {{ border-right: 0; }}
  .broadcast-header h1 {{ font-size: 2.7rem !important; }}
  .broadcast-header p {{ font-size: 15px; }}
  .match-strip .team {{ font-size: 2.5rem; }}
  .telemetry-spec-grid {{ grid-template-columns: 1fr 1fr; }}
  .telemetry-spec {{ min-height: 132px; padding: 18px; }}
  .spec-value {{ font-size: 1.6rem; }}
}}

@media (max-width: 380px) {{
  .st-key-match-selector [role="radiogroup"] {{ grid-template-columns: 1fr; }}
  .st-key-match-selector [data-testid="stRadioOption"] {{
    border-right: 0;
    border-bottom: 1px solid var(--hairline);
  }}
  .st-key-match-selector [data-testid="stRadioOption"]:last-child {{ border-bottom: 0; }}
}}

@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ scroll-behavior: auto !important; transition: none !important; animation: none !important; }}
}}
</style>
"""
