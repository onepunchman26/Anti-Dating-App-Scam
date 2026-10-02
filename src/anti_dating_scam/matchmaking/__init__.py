"""Rendezvous matchmaking engine (nearby discovery + card attestation).

Design contract: `docs/12_rendezvous_matchmaking_plan.md` (ADR-012). The server side
is a bulletin board and a notary — it never stores profile/card content, only
pseudonyms, coarse location buckets, Tier-1 gates, blinded contacts, and card
fingerprints. All compatibility data stays on the user's device.
"""
