import json
import datetime as dt
import os
from f1bot import openf1_client as f1
from f1bot.notify import send_discord

STATE_FILE = "state/seen_alerts.json"
PRIORITY_KEYWORDS = ["FLAG", "SAFETY CAR", "RED FLAG", "VIRTUAL SAFETY CAR", "DRS"]

def load_seen():
    if not os.path.exists(STATE_FILE):
        return []
    with open(STATE_FILE) as f:
        return json.load(f)

def save_seen(seen):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(seen[-500:], f)  # keep only the most recent 500 to avoid unbounded growth

def get_live_or_latest_session(year=2026):
    sessions = f1.get_sessions(year=year)
    now = dt.datetime.now(dt.timezone.utc)
    for s in sessions:
        start = dt.datetime.fromisoformat(s["date_start"].replace("Z", "+00:00"))
        end = dt.datetime.fromisoformat(s["date_end"].replace("Z", "+00:00"))
        if start <= now <= end:
            return s
    return None

def main():
    session = get_live_or_latest_session()
    if not session:
        print("No live session right now — skipping.")
        return

    messages = f1.get_race_control(session["session_key"])
    seen = load_seen()
    seen_ids = set(seen)

    new_alerts = []
    for m in messages:
        uid = f"{m.get('date')}|{m.get('message')}"
        if uid not in seen_ids:
            new_alerts.append((uid, m))

    if not new_alerts:
        print("No new race control messages.")
        return

    for uid, m in new_alerts:
        category = m.get("category", "")
        text = m.get("message", "")
        is_priority = any(k in text.upper() or k in category.upper() for k in PRIORITY_KEYWORDS)
        prefix = "🚨" if is_priority else "ℹ️"
        send_discord(f"{prefix} {category}: {text}")
        seen.append(uid)

    save_seen(seen)

if __name__ == "__main__":
    main()
