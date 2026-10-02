"""Load the versioned packaged app skill, never an installed user's private skill."""

from importlib.resources import files

SKILL_COMMIT = "6db7354a4002dc7c448a9c87ffdad8132570c9d3"
POLICY_VERSION = "3"
SKILL_RESOURCE = "skills/relationship-reflection/SKILL.md"
COACHING_POLICY = files("anti_dating_scam").joinpath(SKILL_RESOURCE).read_text(encoding="utf-8")
if 'version: "3"' not in COACHING_POLICY:
    raise RuntimeError("The packaged conversational skill version is invalid.")
