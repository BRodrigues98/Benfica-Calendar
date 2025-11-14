"""
Fetch and parse the eCal ICS feed(s) from SLBenfica's eCal website: https://benfica.ecal.com/
and normalise events into a structured list.

TODO:
- Create a database and save into it

Author: Bruno Rodrigues (BRodrigues98)
"""


import json

from .client import run_import
from .models import Event, to_serializable


def print_event(event: Event) -> None:
    """Pretty-print one event as JSON."""
    print(
        json.dumps(
            event.to_dict(),
            indent=4,
            ensure_ascii=False,
            sort_keys=True,
            default=to_serializable,
        )
    )

def main():
    events = run_import()
    match_events = [e for e in events if e.event_type == "match"]
    for e in match_events[:50]:
        print_event(e)

if __name__ == "__main__":
    main()