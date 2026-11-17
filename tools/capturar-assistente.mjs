/** Recaptura o perfil Assistente após remover validador, protocolos e contexto. */
import { chromium } from 'playwright';

const OUT = 'C:/Users/offsechen1/Desktop/AF/evidencias';
const b = await chromium.connectOverCDP('http://127.0.0.1:9256');
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const pages = () => b.contexts().flatMap((c) => c.pages());
const findSide = () => pages().find((p) => p.url().startsWith('af://af-desktop/index.html'));
const findLogin = () => pages().find((p) => p.url().includes('login.html'));

async function esperar(fn, rotulo, timeout = 45000) {
  const inicio = Date.now();
  while (Date.now() - inicio < timeout) {
    try { if (await fn()) return true; } catch { /* ignore */ }
    await wait(300);
  }
  throw new Error(`timeout aguardando ${rotulo}`);
}

async function perguntar(s, q, waitTexts, arquivo, meta) {
  const btn = s.locator('#btn-ask');
  await esperar(async () => !(await btn.isDisabled()), 'botao Perguntar');
  await s.locator('#ask-input').fill(q);
  await btn.click();
  await s.locator('#ask-result .ask-meta').filter({ hasText: meta }).first()
    .waitFor({ timeout: 60000 });
  for (const t of waitTexts) {
    await s.locator('#ask-result').getByText(t, { exact: false }).first()
      .waitFor({ timeout: 45000 });
  }
  await wait(900);
  await s.screenshot({ path: `${OUT}/${arquivo}`, animations: 'disabled' });
  console.log(arquivo, 'OK |', (await s.locator('#ask-result').innerText()).replace(/\s+/g, ' ').slice(0, 180));
}

try {
  const l = findLogin();
  if (!l) throw new Error('tela de login nao encontrada');
  await l.locator('#user').fill('assistente.farma');
  await l.locator('#pass').fill('Assist@2026!Senha');
  await wait(500);
  await l.screenshot({ path: `${OUT}/12-conta-assistente.png` });
  await l.locator('#btn').click();
  const s = await (async () => {
    await esperar(() => Boolean(findSide()), 'sidebar');
    await wait(1500);
    return findSide();
  })();

  const secoes = {
    insights: 'section[aria-labelledby="insights-title"]',
    validador: 'section[aria-labelledby="rx-title"]',
    protocolos: 'section[aria-labelledby="analysis-title"]',
    contexto: 'section[aria-labelledby="ctx-title"]',
    perguntarIA: 'section[aria-labelledby="ask-title"]',
  };
  for (const [nome, seletor] of Object.entries(secoes)) {
    console.log(`${nome} visivel:`, await s.locator(seletor).isVisible());
  }
  await wait(700);
  await s.screenshot({ path: `${OUT}/13-assistente-sidebar-completa.png`, animations: 'disabled' });
  console.log('13-assistente-sidebar-completa.png OK');

  await perguntar(s, 'Quantos remédios existem?', ['medicamentos cadastrados'], '15b-assistente-IA-permitida.png', 'Intenção: contagem');
  await perguntar(s, 'Quais pacientes são de Salvador?', ['Acesso negado', 'RBAC aplicado'], '14-assistente-IA-negado.png', 'Intenção: pacientes');
} finally {
  await b.close();
}
