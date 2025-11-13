"""
Fetch and parse the eCal ICS feed(s) from SLBenfica's eCal website: https://benfica.ecal.com/
and normalise events into a structured list.

13/11/2025: Prints and sorts by date

TODO:
- Create a database and save into it

Author: Bruno Rodrigues (BRodrigues98)
"""

import os
import re
import requests
import pytz

from datetime import datetime
from typing import List, Dict, Any
from icalendar import Calendar

# Lisbon Timezone for now
LX_TZ = pytz.timezone("Europe/Lisbon")

# Config the ICS URL(s)
# TODO: Put this in a .env or config
ECAL_URLS = [
    "https://ics.ecal.com/ecal-sub/6915f30f396fa00008c2a014/SL%20Benfica.ics"
]

BENFICA_NAME = "SL Benfica"


# -----------------------------------------
# Helper: Parse a VEVENT into a Python dict
# -----------------------------------------

def parse_vevent(component, source_name:str) -> Dict[str, Any]:
    """Convert an icalendar VEVENT into a normalised dictionary."""

    # basic fields from ICS
    dtstart = component.get("dtstart").dt
    dtend = component.get("dtend").dt if component.get("dtend") else None
    uid = str(component.get("uid"))
    summary = str(component.get("summary") or "")
    description = str(component.get("description") or "")
    location = str(component.get("location") or "")

    # normalize start/end to LX timezone
    if isinstance(dtstart, datetime) and dtstart.tzinfo:
        dtstart = dtstart.astimezone(LX_TZ)
    if isinstance(dtend, datetime) and dtend.tzinfo:
        dtend = dtend.astimezone(LX_TZ)

    # parse summary
    # example:
    # "🤾👩 CA Leça x SL Benfica | Andebol Feminino"
    # left  = "🤾👩 CA Leça x SL Benfica"
    # right = "Andebol Feminino"

    left = summary
    modality_label = ""

    if "|" in summary:
        left, modality_label = [s.strip() for s in summary.split("|", 1)]

    # remove leading emojis from left
    left_clean = re.sub(r"^\W+", "", left).strip()

    team_a = team_b = None
    benfica_home = None
    opponent = None

    if " x " in left_clean:
        team_a, team_b = [s.strip() for s in left_clean.split(" x ", 1)]

        if team_a == BENFICA_NAME and team_b != BENFICA_NAME:
            benfica_home = True
            opponent = team_b
        elif team_b == BENFICA_NAME and team_a != BENFICA_NAME:
            benfica_home = False
            opponent = team_a
        else:
            # neutral / weird
            benfica_home = None
            opponent = team_b or team_a

    # separate sport and gender from modality label, ex "Andebol Feminino"
    sport = None
    gender = None
    modality_label = modality_label.strip()

    if modality_label:
        parts = modality_label.split()
        if len(parts) >= 1:
            sport = parts[0] # "Andebol"
        if len(parts) >= 2:
            gender = " ".join(parts[1:]) # "Feminino"

    # parse description first line
    # example:
    # "Campeonato Nacional Feminino | 25/26 - Jornada 12"
    competition = None
    season = None
    matchday = None

    lines = description.splitlines()
    first_line = lines[0].strip() if lines else ""

    if "|" in first_line:
        comp_name, rest = [s.strip() for s in first_line.split("|", 1)]
        competition = comp_name

        #rest. Ex.: "25/26 - Jornada 12"
        if "-" in rest:
            season_part, rest2 = [s.strip() for s in rest.split("-", 1)]
            season = season_part

            m = re.search(r"Jornada\s+(\d+)", rest2)
            if m:
                matchday = int(m.group(1))
        else:
            season = None
    elif first_line:
        competition = first_line

    # extract ticket url
    ticket_url = None
    desc_lower = description.lower()
    for line in lines:
        line = line.strip()
        if line.startswith("http") and "bilhete" in desc_lower:
            ticket_url = line
            break

    return {
        "uid": uid,
        "source_name": source_name,
        "start": dtstart,
        "end": dtend,
        "summary": summary,
        "description": description,
        "venue_name": location,
        "sport": sport,
        "gender": gender,
        "benfica_home": benfica_home,
        "opponent": opponent,
        "competition": competition,
        "season": season,
        "matchday": matchday,
        "ticket_url": ticket_url
    }


# ----------------------------
# Fetch and Parse each ICS URL
# ----------------------------
def fetch_and_parse(url: str, source_name: str) -> List[Dict[str, Any]]:
    """Download an ICS file from eCal and parse all VEVENTs"""
    print(f"Fetching: {url}")
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()

    cal = Calendar.from_ical(resp.content)
    events: List[Dict[str, Any]] = []

    for component in cal.walk():
        if component.name != "VEVENT":
            continue
        event = parse_vevent(component, source_name=source_name)
        events.append(event)

    return events


# -----------
# Entry Point
# -----------
def run_import() -> List[Dict[str, Any]]:
    """Fetch all configured ICS feeds and return a single list of events (Later into database)"""
    all_events: List[Dict[str, Any]] = []

    for idx, url in enumerate(ECAL_URLS):
        source_name = f"feed_{idx}"
        events = fetch_and_parse(url, source_name)
        all_events.extend(events)

    # sort by start date
    all_events.sort(key=lambda e: e["start"] or datetime.max)

    return all_events


if __name__ == "__main__":
    events = run_import()

    print("\n=== First 15 Parsed Events ===\n")
    for e in events[:15]:
        start_str = e["start"].strftime("%Y-%m-%d %H:%M")
        home_away = "vs" if e["benfica_home"] else "@"
        print(
            f"{start_str} | {e['sport']} {e['gender']} | "
            f"{home_away} {e['opponent']} | {e['competition']}"
            f"(UID={e['uid']})"
        )