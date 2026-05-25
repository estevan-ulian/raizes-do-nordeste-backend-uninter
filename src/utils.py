from datetime import datetime, timezone


def datetime_to_gmt_str(dt: datetime) -> str:
    """Convert a datetime object to a GMT string format."""
    return dt.strftime("%a, %d %b %Y %H:%M:%S GMT")


def get_utc_now() -> datetime:
    """Get the current UTC datetime."""
    return datetime.now(timezone.utc)
