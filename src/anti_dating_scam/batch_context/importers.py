"""Bounded local adapters for explicitly selected exports, URL lists and note folders."""

from __future__ import annotations

import csv
import io
import json
import os
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, parse_qsl, urlencode, urlsplit

from anti_dating_scam.batch_context.models import Material, Preview, Video, fingerprint
from anti_dating_scam.services.report_review import ReportReviewService

URL = re.compile(r"https?://[^\s<>\[\]\"')]+")
MAX_BYTES = 2_000_000
MAX_TOTAL = 16_000_000


def canonical_url(value):
    parts = urlsplit(value.strip().rstrip(".,;，。"))
    host = (parts.hostname or "").lower()
    if (
        parts.scheme not in {"https", "http"}
        or parts.username
        or parts.password
        or parts.port not in {None, 443, 80}
        or "." not in host
        or host.endswith((".local", ".localhost"))
        or re.fullmatch(r"[\d.]+", host)
    ):
        raise ValueError("unsupported_url")
    if host in {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}:
        video_id = (
            parts.path.strip("/") if host == "youtu.be" else parse_qs(parts.query).get("v", [""])[0]
        )
        if parts.path.startswith(("/shorts/", "/embed/", "/live/")):
            video_id = parts.path.split("/")[2]
        if not re.fullmatch(r"[a-zA-Z0-9_-]{11}", video_id):
            raise ValueError("playlist_needs_export")
        return "youtube", f"https://www.youtube.com/watch?v={video_id}", video_id
    if host in {"bilibili.com", "www.bilibili.com", "m.bilibili.com"}:
        match = re.search(r"/video/(BV[a-zA-Z0-9]{10}|av[0-9]+)(?:/|$)", parts.path)
        if not match:
            raise ValueError("collection_needs_export")
        return "bilibili", "https://www.bilibili.com/video/" + match[1], match[1]
    if host in {"tiktok.com", "www.tiktok.com", "m.tiktok.com"}:
        match = re.fullmatch(r"/(@[\w.-]+)/video/([0-9]{10,25})/?", parts.path)
        if not match:
            raise ValueError("short_link_needs_full_url")
        return "tiktok", f"https://www.tiktok.com/{match[1]}/video/{match[2]}", match[2]
    if host in {"vm.tiktok.com", "vt.tiktok.com", "b23.tv"}:
        raise ValueError("short_link_needs_full_url")
    # Generic URLs remain local evidence identifiers and are NEVER fetched.
    query = [
        (k, v)
        for k, v in parse_qsl(parts.query)
        if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid"}
    ]
    if any(re.search(r"token|secret|password|signature|auth|api.?key", k, re.I) for k, _ in query):
        raise ValueError("credential_url")
    clean = f"https://{host}{parts.path}" + ("?" + urlencode(sorted(query)) if query else "")
    return "other", clean, clean


def _date(value):
    if not value:
        return ""
    try:
        return datetime.fromisoformat(str(value).strip().replace("Z", "+00:00")).isoformat()
    except ValueError:
        return ""


def video_from_row(row, label="Imported list / 导入列表"):
    normalized = {re.sub(r"[ _-]", "", str(k)).lower(): v for k, v in row.items()}
    url = (
        normalized.get("url")
        or normalized.get("link")
        or normalized.get("videourl")
        or normalized.get("videolandingpagelink")
    )
    if not url and normalized.get("videoid"):
        url = "https://www.youtube.com/watch?v=" + str(normalized["videoid"])
    source, clean, key = canonical_url(str(url or ""))
    materials = []
    for field, origin in (
        ("transcript", "transcript"),
        ("description", "description"),
        ("summary", "existing_summary"),
        ("existingsummary", "existing_summary"),
        ("annotation", "user_annotation"),
        ("userannotation", "user_annotation"),
    ):
        raw = normalized.get(field)
        if isinstance(raw, str) and raw.strip():
            materials.append(
                Material(
                    origin=origin,
                    text=raw.strip()[:4000],
                    provenance=label[:180],
                    truncated=len(raw.strip()) > 4000,
                )
            )
    return Video(
        id=fingerprint([source, key]),
        url=clean,
        source=source,
        title=str(normalized.get("title") or "")[:300],
        materials=materials,
        collections=[str(normalized.get("collection") or label)[:120]],
        saved_at=_date(
            normalized.get("savedat")
            or normalized.get("date")
            or normalized.get("playlistvideocreationtimestamp")
        ),
    )


