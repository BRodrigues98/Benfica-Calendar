#!/usr/bin/env python3
"""
Fetch and parse the eCal ICS feed(s) from SLBenfica's eCal website: https://benfica.ecal.com/
and normalise events into a structured list.

13/11/2025: Prints and sorts by date

TODO:
- Create a database and save into it

Author: Bruno Rodrigues (BRodrigues98)
"""



import requests
import re
import pytz
import json
from datetime import datetime
from typing import List, Dict, Any
from icalendar import Calendar

TZ = pytz.timezone("Europe/Lisbon")

# Config the ICS URL(s)
# TODO: Put this in a .env or config
ECAL_URLS = [
    "https://ics.ecal.com/ecal-sub/6915f30f396fa00008c2a014/SL%20Benfica.ics"
]

BENFICA_NAME = "SL Benfica"

# keywords for segmentation
SPORT_KEYWORDS = ["Hóquei em Patins", "Andebol", "Futsal", "Basquetebol", "Voleibol", "Futebol", "Hóquei"]
FOOTBALL_SQUAD_KEYWORDS = [
    "Equipa B",
    "Juniores",
    "Sub-19",
    "Sub-23",
    "Sub-17",
    "Sub-15",
    "Juvenis",
    "Iniciados",
]

FOOTBALL_COMP_KEYWORDS = [
    "liga portugal",
    "taça de portugal",
    "liga dos campeões",
    "liga dos campeoes",
    "liga revelação",
    "liga revelacao",
    "liga dos campeões feminina",
    "liga dos campeoes feminina",
    "liga dos campeões feminina uefa",
    "supertaça",
    "supertaca",
    "campeonato nacional feminino ii divisão",
    "campeonato nacional feminino ii divisao",
]

BROADCAST_KEYWORDS = ["📺", "BTV", "DAZN", "Sport TV", "Eleven", "Canal 11", "RTP", "SIC", "TVI", "Benfica TV"]

def is_ticketing_event(summary: str | None,
                       description: str | None,
                       competition: str | None) -> bool:
    """
    Returns True for ECAL entries that are *ticket info / sales criteria*
    and not actual matches.

    Heuristics:
    - DESCRIPTION or competition mention 'CRITÉRIOS DE VENDA'
    - SUMMARY starts with '🎫 Bilhetes' (or just 'Bilhetes')
    - Fallback: SUMMARY contains 'bilhetes' and has no ' | ' separators,
      which normal match summaries use.
    """
    s = (summary or "").strip().lower()
    d = (description or "").strip().lower()
    c = (competition or "").strip().lower()

    # Very strong signal
    if "critérios de venda" in d or c.startswith("critérios de venda"):
        return True

    # Typical ECAL pattern: "🎫 Bilhetes ⚽ SL Benfica x ..."
    if s.startswith("🎫 bilhetes") or s.startswith("bilhetes "):
        return True

    # Fallback: summary talks about tickets but doesn't look like our
    # normal "Team x Team | Sport ..." template (no ' | ').
    if "bilhetes" in s and " | " not in s:
        return True

    return False

def is_benfica_team(name: str) -> bool:
    if not name:
        return False
    return name.startswith("SL Benfica")

