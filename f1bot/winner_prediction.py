import datetime as dt
import joblib
from f1bot import openf1_client as f1
from f1bot.notify import send_discord

def get_current_weekend_country(year=2026):
    """Automatically find the country_name of whichever GP weekend we're
    currently in (or, if between weekends, the next upcoming one) —
    no manual editing needed race to race."""

    meeting = f1.get_current_weekend_meeting()
    country = meeting["country_name"] if meeting else None
    def parse(d):
         return dt.datetime.fromisofformat(d.replace("Z","+00:00"))
        
    for m in meetings:
        start = parse(m["date_start"]) - dt.timedelta(days=1)
        end = parse(m["date_end"]) + dt.timedelta(days=1)
        if start <= now <= end:
            return m["country_name"]

    # 2) Otherwise, fall back to the nearest upcoming weekend
    upcoming = [m for m in meetings if parse(m["date_start"]) > now]
    upcoming.sort(key=lambda m: m["date_start"])
    if upcoming:
        return upcoming[0]["country_name"]

    return None

def get_weekend_sessions(year=2026, country_name=None):
    sessions = f1.get_sessions(year=year, country_name=country_name)
    # .get(...) on each session instead of ["..."] so a session missing a
    # field never raises a KeyError — it's just skipped.
    return {s.get("session_name"): s for s in sessions if s.get("session_name")}

def best_laps_by_driver(laps):
    best = {}
    for lap in laps:
        dur = lap.get("lap_duration")
        num = lap.get("driver_number")
        if not dur or num is None:
            continue
        if num not in best or dur < best[num]:
            best[num] = dur
    return best

def normalize_inverse(scores: dict):
    values = [v for v in scores.values() if v]
    if not values:
        return {}
    fastest = min(values)
    return {k: (fastest / v) * 100 if v else 0 for k, v in scores.items()}

def safe_laps(session):
    """Fetch laps for a session dict that might be missing or empty —
    always returns a dict (never raises), so callers never need to
    special-case a missing session."""
    if not session or not session.get("session_key"):
        return {}
    try:
        return best_laps_by_driver(f1.get_laps(session["session_key"]))
    except Exception as e:
        print(f"Could not fetch laps for {session.get('session_name')}: {e}")
        return {}

def predict(country_name, year=2026, practice_weight=0.4, quali_weight=0.6):
    sessions = get_weekend_sessions(year=year, country_name=country_name)

    fp1 = safe_laps(sessions.get("Practice 1"))
    fp2 = safe_laps(sessions.get("Practice 2"))
    fp3 = safe_laps(sessions.get("Practice 3"))
    quali_session = sessions.get("Qualifying")
    quali = safe_laps(quali_session)

    drivers_meta = {}
    if quali_session and quali_session.get("session_key"):
        try:
            drivers_meta = {d["driver_number"]: d for d in f1.get_drivers(quali_session["session_key"])}
        except Exception as e:
            print(f"Could not fetch driver list: {e}")

    all_drivers = set(fp1) | set(fp2) | set(fp3) | set(quali)
    if not all_drivers:
        return []

    practice_avg = {}
    for d in all_drivers:
        times = [t[d] for t in (fp1, fp2, fp3) if d in t]
        if times:
            practice_avg[d] = sum(times) / len(times)

    practice_score = normalize_inverse(practice_avg)
    quali_score = normalize_inverse(quali)
    model = joblib.load("state/predictor_model.joblib")

    results = []
    for d in all_drivers:
        p_score = practice_score.get(d,0)
        q_score = quali_score.get(d,0)

        predicted_position = model.predict([[practice_score, quali_score]])

     
        meta = drivers_meta.get(d, {})
        name = meta.get("full_name", f"#{d}")
        team = meta.get("team_name", "")
        results.append((name, team, score))

    results.sort(key=lambda r: r[2], reverse=False)
    return results

def main():
    country = get_current_weekend_country()
    if not country:
        print("Could not determine the current/next race weekend.")
        return

    results = predict(country_name=country)
    if not results:
        print(f"Practice/Qualifying data not available yet for {country}.")
        return

    lines = [f"🏆 PREDICTED TOP 5 — {country} GP"]
    for i, (name, team, score) in enumerate(results[:5], start=1):
        lines.append(f"{i}. {name} ({team}) — predicted pos: {pred_pos:.1f}")

    message = "\n".join(lines)
    print(message)
    send_discord(message)

if __name__ == "__main__":
    main()
