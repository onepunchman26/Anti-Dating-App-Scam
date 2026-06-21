import re
from dataclasses import dataclass


class SafetyPolicyViolation(ValueError):
    def __init__(self, message: str, violations: list[str]) -> None:
        super().__init__(message)
        self.violations = violations


@dataclass(frozen=True)
class PolicyCheck:
    allowed: bool
    violations: list[str]
    message: str


class SafetyPolicy:
    """Blocks requests that would turn the project into an abuse tool."""

    PROHIBITED_PATTERNS: dict[str, list[re.Pattern[str]]] = {
        "spying": [
            re.compile(r"\bspy on\b", re.IGNORECASE),
            re.compile(r"\btrack (their|his|her) phone\b", re.IGNORECASE),
            re.compile(r"\bread (their|his|her) (private )?messages\b", re.IGNORECASE),
            re.compile(r"\bstalk (them|him|her)\b", re.IGNORECASE),
        ],
        "hacking": [
            re.compile(r"\bhelp me hack\b", re.IGNORECASE),
            re.compile(r"\bhack (their|his|her|into)\b", re.IGNORECASE),
            re.compile(r"\bbreak into\b", re.IGNORECASE),
            re.compile(r"\bsteal (their|his|her) password\b", re.IGNORECASE),
            re.compile(r"\bbypass .*moderation\b", re.IGNORECASE),
        ],
        "doxxing": [
            re.compile(r"\bdoxx?\b", re.IGNORECASE),
            re.compile(r"\bleak (their|his|her) (address|phone|photos)\b", re.IGNORECASE),
            re.compile(r"\bfind (their|his|her) home address\b", re.IGNORECASE),
            re.compile(r"\bpublish (their|his|her) private\b", re.IGNORECASE),
        ],
        "entrapment": [
            re.compile(r"\btrap (them|him|her)\b", re.IGNORECASE),
            re.compile(r"\bmanipulate (them|him|her)\b", re.IGNORECASE),
            re.compile(r"\bcatfish\b", re.IGNORECASE),
            re.compile(r"\bimpersonate\b", re.IGNORECASE),
        ],
    }

    def check_user_request(self, text: str) -> PolicyCheck:
        violations: list[str] = []
        for category, patterns in self.PROHIBITED_PATTERNS.items():
            if any(pattern.search(text) for pattern in patterns):
                violations.append(category)

        if violations:
            return PolicyCheck(
                allowed=False,
                violations=sorted(set(violations)),
                message=(
                    "This system cannot help with spying, hacking, doxxing, "
                    "impersonation, harassment, revenge, or bypassing moderation."
                ),
            )

        return PolicyCheck(
            allowed=True,
            violations=[],
            message="Request is within the safety policy.",
        )

    def ensure_allowed(self, text: str) -> None:
        check = self.check_user_request(text)
        if not check.allowed:
            raise SafetyPolicyViolation(check.message, check.violations)


SAFETY_DISCLAIMER = "This is a risk-support tool, not a legal, criminal, or psychological judgment."
