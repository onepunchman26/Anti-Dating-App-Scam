import json
import re
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path

from anti_dating_scam.browser_export.export_models import ExportChunk, VisiblePageExport


class _VisibleTextHTMLParser(HTMLParser):
    SKIP_TAGS = {"script", "style", "noscript", "nav", "header", "footer", "svg"}

    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in self.SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self.SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            cleaned = " ".join(data.split())
            if cleaned:
                self.parts.append(cleaned)


class VisibleTextExtractor:
    """Extract only visible page text from DOM/HTML, never hidden API responses."""

    def extract_from_html(
        self,
        html: str,
        *,
        source_url: str,
        page_title: str,
    ) -> VisiblePageExport:
        parser = _VisibleTextHTMLParser()
        parser.feed(html)
        text = self._normalize_text("\n".join(parser.parts))
        chunks = self._to_chunks(text)
        return VisiblePageExport(
            source_url=source_url,
            page_title=page_title,
            chunks=chunks,
        )

    async def extract_from_playwright_page(self, page) -> VisiblePageExport:
        title = await page.title()
        url = page.url
        html = await page.content()
        return self.extract_from_html(html, source_url=url, page_title=title)

    def extract_from_sync_playwright_page(self, page) -> VisiblePageExport:
        title = page.title()
        url = page.url
        html = page.content()
        return self.extract_from_html(html, source_url=url, page_title=title)

    def save_export(self, export: VisiblePageExport, export_folder: str | Path) -> dict[str, Path]:
        folder = Path(export_folder)
        folder.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        base_name = f"visible_page_export_{timestamp}"
        json_path = folder / f"{base_name}.json"
        md_path = folder / f"{base_name}.md"
        payload = export.to_dict()
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        md_path.write_text(self.to_markdown(payload), encoding="utf-8")
        return {"json": json_path, "markdown": md_path}

    def to_markdown(self, export_payload: dict) -> str:
        lines = [
            "# Visible Page Chat Export",
            "",
            f"- Source URL: {export_payload.get('source_url', '')}",
            f"- Page title: {export_payload.get('page_title', '')}",
            f"- Captured at: {export_payload.get('captured_at', '')}",
            "",
            "## Warnings",
        ]
        for warning in export_payload.get("warnings", []):
            lines.append(f"- {warning}")
        lines.extend(["", "## Visible Text"])
        for chunk in export_payload.get("chunks", []):
            lines.append("")
            lines.append(f"### Chunk {chunk.get('order', 0)}")
            lines.append(chunk.get("text", ""))
        return "\n".join(lines).strip() + "\n"

    def _normalize_text(self, text: str) -> str:
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _to_chunks(self, text: str) -> list[ExportChunk]:
        if not text:
            return []
        paragraphs = [part.strip() for part in re.split(r"\n{2,}", text) if part.strip()]
        if not paragraphs:
            paragraphs = [text]
        return [
            ExportChunk(role="unknown", text=paragraph, order=index)
            for index, paragraph in enumerate(paragraphs)
        ]
