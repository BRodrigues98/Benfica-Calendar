from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

@dataclass
class Event:
    """Structured representation of one ECAL VEVENT."""

    uid: str
    source_name: str
    event_type: str  # "match", "ticketing", "other"
    start: datetime
    end: Optional[datetime]
    summary: str
    description: str
    venue_name: str

    sport: Optional[str]
    squad_label: Optional[str]
    benfica_home: Optional[bool]
    opponent: Optional[str]

    competition: Optional[str]
    season: Optional[str]
    matchday: Optional[int]

    ticket_url: Optional[str]
    broadcast: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a plain dict (good for JSON, DB, etc.)."""
        return {
            "uid": self.uid,
            "source_name": self.source_name,
            "event_type": self.event_type,
            "start": self.start,
            "end": self.end,
            "summary": self.summary,
            "description": self.description,
            "venue_name": self.venue_name,
            "sport": self.sport,
            "squad_label": self.squad_label,
            "benfica_home": self.benfica_home,
            "opponent": self.opponent,
            "competition": self.competition,
            "season": self.season,
            "matchday": self.matchday,
            "ticket_url": self.ticket_url,
            "broadcast": self.broadcast,
        }


def to_serializable(obj: Any):
    """Default JSON serializer for objects we care about."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
