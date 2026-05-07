#!/usr/bin/env python3
"""
AI Signal - Daily Briefing Renderer
Claude Code Routine fetches the news and writes briefing_data.json.
This script just renders it to HTML and saves it.
No API calls, no CLI calls, no external dependencies.
"""

import os
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

def load_data() -> dict:
    data_path = Path(__file__).parent / "briefing_data.json"
    if not data_path.exists():
        raise FileNotFoundError("briefing_data.json not found — Claude should write this first")
    with open(data_path) as f:
        return json.load(f)

CATEGORY_COLORS = {
    "models": "#3b82f6", "business": "#f59e0b", "policy": "#ef4444",
    "jobs": "#10b981", "tools": "#8b5cf6", "langgraph": "#06b6d4", "python": "#eab308",
}
SIGNAL_STYLES = {
    "bullish": {"bg": "#0d2b1a", "border": "#1a5c35", "color": "#4ade80", "dot": "#22c55e"},
    "bearish": {"bg": "#2b0d0d", "border": "#5c1a1a", "color": "#f87171", "dot": "#ef4444"},
    "neutral":  {"bg": "#1a1a2b", "border": "#35355c", "color": "#a78bfa", "dot": "#8b5cf6"},
}

def badge(cat):
    c = CATEGORY_COLORS.get(cat, "#888")
    return f'<span style="background:{c}22;color:{c};font-size:10px;font-weight:700;padding:2px 9px;border-radius:10px;font-family:monospace;text-transform:uppercase;">{cat}</span>'

def signal_pill(sig):
    s = SIGNAL_STYLES.get(sig, SIGNAL_STYLES["neutral"])
    return (f'<span style="display:inline-flex;align-items:center;gap:5px;background:{s["bg"]};border:1px solid {s["border"]};color:{s["color"]};font-size:11px;font-weight:700;padding:3px 10px;border-radius:20px;font-family:monospace;">'
            f'<span style="width:6px;height:6px;border-radius:50%;background:{s["dot"]};display:inline-block;"></span>{sig.upper()}</span>')

def render_story(s):
    cc = CATEGORY_COLORS.get(s.get("category",""), "#888")
    tags = " ".join(f'<span style="color:#444;font-size:10px;font-family:monospace;">#{t}</span>' for t in s.get("tags",[]))
    deeper = "".join(f'<div style="display:flex;gap:8px;margin-bottom:5px;"><span style="color:#e8f63c;font-family:monospace;flex-shrink:0;">→</span><span style="color:#ccc;font-size:13px;">{q}</span></div>' for q in s.get("dig_deeper",[]))
    return f"""<div style="background:#111;border:1px solid #1e1e1e;border-left:3px solid {cc};border-radius:14px;padding:22px;margin-bottom:14px;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;flex-wrap:wrap;gap:8px;"><div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center;">{badge(s.get('category',''))} {tags}</div>{signal_pill(s.get('signal','neutral'))}</div>
  <h3 style="color:#f0f0f0;font-size:16px;font-weight:700;margin:0 0 8px;font-family:Georgia,serif;line-height:1.4;">{s.get('title','')}</h3>
  <p style="color:#888;font-size:13px;line-height:1.65;margin:0 0 12px;">{s.get('summary','')}</p>
  <div style="background:#0a1a0f;border:1px solid #1a3826;border-radius:8px;padding:10px 14px;margin-bottom:12px;"><div style="color:#4ade80;font-size:9px;font-family:monospace;font-weight:700;margin-bottom:4px;">⚡ WHY IT MATTERS</div><p style="color:#a7d9b4;font-size:12.5px;line-height:1.6;margin:0;">{s.get('why_it_matters','')}</p></div>
  <div style="color:#e8f63c;font-size:9px;font-family:monospace;font-weight:700;margin-bottom:6px;">🔍 DIG DEEPER</div>{deeper}
</div>"""

