"""Bilingual matching vocabulary; codes stay out of the primary user flow."""

from anti_dating_scam_desktop.i18n import bi

LABELS = {
    "intention": ("Relationship intention", "关系意向"),
    "pace": ("Pace", "相处节奏"),
    "communication": ("Communication", "沟通偏好"),
    "availability": ("Availability", "空闲安排"),
    "smoking": ("Smoking preference", "吸烟情况"),
    "interests": ("Interests", "兴趣"),
    "long_term": ("Long-term relationship", "长期关系"),
    "casual": ("Casual dating", "轻松约会"),
    "unsure": ("Not sure yet", "尚不确定"),
    "slow": ("Slow", "慢慢来"),
    "steady": ("Steady", "稳步推进"),
    "flexible": ("Flexible", "可灵活调整"),
    "direct": ("Direct", "直接表达"),
    "reflective": ("Time to reflect", "需要思考时间"),
    "mixed": ("Depends on context", "视情况而定"),
    "weekdays": ("Weekdays", "工作日"),
    "weekends": ("Weekends", "周末"),
    "no": ("No", "不吸烟"),
    "sometimes": ("Sometimes", "偶尔"),
    "yes": ("Yes", "吸烟"),
    "reading": ("Reading", "阅读"),
    "music": ("Music", "音乐"),
    "art": ("Art", "艺术"),
    "outdoors": ("Outdoors", "户外"),
    "cooking": ("Cooking", "烹饪"),
    "games": ("Games", "游戏"),
    "travel": ("Travel", "旅行"),
    "sport": ("Sport", "运动"),
    "pending": ("Awaiting a recipient", "等待接收人"),
    "claimed": ("Claimed; review both permissions", "已认领，待双方审阅许可"),
    "ready": ("Both approved", "双方已批准"),
    "declined": ("Declined", "已婉拒"),
    "revoked": ("Withdrawn", "已撤销"),
    "expired": ("Expired", "已到期"),
}


def label(key):
    return bi(*LABELS[key]) if key in LABELS else key


ERRORS = {
    "stale": ("Information changed. Refresh and review again.", "资料已变化，请刷新后重新审阅。"),
    "consent_required": ("Both current permissions are needed.", "需要双方对当前版本的许可。"),
    "profile_required": ("Approve a matching profile first.", "请先批准匹配资料。"),
    "unauthorized": ("Connect this device identity again.", "请重新连接本机身份。"),
    "connection_failed": (
        "Cannot reach the configured node. Your data was kept.",
        "无法连接所选节点，输入已保留。",
    ),
    "wrong_recipient": ("This invitation names a different recipient.", "邀请指定了其他接收人。"),
    "already_used": (
        "Another recipient has claimed this invitation.",
        "已有另一位接收人认领这份邀请。",
    ),
    "unavailable": (
        "This item is unavailable under current permissions or requirements.",
        "当前许可或条件下无法使用此项目。",
    ),
    "source_changed": (
        "Source notes changed. Generate and approve again.",
        "来源记忆已变化，请重新生成并批准。",
    ),
    "reconfirm_outdated": ("Reconfirm selected older notes first.", "请先重新确认选中的旧记忆。"),
    "select_sources": ("Select 1–8 confirmed facts first.", "请先选择 1–8 条已确认事实。"),
    "no_current_result": (
        "No current approved result. Compare again if wanted.",
        "暂无有效结果，可按需重新比较。",
    ),
    "invitation_node_mismatch": (
        "This link does not belong to the configured node.",
        "链接不属于当前配置的节点。",
    ),
    "recipient_confirmation_required": (
        "A recipient must claim before both people review.",
        "接收人认领后，双方才能审阅。",
    ),
    "expired": ("The invitation expired. Ask for a new one.", "邀请已到期，需要新邀请。"),
    "revoked": ("The invitation was withdrawn.", "邀请已撤销。"),
    "declined": (
        "This invitation was declined; no further request was sent.",
        "邀请已被婉拒，没有发送后续请求。",
    ),
}


def error_text(error):
    code = str(error)
    return bi(
        *ERRORS.get(
            code,
            (
                "The action did not complete. Review the inputs and try again.",
                "操作未完成，请复核输入后重试。",
            ),
        )
    )
