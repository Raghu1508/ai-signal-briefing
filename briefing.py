#!/usr/bin/env python3
"""
AI Signal - Daily Morning Briefing
Runs inside Claude Code Routines — no API key needed.
Uses the `claude` CLI (already authenticated) to fetch news and generate briefing.
"""

import os
import html
import json
import subprocess
import logging
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

# Load .env from multiple locations — works locally and in Claude Code Routines
def _load_env():
    for env_path in [
        Path(__file__).parent / ".env",  # same folder as script
        Path("/root/.env"),               # Claude Code Routine root
        Path.home() / ".env",            # home directory
    ]:
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, val = line.partition("=")
                        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))
            break

_load_env()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), "briefing.log"))
    ]
)
log = logging.getLogger(__name__)

# ── Prompt ────────────────────────────────────────────────────────────────────

PROMPT = f"""Today is {datetime.now().strftime('%A, %B %d %Y')}.

Search the web for the latest AI news from today and this week, then return a daily briefing as a single JSON object.

CRITICAL: Return ONLY the JSON — no markdown fences, no preamble, no explanation.
Keep total JSON under 3000 tokens. Code snippets max 10 lines, no blank lines inside them.

JSON structure:
{{
  "date": "Month DD, YYYY",
  "headline": "punchy 8-10 word headline of today's biggest AI story",
  "stories": [
    {{
      "id": "s1",
      "category": "one of: models, business, policy, jobs, tools, langgraph, python",
      "title": "story headline",
      "summary": "2-3 sentence summary in plain English",
      "why_it_matters": "1-2 sentences on broader significance",
      "dig_deeper": ["3 specific questions worth exploring"],
      "signal": "bullish or bearish or neutral",
      "tags": ["tag1", "tag2"]
    }}
  ],
  "big_picture": "One paragraph connecting today's stories",
  "word_of_the_day": {{ "term": "one AI/ML term", "definition": "1 sentence plain English" }},
  "learn": {{
    "python_concept": {{
      "topic": "one beginner Python concept useful for AI work",
      "explanation": "2-3 sentences from scratch",
      "analogy": "1 plain-English analogy",
      "code": "8-10 lines, commented, runnable Python 3.10+, no blank lines"
    }},
    "langgraph_concept": {{
      "topic": "one beginner LangGraph concept",
      "explanation": "2-3 sentences from scratch, assume Python knowledge",
      "analogy": "1 plain-English analogy",
      "code": "8-10 lines, commented, pip install langgraph, no blank lines"
    }},
    "challenge": {{
      "title": "short challenge title",
      "which": "python or langgraph",
      "description": "2 sentences, achievable in 20-30 min",
      "hint": "one concrete hint",
      "starter_code": "4-6 lines with TODO comments"
    }},
    "deep_dive": {{
      "title": "real doc page or tutorial title",
      "source": "LangChain Docs / Real Python / etc",
      "url": "real URL or empty string",
      "what_youll_learn": "2 sentences",
      "time_to_read": "e.g. 15 min"
    }}
  }}
}}

Include exactly 5 stories. Always 1+ langgraph story and 1+ python story.
Always include BOTH python_concept and langgraph_concept — never omit either.
Use real, specific company names, model names, and numbers from today's news."""


# ── Fetch briefing via claude CLI ─────────────────────────────────────────────

