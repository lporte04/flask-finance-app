from datetime import date, timedelta
from flask import session

def get_effective_date():
    """
    Returns the current date plus any simulation offset set in the session.
    For admin users demonstrating features with time simulation.
    """
    today = date.today()
    # Get days_offset from session (default to 0 if not set)
    days_offset = session.get('date_simulation_offset', 0)
    
    if days_offset:
        return today + timedelta(days=days_offset)
    return today