# Chat2file Automation Limits

Chat2file-assisted export is experimental and optional.

## Why It Is Fragile

- Extension popup automation may be unreliable.
- Playwright can load unpacked extensions in bundled Chromium with a persistent context, but Google Chrome or Microsoft Edge may restrict side-loading flags.
- Extension ids can change.
- DOM selectors can break when the extension or website updates.
- Platform UI can change without notice.
- Download timing can vary.

## Required Behavior On Failure

Failures should pause instead of forcing actions. The user should be able to manually intervene, resume, or stop.

The assistant must not:

- bypass login;
- bypass CAPTCHA;
- use hidden APIs;
- scrape network responses;
- read browser storage;
- run unlimited exports;
- run invisibly in the background.

## Current MVP Behavior

The MVP builds a safe Chat2file-assisted plan and exposes the GUI controls, but it does not force extension popup automation. Native visible-page export is the safer fallback.
