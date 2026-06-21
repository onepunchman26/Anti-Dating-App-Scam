# Browser Export Safety

Assisted browser export exists for user self-access to the user's own data.

## Hard Boundaries

The project must not:

- steal cookies, tokens, passwords, sessionStorage, localStorage, or browser secrets;
- bypass login;
- bypass CAPTCHA;
- bypass rate limits or platform restrictions;
- reverse-engineer private APIs;
- scrape hidden network responses;
- scrape other users' private data;
- run invisibly in the background;
- upload exported chats to any server;
- send exported chats to an LLM provider without explicit user consent;
- generate fake evidence;
- modify conversations or impersonate the user;
- bypass dating or social platform moderation.

## Allowed Behavior

The project may:

- launch a visible local browser session;
- require the user to manually log in;
- wait for the user to confirm readiness;
- navigate visible chat list items;
- click visible user-facing export controls;
- interact with a user-installed extension when technically feasible;
- save downloaded or captured files locally;
- pause on errors;
- keep an audit log that excludes full chat contents;
- import exported local files into the profile builder.

## Redaction Recommendations

Before profile generation, users should review and redact:

- identity documents;
- financial details;
- private images;
- passwords or recovery phrases;
- third-party personal information;
- sensitive health, legal, or workplace information.

## Consent Reminder

Import only your own data or data you have permission to process. Exported data stays local in the MVP unless the user explicitly shares or uploads it elsewhere.
