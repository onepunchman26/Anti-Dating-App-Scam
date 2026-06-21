# Vocabulary

## AI-SlowMatch

The conceptual system name for the local-first AI relationship-trust and scam-risk support tool.

## Trust Ladder

A staged pacing model that helps users avoid escalating intimacy faster than trust evidence supports.

## Risk Signal

A behavior or text pattern that deserves caution. A risk signal is not proof of intent, identity, wrongdoing, or danger.

## Uncertainty Note

A statement that explains missing context, limits of analysis, or why the output should not be treated as certainty.

## Personal Relationship Profile

A user-owned local document describing relationship values, boundaries, communication preferences, reflections, and trust ladder history. It is not a trained personal model.

## Verifiable Risk Report

A schema-valid local report describing risk signals, uncertainty, recommendations, hashes, provider metadata, and optional signature metadata.

## Provider Adapter

A module that connects the core engine to an AI provider through a shared interface and returns structured dict-like output.

## Local-First

A design principle where user data is stored and processed locally by default, with remote calls only through explicit user choice.

## Consent-First

A design principle where user action and authorization are required before analysis, persistence, provider calls, or imports.

## Relationship Trust Infrastructure

Tools, documents, education, and workflows that help people build trust safely without turning relationships into public scores.

## Mutual Riskification

The process where users increasingly perceive each other through risk, suspicion, and defensive filtering.

## Trust Spiral Decline

The cycle where weak trust infrastructure increases suspicion, scams, and user exit, which then deepens the trust deficit.

## Schema-Valid Report

A report that conforms to the project JSON Schema. Schema validity does not prove truth.

## Signed Report

A report with signature metadata over canonical JSON. A valid signature means the signed content has not changed and was signed by the relevant key.

## Unknown Signer

A verification state where the signature may be structurally valid, but the verifier does not recognize or trust the signing key.

## Modified Report

A verification state where content no longer matches the signed hash or signature.
