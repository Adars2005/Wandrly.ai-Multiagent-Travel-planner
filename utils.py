# backend/utils.py
import re
from datetime import datetime, timedelta
import dateparser

def parse_trip_sentence(sentence: str):
    """
    Extract city, start_date, end_date, duration from a natural language trip sentence.
    Example: "Plan a 2-day trip to New Delhi starting tomorrow"
    """
    # 1) Duration in days
    duration_match = re.search(r'(\d+)-day', sentence)
    duration_days = int(duration_match.group(1)) if duration_match else 1

    # 2) Start date (e.g., "starting tomorrow" or "from Sep 24")
    date_match = re.search(r'starting (.+)', sentence)
    if date_match:
        start_date_text = date_match.group(1)
        start_date = dateparser.parse(start_date_text).date()
    else:
        start_date = datetime.today().date()

    # 3) End date
    end_date = start_date + timedelta(days=duration_days - 1)

    # 4) City (simple heuristic: after 'trip to')
    city_match = re.search(r'trip to ([\w\s]+?)(?: starting|$)', sentence)
    city = city_match.group(1).strip() if city_match else "Unknown"

    return {
        "city": city,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "preferences": {}
    }
