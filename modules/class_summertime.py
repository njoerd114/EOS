import datetime
import pytz

def is_dst_change(tag, timezone="Europe/Berlin"):
    """Prüft, ob an einem gegebenen Tag die Sommerzeit beginnt oder endet."""
    tz = pytz.timezone(timezone)
    # Hole den aktuellen Tag und den nächsten Tag
    current_day = datetime.datetime(tag.year, tag.month, tag.day)
    next_day = current_day + datetime.timedelta(days=1)

    # Lokalisiere die Tage in der gegebenen Zeitzone
    current_day_localized = tz.localize(current_day, is_dst=None)
    next_day_localized = tz.localize(next_day, is_dst=None)

    # Prüfe, ob die UTC-Offsets unterschiedlich sind (DST-Wechsel)
    dst_change = current_day_localized.dst() != next_day_localized.dst()

    return dst_change

# # Beispielverwendung
# start_datum = datetime.datetime(2024, 3, 31)  # Datum der DST-Umstellung
# if is_dst_change(start_datum):
    # prediction_hours = 23  # Anpassung auf 23 hours für DST-Wechseltage
# else:
    # prediction_hours = 24  # Standardwert für Tage ohne DST-Wechsel
