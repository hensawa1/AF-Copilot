import { readFileSync } from 'node:fs';
const token = readFileSync('../ai-backend/runtime/auth_token', 'utf8').trim();
const base = 'http://127.0.0.1:8000/api/v1';
const login = await (await fetch(base + '/auth/login', {
  method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'henriquecarvalho', password: '3246Hz!@#Hz' }),
})).json();
for (const q of ['Medicamentos cadastrados', 'outros pacientes', 'Qual o fornecedor de Salvador?']) {
  const r = await fetch(base + '/admin/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Internal-Auth-Token': token, 'X-Session-Token': login.session_token },
    body: JSON.stringify({ pergunta: q }),
  });
  const d = await r.json();
  console.log(q, '->', r.status, d.intent, 'linhas:', d.rows?.length, '|', d.answer?.slice(0, 80), '| rows0:', d.rows?.[0]);
}
