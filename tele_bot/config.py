from datetime import time

CONFIG = {
    "BOT_TOKEN": "7305046364:AAGHE_yJ84H63C_eBHGw_YKK1JVLmE8XTgo",
    "STATION_DATA_URL": "https://raw.githubusercontent.com/Ratana-tep/PTT_STATION_MAP/master/data/markers.json",
    "DEFAULT_OPEN_TIME": time(5, 0),  # 5:00 AM
    "DEFAULT_CLOSE_TIME": time(20, 30),  # 8:30 PM
}

SERVICES = {
    "Amazon": {"name": "Amazon Coffee", "icon": "☕", "commands": ["amazon"]},
    "7-Eleven": {"name": "7-Eleven Store", "icon": "🏪", "commands": ["7eleven", "7-eleven", "7eleven"]},
    "Otr": {"name": "Otteri Store", "icon": "👕", "commands": ["otr"]},
    "Fleet card": {"name": "Fleet Card Accepted", "icon": "💳", "commands": ["fleet", "fleet card", "wing"]},
    "KHQR": {"name": "KHQR Payment", "icon": "📍", "commands": ["khqr"]},
    "Cash": {"name": "Cash Payment", "icon": "💸", "commands": ["cash"]},
    "EV": {"name": "EV Charging Station", "icon": "⚡", "commands": ["ev"]}
}