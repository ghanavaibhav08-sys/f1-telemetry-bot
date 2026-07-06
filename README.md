
Automatically tracks Formula 1 race weekends and sends updates straight to Discord and Gmail:

- 📊 **Post-race analytics** — fastest lap, pit stop stats, tyre strategy — emailed/posted right after each race ends
- 🚨 **Instant alerts** — flags, safety cars, and incidents during a live session
- 🏆 **Winner prediction** — a predicted top 5 sent right after Qualifying ends, based on practice + qualifying pace

Built entirely on free tools: [OpenF1 API](https://openf1.org) for data, GitHub Actions for scheduling, Discord webhooks and Gmail for notifications. No server, no paid plan, no n8n.

## How it works
`f1bot/session_watcher.py` checks every 15 minutes whether Qualifying or the Race has just ended, and automatically triggers the right report. `f1bot/instant_alerts.py` checks every 5 minutes for new race control messages during a live session.

## Setup (for anyone forking this repo)
1. Fork or clone this repo.
2. Create a Discord webhook URL (see guide, Section 2.3) and a Gmail App Password (Section 8.1).
3. Add these as repo secrets under **Settings → Secrets and variables → Actions**:
   - `DISCORD_WEBHOOK_URL`
   - `GMAIL_ADDRESS`
   - `GMAIL_APP_PASSWORD`
   - `GMAIL_RECIPIENT` (optional)
4. That's it — the workflows in `.github/workflows/` run automatically on their schedules. You can also trigger any of them manually from the **Actions** tab using the "Run workflow" button.

## Project structure
- `f1bot/openf1_client.py` — talks to the OpenF1 API
- `f1bot/notify.py` — sends Discord and Gmail messages
- `f1bot/post_race_analytics.py` — builds the post-race report
- `f1bot/instant_alerts.py` — live session alerts
- `f1bot/winner_prediction.py` — practice + qualifying based prediction
- `f1bot/session_watcher.py` — decides *when* the above should run, based on real session end times
- `.github/workflows/` — GitHub Actions schedules for each script                                                                                                                                                                     EOF 
