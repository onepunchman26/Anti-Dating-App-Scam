'use client';

import { useState } from 'react';

type Status = { version: string; protocol: string; scope: string; access: string; read: string };

export default function ServiceStatus() {
  const [status, setStatus] = useState<Status | null>(null);
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  async function check() {
    setBusy(true); setFailed(false); setStatus(null);
    try {
      const response = await fetch('/api/matching', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'slowmatch_channel_check', arguments: { write: false, client_protocol: '1.0' } }),
      });
      const raw: unknown = await response.json();
      if (!response.ok || !raw || typeof raw !== 'object') throw new Error('unavailable');
      const body = raw as Record<string, unknown>;
      const scope = body.data_scope as Record<string, unknown> | undefined;
      if (body.authenticated !== true || typeof body.service_version !== 'string' ||
          typeof body.service_protocol_version !== 'string' || typeof body.database_read !== 'string' ||
          !scope || typeof scope.kind !== 'string' || typeof scope.access !== 'string') throw new Error('unavailable');
      setStatus({ version: body.service_version, protocol: body.service_protocol_version,
        scope: scope.kind, access: scope.access, read: body.database_read });
    } catch { setFailed(true); } finally { setBusy(false); }
  }
  return <section className="panel"><h2>Service check / 服务自检</h2>
    <p>Checks this browser’s signed-in service connection. Desktop Skill loading and local file access need their own checks. / 检查此浏览器已登录的服务连接；桌面 Skill 加载与本机文件访问须分别验证。</p>
    <button className="button" onClick={check} disabled={busy}>{busy ? 'Checking / 检查中' : 'Check connection / 检查连接'}</button>
    <div aria-live="polite">
      {failed && <p>Connection check blocked or failed. Sign in with an authorized account and retry after resolving access. / 连接检查受阻或失败，请以获准账号登录并解决访问问题后重试。</p>}
      {status && <p>Service / 服务：{status.version} · Protocol / 协议：{status.protocol}<br/>
        Scope / 范围：{status.scope === 'controlled_test' ? 'Controlled test / 受控测试' : 'Production / 正式数据'} · Access / 权限：{status.access}<br/>
        Database read / 数据库读取：{status.read} · Native desktop and local files / 桌面原生与本机文件：NOT_CHECKED</p>}
    </div>
  </section>;
}
