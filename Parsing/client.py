import requests
from datetime import datetime
from typing import List
from icalendar import Calendar

from .config import ECAL_URLS
from .models import Event
from .parsing import parse_event

def fetch_and_parse(url: str, source_name: str) -> List[Event]:
    print(f"Fetching: {url}")
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()

    cal = Calendar.from_ical(resp.content)
    events: List[Event] = []

    for component in cal.walk():
        if component.name != "VEVENT":
            continue
        events.append(parse_event(component, source_name=source_name))

    return events


def run_import() -> List[Event]:
    all_events: List[Event] = []

    for idx, url in enumerate(ECAL_URLS):
        source_name = f"feed_{idx}"
        events = fetch_and_parse(url, source_name)
        all_events.extend(events)

    # sort by start time
    all_events.sort(key=lambda e: e.start or datetime.max)
    return all_events
