from dotenv import load_dotenv
load_dotenv()
import csv
import time
from f1bot import openf1_client as f1
from f1bot.winner_prediction import best_laps_by_driver, normalize_inverse

OUTPUT_PATH = "state/training_data.csv"

def get_weekend_sessions_for_meeting(meeting_key):
    """All sessions belonging to one race weekend, keyed by session_name."""
    sessions = f1.get("sessions", meeting_key=meeting_key)
    return {s.get("session_name"): s for s in sessions if s.get("session_name")}

def get_final_positions(race_session_key):
    """driver_number -> final race classification position."""
    results = f1.get_session_result(race_session_key)
    return {r["driver_number"]: r.get("position") for r in results if r.get("position")}

def build_rows_for_meeting(meeting):
    rows = []
    sessions = get_weekend_sessions_for_meeting(meeting["meeting_key"])

    race_session = sessions.get("Race")
    quali_session = sessions.get("Qualifying")
    if not race_session or not quali_session:
        return rows  # skip weekends missing a session we need (e.g. sprint-only weekends)

    fp1 = best_laps_by_driver(f1.get_laps(sessions["Practice 1"]["session_key"])) if "Practice 1" in sessions else {}
    fp2 = best_laps_by_driver(f1.get_laps(sessions["Practice 2"]["session_key"])) if "Practice 2" in sessions else {}
    fp3 = best_laps_by_driver(f1.get_laps(sessions["Practice 3"]["session_key"])) if "Practice 3" in sessions else {}
    quali = best_laps_by_driver(f1.get_laps(quali_session["session_key"]))
    final_positions = get_final_positions(race_session["session_key"])

    all_drivers = set(fp1) | set(fp2) | set(fp3) | set(quali)
    practice_avg = {}
    for d in all_drivers:
        times = [t[d] for t in (fp1, fp2, fp3) if d in t]
        if times:
            practice_avg[d] = sum(times) / len(times)

    practice_score = normalize_inverse(practice_avg)
    quali_score = normalize_inverse(quali)

    for d in all_drivers:
        if d not in final_positions:
            continue  # driver didn't finish / no classification (DNF, DSQ, etc.) — skip for now
        rows.append({
            "meeting_key": meeting["meeting_key"],
            "circuit": meeting.get("circuit_short_name", ""),
            "driver_number": d,
            "practice_score": round(practice_score.get(d, 0), 2),
            "quali_score": round(quali_score.get(d, 0), 2),
            "actual_finish_position": final_positions[d],
        })
    return rows

def main(years=(2023, 2024, 2025)):
    all_rows = []
    for year in years:
        meetings = f1.get("meetings", year=year)
        for meeting in meetings:
            print(f"Processing {meeting.get('circuit_short_name')} {year}...")
            try:
                rows = build_rows_for_meeting(meeting)
                all_rows.extend(rows)
            except Exception as e:
                print(f"  Skipped due to error: {e}")
            time.sleep(0.5)  # be polite to the free API — avoid hammering it with rapid requests

    if not all_rows:
        print("No rows collected — nothing written.")
        return

    with open(OUTPUT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Wrote {len(all_rows)} rows to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
