# Data Governance

The current prototype has no database. This is intentional. Early work should stabilize safety behavior before retaining sensitive relationship data.

## Data Minimization

Collect only the text required for a user-requested analysis. Do not collect device contacts, hidden profile data, private social media data, or location history.

## Deletion

Future storage must support deletion of local records. Deletion should include submitted text, journal entries, generated outputs, and metadata where feasible.

## Export

Users should be able to export their own records in a readable format before deleting or migrating them.

## Local-First Future Option

A future design should explore local-first storage so sensitive relationship data can remain on the user's device by default.

## Encryption Future Option

If persistent storage is added, encryption at rest and in transit should be mandatory. Key management and backup recovery need explicit design before production use.

## Audit Logs

Future audit logs should track user-controlled actions such as creation, export, deletion, and model-provider calls. Audit logs should not become surveillance logs.

## Model-Output Retention Policy

Model outputs should have retention limits. Users should be able to delete outputs and see whether a provider call was made.

## No Real User Data In Repo

Tests, examples, fixtures, screenshots, and docs must use synthetic data only.