def fetch_briefing() -> dict:
    """Call the claude CLI with web search enabled and parse the JSON response."""
    log.info("Calling claude CLI with web search...")

    # Try tool name variants — Claude Code Routines use "WebSearch" not "web_search"
    for tool_name, perm_mode in [
        ("WebSearch", "auto"),
        ("web_search", "auto"),
        ("WebSearch", "bypassPermissions"),
        ("web_search", "bypassPermissions"),
    ]:
        result = subprocess.run(
            [
                "claude",
                "--print",
                "--allowedTools", tool_name,
                "--permission-mode", perm_mode,
                "--output-format", "text",
                PROMPT
            ],
            capture_output=True,
            text=True,
            timeout=300
        )
        # If we got meaningful output, use it
        if result.returncode == 0 and len(result.stdout.strip()) > 200:
            log.info(f"claude CLI succeeded with tool={tool_name} mode={perm_mode}")
            break
        log.warning(f"claude CLI failed with tool={tool_name} mode={perm_mode}: {result.stderr[:100]}")

    if result.returncode != 0:
        raise RuntimeError(f"claude CLI failed (exit {result.returncode}): {result.stderr[:500]}")

    output = result.stdout.strip()
    if not output:
        raise ValueError("Empty response from claude CLI")

    log.info(f"Got {len(output)} chars from claude CLI")

    # Extract JSON — find the outermost { ... }
    start = output.find("{")
    end = output.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON found. Response start: {output[:300]}")

    data = json.loads(output[start:end])

    if "stories" not in data or not isinstance(data["stories"], list):
        raise ValueError("Missing or invalid 'stories' in response")

    log.info(f"Parsed {len(data['stories'])} stories successfully")
    return data


# ── HTML email renderer ───────────────────────────────────────────────────────

SIGNAL_STYLES = {
    "bullish": {"bg": "#0d2b1a", "border": "#1a5c35", "color": "#4ade80", "dot": "#22c55e"},
    "bearish": {"bg": "#2b0d0d", "border": "#5c1a1a", "color": "#f87171", "dot": "#ef4444"},
    "neutral":  {"bg": "#1a1a2b", "border": "#35355c", "color": "#a78bfa", "dot": "#8b5cf6"},
}
CATEGORY_COLORS = {
    "models": "#3b82f6", "business": "#f59e0b", "policy": "#ef4444",
    "jobs": "#10b981", "tools": "#8b5cf6", "langgraph": "#06b6d4", "python": "#eab308",
}

def signal_badge(signal: str) -> str:
    s = SIGNAL_STYLES.get(signal, SIGNAL_STYLES["neutral"])
    return (f'<span style="display:inline-flex;align-items:center;gap:5px;background:{s["bg"]};'
            f'border:1px solid {s["border"]};color:{s["color"]};font-size:11px;font-weight:700;'
            f'padding:3px 10px;border-radius:20px;letter-spacing:0.05em;font-family:monospace;">'
            f'<span style="width:6px;height:6px;border-radius:50%;background:{s["dot"]};display:inline-block;"></span>'
            f'{signal.upper()}</span>')

def category_pill(cat: str) -> str:
    color = CATEGORY_COLORS.get(cat, "#888")
    return (f'<span style="background:{color}22;color:{color};font-size:10px;font-weight:700;'
            f'padding:2px 9px;border-radius:10px;font-family:monospace;text-transform:uppercase;'
            f'letter-spacing:0.08em;">{cat.replace("_", " ")}</span>')

def render_story(story: dict, index: int) -> str:
    cat_color = CATEGORY_COLORS.get(story.get("category", ""), "#888")
    tags_html = " ".join(
        f'<span style="color:#555;font-size:10px;font-family:monospace;">#{t}</span>'
        for t in story.get("tags", [])
    )
    dig_html = "".join(
        f'<div style="display:flex;gap:8px;margin-bottom:6px;">'
        f'<span style="color:#e8f63c;font-family:monospace;flex-shrink:0;">→</span>'
        f'<span style="color:#ccc;font-size:13px;line-height:1.5;">{q}</span></div>'
        for q in story.get("dig_deeper", [])
    )
    return f"""
    <div style="background:#111;border:1px solid #222;border-left:3px solid {cat_color};
        border-radius:16px;padding:24px;margin-bottom:16px;">
        <div style="display:flex;justify-content:space-between;align-items:center;
            margin-bottom:10px;flex-wrap:wrap;gap:8px;">
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                {category_pill(story.get('category',''))}
                {tags_html}
            </div>
            {signal_badge(story.get('signal','neutral'))}
        </div>
        <h3 style="color:#f0f0f0;font-size:17px;font-weight:700;margin:0 0 10px;
            font-family:Georgia,serif;line-height:1.4;">{story.get('title','')}</h3>
        <p style="color:#aaa;font-size:13.5px;line-height:1.65;margin:0 0 14px;">
            {story.get('summary','')}</p>
        <div style="background:#0d1f14;border:1px solid #1a3826;border-radius:10px;
            padding:14px;margin-bottom:14px;">
            <div style="color:#4ade80;font-size:10px;font-weight:700;margin-bottom:6px;
                font-family:monospace;letter-spacing:0.08em;">⚡ WHY IT MATTERS</div>
            <p style="color:#c0e8c8;font-size:13px;line-height:1.6;margin:0;">
                {story.get('why_it_matters','')}</p>
        </div>
        <div style="color:#e8f63c;font-size:10px;font-weight:700;margin-bottom:8px;
            font-family:monospace;letter-spacing:0.08em;">🔍 DIG DEEPER</div>
        {dig_html}
    </div>"""