def render_concept(concept, color, label):
    import html as hl
    code = hl.escape(concept.get("code",""))
    code_color = "#86efac" if label == "LANGGRAPH" else "#fde68a"
    return f"""<div style="background:#0d0d0d;border:1px solid #1e1e1e;border-left:3px solid {color};border-radius:14px;padding:20px;margin-bottom:12px;">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;"><span style="background:{color}22;color:{color};font-size:10px;font-weight:700;padding:2px 9px;border-radius:10px;font-family:monospace;text-transform:uppercase;">{label}</span><span style="color:#333;font-size:9px;font-family:monospace;">CONCEPT OF THE DAY</span></div>
  <h3 style="color:#f0f0f0;font-size:15px;font-weight:700;margin:0 0 10px;font-family:Georgia,serif;">{concept.get('topic','')}</h3>
  <p style="color:#888;font-size:13px;line-height:1.7;margin:0 0 10px;">{concept.get('explanation','')}</p>
  <div style="background:#111;border:1px solid #222;border-radius:8px;padding:10px 14px;margin-bottom:10px;"><div style="color:#e8f63c;font-size:9px;font-family:monospace;font-weight:700;margin-bottom:4px;">💡 ANALOGY</div><p style="color:#d4d4a8;font-size:12.5px;line-height:1.6;margin:0;font-style:italic;">{concept.get('analogy','')}</p></div>
  <div style="background:#070f07;border:1px solid #1a2a1a;border-radius:8px;padding:12px 14px;"><div style="color:#4ade80;font-size:9px;font-family:monospace;font-weight:700;margin-bottom:6px;">👨‍💻 CODE</div><pre style="margin:0;overflow-x:auto;"><code style="font-family:'Courier New',monospace;font-size:11.5px;line-height:1.7;color:{code_color};white-space:pre;">{code}</code></pre></div>
</div>"""

def build_html(data):
    import html as hl
    stories_html = "".join(render_story(s) for s in data.get("stories",[]))
    learn = data.get("learn", {})
    py_html = render_concept(learn.get("python_concept",{}), "#eab308", "PYTHON")
    lg_html = render_concept(learn.get("langgraph_concept",{}), "#06b6d4", "LANGGRAPH")
    ch = learn.get("challenge", {})
    dd = learn.get("deep_dive", {})
    wotd = data.get("word_of_the_day", {})
    starter = hl.escape(ch.get("starter_code",""))
    ch_color = "#06b6d4" if ch.get("which") == "langgraph" else "#eab308"
    deep_link = (f'<a href="{dd.get("url","")}" style="color:#c4b5fd;text-decoration:underline;">{dd.get("title","")}</a>' if dd.get("url") else f'<span style="color:#c4b5fd;">{dd.get("title","")}</span>')

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>AI Signal – {data.get('date','')}</title></head>
<body style="margin:0;padding:0;background:#080808;font-family:'Helvetica Neue',Arial,sans-serif;">
<div style="max-width:660px;margin:0 auto;padding:24px;">
<div style="border-bottom:1px solid #161616;padding-bottom:14px;margin-bottom:18px;">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;"><span style="color:#e8f63c;font-size:10px;font-weight:700;font-family:monospace;letter-spacing:0.12em;">AI SIGNAL</span><span style="width:4px;height:4px;background:#e8f63c;border-radius:50%;display:inline-block;"></span><span style="color:#252525;font-size:10px;font-family:monospace;">{data.get('date','')}</span></div>
  <h1 style="color:#f0f0f0;font-size:20px;font-weight:900;font-family:Georgia,serif;margin:0;line-height:1.3;">{data.get('headline','')}</h1>
</div>
<div style="background:#0d1520;border:1px solid #1a2d40;border-radius:10px;padding:12px 16px;margin-bottom:18px;">
  <span style="color:#3b82f6;font-size:9px;font-family:monospace;font-weight:700;">TERM OF THE DAY  </span><span style="color:#93c5fd;font-size:12px;font-weight:700;font-family:monospace;">{wotd.get('term','')}</span><span style="color:#374151;font-size:11px;margin-left:8px;">— {wotd.get('definition','')}</span>
