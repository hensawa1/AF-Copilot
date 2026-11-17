import { readFileSync } from 'node:fs';

const token = readFileSync('../ai-backend/runtime/auth_token', 'utf8').trim();
const base = 'http://127.0.0.1:8000/api/v1';

async function login(username, password) {
  const r = await fetch(base + '/auth/login', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  return (await r.json()).session_token;
}

async function ask(session, pergunta) {
  const r = await fetch(base + '/admin/ask', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Internal-Auth-Token': token,
      'X-Session-Token': session,
    },
    body: JSON.stringify({ pergunta }),
  });
  const d = await r.json();
  console.log(`\n[${pergunta}] status=${r.status} intent=${d.intent} model=${d.model}`);
  console.log('answer:', d.answer);
  console.log('columns:', d.columns?.join(' | '));
  console.log('linhas:', d.rows?.length, '| primeira:', d.rows?.[0]);
  if (d.security_notice) console.log('notice:', d.security_notice);
}

const farm = await login('henriquecarvalho', '3246Hz!@#Hz');
for (const q of [
  'Quantos pacientes estão em tratamento em Salvador?',
  'Quais pacientes são de Salvador?',
  'Quantos remédios existem?',
  'Mostre os fornecedores de Recife',
  'Quais LMEs estão pendentes em Salvador?',
  'Liste todos os pacientes',
]) await ask(farm, q);

const assist = await login('assistente.farma', 'Assist@2026!Senha');
for (const q of ['Quais pacientes são de Salvador?', 'Quantos remédios existem?']) {
  await ask(assist, q);
}