def render_concept_block(concept: dict, color: str, label: str) -> str:
    import html as html_lib
    code_escaped = html_lib.escape(concept.get("code", ""))
    code_color = "#86efac" if label == "LANGGRAPH" else "#fde68a"
    bg_code    = "#0a0f0a" if label == "LANGGRAPH" else "#0f0d07"
    border_code= "#1a2a1a" if label == "LANGGRAPH" else "#2a2010"
    return f"""
    <div style="background:#0d0d0d;border:1px solid #1e1e1e;border-left:3px solid {color};
        border-radius:14px;padding:22px;margin-bottom:16px;">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;">
            <span style="background:{color}22;color:{color};font-size:10px;font-weight:700;
                padding:2px 9px;border-radius:10px;font-family:monospace;text-transform:uppercase;
                letter-spacing:0.08em;">{label}</span>
            <span style="color:#555;font-size:10px;font-family:monospace;">CONCEPT OF THE DAY</span>
        </div>
        <h3 style="color:#f0f0f0;font-size:16px;font-weight:700;margin:0 0 12px;
            font-family:Georgia,serif;">{concept.get('topic','')}</h3>
        <p style="color:#aaa;font-size:13.5px;line-height:1.7;margin:0 0 10px;">
            {concept.get('explanation','')}</p>
        <div style="background:#111;border:1px solid #222;border-radius:8px;
            padding:12px 16px;margin-bottom:14px;">
            <div style="color:#e8f63c;font-size:10px;font-family:monospace;font-weight:700;
                margin-bottom:6px;">💡 ANALOGY</div>
            <p style="color:#d4d4a8;font-size:13px;line-height:1.6;margin:0;font-style:italic;">
                {concept.get('analogy','')}</p>
        </div>
        <div style="background:{bg_code};border:1px solid {border_code};border-radius:8px;
            padding:14px 16px;">
            <div style="color:#4ade80;font-size:10px;font-family:monospace;font-weight:700;
                margin-bottom:8px;">👨‍💻 CODE</div>
            <pre style="margin:0;overflow-x:auto;"><code style="font-family:'Courier New',monospace;
                font-size:12px;line-height:1.7;color:{code_color};white-space:pre;">{code_escaped}</code></pre>
        </div>
    </div>"""


