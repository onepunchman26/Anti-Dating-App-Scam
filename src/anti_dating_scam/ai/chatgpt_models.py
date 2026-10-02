"""Account-catalog choices and explicitly heuristic lightweight defaults."""

from __future__ import annotations

import re
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict

from anti_dating_scam.ai.chatgpt_auth import ChatGPTModelChoice


class ChatGPTModelRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    slug: str
    lightweight_hint: bool
    reason_en: str
    reason_zh: str
    # The documented account catalog supplies names, not a capability guarantee.
    structured_output_verified: bool = False


def recommend_chatgpt_model(
    models: Sequence[ChatGPTModelChoice],
) -> ChatGPTModelRecommendation | None:
    """Choose only an actually returned slug, without testing paid inference.

    A mini/nano/small/luna name is a size hint. Neither speed, usage cost nor
    portrait structured-output compatibility has been measured here. Account
    ordering breaks ties and provides the fallback for general chat choices.
    """
    general = []
    for model in models:
        name = f"{model.slug} {model.display_name}".lower()
        if re.search(
            r"(?:^|[\s_./:-])(embedding?|moderation|realtime|audio|whisper|tts|"
            r"transcri\w*|image|dall-e|sora|video)(?:$|[\s_./:-])",
            name,
        ):
            continue
        general.append(model)
    if not general:
        return None
    for model in general:
        name = f"{model.slug} {model.display_name}".lower()
        if re.search(r"(?:^|[\s_./:-])(mini|nano|small|luna)(?:$|[\s_./:-])", name):
            return ChatGPTModelRecommendation(
                slug=model.slug,
                lightweight_hint=True,
                reason_en=(
                    "Suggested for lightweight conversation from this account's model list. "
                    "The name suggests a smaller model; "
                    "this does not guarantee speed or answer quality. "
                    "Review the result, especially when creating a reflection."
                ),
                reason_zh=(
                    "从此账号实际返回的模型中建议用于轻量聊天。名称暗示模型较小，"
                    "不保证速度或回答质量，尤其生成画像时请核对结果。"
                ),
            )
    return ChatGPTModelRecommendation(
        slug=general[0].slug,
        lightweight_hint=False,
        reason_en=(
            "No clearly smaller chat model was listed. Suggested the first general model "
            "in the account's ordering; speed and portrait compatibility have not been verified."
        ),
        reason_zh=(
            "此账号未列出名称明确表示较小的聊天模型。按账号返回顺序建议首个通用模型；"
            "速度和自我画像格式兼容性尚未验证。"
        ),
    )
