# Assisted Browser Export

Local Assisted Chat Exporter is a user-assisted local automation helper for exporting the user's own AI chat history from a visible browser session.

It is designed to reduce repetitive clicking. It is not a stealth scraper, login bypasser, anti-bot bypass tool, cookie reader, or mass data exfiltration tool.

## Safety Model

The flow is:

```text
User launches local desktop app
  -> opens Assisted Browser Export tab
  -> reads safety checklist
  -> confirms "I am exporting my own data"
  -> app launches visible browser session
  -> user manually logs in
  -> user clicks "I am ready"
  -> automation either assists visible export clicks or captures visible page text
  -> local files are saved
  -> user imports exported files into the local profile builder
```

The browser session must be headed/visible for real user export. The app must not bypass login, CAPTCHA, rate limits, private APIs, or platform restrictions.

## Mode A: Chat2file-Assisted Export

This mode is experimental. It attempts to plan repetitive visible UI clicks around a user-installed Chat2file extension or visible export button. It may require:

- an unpacked extension path;
- an extension id;
- visible chat list selectors;
- visible export button selectors;
- a max chats per run limit;
- delay between export actions.

If extension automation is unreliable, the tool should pause and ask for manual intervention. It must not force actions or bypass platform protections.

## Mode B: Native Visible-Page Export

This safer fallback captures only visible text from the current page DOM. It saves local JSON and Markdown files with source URL, page title, timestamp, text chunks, and warnings.

It does not:

- access hidden network responses;
- read cookies;
- read localStorage or sessionStorage;
- call private APIs;
- upload exported files.

Visible-page export may be incomplete because it captures only what the browser page currently renders.

## Why Official Export Is Preferred

Official data export tools are usually more complete and less fragile than UI automation. Use official exports when available. Use assisted browser export only when official export is unavailable, incomplete, or too repetitive for local personal use.

## Troubleshooting

- If Playwright is missing, install `pip install -e ".[browser]"`.
- If browser launch fails, verify the export folder and user data directory are local paths.
- If extension automation fails, use visible-page export.
- If selectors stop working, the platform or extension UI may have changed.
- If CAPTCHA or login appears, complete it manually. The app must not bypass it.
