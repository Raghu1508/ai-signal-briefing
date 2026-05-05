# 🤖 AI Signal – Daily Morning Briefing

A Claude-powered script that fetches the latest AI news every morning at 9 AM
and delivers a rich briefing straight to your inbox (+ Telegram optional).

---

## What you'll receive every morning

- **5 curated AI stories** with category, signal (bullish/bearish/neutral), and tags
- **Why it matters** — broader significance for each story
- **Dig deeper** — 3 questions to explore further per story
- **The Big Picture** — a connecting narrative across today's stories
- **Term of the Day** — one AI/ML concept explained simply

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.9+ |
| pip | any |
| A machine that stays on (Mac, Linux, or a cheap VPS) | — |

---

## Quick Setup (5 minutes)

### Step 1 — Clone / download this folder

```bash
# If using Claude Code, the files are already here
cd ai-briefing
```

### Step 2 — Fill in your credentials

```bash
cp .env.example .env
nano .env   # or open in any editor
```

Fill in:

| Variable | Where to get it |
|----------|----------------|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) → API Keys |
| `BRIEFING_FROM_EMAIL` | Your Gmail address |
| `BRIEFING_EMAIL_PASSWORD` | Gmail → Manage Account → Security → **App Passwords** (NOT your real password) |
| `BRIEFING_TO_EMAIL` | Where to deliver (can be same Gmail or any email) |

> **Gmail App Password**: Go to [myaccount.google.com](https://myaccount.google.com) → Security → 2-Step Verification → App Passwords → Select app: Mail → Generate. Use the 16-character code.

### Step 3 — Run setup

```bash
chmod +x setup.sh
./setup.sh
```

This will:
1. Install `anthropic` and `python-dotenv`
2. Run a test fetch so you can verify it works
3. Install the cron job at 9:00 AM daily

---

## Optional: Telegram notifications (highly recommended for phone)

Telegram gives you instant phone notifications alongside email. Takes 2 minutes:

1. Open Telegram → search **@BotFather** → send `/newbot` → follow steps → copy **Bot Token**
2. Open Telegram → search **@userinfobot** → send `/start` → copy your **Chat ID**
3. Add both to your `.env`:
   ```
   TELEGRAM_BOT_TOKEN=7123456789:AAF...
   TELEGRAM_CHAT_ID=123456789
   ```

That's it — you'll get a Telegram message every morning alongside the email.

---

## Running manually

```bash
# From the ai-briefing directory
set -a && source .env && set +a
python3 briefing.py
```

---

## Cron management

```bash
# View current cron jobs
crontab -l

# Remove the briefing cron job
crontab -l | grep -v briefing.py | crontab -

# Change time — edit and re-run setup.sh, or edit crontab directly
crontab -e
```

### Running on a Mac that sleeps

If your Mac is asleep at 9 AM, the cron job won't run. Two options:

**Option A** — Use a cheap VPS (DigitalOcean $4/mo, Railway free tier, etc.)

**Option B** — Use `launchd` instead of cron on Mac:
```bash
# setup.sh will detect macOS and offer this automatically in a future update
```

---

## File structure

```
ai-briefing/
├── briefing.py        # Main script
├── setup.sh           # One-time setup & cron installer
├── .env.example       # Credentials template
├── .env               # Your credentials (never commit this)
├── briefing.log       # Daily run log
└── briefing_YYYYMMDD.html   # Saved HTML of each day's briefing
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ANTHROPIC_API_KEY not set` | Check `.env` is in the same folder as `briefing.py` |
| `SMTPAuthenticationError` | Use an App Password, not your real Gmail password |
| `No JSON in response` | Temporary API issue — it will retry tomorrow automatically |
| Cron not running | Run `crontab -l` to verify. Also check `briefing.log` for errors |
| Email in spam | Add your sender address to contacts |