def render_learn_section(learn: dict) -> str:
    if not learn:
        return ""
    import html as html_lib

    py_block = render_concept_block(learn.get("python_concept", {}), "#eab308", "PYTHON")
    lg_block = render_concept_block(learn.get("langgraph_concept", {}), "#06b6d4", "LANGGRAPH")

    ch = learn.get("challenge", {})
    dd = learn.get("deep_dive", {})
    starter_escaped = html_lib.escape(ch.get("starter_code", ""))
    ch_which = ch.get("which", "python")
    ch_color = "#06b6d4" if ch_which == "langgraph" else "#eab308"

    deep_url = dd.get("url", "")
    deep_link = (f'<a href="{deep_url}" style="color:#c4b5fd;text-decoration:underline;">'
                 f'{dd.get("title","")}</a>' if deep_url
                 else f'<span style="color:#c4b5fd;">{dd.get("title","")}</span>')

    return f"""
    <div style="margin-top:32px;">
        <div style="border-top:2px solid #1a1a1a;padding-top:24px;margin-bottom:20px;">
            <div style="display:flex;align-items:center;gap:10px;">
                <span style="color:#e8f63c;font-size:13px;font-weight:700;font-family:monospace;
                    letter-spacing:0.12em;">📚 LEARN</span>
                <span style="color:#2a2a2a;font-size:11px;font-family:monospace;">
                    DAILY STUDY · BEGINNER FRIENDLY · PYTHON + LANGGRAPH</span>
            </div>
        </div>
        {py_block}
        {lg_block}
        <div style="background:#0d0d0d;border:1px solid #1e1e1e;border-left:3px solid #f59e0b;
            border-radius:14px;padding:22px;margin-bottom:16px;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;flex-wrap:wrap;">
                <span style="background:#f59e0b22;color:#f59e0b;font-size:10px;font-weight:700;
                    padding:2px 9px;border-radius:10px;font-family:monospace;text-transform:uppercase;">
                    challenge</span>
                <span style="background:{ch_color}22;color:{ch_color};font-size:10px;font-weight:700;
                    padding:2px 9px;border-radius:10px;font-family:monospace;text-transform:uppercase;">
                    {ch_which}</span>
                <span style="color:#555;font-size:10px;font-family:monospace;">~20-30 MIN · BEGINNER</span>
            </div>
            <h3 style="color:#f0f0f0;font-size:16px;font-weight:700;margin:0 0 12px;
                font-family:Georgia,serif;">{ch.get('title','')}</h3>
            <p style="color:#aaa;font-size:13.5px;line-height:1.7;margin:0 0 12px;">
                {ch.get('description','')}</p>
            <div style="background:#111;border:1px solid #2a2010;border-radius:8px;
                padding:12px 16px;margin-bottom:14px;">
                <div style="color:#f59e0b;font-size:10px;font-family:monospace;font-weight:700;
                    margin-bottom:6px;">🔑 HINT</div>
                <p style="color:#fcd38d;font-size:13px;line-height:1.6;margin:0;">
                    {ch.get('hint','')}</p>
            </div>
            <div style="background:#0f0d07;border:1px solid #2a2010;border-radius:8px;
                padding:14px 16px;">
                <div style="color:#f59e0b;font-size:10px;font-family:monospace;font-weight:700;
                    margin-bottom:8px;">🚀 STARTER CODE</div>
                <pre style="margin:0;overflow-x:auto;"><code style="font-family:'Courier New',monospace;
                    font-size:12px;line-height:1.7;color:#fde68a;white-space:pre;">{starter_escaped}</code></pre>
            </div>
        </div>
        <div style="background:#0d0d0d;border:1px solid #1e1e1e;border-left:3px solid #8b5cf6;
            border-radius:14px;padding:22px;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;">
                <span style="background:#8b5cf622;color:#8b5cf6;font-size:10px;font-weight:700;
                    padding:2px 9px;border-radius:10px;font-family:monospace;text-transform:uppercase;">
                    deep dive</span>
                <span style="color:#555;font-size:10px;font-family:monospace;">
                    {dd.get('source','')} · {dd.get('time_to_read','')}</span>
            </div>
            <h3 style="color:#f0f0f0;font-size:16px;font-weight:700;margin:0 0 10px;
                font-family:Georgia,serif;">{deep_link}</h3>
            <p style="color:#aaa;font-size:13.5px;line-height:1.7;margin:0;">
                {dd.get('what_youll_learn','')}</p>
        </div>
    </div>"""


