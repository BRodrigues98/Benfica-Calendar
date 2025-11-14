from datetime import datetime
from typing import Any, Dict, Optional
import re
from icalendar import Event as ICalEvent

from .config import (
    TZ,
    BENFICA_NAME,
    SPORT_KEYWORDS,
    FOOTBALL_SQUAD_KEYWORDS,
    FOOTBALL_COMP_KEYWORDS,
    BROADCAST_KEYWORDS,
)
from .models import Event

# -------------------------------------------------------------------
# Helper functions (pure-ish logic)
# -------------------------------------------------------------------


def is_ticketing_event(
    summary: Optional[str],
    description: Optional[str],
    competition: Optional[str],
) -> bool:
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
    return name.startswith(BENFICA_NAME)


def parse_competition_line(
    first_line: str,
) -> tuple[Optional[str], Optional[str], Optional[int]]:
    """
    Parse the first line of the DESCRIPTION into:
    - competition
    - season
    - matchday

    Handles things like:
    - "Campeonato Nacional Masculino | 25/26 - Jornada 4"
    - "Segunda Liga 25/26 - Jornada 9"
    - "CEV Challenge Cup 25/26"
    """
    first_line = first_line.strip()
    if not first_line:
        return None, None, None

    competition: Optional[str] = None
    season: Optional[str] = None
    matchday: Optional[int] = None

    if "|" in first_line:
        comp_name, rest = [s.strip() for s in first_line.split("|", 1)]
        competition = comp_name
        rest = rest.strip()

        if "-" in rest:
            # e.g. "25/26 - Jornada 4"
            season_part, rest2 = [s.strip() for s in rest.split("-", 1)]
            season = season_part

            m = re.search(r"Jornada\s+(\d+)", rest2)
            if m:
                matchday = int(m.group(1))
        else:
            # just "25/26" → treat as season
            if re.match(r"^\d{2}/\d{2}$", rest) or re.match(r"^\d{4}/\d{2}$", rest):
                season = rest
    else:
        # Try "Segunda Liga 25/26 - Jornada 9" or "CEV Challenge Cup 25/26"
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

    return competition, season, matchday


def extract_ticket_url(description: str) -> Optional[str]:
    """Find the first HTTP(S) URL in the description (usually the ticket link)."""
    for line in description.splitlines():
        line = line.strip()
        if line.startswith("http"):
            return line
    return None


def parse_summary(summary: str) -> Dict[str, Any]:
    """
    Break SUMMARY into:
    - event_type: "match" or "other"
    - team_a, team_b
    - benfica_home, opponent
    - sport, squad_label
    - broadcast (e.g. "📺 BTV")
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
            "broadcast": None,
        }

    # e.g. "⚽ SL Benfica x Paços Ferreira | Equipa B | 📺 BTV"
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
            "broadcast": None,
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

    # 2) Look at segments AFTER the match for modality / broadcast info
    metadata_segments = segments[match_idx + 1 :]

    modality_segment: Optional[str] = None
    broadcast_info: Optional[str] = None

    for seg in metadata_segments:
        # If it looks like TV/broadcast info, stash separately and skip for modality
        if any(b in seg for b in BROADCAST_KEYWORDS):
            broadcast_info = seg
            continue

        # First non-broadcast segment after the match we treat as "modality / squad"
        if modality_segment is None:
            modality_segment = seg

    sport: Optional[str] = None
    squad_label: Optional[str] = None

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
        "broadcast": broadcast_info,
    }


# -------------------------------------------------------------------
# Core parsing logic
# -------------------------------------------------------------------


def parse_event(component, source_name: str) -> Event:
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

    lines = description.splitlines()
    first_line = lines[0].strip() if lines else ""
    competition, season, matchday = (
        parse_competition_line(first_line) if first_line else (None, None, None)
    )

    # 1) Ticketing events short-circuit
    if is_ticketing_event(summary, description, competition):
        ticket_url = extract_ticket_url(description)
        return Event(
            uid=uid,
            source_name=source_name,
            event_type="ticketing",
            start=dtstart,
            end=dtend,
            summary=summary,
            description=description,
            venue_name=location,
            sport=None,
            squad_label=None,
            benfica_home=None,
            opponent=None,
            competition=competition,
            season=season,
            matchday=matchday,
            ticket_url=ticket_url,
            broadcast=None,
        )

    # 2) Normal summary parsing (matches / other events)
    summary_info = parse_summary(summary)

    event_type = summary_info["event_type"]
    benfica_home = summary_info["benfica_home"]
    opponent = summary_info["opponent"]
    sport = summary_info["sport"]
    squad_label = summary_info["squad_label"]
    broadcast = summary_info["broadcast"]

    # 3) Ticket URL extraction (for matches & other events)
    ticket_url = None
    if "bilhete" in description.lower():
        ticket_url = extract_ticket_url(description)

    # 4) Football fallback heuristic
    if event_type == "match" and sport is None:
        summary_lower = summary.lower()
        comp_lower = (competition or "").lower()

        looks_like_football = False

        # football emoji in summary
        if "⚽" in summary or "⚽️" in summary:
            looks_like_football = True

        # or competition name hints it's football
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

    return Event(
        uid=uid,
        source_name=source_name,
        event_type=event_type,
        start=dtstart,
        end=dtend,
        summary=summary,
        description=description,
        venue_name=location,
        sport=sport,
        squad_label=squad_label,
        benfica_home=benfica_home,
        opponent=opponent,
        competition=competition,
        season=season,
        matchday=matchday,
        ticket_url=ticket_url,
        broadcast=broadcast,
    )
