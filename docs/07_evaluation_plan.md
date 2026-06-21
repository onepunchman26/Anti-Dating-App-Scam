# Evaluation Plan

Evaluation should use synthetic and consented data only. The goal is not to prove that AI can know intent. The goal is to test whether the system notices known risk patterns, explains uncertainty, and avoids harmful advice.

## Synthetic Test Cases

- money request;
- crypto or investment romance pitch;
- emergency story without money request;
- immediate off-platform pressure;
- repeated boundary violation;
- normal respectful chat;
- ambiguous short conversation;
- private image request;
- request for identity documents.

## False Positive And False Negative Analysis

False positives may make users overly suspicious. False negatives may leave users exposed to scams. Evaluation should track both, with special attention to uncertainty language and recommended next steps.

## Bias Checks

Risk detection should not depend on gender, nationality, accent, income, occupation, or relationship preference. Synthetic cases should vary demographic hints while preserving the same risk behavior to check for inconsistent outputs.

## Explainability Checks

Every risk output should include:

- specific risk signals;
- evidence category;
- uncertainty notes;
- next steps;
- a disclaimer that the system is not making legal, criminal, or psychological judgments.

## Safety-Policy Tests

The system should block requests for:

- spying;
- hacking;
- doxxing;
- impersonation;
- harassment;
- revenge;
- dating-app moderation bypass;
- manipulative entrapment.

## User Comprehension Testing

Future testing should ask whether users understand:

- the difference between risk signal and proof;
- why slowing down is recommended;
- why sending money is unsafe;
- what consent-based verification means;
- how to delete or export data if storage is added.

## Privacy Red-Team Checklist

- Can hidden scraping be triggered?
- Can real user data enter examples or tests?
- Can output become a public score?
- Can model calls retain sensitive text without user awareness?
- Can logs expose private conversation content?
- Can prompts encourage emotional dependency?
