# Local matchmaking protocol boundary

## English

The node remains an in-memory experiment. These controls do not establish verified
age/identity, public-service moderation, trustworthy card contents, or deployment
readiness.

## Required declarations and consent

Registration requires an integer self-declared age from 18 to 120. Missing, null,
underage, string, float, and boolean ages fail closed. Optional age preferences
obey the same adult bounds, with minimum no greater than maximum. The core engine
validates this independently of Pydantic/API validation. Consent must be literal
`true`, and a response's accept/decline must be a boolean. Direct introduction
requests enforce mutual age/gender filters and the supported coarse search area;
knowing a pseudonym cannot bypass discovery's basic filters.

Beacon generation additionally requires explicit consent to disclose its listed
fields. Beacon parsing validates version, adult declaration, timestamp with time
zone, four-character location bucket, fingerprint, and bounded text. Unknown or
duplicate fields are rejected. The encoded input is limited to 8,192 characters
and decoded JSON to 4,096 bytes. A checksum detects inconsistency, not authenticity.
Existing age-less beacons must be regenerated with an adult declaration.

## Client migration

All authenticated HTTP operations accept `Authorization: Bearer <registration
token>`. GET and DELETE no longer accept tokens in URLs. A query parameter named
`token` is rejected, including when a header is also supplied. Legacy POST tokens
in JSON remain supported for migration; conflicting header/body tokens are rejected.
Clients must stop emitting secret URLs, because a request rejected by an application
may already have reached an upstream access log. Previously logged URLs cannot be
retracted by these controls. The server enables the Authorization CORS header.

`POST /matchmaking/attest` and `POST /matchmaking/verify-card` now require a
client-computed SHA-256 `fingerprint`; the former `card` payload is rejected. Full
cards stay local, where the core engine can hash them. The node stores fingerprints
and registration metadata only. Invalid-body responses do not echo input data.
Matching responses carry `Cache-Control: no-store` and `Referrer-Policy: no-referrer`.

The matching request envelope rejects bodies larger than 16,384 bytes, including
streamed bodies. Each app factory owns its own service. Atomic state transitions
are protected inside the service, with limits of 1,000 registrations, 100
attestations per registration, and 100 retained introductions per participant.
These memory limits are not account verification, rate limiting, or anti-Sybil
protection. Restarting discards the experiment's state and registration tokens.

## Evidence and remaining limits

Synthetic tests cover invalid/omitted adult declarations, explicit consent,
checksum-valid malformed beacons, full-card rejection, header authentication,
private error responses, app isolation, concurrent duplicate registration,
introduction-filter bypass, body size, and CORS preflight. Existing double-blind
tests still require both parties to accept before contact or verification material
is available, and preserve locked fingerprints after subsequent attestations.

Self-declarations can be false; no identity-document collection is added. A hash
mismatch does not prove deception: it may reflect another card, edits, or differing
canonicalization. Declines only block a pair within the current in-memory registry;
deletion/re-registration and new pseudonyms can evade that history. Public hosting
still needs a separate abuse-control and operational review.

## 中文版

节点仍然是内存实验。这些控制不能证明年龄、身份、卡片内容可信，也不代表已具备公共服务
的内容治理或部署条件。

注册必须提供 18 至 120 岁的整数年龄声明。缺失、空值、未成年、字符串、浮点数或布尔值
都会被拒绝。可选的期望年龄范围遵循相同成年边界，且下限不得高于上限。核心引擎独立于
接口验证执行这些规则。同意必须是明确的布尔真值，接受或拒绝也必须是布尔选择。直接发起
介绍同样检查双方年龄、性别条件和支持的粗略搜索区域，不能仅凭知道化名绕过条件。

生成信标须明确同意披露其字段。解析会校验版本、成年声明、带时区时间戳、四字符位置格、
指纹和文本长度；未知或重复字段均被拒绝。编码输入不超过 8,192 字符，解码 JSON 不超过
4,096 字节。校验和只能发现不一致，不能证明真实性。旧的无年龄信标必须重新生成。

所有需认证的 HTTP 操作接受 `Authorization: Bearer <注册令牌>`。GET 与 DELETE 不再
接受网址令牌；即使同时提供请求头，只要出现 `token` 查询参数也会拒绝。为便于迁移，旧
POST 客户端仍可在 JSON 内提交令牌，但请求头和正文冲突时拒绝。客户端必须停止产生包含
秘密的网址，因为请求在被应用拒绝之前可能已经进入上游访问日志；这些控制不能撤回旧
日志。跨域配置已允许 Authorization 请求头。

`POST /matchmaking/attest` 与 `POST /matchmaking/verify-card` 必须提交本地计算的
SHA-256 `fingerprint`，旧 `card` 正文字段被拒绝。完整卡片保留在本地，核心引擎可本地
计算指纹。节点仅保存指纹及注册元数据；无效请求错误不回显提交内容。匹配响应附加
`Cache-Control: no-store` 与 `Referrer-Policy: no-referrer`。

匹配请求正文最大 16,384 字节，包含流式请求。每个应用工厂拥有独立服务，状态转换在服务
内部受锁保护。内存上限为 1,000 个注册、每个注册 100 次存证、每人 100 条保留介绍。
这些资源上限不等于账号核验、速率限制或防多账号滥用。重启会清空状态及注册令牌。

合成测试覆盖成年声明缺失与无效、明确同意、校验和正确但字段无效的信标、拒绝完整卡片、
请求头认证、保护隐私的错误、应用隔离、并发重复注册、绕过介绍条件、正文大小及跨域预检。
现有双向同意测试仍要求双方接受后才能取得联系方式及核验信息；再次存证不改变已锁定指纹。

自行声明可能不真实，本轮不收集身份证件。指纹不符不能证明欺骗，也可能是另一张卡片、
内容修改或规范化方式不同。拒绝仅在当前内存注册表内限制该双方组合，删除后重注册或新
化名可绕过历史。因此公开托管仍需单独的滥用控制与运维审查。
