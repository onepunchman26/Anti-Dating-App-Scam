# Personal Profile Format

The local personal relationship profile is a user-owned JSON document. It is not training a personal model and should not be treated as a psychological diagnosis.

Schema file:

```text
src/anti_dating_scam/schemas/personal_profile.schema.json
```

Required top-level fields:

- `schema_version`
- `created_at`
- `updated_at`
- `owner_label`
- `source_summary`
- `relationship_values`
- `boundary_preferences`
- `communication_preferences`
- `risk_tolerance_notes`
- `trust_ladder_preferences`
- `self_reflection_notes`
- `uncertainty_notes`

The profile is generated from user-provided local text such as manual notes, pasted Memory Summary, and limited snippets from a local ChatGPT export.

Uncertainty notes are required because user-provided local text may be incomplete, outdated, or context-dependent.
