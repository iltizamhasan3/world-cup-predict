"""Ferrari-inspired tokens adapted to a local football telemetry dashboard."""

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
  --canvas: #181818;
  --canvas-elevated: #303030;
  --canvas-light: #ffffff;
  --surface-soft: #f7f7f7;
  --ink: #ffffff;
  --body: #969696;
  --muted: #666666;
  --hairline: #303030;
  --hairline-light: #d2d2d2;
  --focus: #f6e500;
  --info: #4c98b9;
}}

html, body, [class*="css"] {{
  font-family: 'FerrariSans', 'WC Sans', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
}}
.stApp {{ color: var(--ink); background: var(--canvas); }}
[data-testid="stHeader"] {{ background: rgba(24,24,24,.94); }}
[data-testid="stToolbar"] {{ color: var(--ink); }}
[data-testid="stAppViewContainer"] > .main .block-container {{
  max-width: 1280px;
  padding: 0 48px 96px;
}}
[data-testid="stSidebar"] {{ display: none; }}

h1, h2, h3 {{
  color: var(--ink);
  font-family: 'FerrariSans', 'WC Sans', system-ui, sans-serif;
  font-weight: 500 !important;
  letter-spacing: -0.01em;
}}
h1 {{ font-size: clamp(3.1rem, 7vw, 5rem) !important; line-height: 1.05 !important; }}
h2 {{ font-size: clamp(2rem, 4vw, 2.25rem) !important; margin-top: 64px !important; }}
h3 {{ font-size: 1.625rem !important; }}
p, li, [data-testid="stCaptionContainer"] {{ color: var(--body); line-height: 1.5; }}
code, [data-testid="stMetricValue"], .data-label {{ font-family: 'WC Data', monospace !important; }}
a {{ color: var(--ink); text-decoration-color: var(--rosso); text-underline-offset: 4px; }}
hr {{ border-color: var(--hairline) !important; }}

/* Top navigation: the 64px dark precision bar from DESIGN.md. */
.st-key-top-navigation {{
  min-height: 64px;
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: 32px;
  border-bottom: 1px solid var(--hairline);
  background: var(--canvas);
  position: sticky;
  top: 0;
  z-index: 999;
}}
.st-key-top-navigation > div {{ margin: 0 !important; }}
.brand-lockup {{ display: flex; align-items: center; min-height: 64px; gap: 16px; }}
.brand-mark {{
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  background: var(--rosso);
  color: var(--ink);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: .08em;
}}
.brand-name, .brand-meta {{ font-size: 12px; font-weight: 600; letter-spacing: .1em; }}
.brand-meta {{ color: var(--body); font-weight: 400; }}
.st-key-top-navigation [data-testid="stRadio"] {{ width: auto; }}
.st-key-top-navigation [role="radiogroup"] {{ flex-wrap: nowrap; gap: 0 !important; }}
.st-key-top-navigation [role="radiogroup"] label {{
  min-height: 64px;
  padding: 0 16px !important;
  border-bottom: 3px solid transparent;
  border-radius: 0 !important;
  text-transform: uppercase;
  letter-spacing: .065em;
  font-size: 13px;
  font-weight: 600;
}}
.st-key-top-navigation [role="radiogroup"] label:has(input:checked) {{
  border-bottom-color: var(--rosso);
  background: transparent;
}}
.st-key-top-navigation [data-testid="stWidgetLabel"] {{ display: none; }}

/* Cinematic editorial opening; actual match telemetry replaces licensed photography. */
.broadcast-header {{
  position: relative;
  padding: 96px 0 64px;
  margin: 0;
  border-bottom: 1px solid var(--hairline);
  overflow: hidden;
}}
.broadcast-header::after {{
  content: '';
  position: absolute;
  right: 0;
  bottom: 0;
  width: 96px;
  height: 6px;
  background: var(--rosso);
}}
.broadcast-kicker {{
  color: var(--rosso);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: .1em;
  text-transform: uppercase;
  margin-bottom: 24px;
}}
.broadcast-header h1 {{ max-width: 12ch; margin: 0; }}
.broadcast-header p {{ max-width: 62ch; margin: 24px 0 0; font-size: 16px; }}

/* Match hero: one red timing line is the visual signature. */
.match-strip {{
  position: relative;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: end;
  gap: 32px;
  min-height: 220px;
  padding: 64px 0 32px;
  border-bottom: 1px solid var(--hairline);
  background:
    linear-gradient(115deg, rgba(255,255,255,.035), transparent 42%),
    var(--canvas);
}}
.match-strip::before {{
  content: '';
  position: absolute;
  left: 50%;
  top: 24px;
  bottom: 24px;
  width: 2px;
  background: var(--rosso);
}}
.match-strip .team {{
  color: var(--ink);
  font-size: clamp(2.5rem, 6vw, 4.5rem);
  font-weight: 500;
  line-height: 1;
  letter-spacing: -.02em;
}}
.match-strip .team:last-child {{ text-align: right; }}
.match-strip .versus {{
  z-index: 1;
  padding: 8px 12px;
  background: var(--rosso);
  color: var(--ink);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .1em;
  text-transform: uppercase;
}}
.match-meta {{
  color: var(--body);
  font-family: 'WC Data', monospace;
  font-size: 12px;
  letter-spacing: .04em;
  padding: 16px 0 48px;
  text-transform: uppercase;
}}

