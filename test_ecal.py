from icalendar import Calendar
from datetime import datetime
import pytz


events = []
#Open file
with open("SL_Benfica.ics", "rb") as f:
    cal = Calendar.from_ical(f.read())

print("Events found:\n")

test = 0
for component in cal.walk():
    if component.name == "VEVENT":
        start = component.get("dtstart").dt
        if isinstance(start, datetime) and start.tzinfo:
            start = start.astimezone(pytz.timezone("Europe/Lisbon"))

        events.append({
            "start": start,
            "summary": component.get("summary"),
            "location": component.get("location"),
            "uid": component.get("uid"),
        })
        test = test + 1


# 🔥 Sort by date
events = sorted(events, key=lambda e: e["start"])

# Print
for e in events:
    print(e["start"], "|", e["summary"], "|", e["location"], "| UID=" + e["uid"])

print("Done")