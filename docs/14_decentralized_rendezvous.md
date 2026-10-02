# Decentralized Rendezvous (No Single Operator)

Agent-facing technical detail. English-only per the bilingual rule in `AGENTS.md`.
Owner decision 2026-07-06 (ADR-013): the rendezvous layer must not depend on one
server owned or rented by one person. It must support community-hosted private
nodes (the "private game server" model) and be able to ride on existing social
platforms (Facebook, 小红书, Discord, forums...) with **minimal server
requirements** — all AI and data processing stays on each user's own device with
their own AI (the desktop app's Connect AI backends).

## Three deployment models

| Model | Infrastructure | Who runs it | Status |
|---|---|---|---|
| A. Private nodes | `run_rendezvous_node.py` (FastAPI, stdlib-only engine, in-memory) | Anyone: a friend group, a community, a Pi at home | P0 shipped |
| B. Platform relay (serverless) | **None** — beacons posted manually on existing platforms | The users themselves | P0 shipped |
| C. Federation | Nodes exchange presence summaries | Node operators opt in | P2+ design |

### Model A — private nodes ("Minecraft server" model)

The node from `docs/12` is already tiny (bulletin board + notary; no profiles, no
cards, no analysis). Decentralization is achieved by making it trivially
self-hostable: `python run_rendezvous_node.py` on any machine. Users pick which
node(s) to register on — their hiking club's, their city community's — exactly
like choosing a private game server. Each node is its own notary: attestation
tokens are only meaningful within the node that issued them, which is fine
because introductions are brokered by the same node. No node ever becomes "the"
server; the app treats node URLs as user-supplied configuration.

Minimal-requirements rule (hard): a node must run on a single small machine.
Anything that needs GPUs, model inference, or bulk storage belongs client-side —
the app's own connected AI (Claude Code / Ollama / Anthropic) does all analysis.

### Model B — platform relay (no server at all)

`src/anti_dating_scam/matchmaking/beacon.py` implements armored **beacon** text
blocks (`-----BEGIN AI-SLOWMATCH BEACON-----` ... `END`): pseudonym, coarse
geohash bucket, Tier-1 gates, card fingerprint, optional contact hint, checksum.

Flow: generate your beacon in the app → post it *yourself* in a community you
trust (a Facebook group, a 小红书 post, a Discord channel) → others copy beacon
text into their app → the app parses, integrity-checks, and runs the mutual
gate/bucket check locally → if both sides like the result, they contact each
other via the platform's own DM and exchange compatibility cards peer-to-peer
(docs/11), pinning each other's `card_fingerprint` from the beacon.

Hard rules, restating existing policy:
- **No scraping and no login automation, ever.** Humans post and copy beacons by
  hand. The app never fetches platform content. This is both the project's own
  rule and what keeps the mechanism platform-ToS-safe.
- The beacon never contains real names, precise locations, or addresses; the
  contact hint should be "DM me here", not a phone number.
- Matching output is facts (bucket match, gates both ways), never a score.

Trust model, honestly stated: the *platform account* that posted the beacon is
the identity anchor and the platform's post timestamp is the public witness.
The checksum catches corruption and casual edits, not a determined forger;
peer-side fingerprint pinning at first contact provides the tamper-evidence for
the card exchange (same mechanism the node uses at introduction time). Real
user-keypair signatures (Ed25519, `cryptography` optional extra) are the P1
upgrade for both models.

### Model C — federation (later)

Community nodes optionally exchange signed presence summaries (pseudonym, bucket
prefix, attestation summary — nothing more) so a user on node X can discover a
user on node Y. Requires the P1 keypair work first so cross-node claims are
verifiable. Design only; do not build before P1.

## What changed vs docs/12

`docs/12` stands (thin node, data minimization, threat model), with two scope
amendments: (1) the node is a *self-hostable artifact*, not a hosted service run
by the project owner; (2) the serverless beacon path is a first-class equal, not
a fallback. ADR-012's data-minimization table applies to every node operator.

## Threat notes specific to decentralization

| Threat | Mitigation |
|---|---|
| Malicious node operator | Node never holds profiles/cards; users can register on multiple nodes; open-source node code; federation keeps exit costs low |
| Fake beacons flooding a group | Community moderation of the group itself (the platform is the spam filter); checksum rejects mangled posts; P1 signatures make impersonation detectable |
| Beacon reposted/replayed elsewhere | `created_at` staleness check in the UI; contact goes through the platform account, which a replayer does not control |
| Platform bans such posts | Beacons are ordinary user text posted manually; communities choose where; nodes (Model A) remain available |
