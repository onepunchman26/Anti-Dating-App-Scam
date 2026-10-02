"""Browser boundary for the loopback client; not authentication for a public API."""

from urllib.parse import urlsplit

from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


def _origin(value: str) -> tuple[str, str, int] | None:
    try:
        parsed = urlsplit(value)
        if (
            parsed.scheme not in ("http", "https")
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
        ):
            return None
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        return parsed.scheme, parsed.hostname.lower(), port
    except ValueError:
        return None


class LocalBrowserBoundary:
    """Reject foreign origins and DNS-rebinding hosts before route execution.

    No-Origin requests remain available to local non-browser clients. This is
    not protection against other processes running as the same OS user.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = Headers(scope=scope)
        hosts = headers.getlist("host")
        target = _origin(f"{scope['scheme']}://{hosts[0]}") if len(hosts) == 1 else None
        allowed = target is not None and target[1] in {"127.0.0.1", "localhost", "::1"}
        origins = headers.getlist("origin")
        if origins:
            allowed = allowed and len(origins) == 1 and _origin(origins[0]) == target
        # Browser requests with stripped Origin still carry fetch metadata.
        if headers.get("sec-fetch-site") in {"cross-site", "same-site"}:
            allowed = False
        if not allowed:
            response = JSONResponse(
                {"detail": "Local app requests must come from its own loopback origin."},
                status_code=403,
            )
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)
