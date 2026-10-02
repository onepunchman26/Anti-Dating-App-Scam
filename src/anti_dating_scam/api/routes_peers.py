"""Thin authenticated routes for the persistent consent-controlled rendezvous mode."""

from __future__ import annotations

import html
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import Field, field_validator

from anti_dating_scam.api.routes_matchmaking import PrivateValidationRoute, _access_token
from anti_dating_scam.matchmaking.peer_coordinator import PeerCoordinator, PeerError
from anti_dating_scam.matchmaking.peer_models import (
    CompareFinish,
    Contract,
    InviteAction,
    InviteCreate,
    ProfileUpdate,
    PublicUpdate,
    Registration,
)


class PeerResponse(Contract):
    data: dict[str, Any]


class InvitationID(Contract):
    invitation: str = Field(pattern=r"^[A-Za-z0-9_-]{43}$")


class DiscoveryChoice(Contract):
    authorized_only: bool = False


class Control(Contract):
    action: Literal["pause", "withdraw", "block", "delete"]
    target: str | None = Field(default=None, pattern=r"^[a-f0-9]{32}$")
    confirmed: Literal[True]

    @field_validator("confirmed", mode="before")
    @classmethod
    def exact_confirmation(cls, value):
        if value is not True:
            raise ValueError("confirmation_required")
        return value


router = APIRouter(prefix="/peer", route_class=PrivateValidationRoute)
landing_router = APIRouter()


def coordinator(request: Request):
    return request.app.state.peer_coordinator


def token(request: Request):
    if request.query_params:
        raise HTTPException(400, "query_parameters_rejected")
    return _access_token(request)


Service = Annotated[PeerCoordinator, Depends(coordinator)]
Token = Annotated[str, Depends(token)]


def result(call, *args, **kwargs):
    try:
        return PeerResponse(data=call(*args, **kwargs))
    except PeerError as exc:
        raise HTTPException(409, str(exc)) from None
    except Exception:
        raise HTTPException(400, "request_failed") from None


@router.post("/register", response_model=PeerResponse)
def register(body: Registration, service: Service):
    return result(service.register, body)


@router.get("/me", response_model=PeerResponse)
def me(service: Service, access: Token):
    return result(service.me, access)


@router.post("/profile", response_model=PeerResponse)
def profile(body: ProfileUpdate, service: Service, access: Token):
    return result(service.update_profile, access, body)


@router.post("/public", response_model=PeerResponse)
def public(body: PublicUpdate, service: Service, access: Token):
    return result(service.public_update, access, body)


@router.post("/discover", response_model=PeerResponse)
def discover(body: DiscoveryChoice, service: Service, access: Token):
    return result(service.discover, access, authorized_only=body.authorized_only)


@router.post("/invite", response_model=PeerResponse)
def invite(body: InviteCreate, service: Service, access: Token):
    return result(service.create_invitation, access, body)


@router.get("/invitations", response_model=PeerResponse)
def invitations(service: Service, access: Token):
    return result(service.invitations, access)


@router.post("/invitation-action", response_model=PeerResponse)
def invitation_action(body: InviteAction, service: Service, access: Token):
    return result(service.act, access, body)


@router.post("/preview", response_model=PeerResponse)
def preview(body: InvitationID, service: Service, access: Token):
    return result(service.preview_pair, access, body.invitation)


@router.post("/prepare", response_model=PeerResponse)
def prepare(body: InvitationID, service: Service, access: Token):
    return result(service.prepare_comparison, access, body.invitation)


@router.post("/finish", response_model=PeerResponse)
def finish(body: CompareFinish, service: Service, access: Token):
    return result(service.finish_comparison, access, body.invitation, body.ticket, body.report)


@router.post("/result", response_model=PeerResponse)
def read_result(body: InvitationID, service: Service, access: Token):
    return result(service.read_comparison, access, body.invitation)


@router.post("/control", response_model=PeerResponse)
def control(body: Control, service: Service, access: Token):
    if body.confirmed is not True:
        raise HTTPException(400, "confirmation_required")
    return result(service.control, access, body.action, body.target)


@landing_router.get("/invite", response_class=HTMLResponse)
def landing():
    # The fragment is never sent to this server or rendered from private profile data.
    return HTMLResponse(
        """<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width">
<title>AI-SlowMatch invitation / 邀请</title>
<main><h1>Private comparison invitation / 私密比较邀请</h1>
<p>For self-declared adults aged 18+. Opening this page shares no profile and gives no consent.
Recipient claims are single-recipient; the sender must confirm the claimant before comparison.</p>
<p>仅限自行声明年满 18 岁的成年人。打开页面不分享资料，也不表示同意。每份邀请限一位接收人，
认领后发起人仍须确认对方，再由双方批准比较。</p>
<p>Already installed? Open the app or paste this whole link into Introductions &amp; invitations.
If the application is absent, obtain the app from its owner. No software downloads automatically.
A browser-only participation flow is not available.</p>
<p>已安装？打开应用，或把完整链接粘贴到“介绍与邀请”。尚未安装时请向应用所有者取得程序。
不会自动下载软件，目前不提供纯浏览器参与流程。本机链接只能在同一电脑使用。</p>
<p><a id="open">Open installed app / 打开已安装应用</a></p>
<p>Use a pseudonym, check age eligibility, approve a limited matching profile,
and review permissions.
Link possession never gives access to a private personal database. No emails are sent.</p>
<p>使用化名，确认成年资格，批准有限匹配资料并审阅权限。持有链接不能访问私人模型，不会发送邮件。</p>
</main><script>
const id=location.hash.slice(1); const a=document.getElementById('open');
if (/^[A-Za-z0-9_-]{43}$/.test(id)) {
 a.href='slowmatch://invite?node='+encodeURIComponent(location.origin)
     +'&id='+encodeURIComponent(id);
} else { a.textContent='Invalid invitation / 邀请格式无效'; }
</script></html>""".replace("\n+", "\n"),
        headers={
            "Cache-Control": "no-store",
            "Referrer-Policy": "no-referrer",
            "Content-Security-Policy": (
                "default-src 'none'; script-src 'unsafe-inline'; frame-ancestors 'none'"
            ),
            "X-Content-Type-Options": "nosniff",
        },
    )


@landing_router.get("/p/{identity}", response_class=HTMLResponse)
def public_intro(identity: str, service: Service):
    import re

    if not re.fullmatch(r"[a-f0-9]{32}", identity):
        raise HTTPException(404, "unavailable")
    try:
        data = service.public_read(identity)
    except PeerError:
        raise HTTPException(404, "unavailable") from None
    return HTMLResponse(
        '<!doctype html><meta charset="utf-8"><h1>'
        + html.escape(data["alias"])
        + "</h1><pre>"
        + html.escape(data["text"])
        + "</pre>",
        headers={
            "Cache-Control": "no-store",
            "Referrer-Policy": "no-referrer",
            "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
            "X-Content-Type-Options": "nosniff",
        },
    )
