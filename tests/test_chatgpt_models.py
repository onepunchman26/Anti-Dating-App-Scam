"""Account-only defaults remain uncertain and cannot invent a usable model."""

import pytest

from anti_dating_scam.ai.chatgpt_auth import ChatGPTModelChoice
from anti_dating_scam.ai.chatgpt_models import recommend_chatgpt_model


def choice(slug, name=None):
    return ChatGPTModelChoice(slug=slug, display_name=name or slug)


@pytest.mark.parametrize(
    "small", ["synthetic-mini", "synthetic-nano", "synthetic-small", "synthetic-luna"]
)
def test_small_name_recommended_only_when_returned_in_account_catalog(small):
    catalog = (choice("synthetic-large"), choice(small))
    recommendation = recommend_chatgpt_model(catalog)
    assert recommendation.slug == small and recommendation.lightweight_hint
    assert not recommendation.structured_output_verified
    assert (
        "does not guarantee" in recommendation.reason_en and "不保证" in recommendation.reason_zh
    )


def test_preserves_account_order_among_equivalent_small_choices():
    assert (
        recommend_chatgpt_model((choice("first-mini"), choice("second-small"))).slug == "first-mini"
    )


def test_no_smaller_model_falls_back_to_account_general_order():
    recommendation = recommend_chatgpt_model((choice("synthetic-large"), choice("synthetic-other")))
    assert recommendation.slug == "synthetic-large" and not recommendation.lightweight_hint


def test_empty_or_explicitly_nonchat_catalog_has_no_invented_default():
    assert recommend_chatgpt_model(()) is None
    assert (
        recommend_chatgpt_model((choice("text-embedding-small"), choice("gpt-image-mini"))) is None
    )


def test_specialized_smaller_model_is_not_recommended_over_general_choice():
    catalog = (choice("gpt-realtime-mini"), choice("synthetic-chat"))
    assert recommend_chatgpt_model(catalog).slug == "synthetic-chat"