# --------------------------------------------------
# Helper: parse SUMMARY into match info / modality
# --------------------------------------------------
def parse_summary(summary: str) -> Dict[str, Any]:
    """
    Break SUMMARY into:
    - event_type: "match" or "other"
    - team_a, team_b
    - benfica_home, opponent
    - sport, squad_label
    """
    summary = summary.strip()
    if not summary:
        return {
            "event_type": "other",
            "team_a": None,
            "team_b": None,
            "benfica_home": None,
            "opponent": None,
            "sport": None,
            "squad_label": None,
        }

    # Split by '|' because eCal uses it to separate pieces:
    # e.g. "⚽ Paços Ferreira x SL Benfica | Equipa B | 📺 BTV"
    segments = [s.strip() for s in summary.split("|") if s.strip()]

    # 1) Find the segment that has the actual match (contains " x ")
    match_idx = None
    for i, seg in enumerate(segments):
        if " x " in seg:
            match_idx = i
            break

    # If there's no "x", we treat this as non-match (museum, tickets, etc.)
    if match_idx is None:
        return {
            "event_type": "other",
            "team_a": None,
            "team_b": None,
            "benfica_home": None,
            "opponent": None,
            "sport": None,
            "squad_label": None,
        }

    match_seg = segments[match_idx]

    # Remove leading emojis / non-word chars
    match_clean = re.sub(r"^\W+", "", match_seg).strip()

    team_a = team_b = None
    benfica_home = None
    opponent = None

    if " x " in match_clean:
        team_a, team_b = [s.strip() for s in match_clean.split(" x ", 1)]

        # normalize whitespace in team names
        team_a = re.sub(r"\s+", " ", team_a)
        team_b = re.sub(r"\s+", " ", team_b)

        a_is_benfica = is_benfica_team(team_a)
        b_is_benfica = is_benfica_team(team_b)

        if a_is_benfica and not b_is_benfica:
            benfica_home = True
            opponent = team_b
        elif b_is_benfica and not a_is_benfica:
            benfica_home = False
            opponent = team_a
        else:
            benfica_home = None
            opponent = team_b or team_a

    # 2) Look at segments AFTER the match for modality / squad info
    metadata_segments = segments[match_idx + 1 :]

    modality_segment = None
    broadcast_info = None

    for seg in metadata_segments:
        # If it looks like TV/broadcast info, stash separately and skip for modality
        if any(b in seg for b in BROADCAST_KEYWORDS):
            broadcast_info = seg
            continue

        # First non-broadcast segment after the match we treat as "modality / squad"
        if modality_segment is None:
            modality_segment = seg

    sport = None
    squad_label = None

    # Heuristics: decide sport + squad_label
    if modality_segment:
        # If the segment contains a known sport keyword
        for sk in SPORT_KEYWORDS:
            if sk in modality_segment:
                sport = sk
                # Everything after the sport word becomes "squad label"
                # e.g. "Andebol Feminino" -> squad_label="Feminino"
                after = modality_segment.split(sk, 1)[1].strip()
                squad_label = after if after else None
                break

        # If we still don't know sport but we see football squad words,
        # assume it's football and use the whole segment as squad label.
        if sport is None:
            for fk in FOOTBALL_SQUAD_KEYWORDS:
                if fk in modality_segment:
                    sport = "Futebol"
                    squad_label = modality_segment
                    break

    return {
        "event_type": "match",
        "team_a": team_a,
        "team_b": team_b,
        "benfica_home": benfica_home,
        "opponent": opponent,
        "sport": sport,
        "squad_label": squad_label,
    }


# --------------------------------------------------
# Parse a VEVENT into our normalised dict
# --------------------------------------------------
def parse_event(component, source_name: str) -> Dict[str, Any]:
    dtstart = component.get("dtstart").dt
    dtend = component.get("dtend").dt if component.get("dtend") else None
    uid = str(component.get("uid"))
    summary = str(component.get("summary") or "")
    description = str(component.get("description") or "")
    location = str(component.get("location") or "")

    # Normalise dates to Lisbon time
    if isinstance(dtstart, datetime) and dtstart.tzinfo:
        dtstart = dtstart.astimezone(TZ)
    if isinstance(dtend, datetime) and dtend.tzinfo:
        dtend = dtend.astimezone(TZ)

    # --------------------------------------------------
    # DESCRIPTION first line → competition/season/jornada
    # --------------------------------------------------
    competition = None
    season = None
    matchday = None

    lines = description.splitlines()
    first_line = lines[0].strip() if lines else ""

    if "|" in first_line:
        comp_name, rest = [s.strip() for s in first_line.split("|", 1)]
        competition = comp_name
        rest = rest.strip()

        if "-" in rest:
            # "25/26 - Jornada 4"  or  "2025/26 - Jornada 3"
            season_part, rest2 = [s.strip() for s in rest.split("-", 1)]
            season = season_part

            m = re.search(r"Jornada\s+(\d+)", rest2)
            if m:
                matchday = int(m.group(1))
        else:
            # just "25/26" → treat as season
            if re.match(r"^\d{2}/\d{2}$", rest) or re.match(r"^\d{4}/\d{2}$", rest):
                season = rest

    elif first_line:
        # Try: "Segunda Liga 25/26 - Jornada 9"
        #   or "CEV Challenge Cup 25/26"
        m = re.match(
            r"(?P<comp>.+?)\s+(?P<season>\d{2}/\d{2}|\d{4}/\d{2})"
            r"(?:\s*-\s*Jornada\s+(?P<j>\d+))?$",
            first_line,
        )
        if m:
            competition = m.group("comp").strip()
            season = m.group("season").strip()
            j = m.group("j")
            if j:
                matchday = int(j)
        else:
            # plain label, e.g. "Campeonato Nacional Masculino"
            competition = first_line

    # --------------------------------------------------
    # 1) TICKETING EVENTS SHORT-CIRCUIT
    # --------------------------------------------------
    if is_ticketing_event(summary, description, competition):
        # basic ticket url extraction from description
        ticket_url = None
        for line in lines:
            line = line.strip()
            if line.startswith("http"):
                ticket_url = line
                break

        return {
            "uid": uid,
            "source_name": source_name,
            "event_type": "ticketing",
            "start": dtstart,
            "end": dtend,
            "summary": summary,
            "description": description,
            "venue_name": location,
            "sport": None,
            "squad_label": None,
            "benfica_home": None,
            "opponent": None,
            "competition": competition,
            "season": season,
            "matchday": matchday,
            "ticket_url": ticket_url,
        }

    # --------------------------------------------------
    # 2) NORMAL SUMMARY PARSING (MATCHES / OTHER EVENTS)
    # --------------------------------------------------
    summary_info = parse_summary(summary)

    event_type = summary_info["event_type"]
    benfica_home = summary_info["benfica_home"]
    opponent = summary_info["opponent"]
    sport = summary_info["sport"]
    squad_label = summary_info["squad_label"]

    # --------------------------------------------------
    # 3) Ticket URL extraction (for matches & other events)
    # --------------------------------------------------
    ticket_url = None
    desc_lower = description.lower()
    if "bilhete" in desc_lower:
        for line in lines:
            line = line.strip()
            if line.startswith("http"):
                ticket_url = line
                break

    # --------------------------------------------------
    # 4) Football fallback heuristic (now OUTSIDE the 'bilhete' block)
    # --------------------------------------------------
    if event_type == "match" and sport is None:
        summary_lower = summary.lower()
        comp_lower = (competition or "").lower()

        looks_like_football = False

        # 1) football emoji in summary
        if "⚽" in summary or "⚽️" in summary:
            looks_like_football = True

        # 2) or competition name hints it's football
        if any(key in comp_lower for key in FOOTBALL_COMP_KEYWORDS):
            looks_like_football = True

        if looks_like_football:
            sport = "Futebol"

            # if we still don't know the squad/gender, try to guess
            if squad_label is None:
                if (
                    "feminina" in comp_lower
                    or "feminino" in comp_lower
                    or "feminina" in summary_lower
                    or "feminino" in summary_lower
                ):
                    squad_label = "Feminino"
                elif any(
                    k in summary
                    for k in [
                        "Sub-23",
                        "Sub 23",
                        "Sub-19",
                        "Sub 19",
                        "Juniores",
                        "Equipa B",
                    ]
                ):
                    # leave as-is; parse_summary usually sets it anyway
                    pass
                else:
                    # default to senior men's team
                    squad_label = "Masculino"

    return {
        "uid": uid,
        "source_name": source_name,
        "event_type": event_type,  # "match", "other", etc.
        "start": dtstart,
        "end": dtend,
        "summary": summary,
        "description": description,
        "venue_name": location,
        "sport": sport,               # e.g. "Futsal", "Andebol", "Futebol"
        "squad_label": squad_label,   # e.g. "Feminino", "Equipa B", "Sub-19"
        "benfica_home": benfica_home,
        "opponent": opponent,
        "competition": competition,
        "season": season,
        "matchday": matchday,
        "ticket_url": ticket_url,
    }


