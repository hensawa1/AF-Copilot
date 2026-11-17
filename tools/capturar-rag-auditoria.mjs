/** Captura o fluxo RAG real (portal -> sanitização -> análise) e a auditoria. */
import { chromium } from 'playwright';

const OUT = 'C:/Users/offsechen1/Desktop/AF/evidencias';
const b = await chromium.connectOverCDP('http://127.0.0.1:9256');
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const pages = () => b.contexts().flatMap((c) => c.pages());
const findSide = () => pages().find((p) => p.url().startsWith('af://af-desktop/index.html'));
const findLogin = () => pages().find((p) => p.url().includes('login.html'));
const findClone = () => pages().find((p) => p.url().includes('clone/index.html'));

async function esperar(fn, rotulo, timeout = 60000) {
  const inicio = Date.now();
  while (Date.now() - inicio < timeout) {
    try { if (await fn()) return; } catch { /* aguarda */ }
    await wait(300);
  }
  throw new Error(`timeout aguardando ${rotulo}`);
}

try {
  const login = findLogin();
  if (!login) throw new Error('tela de login nao encontrada');
  await login.locator('#user').fill('admin.sesab');
  await login.locator('#pass').fill('Adm@2026!Senha');
  await login.locator('#btn').click();

  await esperar(() => Boolean(findSide()) && Boolean(findClone()), 'app principal');
  const s = findSide();
  const clone = findClone();
  await wait(1800);

  // Abre uma tela com campo de filtro/contexto.
  await clone.locator('.menu__item').filter({ hasText: 'Componente Especializado' }).first().click();
  await clone.locator('.submenu__item').filter({ hasText: 'LME' }).first().click();
  await wait(1200);

  // Digita termo clínico + CPF fictício: o REA/LGPD deve remover o CPF.
  const termo = 'metformina 850 mg E11 diabetes CPF 123.456.789-00';
  await clone.locator('#filtro').fill(termo);
  await wait(1200);

  await esperar(async () => (await s.locator('#ctx-status').innerText()).includes('fármaco'), 'contexto capturado');
  const contexto = await s.locator('#context-view').innerText();
  console.log('contexto capturado:', contexto.replace(/\s+/g, ' ').slice(0, 240));

  // Print do contexto já sanitizado (sem CPF).
  await s.locator('section[aria-labelledby="ctx-title"]').screenshot({
    path: `${OUT}/22-RAG-contexto-LGPD.png`,
  });
  console.log('22-RAG-contexto-LGPD.png OK');

  // Executa a análise RAG e espera o resultado real aparecer.
  await s.locator('#btn-analyze').click();
  await s.locator('#analysis-result').getByText('glicemia', { exact: false }).first()
    .waitFor({ timeout: 60000 });
  await s.locator('#analysis-result').getByText('Critérios', { exact: false }).first()
    .waitFor({ timeout: 60000 });
  await wait(1200);
  console.log('resultado RAG:', (await s.locator('#analysis-result').innerText()).replace(/\s+/g, ' ').slice(0, 240));

  await s.locator('section[aria-labelledby="analysis-title"]').screenshot({
    path: `${OUT}/23-RAG-resultado.png`,
  });
  console.log('23-RAG-resultado.png OK');

  await s.screenshot({ path: `${OUT}/24-RAG-sidebar-completa.png`, fullPage: true });
  console.log('24-RAG-sidebar-completa.png OK');

  // Auditoria real no clone (quem, o que, quando).
  await clone.locator('#btn-audit-view').click();
  await clone.getByText('Log de auditoria', { exact: false }).first().waitFor({ timeout: 30000 });
  await clone.locator('#modal-info').getByText('consulta_ia', { exact: false }).first()
    .or(clone.locator('#modal-info').getByText('analise_protocolos', { exact: false }).first())
    .waitFor({ timeout: 30000 }).catch(() => {});
  await wait(1200);
  await clone.screenshot({ path: `${OUT}/09-auditoria-app.png` });
  console.log('09-auditoria-app.png OK');
  console.log('modal:', (await clone.locator('#modal-info').innerText()).replace(/\s+/g, ' ').slice(0, 300));
} finally {
  await b.close();
}
