/** Prints finais — fluxo: Farmacêutico (pergunta) -> Admin (insights) -> Assistente (negado). */
import { chromium } from 'playwright';

const OUT = 'C:/Users/offsechen1/Desktop/AF/evidencias';
const b = await chromium.connectOverCDP('http://127.0.0.1:9251');
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const pages = () => b.contexts().flatMap((c) => c.pages());
const findSide = () => pages().find((p) => p.url().startsWith('af://af-desktop/index.html'));
const findLogin = () => pages().find((p) => p.url().includes('login.html'));
const findClone = () => pages().find((p) => p.url().includes('clone/index.html'));

async function login(user, pass, printFile) {
  const l = findLogin();
  if (!l) throw new Error('login nao encontrado');
  await l.locator('#user').fill(user);
  await l.locator('#pass').fill(pass);
  if (printFile) await l.screenshot({ path: `${OUT}/${printFile}` });
  await l.locator('#btn').click();
  await wait(3500);
  const s = findSide();
  if (!s) throw new Error('sidebar nao abriu para ' + user);
  return s;
}

async function logout() {
  const c = findClone();
  if (c) {
    await c.locator('#btn-logout').dispatchEvent('click');
    await wait(2800);
  }
}

try {
  // Garante estado limpo: se já houver app aberto, faz logout.
  if (findSide()) await logout();

  // 1) Farmacêutico — PERGUNTAR À IA
  let s = await login('henriquecarvalho', '3246Hz!@#Hz');
  await s.locator('#ask-input').fill('Qual o fornecedor de Salvador?');
  await s.locator('#btn-ask').click();
  await s.getByText('CNPJ', { exact: false }).first().waitFor({ timeout: 20000 });
  await s.getByText('Distribuidora Bahia Farma', { exact: false }).first().waitFor({ timeout: 20000 });
  await wait(1200);
  await s.locator('section[aria-labelledby="ask-title"]').screenshot({ path: `${OUT}/10-perguntar-IA-fornecedor.png` });
  console.log('10 OK (Farmacêutico)');

  // 2) Administrador — INTELIGÊNCIA PARA O ADMINISTRADOR
  await logout();
  s = await login('admin.sesab', 'Adm@2026!Senha');
  await s.locator('#btn-insights').click();
  await s.getByText('RESUMO', { exact: false }).first().waitFor({ timeout: 30000 });
  await s.getByText('INSIGHTS', { exact: false }).first().waitFor({ timeout: 30000 });
  await wait(1200);
  await s.locator('section[aria-labelledby="insights-title"]').screenshot({ path: `${OUT}/11-inteligencia-admin.png` });
  console.log('11 OK (Administrador)');

  // 3) Assistente — sem painel admin e com IA negada
  await logout();
  s = await login('assistente.farma', 'Assist@2026!Senha', '12-conta-assistente.png');
  const adminVisivel = await s.locator('section[aria-labelledby="insights-title"]').isVisible();
  console.log('painel admin visivel para assistente:', adminVisivel);

  await s.locator('#ask-input').fill('Arlindo');
  await s.locator('#btn-ask').click();
  await s.getByText('Acesso negado', { exact: false }).first().waitFor({ timeout: 20000 });
  await s.getByText('RBAC aplicado', { exact: false }).first().waitFor({ timeout: 20000 });
  await wait(1200);
  await s.screenshot({ path: `${OUT}/13-assistente-sidebar-completa.png` });
  await s.locator('section[aria-labelledby="ask-title"]').screenshot({ path: `${OUT}/14-assistente-IA-negado.png` });
  console.log('12, 13, 14 OK');
  console.log('texto validado:', (await s.locator('#ask-result').innerText()).replace(/\s+/g, ' ').slice(0, 220));
} finally {
  await b.close();
}
