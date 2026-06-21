SYNTHETIC_CASES = [
    {
        "name": "money_request",
        "conversation_text": "I love you. Please send gift cards for my hospital emergency.",
        "expected_risk": "HIGH",
    },
    {
        "name": "respectful_chat",
        "conversation_text": (
            "Nice talking with you. No pressure if you prefer to keep chatting here."
        ),
        "expected_risk": "LOW",
    },
    {
        "name": "ambiguous_short",
        "conversation_text": "Hey, how are you?",
        "expected_risk": "UNKNOWN",
    },
]