# --------------------------------------------------
# Download & parse one ICS
# --------------------------------------------------
def fetch_and_parse(url: str, source_name: str) -> List[Dict[str, Any]]:
    print(f"Fetching: {url}")
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()

    cal = Calendar.from_ical(resp.content)
    events: List[Dict[str, Any]] = []

    for component in cal.walk():
        if component.name != "VEVENT":
            continue
        event = parse_event(component, source_name=source_name)
        events.append(event)

    return events


def run_import() -> List[Dict[str, Any]]:
    all_events: List[Dict[str, Any]] = []

    for idx, url in enumerate(ECAL_URLS):
        source_name = f"feed_{idx}"
        events = fetch_and_parse(url, source_name)
        all_events.extend(events)

    all_events.sort(key=lambda e: e["start"] or datetime.max)
    return all_events

def print_event_dict(event:dict):
    """Pretty-print one event dictionary, with sorted keys."""
    print(json.dumps(
        event,
        indent=4,
        ensure_ascii=False,
        sort_keys=True,
        default=to_serializable  # <--- HERE
    ))

def to_serializable(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj

if __name__ == "__main__":
    events = run_import()

    print("\n=== MATCH EVENTS (first 20) ===\n")
    match_events = [e for e in events if e["event_type"] == "match"]

    for e in match_events[:50]:
        print_event_dict(e)
        # start_str = e["start"].strftime("%Y-%m-%d %H:%M")
        # home_away = "vs" if e["benfica_home"] else "@"
        # squad_info = f"{e['sport']} {e['squad_label']}".strip()
        # print(
        #     f"{start_str} | {squad_info} | {home_away} {e['opponent']} | "
        #     f"{e['competition']} (UID={e['uid']})"
        # )

    print("\n=== OTHER CLUB EVENTS (first 10) ===\n")
    other_events = [e for e in events if e["event_type"] == "other"]
    for e in other_events[:10]:
        start_str = e["start"].strftime("%Y-%m-%d %H:%M")
        print(
            f"{start_str} | OTHER | {e['summary']} "
            f"| {e['competition']} (UID={e['uid']})"
        )
