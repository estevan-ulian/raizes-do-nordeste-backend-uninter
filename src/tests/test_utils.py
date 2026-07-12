from starlette.requests import Request

from src.utils import get_request_ip


def make_request(headers: dict[str, str] | None = None) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [(key.lower().encode(), value.encode()) for key, value in (headers or {}).items()],
            "client": ("127.0.0.1", 12345),
        }
    )


def test_get_request_ip_prefers_first_forwarded_for_ip():
    request = make_request({"X-Forwarded-For": "203.0.113.10, 10.0.0.1"})

    assert get_request_ip(request) == "203.0.113.10"


def test_get_request_ip_uses_real_ip_before_client_host():
    request = make_request({"X-Real-IP": "203.0.113.11"})

    assert get_request_ip(request) == "203.0.113.11"


def test_get_request_ip_falls_back_to_client_host():
    request = make_request()

    assert get_request_ip(request) == "127.0.0.1"
