"""Small request envelope for the in-memory matching experiment.

This is a resource bound, not a public-service abuse/rate-limiting solution.
"""

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

MAX_MATCHMAKING_BODY = 16_384
MAX_PEER_RESULT_BODY = 128_000


class MatchmakingBoundary:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not scope["path"].startswith(("/matchmaking/", "/peer/")):
            await self.app(scope, receive, send)
            return
        body = bytearray()
        limit = MAX_PEER_RESULT_BODY if scope["path"] == "/peer/finish" else MAX_MATCHMAKING_BODY
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > limit:
                response = JSONResponse(status_code=413, content={"detail": "Request too large."})
                await response(scope, receive, send)
                return
            if not message.get("more_body", False):
                break
        delivered = False

        async def bounded_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        async def private_send(message):
            if message["type"] == "http.response.start":
                message["headers"] = list(message.get("headers", [])) + [
                    (b"cache-control", b"no-store"),
                    (b"referrer-policy", b"no-referrer"),
                ]
            await send(message)

        await self.app(scope, bounded_receive, private_send)
