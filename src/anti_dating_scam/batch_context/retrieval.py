"""Optional public oEmbed titles only. No cookies, redirects, arbitrary hosts or HTML."""

import json
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from anti_dating_scam.batch_context.importers import canonical_url


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class PublicMetadata:
    ENDPOINTS = {
        "youtube": "https://www.youtube.com/oembed",
        "tiktok": "https://www.tiktok.com/oembed",
    }

    def fetch(self, video):
        source, url, _ = canonical_url(video.url)
        if source != video.source or source not in self.ENDPOINTS:
            raise ValueError("metadata_unsupported")
        request = Request(
            self.ENDPOINTS[source] + "?" + urlencode({"url": url, "format": "json"}),
            headers={"Accept": "application/json", "User-Agent": "AI-SlowMatch"},
        )
        opener = build_opener(ProxyHandler({}), NoRedirect())
        with opener.open(request, timeout=8) as response:
            raw = response.read(65_537)
        if len(raw) > 65_536:
            raise ValueError("metadata_too_large")
        title = json.loads(raw).get("title")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("metadata_unavailable")
        # Ignore author identifiers, images, HTML and arbitrary embedded URLs entirely.
        return video.model_copy(update={"title": title.strip()[:300]})
