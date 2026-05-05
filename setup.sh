#!/usr/bin/env bash
# setup.sh — One-time setup for AI Signal daily briefing
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON=$(which python3)
CRON_HOUR=9    # 9 AM
CRON_MIN=0

echo ""
echo "╔══════════════════════════════════════╗"
echo "║     AI Signal – Setup & Install      ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── 1. Install dependencies ────────────────────────────────────────────────────
echo "▶ Installing Python dependencies..."
pip3 install anthropic python-dotenv --quiet
echo "  ✓ Dependencies installed"

# ── 2. Create .env if missing ──────────────────────────────────────────────────
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    echo ""
    echo "  ⚠️  Created .env from template."
    echo "  👉 Open $SCRIPT_DIR/.env and fill in your API keys before continuing."
    echo ""
    read -p "  Press Enter once you've filled in .env to continue setup..." 
fi

# ── 3. Test run ────────────────────────────────────────────────────────────────
echo ""
echo "▶ Running a test fetch (this may take 30-60 seconds)..."
cd "$SCRIPT_DIR"
set -a; source .env; set +a
$PYTHON briefing.py
echo "  ✓ Test run complete — check briefing_$(date +%Y%m%d).html"

# ── 4. Install cron job ────────────────────────────────────────────────────────
echo ""
echo "▶ Installing cron job (daily at ${CRON_HOUR}:00 AM local time)..."

CRON_CMD="$CRON_MIN $CRON_HOUR * * * cd $SCRIPT_DIR && set -a && source $SCRIPT_DIR/.env && set +a && $PYTHON $SCRIPT_DIR/briefing.py >> $SCRIPT_DIR/briefing.log 2>&1"

# Add to crontab if not already present
(crontab -l 2>/dev/null | grep -v "briefing.py"; echo "$CRON_CMD") | crontab -

echo "  ✓ Cron job installed"
echo ""
echo "  Verify with:  crontab -l"
echo "  Remove with:  crontab -l | grep -v briefing.py | crontab -"
echo ""
echo "╔══════════════════════════════════════╗"
echo "║          Setup complete! ✅           ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "  Your briefing will land every morning at ${CRON_HOUR}:00 AM."
echo "  Logs: $SCRIPT_DIR/briefing.log"
echo ""
