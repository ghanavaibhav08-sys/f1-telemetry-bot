import requests
import time

BASE_URL = "https://api.openf1.org/v1"

def get(endpoint, **params):
    """Generic GET helper for any OpenF1 endpoint."""
    time.sleep(0.5)
    url = f"{BASE_URL}/{endpoint}"
    resp = requests.get(url, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()

def get_sessions(year=2026, session_type=None, country_name=None):
    params = {"year": year}
    if session_type:
        params["session_type"] = session_type
    if country_name:
        params["country_name"] = country_name
    return get("sessions", **params)

def get_laps(session_key):
    return get("laps", session_key=session_key)

def get_stints(session_key):
    return get("stints", session_key=session_key)

def get_pit(session_key):
    return get("pit", session_key=session_key)

def get_weather(session_key):
    return get("weather", session_key=session_key)

def get_race_control(session_key):
    return get("race_control", session_key=session_key)

def get_drivers(session_key):
    return get("drivers", session_key=session_key)

def get_session_result(session_key):
    return get("session_result", session_key=session_key)
import datetime as dt

def get_current_weekend_meeting(year=2026):
    """Returns the full meeting dict for whichever GP weekend we're
    currently in, or the nearest upcoming one if between weekends."""
    meetings = get("meetings", year=year)
    now = dt.datetime.now(dt.timezone.utc)

    def parse(d):
        return dt.datetime.fromisoformat(d.replace("Z", "+00:00"))

    for m in meetings:
        start = parse(m["date_start"]) - dt.timedelta(days=1)
        end = parse(m["date_end"]) + dt.timedelta(days=1)
        if start <= now <= end:
            return m

    upcoming = [m for m in meetings if parse(m["date_start"]) > now]
    upcoming.sort(key=lambda m: m["date_start"])
    return upcoming[0] if upcoming else None