</div>
<div style="background:#0a1a0f;border:1px solid #1a3826;border-radius:12px;padding:14px 18px;margin-bottom:20px;">
  <div style="color:#4ade80;font-size:9px;font-weight:700;font-family:monospace;margin-bottom:5px;">🌐 THE BIG PICTURE</div>
  <p style="color:#a7d9b4;font-size:13px;line-height:1.65;margin:0;">{data.get('big_picture','')}</p>
</div>
{stories_html}
<div style="border-top:2px solid #161616;padding-top:20px;margin-top:24px;margin-bottom:16px;">
  <span style="color:#e8f63c;font-size:12px;font-weight:700;font-family:monospace;letter-spacing:0.1em;">📚 LEARN</span>
  <span style="color:#1a1a1a;font-size:10px;font-family:monospace;margin-left:10px;">PYTHON + LANGGRAPH · BEGINNER</span>
</div>
{py_html}{lg_html}
<div style="background:#0d0d0d;border:1px solid #1e1e1e;border-left:3px solid #f59e0b;border-radius:14px;padding:20px;margin-bottom:12px;">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;flex-wrap:wrap;"><span style="background:#f59e0b22;color:#f59e0b;font-size:10px;font-weight:700;padding:2px 9px;border-radius:10px;font-family:monospace;text-transform:uppercase;">challenge</span><span style="background:{ch_color}22;color:{ch_color};font-size:10px;font-weight:700;padding:2px 9px;border-radius:10px;font-family:monospace;text-transform:uppercase;">{ch.get('which','python')}</span><span style="color:#333;font-size:9px;font-family:monospace;">~20-30 MIN</span></div>
  <h3 style="color:#f0f0f0;font-size:15px;font-weight:700;margin:0 0 10px;font-family:Georgia,serif;">{ch.get('title','')}</h3>
  <p style="color:#888;font-size:13px;line-height:1.7;margin:0 0 10px;">{ch.get('description','')}</p>
  <div style="background:#111;border:1px solid #2a2010;border-radius:8px;padding:10px 14px;margin-bottom:10px;"><div style="color:#f59e0b;font-size:9px;font-family:monospace;font-weight:700;margin-bottom:4px;">🔑 HINT</div><p style="color:#fcd38d;font-size:12.5px;line-height:1.6;margin:0;">{ch.get('hint','')}</p></div>
  <div style="background:#0f0d07;border:1px solid #2a2010;border-radius:8px;padding:12px 14px;"><div style="color:#f59e0b;font-size:9px;font-family:monospace;font-weight:700;margin-bottom:6px;">🚀 STARTER CODE</div><pre style="margin:0;"><code style="font-family:'Courier New',monospace;font-size:11.5px;line-height:1.7;color:#fde68a;white-space:pre;">{starter}</code></pre></div>
</div>
<div style="background:#0d0d0d;border:1px solid #1e1e1e;border-left:3px solid #8b5cf6;border-radius:14px;padding:20px;">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;"><span style="background:#8b5cf622;color:#8b5cf6;font-size:10px;font-weight:700;padding:2px 9px;border-radius:10px;font-family:monospace;text-transform:uppercase;">deep dive</span><span style="color:#333;font-size:9px;font-family:monospace;">{dd.get('source','')} · {dd.get('time_to_read','')}</span></div>
  <h3 style="color:#f0f0f0;font-size:15px;font-weight:700;margin:0 0 8px;font-family:Georgia,serif;">{deep_link}</h3>
  <p style="color:#888;font-size:13px;line-height:1.7;margin:0;">{dd.get('what_youll_learn','')}</p>
</div>
<p style="color:#141414;font-size:9px;font-family:monospace;text-align:center;margin-top:24px;">AI SIGNAL · {data.get('date','').upper()}</p>
</div></body></html>"""

def main():
    log.info("Loading briefing data...")
    data = load_data()
    log.info(f"Loaded {len(data.get('stories',[]))} stories")
    html = build_html(data)
    out = Path(__file__).parent / f"briefing_{datetime.now().strftime('%Y%m%d')}.html"
    out.write_text(html)
    log.info(f"Saved → {out} ({len(html):,} bytes)")

if __name__ == "__main__":
    main()