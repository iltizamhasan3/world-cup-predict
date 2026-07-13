"""Token visual dan CSS offline untuk meja analisis siaran."""

from __future__ import annotations

import base64
from pathlib import Path


def _font_uri(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def dashboard_css(project_root: Path) -> str:
    font_root = project_root / "assets" / "fonts"
    sans = _font_uri(font_root / "UbuntuSans.ttf")
    display = _font_uri(font_root / "Ubuntu.ttf")
    mono = _font_uri(font_root / "UbuntuMono.ttf")
    return f"""
<style>
@font-face {{
  font-family: 'WC Sans';
  src: url(data:font/ttf;base64,{sans}) format('truetype');
  font-display: swap;
}}
@font-face {{
  font-family: 'WC Display';
  src: url(data:font/ttf;base64,{display}) format('truetype');
  font-display: swap;
}}
@font-face {{
  font-family: 'WC Data';
  src: url(data:font/ttf;base64,{mono}) format('truetype');
  font-display: swap;
}}

:root {{
  --broadcast-navy: #071B33;
  --pitch-teal: #0A7C75;
  --signal-amber: #F4B942;
  --mist: #EAF1F5;
  --paper: #FCFEFF;
  --ink-muted: #526779;
  --line: #CAD7DF;
}}

html, body, [class*="css"] {{ font-family: 'WC Sans', sans-serif; }}
.stApp {{
  color: var(--broadcast-navy);
  background:
    linear-gradient(90deg, transparent 49.92%, rgba(10,124,117,.055) 50%, transparent 50.08%),
    linear-gradient(180deg, #f8fbfc 0%, var(--mist) 100%);
}}
[data-testid="stHeader"] {{ background: rgba(248,251,252,.88); }}
[data-testid="stSidebar"] {{
  background: var(--broadcast-navy);
  border-right: 1px solid rgba(255,255,255,.12);
}}
[data-testid="stSidebar"] * {{ color: #F4F8FA; }}
[data-testid="stSidebar"] [role="radiogroup"] label {{
  border-bottom: 1px solid rgba(255,255,255,.14);
  padding: .65rem .1rem;
}}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{ color: #CAD7DF; }}

h1, h2, h3 {{
  font-family: 'WC Display', sans-serif;
  color: var(--broadcast-navy);
  letter-spacing: -.025em;
}}
h1 {{ font-size: clamp(2.15rem, 5vw, 4.1rem) !important; line-height: .98 !important; }}
h2 {{ margin-top: 1.8rem !important; }}
p, li {{ line-height: 1.58; }}
code, [data-testid="stMetricValue"], .data-label {{ font-family: 'WC Data', monospace !important; }}

.broadcast-kicker {{
  color: var(--pitch-teal);
  font-family: 'WC Data', monospace;
  font-size: .78rem;
  font-weight: 700;
  letter-spacing: .16em;
  text-transform: uppercase;
  margin-bottom: .7rem;
}}
.broadcast-header {{
  border-top: 5px solid var(--signal-amber);
  border-bottom: 1px solid var(--line);
  padding: 1.2rem 0 1.35rem;
  margin-bottom: 1.3rem;
}}
.broadcast-header h1 {{ margin: 0; max-width: 14ch; }}
.broadcast-header p {{ color: var(--ink-muted); max-width: 68ch; margin: .7rem 0 0; }}

.match-strip {{
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: .9rem;
  padding: .95rem 1.1rem;
  background: var(--broadcast-navy);
  color: white;
  border-radius: 2px;
  box-shadow: 0 12px 30px rgba(7,27,51,.13);
}}
.match-strip .team:last-child {{ text-align: right; }}
.match-strip .team {{ font-family: 'WC Display'; font-size: clamp(1.2rem, 3vw, 2rem); font-weight: 650; }}
.match-strip .versus {{ color: var(--signal-amber); font-family: 'WC Data'; font-size: .82rem; letter-spacing: .12em; }}
.match-meta {{ color: var(--ink-muted); font-family: 'WC Data'; font-size: .8rem; margin: .65rem 0 1.3rem; }}

.team-panel {{
  min-height: 10rem;
  padding: 1rem;
  border-top: 3px solid var(--pitch-teal);
  background: rgba(252,254,255,.84);
  box-shadow: inset 0 0 0 1px var(--line);
}}
.team-panel.away {{ border-top-color: var(--signal-amber); text-align: right; }}
.team-panel .name {{ font-family: 'WC Display'; font-size: 1.45rem; font-weight: 700; }}
.team-panel .number {{ font-family: 'WC Data'; font-size: 2.15rem; line-height: 1.05; margin-top: .75rem; }}
.team-panel .label {{ color: var(--ink-muted); font-size: .78rem; text-transform: uppercase; letter-spacing: .09em; }}

.score-chip {{
  display: inline-flex;
  flex-direction: column;
  min-width: 6.2rem;
  padding: .62rem .75rem;
  margin: 0 .35rem .5rem 0;
  background: var(--paper);
  border-left: 3px solid var(--signal-amber);
  box-shadow: inset 0 0 0 1px var(--line);
}}
.score-chip strong {{ font-family: 'WC Data'; font-size: 1.15rem; }}
.score-chip span {{ color: var(--ink-muted); font-size: .75rem; }}
.section-rule {{ border-top: 1px solid var(--line); margin: 2rem 0 1rem; }}
.confidence-low {{ color: #8A4F0A; background: #FFF3D6; padding: .15rem .45rem; font-family: 'WC Data'; font-size: .75rem; }}

[data-testid="stMetric"] {{
  background: rgba(252,254,255,.78);
  border: 1px solid var(--line);
  border-radius: 2px;
  padding: .85rem 1rem;
}}
[data-testid="stMetricLabel"] {{ color: var(--ink-muted); }}
.stButton > button, .stDownloadButton > button {{ border-radius: 2px; }}
button:focus-visible, input:focus-visible, [role="radio"]:focus-visible,
[data-baseweb="select"]:focus-within {{
  outline: 3px solid var(--signal-amber) !important;
  outline-offset: 2px;
}}

@media (max-width: 760px) {{
  .match-strip {{ grid-template-columns: 1fr; text-align: left; }}
  .match-strip .team:last-child {{ text-align: left; }}
  .match-strip .versus {{ border-top: 1px solid rgba(255,255,255,.18); padding-top: .6rem; }}
  .team-panel, .team-panel.away {{ min-height: auto; text-align: left; }}
}}

@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ scroll-behavior: auto !important; transition: none !important; animation: none !important; }}
}}
</style>
"""

