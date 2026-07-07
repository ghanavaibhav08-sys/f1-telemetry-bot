import datetime as dt
import os
import pandas as pd
import csv
import dateutil
import parser

from f1bot import openf1_client as f1
from f1bot.notify import send_discord

def get_latest_finished_race(year=None):
    if year is None: 
        year = dt.datetime.now().year
    try:
        sessions = f1.get_sessions(year=year, session_type="Race")
    except Exception:
        return None

    if not sessions:
        return None
    now = dt.datetime.now(dt.timezone.utc)
    past_races = []
    for s in sessions:
        date_end_str = s["date_end"].replace("Z", "+00:00")
        if parser.parse(date_end_str) < now:
            past_races.append(s)

    if not past_races: 
        return None

    past_races.sort(key=lambda s: s["data_end"], reverse=True)
    return past_races[0]
   
def build_report(session_key, circuit_name):
    laps = pd.DataFrame(f1.get_laps(session_key))
    stints = pd.DataFrame(f1.get_stints(session_key))
    pits = pd.DataFrame(f1.get_pit(session_key))
    weather = pd.DataFrame(f1.get_weather(session_key))
    drivers = {d["driver_number"]: d["full_name"] for d in f1.get_drivers(session_key)}

    laps = laps[laps["lap_duration"].notnull()]
    fastest = laps.loc[laps["lap_duration"].idxmin()]
    fastest_driver = drivers.get(fastest["driver_number"], fastest["driver_number"])

    avg_pit = pits["pit_duration"].mean() if not pits.empty else 0
    tyre_usage = stints["compound"].value_counts().to_dict() if not stints.empty else {}
    avg_track_temp = weather["track_temperature"].mean() if not weather.empty else None

    report = (
        f"🏁 POST-RACE ANALYTICS — {circuit_name}\n"
        f"Fastest Lap: {fastest_driver} — {fastest['lap_duration']:.3f}s\n"
        f"Average Pit Stop: {avg_pit:.2f}s\n"
        f"Total Pit Stops: {len(pits)}\n"
        f"Tyre Usage: {tyre_usage}\n"
        f"Avg Track Temp: {avg_track_temp:.1f}°C" if avg_track_temp else ""
    )
    append_to_archive(circuit_name, fastest_driver,fastest['lap_duration'], avg_pit, len(pits))
    return report

def append_to_archive(circuit, fastest_driver, fastest_time, avg_pit, total_pits):
    path = "state/season_archive.csv"
    file_exists = os.path.exists(path)
    with open(path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["circuit", "fastest_driver", "fastest_lap_time", "avg_pit_seconds", "total_pit_stops"])
        writer.writerow([circuit, fastest_driver, fastest_time, avg_pit, total_pits])
    
    

def main():
    race = get_latest_finished_race()
    if not race:
        print("No completed race found yet.")
        return
    report = build_report(race["session_key"], race["circuit_short_name"])
    send-discord(report)
    

if __name__ == "__main__":
    main()
import matplotlib
matplotlib.use("Agg")  # no display available on GitHub's runners
import matplotlib.pyplot as plt

def save_pit_chart(pits_df, path="state/pit_chart.png"):
    plt.figure(figsize=(8, 4))
    plt.bar(pits_df["driver_number"].astype(str), pits_df["pit_duration"])
    plt.xlabel("Driver Number")
    plt.ylabel("Pit Duration (s)")
    plt.title("Pit Stop Durations")
    plt.savefig(path)
    plt.close()
