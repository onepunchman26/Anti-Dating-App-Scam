# ChatGPT Data Import

The desktop MVP supports local import of user-selected ChatGPT export files and pasted ChatGPT Memory Summary text.

## How Users Get An Export

Users can request ChatGPT data export from ChatGPT settings or the relevant privacy portal. The export ZIP may include chat history and other account data.

## Local Processing

The MVP:

- accepts a local `.zip` or `.json` file selected by the user;
- tries to find `conversations.json` or a similar exported chat history file;
- counts conversations and messages when the structure is recognized;
- summarizes a date range when timestamps are available;
- extracts limited snippets for local profile generation;
- does not upload the export anywhere.

If the structure is unknown, the parser fails gracefully and reports a warning or error.

## Memory Summary

Users may paste a ChatGPT Memory Summary manually. Memory Summary may not include everything ChatGPT remembers. Treat it as one input source, not an authoritative full self-profile.

## Privacy Guidance

- Import only your own data.
- Review and redact sensitive information before analysis.
- Do not commit export files, memory summaries, private chats, emails, API keys, or identity documents to the repository.
- The current MVP processes imports locally.
