"""Explicit node configuration and pasted invitation parsing; no arbitrary URL fetching."""

from __future__ import annotations

import json
import re
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


class PeerClientError(ValueError):
    pass


def node_origin(value):
    parsed = urlsplit(value)
    if (
        parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in ("", "/")
        or not parsed.hostname
    ):
        raise PeerClientError("invalid_node")
    if parsed.scheme != "https" and not (
        parsed.scheme == "http" and parsed.hostname == "127.0.0.1"
    ):
        raise PeerClientError("https_required")
    if parsed.port is not None and not 1 <= parsed.port <= 65535:
        raise PeerClientError("invalid_node")
    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


def invitation_link(origin, identity):
    if not re.fullmatch(r"[A-Za-z0-9_-]{43}", identity):
        raise PeerClientError("invalid_invitation")
    return node_origin(origin) + "/invite#" + identity


def parse_invitation(value, configured_origin):
    origin = node_origin(configured_origin)
    parsed = urlsplit(value.strip())
    if parsed.scheme == "slowmatch" and parsed.netloc == "invite":
        if parsed.path or parsed.fragment:
            raise PeerClientError("invalid_invitation")
        query = parse_qs(parsed.query, strict_parsing=True)
        if set(query) != {"node", "id"} or any(len(v) != 1 for v in query.values()):
            raise PeerClientError("invalid_invitation")
        value = invitation_link(query["node"][0], query["id"][0])
        parsed = urlsplit(value)
    if (
        f"{parsed.scheme}://{parsed.netloc}" != origin
        or parsed.path != "/invite"
        or parsed.query
        or not re.fullmatch(r"[A-Za-z0-9_-]{43}", parsed.fragment)
    ):
        raise PeerClientError("invitation_node_mismatch")
    return parsed.fragment


def app_link(origin, identity):
    return "slowmatch://invite?" + urlencode({"node": node_origin(origin), "id": identity})


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise PeerClientError("redirect_rejected")


class PeerClient:
    def __init__(self, origin, token="", *, opener=None):
        self.origin = node_origin(origin)
        self.token = token
        self.opener = opener or build_opener(ProxyHandler({}), NoRedirect())

    def call(self, route, payload=None, *, authenticated=True):
        if not re.fullmatch(r"/peer/[a-z-]+", route):
            raise PeerClientError("invalid_route")
        headers = {"Content-Type": "application/json"}
        if authenticated:
            if not self.token:
                raise PeerClientError("unauthorized")
            headers["Authorization"] = "Bearer " + self.token
        raw = None if payload is None else json.dumps(payload, ensure_ascii=False).encode()
        request = Request(self.origin + route, data=raw, headers=headers)
        try:
            with self.opener.open(request, timeout=35) as response:
                result = response.read(96_001)
                if len(result) > 96_000:
                    raise PeerClientError("response_too_large")
                return json.loads(result)["data"]
        except HTTPError as exc:
            # API errors expose only known stable codes, never body excerpts.
            try:
                code = json.loads(exc.read(1024)).get("detail", "request_failed")
                if not isinstance(code, str) or not re.fullmatch(r"[a-z_]{1,50}", code):
                    code = "request_failed"
            except Exception:
                code = "request_failed"
            raise PeerClientError(code) from None
        except PeerClientError:
            raise
        except Exception:
            raise PeerClientError("connection_failed") from None