def _json_rows(data):
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        raise ValueError("unsupported_export")
    if isinstance(data.get("items"), list):
        return data["items"]
    # Only the recognized saved/liked sections; no recursive extraction of messages/history.
    activity = data.get(
        "Likes and Favourites",
        data.get("Likes and Favorites", data.get("Activity", data.get("Your Activity", data))),
    )
    rows = []
    if isinstance(activity, dict):
        for section in ("Like List", "Favorite Videos", "Favourite Videos"):
            value = activity.get(section, {})
            if isinstance(value, list):
                rows += [dict(item, collection=section) for item in value if isinstance(item, dict)]
            if isinstance(value, dict):
                for field in ("ItemFavoriteList", "FavoriteVideoList", "VideoList", "ItemList"):
                    if isinstance(value.get(field), list):
                        rows += [
                            dict(item, collection=section)
                            for item in value[field]
                            if isinstance(item, dict)
                        ]
    if not rows:
        raise ValueError("unsupported_export")
    return rows


def parse_text(text, suffix=".txt", label="Pasted list / 粘贴列表"):
    if len(text.encode("utf-8")) > MAX_BYTES:
        raise ValueError("file_too_large")
    if suffix == ".json":
        return _json_rows(json.loads(text))
    if suffix == ".csv":
        # Takeout playlist CSVs may include an initial playlist-metadata table.
        lines = text.splitlines()
        for index, line in enumerate(lines):
            if re.match(r"\s*\"?Video\s*Id\"?\s*,", line, re.I):
                lines = lines[index:]
                break
        return list(csv.DictReader(io.StringIO("\n".join(lines))))
    if suffix == ".md":
        # A note is supplied context, not proof of authorship or agreement.
        urls = list(dict.fromkeys(URL.findall(text)))
        fields = {}
        recognized = {
            "transcript": "transcript",
            "description": "description",
            "summary": "summary",
            "user annotation": "annotation",
            "字幕": "transcript",
            "描述": "description",
            "摘要": "summary",
            "我的备注": "annotation",
        }
        for heading, body in re.findall(
            r"^#{1,6}\s+([^\n]+)\n(.*?)(?=^#{1,6}\s|\Z)", text, re.M | re.S
        ):
            key = recognized.get(heading.strip().lower())
            if key:
                fields[key] = body.strip()
        if not fields:
            prose = URL.sub("", text).strip()
            if prose:
                fields["summary"] = prose
        return [dict(fields, url=url, collection=label) for url in urls]
    rows = []
    date = ""
    for line in text.splitlines():
        if line.strip().startswith("Date:"):
            date = line.split(":", 1)[1].strip()
        for url in URL.findall(line):
            rows.append({"url": url, "date": date, "collection": label})
    return rows


def preview_rows(rows, *, notices=()):
    videos, duplicates, invalid = {}, 0, 0
    for row in rows:
        try:
            video = video_from_row(row)
        except (ValueError, TypeError, AttributeError):
            invalid += 1
            continue
        old = videos.get(video.id)
        if not old and len(videos) >= 1000:
            raise ValueError("batch_limit_1000")
        if old:
            duplicates += 1
            # Same text in a derivative note has one origin in this batch.
            material = {m.text.strip(): m for m in old.materials}
            for item in video.materials:
                material.setdefault(item.text.strip(), item)
            video = old.model_copy(
                update={
                    "materials": list(material.values())[:8],
                    "title": old.title or video.title,
                    "collections": list(dict.fromkeys(old.collections + video.collections))[:30],
                    "saved_at": min(filter(None, [old.saved_at, video.saved_at]), default=""),
                }
            )
        videos[video.id] = video
    return Preview(
        videos=list(videos.values()),
        duplicates=duplicates,
        invalid=invalid,
        notices=list(notices)[:100],
    )


def import_files(paths):
    rows, notices, total = [], [], 0
    for path in paths:
        path = Path(os.path.abspath(path))
        if path.suffix.lower() not in {".txt", ".csv", ".json", ".md"}:
            notices.append("unsupported_file")
            continue
        guard = ReportReviewService(path.parent)
        try:
            raw = guard._read(path, MAX_BYTES)
            total += len(raw)
            if total > MAX_TOTAL:
                raise ValueError("selection_too_large")
            incoming = parse_text(raw.decode("utf-8-sig"), path.suffix.lower(), path.stem[:120])
            rows += incoming
            if len(rows) > 5000:
                raise ValueError("selection_too_large")
        except (OSError, UnicodeError, ValueError):
            if total > MAX_TOTAL or len(rows) > 5000:
                raise ValueError("selection_too_large") from None
            notices.append("file_unreadable_or_unsupported")
    return preview_rows(rows, notices=notices)


def import_notes(folder):
    root = Path(os.path.abspath(folder))
    guard = ReportReviewService(root)
    guard._check(root, directory=True)
    paths = []
    for directory, children, files in os.walk(root, followlinks=False):
        guard._check(Path(directory), directory=True)
        children[:] = [name for name in children if not name.startswith(".")]
        for child in children:
            guard._check(Path(directory) / child, directory=True)
        for name in files:
            if name.lower().endswith(".md") and not name.startswith("."):
                paths.append(Path(directory) / name)
                if len(paths) > 1000:
                    raise ValueError("folder_limit_1000")
    return import_files(sorted(paths))