def build_html_email(data: dict) -> str:
    stories_html = "".join(render_story(s, i) for i, s in enumerate(data.get("stories", [])))
    learn_html   = render_learn_section(data.get("learn", {}))
    wotd = data.get("word_of_the_day", {})
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>AI Signal – {data.get('date','')}</title></head>
<body style="margin:0;padding:0;background:#0a0a0a;font-family:'Helvetica Neue',Arial,sans-serif;">
<div style="max-width:680px;margin:0 auto;padding:24px;">

    <div style="border-bottom:1px solid #1a1a1a;padding-bottom:16px;margin-bottom:20px;">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
            <span style="color:#e8f63c;font-size:11px;font-weight:700;font-family:monospace;
                letter-spacing:0.12em;">AI SIGNAL</span>
            <span style="width:4px;height:4px;background:#e8f63c;border-radius:50%;
                display:inline-block;"></span>
            <span style="color:#444;font-size:11px;font-family:monospace;">DAILY BRIEFING</span>
        </div>
        <h1 style="color:#f0f0f0;font-size:22px;font-weight:900;font-family:Georgia,serif;margin:0;
            line-height:1.3;">{data.get('headline','Today in AI')}</h1>
    </div>

    <div style="display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap;">
        <div style="background:#111;border:1px solid #1e1e1e;border-radius:10px;padding:12px 18px;">
            <div style="color:#555;font-size:10px;font-family:monospace;margin-bottom:3px;">DATE</div>
            <div style="color:#f0f0f0;font-size:13px;font-weight:600;font-family:monospace;">
                {data.get('date','')}</div>
        </div>
        <div style="background:#0d1520;border:1px solid #1a2d40;border-radius:10px;
            padding:12px 18px;flex:1;min-width:200px;">
            <div style="color:#3b82f6;font-size:10px;font-family:monospace;margin-bottom:3px;">
                TERM OF THE DAY</div>
            <span style="color:#93c5fd;font-size:13px;font-weight:700;font-family:monospace;">
                {wotd.get('term','')}</span>
            <span style="color:#6b7280;font-size:12px;margin-left:8px;">
                — {wotd.get('definition','')}</span>
        </div>
    </div>

    <div style="background:#0d1a0f;border:1px solid #1a3826;border-radius:12px;
        padding:16px 20px;margin-bottom:24px;">
        <div style="color:#4ade80;font-size:10px;font-weight:700;margin-bottom:6px;
            font-family:monospace;letter-spacing:0.1em;">🌐 THE BIG PICTURE</div>
        <p style="color:#a7d9b4;font-size:13.5px;line-height:1.65;margin:0;">
            {data.get('big_picture','')}</p>
    </div>

    {stories_html}
    {learn_html}

    <p style="color:#2a2a2a;font-size:11px;font-family:monospace;text-align:center;
        margin-top:32px;padding-top:16px;border-top:1px solid #1a1a1a;">
        AI SIGNAL · POWERED BY CLAUDE · {data.get('date','').upper()}
    </p>
</div>
</body></html>"""





# ── Telegram ──────────────────────────────────────────────────────────────────

def send_telegram(data: dict):
    token   = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    lines = [
        f"🤖 *AI Signal – {data.get('date','')}*",
        f"_{data.get('headline','')}_\n",
        f"🌐 *Big Picture*\n{data.get('big_picture','')}\n",
    ]
    for s in data.get("stories", []):
        emoji = {"bullish": "🟢", "bearish": "🔴", "neutral": "🟣"}.get(s.get("signal",""), "⚪")
        lines.append(f"{emoji} *{s.get('title','')}*")
        lines.append(f"{s.get('summary','')}\n")
    learn = data.get("learn", {})
    py_c = learn.get("python_concept", {})
    lg_c = learn.get("langgraph_concept", {})
    ch   = learn.get("challenge", {})
    if py_c:
        lines.append(f"🐍 *Python:* {py_c.get('topic','')}")
    if lg_c:
        lines.append(f"🔵 *LangGraph:* {lg_c.get('topic','')}")
    if ch:
        lines.append(f"⚡ *Challenge:* {ch.get('title','')}")
    text = "\n".join(lines)
    payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload, headers={"Content-Type": "application/json"}
    )
    urllib.request.urlopen(req)
    log.info("Telegram sent!")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 50)
    log.info("AI Signal Daily Briefing Starting")
    log.info("=" * 50)

    data = fetch_briefing()

    # Always save HTML locally
    out_dir   = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(out_dir, f"briefing_{datetime.now().strftime('%Y%m%d')}.html")
    with open(html_path, "w") as f:
        f.write(build_html_email(data))
    log.info(f"HTML saved → {html_path}")

    # Send Telegram
    send_telegram(data)

    log.info("Done!")


if __name__ == "__main__":
    main()