from anti_dating_scam.browser_export.visible_text_extractor import VisibleTextExtractor


def test_visible_text_extractor_strips_script_style_and_nav_content() -> None:
    html = """
    <html>
      <head><style>.hidden { display: none; }</style></head>
      <body>
        <nav>Navigation noise</nav>
        <main>
          <h1>Conversation Title</h1>
          <p>User: I value slow trust.</p>
          <script>window.secretToken = "do-not-include";</script>
          <p>Assistant: Consider clear boundaries.</p>
        </main>
      </body>
    </html>
    """

    export = VisibleTextExtractor().extract_from_html(
        html,
        source_url="https://example.test/chat",
        page_title="Synthetic chat",
    )
    payload = export.to_dict()
    text = "\n".join(chunk["text"] for chunk in payload["chunks"])

    assert "Conversation Title" in text
    assert "slow trust" in text
    assert "clear boundaries" in text
    assert "Navigation noise" not in text
    assert "secretToken" not in text
    assert payload["source"] == "visible_page_export"