/* Sharp technical spec cells; no generic card shadows. */
.team-panel {{
  min-height: 240px;
  padding: 32px 0;
  border-top: 1px solid var(--hairline);
  border-bottom: 1px solid var(--hairline);
  background: transparent;
}}
.team-panel.away {{ text-align: right; }}
.team-panel .name {{ font-size: 18px; font-weight: 700; }}
.team-panel .number {{
  color: var(--ink);
  font-size: clamp(2.8rem, 5vw, 4.8rem);
  font-weight: 700;
  line-height: 1;
  letter-spacing: -.02em;
  margin-top: 24px;
}}
.team-panel.away .number {{ color: var(--rosso); }}
.team-panel .label {{
  color: var(--body);
  font-size: 11px;
  font-weight: 600;
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
.section-rule {{ border-top: 1px solid var(--hairline); margin: 64px 0 24px; }}
.confidence-low {{
  display: inline-block;
  color: var(--ink);
  background: var(--rosso);
  padding: 6px 12px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: .1em;
}}

[data-testid="stMetric"] {{
  min-height: 124px;
  padding: 24px 0;
  border-top: 1px solid var(--hairline);
  border-bottom: 1px solid var(--hairline);
  border-radius: 0;
  background: transparent;
}}
[data-testid="stMetricLabel"] {{ color: var(--body); font-size: 11px; letter-spacing: .08em; text-transform: uppercase; }}
[data-testid="stMetricValue"] {{ color: var(--ink); font-size: clamp(1.8rem, 4vw, 3rem); }}
[data-testid="stMetricDelta"] {{ color: var(--rosso); }}

/* Streamlit controls mapped to Ferrari's sharp form and button vocabulary. */
.stButton > button, .stDownloadButton > button {{
  min-height: 48px;
  border: 1px solid var(--ink);
  border-radius: 0;
  background: transparent;
  color: var(--ink);
  font-size: 14px;
  font-weight: 700;
  letter-spacing: .1em;
  text-transform: uppercase;
}}
.stButton > button[kind="primary"] {{ border-color: var(--rosso); background: var(--rosso); }}
[data-baseweb="select"] > div, [data-baseweb="input"] > div, .stTextInput input {{
  min-height: 48px;
  border-color: var(--hairline) !important;
  border-radius: 4px !important;
  background: var(--canvas) !important;
  color: var(--ink) !important;
}}
[data-baseweb="popover"], [role="listbox"] {{ background: var(--canvas-elevated) !important; }}
[data-testid="stRadio"] [role="radiogroup"] label {{
  border-radius: 0 !important;
}}
[data-testid="stDataFrame"], [data-testid="stTable"] {{ border: 1px solid var(--hairline); }}
[data-testid="stExpander"] {{ border: 1px solid var(--hairline); border-radius: 0; background: transparent; }}
[data-testid="stAlert"] {{ border-radius: 0; border-left-width: 4px; }}

button:focus-visible, input:focus-visible, [role="radio"]:focus-visible,
[data-baseweb="select"]:focus-within {{
  outline: 3px solid var(--focus) !important;
  outline-offset: 2px;
}}

.site-footer {{
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 24px;
  align-items: center;
  margin-top: 96px;
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
  [data-testid="stAppViewContainer"] > .main .block-container {{ padding: 0 24px 64px; }}
  .st-key-top-navigation {{ position: static; grid-template-columns: 1fr; gap: 0; }}
  .brand-lockup {{ border-bottom: 1px solid var(--hairline); }}
  .st-key-top-navigation [role="radiogroup"] {{ overflow-x: auto; }}
  .st-key-top-navigation [role="radiogroup"] label {{ min-height: 48px; padding: 0 12px !important; }}
  .broadcast-header {{ padding: 64px 0 48px; }}
  .match-strip {{ min-height: 0; grid-template-columns: 1fr; align-items: start; padding: 48px 0 32px; }}
  .match-strip::before {{ left: 0; top: 24px; bottom: 24px; }}
  .match-strip .team, .match-strip .team:last-child {{ padding-left: 24px; text-align: left; }}
  .match-strip .versus {{ justify-self: start; margin-left: 24px; }}
  .team-panel, .team-panel.away {{ min-height: auto; text-align: left; }}
  .site-footer {{ grid-template-columns: 1fr; }}
  .site-footer span:nth-child(2), .site-footer span:last-child {{ text-align: left; }}
}}

@media (max-width: 520px) {{
  .brand-meta {{ display: none; }}
  .brand-name {{ font-size: 11px; }}
  .broadcast-header h1 {{ font-size: 2.5rem !important; }}
  .match-strip .team {{ font-size: 2.4rem; }}
}}

@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ scroll-behavior: auto !important; transition: none !important; animation: none !important; }}
}}
</style>
"""
