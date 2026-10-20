export const interviewMessages={
 title:['Your relationship draft','你的关系草稿'],
 intro:['Start with a few short questions about the relationship you want. View your draft at any time; you can explore life direction later.','先用几个短问题聊聊你期待的关系，随时查看草稿，之后再按意愿展开人生方向。'],
 count:['Initial questions asked (maximum 8, including follow-ups)','首轮已提问（最多8次，含追问）'],
 draft:['View draft now','先看草稿'],pause:['Pause interview','暂停访谈'],resume:['Resume interview','继续访谈'],
 skip:['Skip this question','跳过这题'],unknown:['Not sure yet','暂时不确定'],inexperienced:['No experience yet','暂时没有经验'],
 private:['These are provisional summaries of what you said. Check the source and correct them. They are saved only with this local conversation, not your confirmed profile or shared summary. Removing a draft item does not erase the original conversation.','这些是对本人陈述的暂时理解，请核对原话并修正。只随本机会话保存，不自动写入已确认档案或共享摘要。移除草稿条目不会删除原始会话。'],
 goal:['Relationship hopes','关系期待'],pace:['Comfortable pace','舒服的接触节奏'],care:['Feeling cared for','希望怎样被关心'],communication:['Communication and disagreement','沟通与分歧'],boundaries:['Boundaries','相处边界'],availability:['Time and practical arrangements','时间与现实安排'],distance:['Distance and location expectations','距离与地区期待'],interests:['Shared activities','共同活动'],mind:['Thinking and learning','思考与学习'],body:['Energy and daily rhythm','精力与生活节奏'],spirit:['Connection, meaning and belonging','连接、意义与归属'],vocation:['Work and life direction','工作与人生方向'],
 missing:['Not yet understood','尚未了解'],draftStatus:['AI summary · unconfirmed self-report','AI整理 · 尚未确认的自述'],confirmed:['Reviewed by you · not independently verified','本人已审阅 · 未经独立核实'],skipped:['Skipped by you','本人已跳过'],removed:['Removed from this draft','已从草稿移除'],quote:['Your words','本人原话'],edit:['Correct wording','修正措辞'],editLabel:['Your wording for this private draft','本人对私人草稿的措辞'],consent:['I confirm this wording for my private draft only.','我确认此措辞，仅用于私人草稿。'],save:['Save correction','保存修正'],remove:['Remove draft item','移除草稿条目'],use:['Review for private profile','转入私人档案审阅'],
 later:['Explore further when you want','愿意时再深入'],focus:['Choose one area','选择一个方向'],explore:['Continue with this area','继续这一方向'],laterHint:['Optional. This changes your interview focus only; it does not call AI or publish anything. Send a message when ready.','完全可选。此操作仅改变访谈方向，不调用AI或发布内容；准备好后再发送消息。'],
 paused:['Paused. Your draft and question count are kept.','已暂停，草稿与提问次数已保留。'],
 reuse:['Reuse a selected relationship draft, including skipped and corrected items','复用选定的关系草稿，包括跳过与修正记录'],reuseChoice:['Draft to reuse (same topic)','要复用的草稿（同一主题）'],
 upgrade:['This interview needs local assistant 0.8.3 or later. Install the verified update, reopen the assistant and pair again. Existing conversations remain available.','此访谈需要0.8.3或更新的本机助手。请安装已验证更新、重开助手并重新配对，已有会话会保留。'],
 startDating:['If you met someone suitable, how would you like the relationship to develop?','如果遇到合适的人，你希望关系怎样发展？'],startFriendship:['What would you enjoy sharing with a friend?','你希望和朋友一起分享怎样的时光？'],
 next:['Continue from what I have shared; ask one useful short question only if needed.','请从我已分享的内容继续，只在需要时问一个有用的短问题。'],nextButton:['Continue the conversation','继续聊聊'],
};
export const interviewText=(locale,key)=>interviewMessages[key]?.[locale==='zh-CN'?1:0]||'';
export const initialInterviewAreas=['goal','pace','care','communication','boundaries','availability','distance','interests'];
