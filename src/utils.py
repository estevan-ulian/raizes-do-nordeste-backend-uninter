from datetime import datetime, timezone

from fastapi import Request


def datetime_to_gmt_str(dt: datetime) -> str:
    """Convert a datetime object to a GMT string format."""
    return dt.strftime("%a, %d %b %Y %H:%M:%S GMT")


def get_utc_now() -> datetime:
    """Get the current UTC datetime."""
    return datetime.now(timezone.utc)


def get_request_ip(request: Request) -> str | None:
    """Return the best available client IP address for audit logs."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", maxsplit=1)[0].strip() or None
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip() or None
    return request.client.host if request.client else None
