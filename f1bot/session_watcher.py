import os
import json
import datetime as dt
from f1bot import openf1_client as f1
from f1bot.notify import send_email
from f1bot.winner_prediction import predict
from f1bot.post_race_analytics import build_report

STATE_FILE = "state/processed_sessions.json"
WATCHED_SESSION_NAMES = {"Qualifying", "Race"}
GRACE_MINUTES = 90  # only look at sessions that ended within the last 90 minutes

def load_processed():
    if not os.path.exists(STATE_FILE):
        return []
    with open(STATE_FILE) as f:
        return json.load(f)

def save_processed(ids):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(ids[-200:], f)

def get_recently_ended_sessions(year=2026):
    sessions = f1.get_sessions(year=year)
    now = dt.datetime.now(dt.timezone.utc)
    ended = []
    for s in sessions:
        if s.get("session_name") not in WATCHED_SESSION_NAMES:
            continue
        end = dt.datetime.fromisoformat(s["date_end"].replace("Z", "+00:00"))
        if end < now and (now - end) < dt.timedelta(minutes=GRACE_MINUTES):
            ended.append(s)
    return ended

def main():
    processed = load_processed()
    processed_set = set(processed)

    recently_ended = get_recently_ended_sessions()
    if not recently_ended:
        print("No sessions ended in the last 90 minutes.")
        return

    for session in recently_ended:
        session_id = str(session["session_key"])
        if session_id in processed_set:
            continue  # already emailed for this one

        name = session["session_name"]
        circuit = session.get("circuit_short_name", "")
        country = session.get("country_name", "")

        if name == "Qualifying":
            results = predict(country_name=country)
            if not results:
                print(f"Qualifying just ended for {circuit} but no lap data yet — will retry next run.")
                continue  # don't mark as processed; try again in 15 minutes
            lines = [f"🏆 Qualifying just ended — Predicted Top 5 for the {circuit} GP"]
            for i, (drv_name, team, score) in enumerate(results[:5], start=1):
                lines.append(f"{i}. {drv_name} ({team}) — score {score:.1f}")
            send_email(f"F1: Qualifying predictions — {circuit}", "\n".join(lines))
            print(f"Emailed qualifying prediction for {circuit}.")

        elif name == "Race":
            report = build_report(session["session_key"], circuit)
            send_email(f"F1: Post-race analytics — {circuit}", report)
            print(f"Emailed post-race analytics for {circuit}.")

        processed.append(session_id)

    save_processed(processed)

if __name__ == "__main__":
    main()
