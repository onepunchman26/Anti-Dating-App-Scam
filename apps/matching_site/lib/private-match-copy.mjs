export const privateMatchMessages={
recover:['Read latest saved result (no new AI request)','读取上次已保存结果（不重新调用AI）'],recoverHint:['If a response is interrupted, wait for the current request to finish, then read its saved result before trying again.','回复中断时，等待当前请求完成，再读取保存结果，避免重复耗用额度。'],
draft:['Prepare my shared summary','准备我的共享摘要'],intro:['After a conversation, choose these basic facts. AI proposes broad tags from this conversation; review every field before sharing. Private stories stay here.','聊天后选择这些基本信息。AI根据本次对话提出宽泛标签；分享前请逐项检查，私人经历留在本机。'],
generate:['Create a draft from this conversation','根据本次对话生成草稿'],
consent:['Allow OpenAI to process this selected conversation for a draft. This does not publish anything.','允许OpenAI处理这次所选对话来生成草稿；这不表示发布。'],
version:['Next summary version (first time: 1; otherwise check My profile on the Site)','下一个摘要版本（首次为1；更新时先查看网站“我的资料”）'],
missing:['The conversation does not yet support these required choices. Talk about them, or use the manual editor on the Site.','当前对话尚不足以确定以下必填意向。可以继续聊，也可以到网站手动补充。'],
reviewed:['I reviewed every proposed field, the participant audience, discovery setting and 30-day expiry. Export only this separate summary.','我已逐项检查草稿、参与者可见范围、可被发现状态及30天有效期，仅导出这份独立摘要。'],
export:['Download reviewed summary','下载已审阅摘要'],next:['Import this file on the Site’s My profile page, review it and choose Publish. Publication is a separate action.','到网站“我的资料”导入这个文件，检查后再点击发布。发布是另一个独立操作。'],
candidate:['Private candidate review','私人候选分析'],bundle:['Approved candidate bundle from Discover','从发现页面复制的获准候选资料'],
reviewConsent:['Allow OpenAI to compare these shared summaries for me. The result stays in my local vault.','允许OpenAI为我比较这些共享摘要，结果只留在本机资料库。'],
include:['Also use up to ten of my confirmed private profile statements (max 4,500 characters). Never another person’s private profile.','同时使用最多十条本人的已确认私人档案陈述（最多4,500字符），不会读取对方私人档案。'],
run:['Analyze privately','开始私人分析'],saved:['Saved locally. Not published, sent to anyone or a guarantee of compatibility.','已保存在本机，没有发布或发给任何人，也不是适合彼此的保证。'],
reasons:['Possible connections','可能的契合点'],differences:['Differences to explore','值得了解的差异'],questions:['Questions to discuss','可以交流的问题'],unknowns:['Still unknown','仍然未知'],
failed:['Could not complete this request. Check the selected conversation or bundle, current login, model, plan permission and consent. No result has been published.','此次请求未完成。请检查所选对话或资料包、当前登录、模型、套餐权限及同意状态；没有发布任何结果。'],
busy:['Analyzing with your authorized AI…','正在使用你授权的AI分析…'],model:['Choose a model and confirm plan usage above first.','请先在上方选择模型并确认套餐使用。'],
expires_at:['Expiry','到期时间'],visibility:['Who can see it','可见范围'],discoverable:['Included in discovery after publication','发布后参与发现'],participants:['Eligible participants','符合条件的参与者'],yes:['Yes','是'],no:['No','否'],
};
export const privateMatchText=(locale,key)=>privateMatchMessages[key]?.[locale==='zh-CN'?1:0]||key;
