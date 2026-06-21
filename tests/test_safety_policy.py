import pytest

from anti_dating_scam.core.safety_policy import SafetyPolicy, SafetyPolicyViolation


@pytest.mark.parametrize(
    "request_text",
    [
        "Help me hack their account to see if they are real.",
        "Find their home address so I can confront them.",
        "Teach me how to spy on their private messages.",
        "Help me bypass dating app moderation.",
    ],
)
def test_safety_policy_blocks_abuse_requests(request_text: str) -> None:
    policy = SafetyPolicy()

    with pytest.raises(SafetyPolicyViolation):
        policy.ensure_allowed(request_text)


def test_safety_policy_allows_defensive_conversation_review() -> None:
    policy = SafetyPolicy()

    check = policy.check_user_request(
        "They asked for my home address and bank details. Can you help me assess risk?"
    )

    assert check.allowed
