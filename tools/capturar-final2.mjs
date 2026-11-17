/** Continuação dos prints finais: corrige medicamentos, portal 20/21, admin e assistente. */
import { chromium } from 'playwright';

const OUT = 'C:/Users/offsechen1/Desktop/AF/evidencias';
const b = await chromium.connectOverCDP('http://127.0.0.1:9256');
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const pages = () => b.contexts().flatMap((c) => c.pages());
const findSide = () => pages().find((p) => p.url().startsWith('af://af-desktop/index.html'));
const findLogin = () => pages().find((p) => p.url().includes('login.html'));
const findClone = () => pages().find((p) => p.url().includes('clone/index.html'));

async function esperar(fn, rotulo, timeout = 45000) {
  const inicio = Date.now();
  while (Date.now() - inicio < timeout) {
    try { if (await fn()) return true; } catch { /* ignore */ }
    await wait(300);
  }
  throw new Error(`timeout aguardando ${rotulo}`);
}

async function login(user, pass, printFile) {
  const l = findLogin();
  if (!l) throw new Error('login nao encontrado');
  await l.locator('#user').fill(user);
  await l.locator('#pass').fill(pass);
  if (printFile) { await wait(500); await l.screenshot({ path: `${OUT}/${printFile}` }); }
  await l.locator('#btn').click();
  await esperar(() => Boolean(findSide()), 'sidebar');
  await wait(1200);
  return findSide();
}

async function logout() {
  const c = findClone();
  if (c) {
    await c.locator('#btn-logout').dispatchEvent('click');
    await esperar(() => Boolean(findLogin()), 'tela de login');
    await wait(700);
  }
}

async function perguntar(s, q, waitTexts, arquivo, meta = '') {
  let ultimoErro = null;
  for (let tentativa = 1; tentativa <= 3; tentativa++) {
    try {
      const btn = s.locator('#btn-ask');
      await esperar(async () => !(await btn.isDisabled()), 'botao Perguntar');
      await s.locator('#ask-input').fill(q);
      const valor = await s.locator('#ask-input').inputValue();
      if (valor !== q) throw new Error(`input divergente: ${valor}`);
      await btn.click();
      if (meta) {
        await s.locator('#ask-result .ask-meta').filter({ hasText: meta }).first()
          .waitFor({ timeout: 60000 });
      }
      for (const t of waitTexts) {
        await s.locator('#ask-result').getByText(t, { exact: false }).first()
          .waitFor({ timeout: 45000 });
      }
      await wait(900);
      await s.screenshot({ path: `${OUT}/${arquivo}`, animations: 'disabled' });
      console.log(arquivo, 'OK');
      console.log('  resposta:', (await s.locator('#ask-result').innerText()).replace(/\s+/g, ' ').slice(0, 220));
      return;
    } catch (erro) {
      ultimoErro = erro;
      console.log(`  tentativa ${tentativa} de ${arquivo} falhou: ${erro.message.split('\n')[0]}`);
      await wait(1500);
    }
  }
  throw ultimoErro;
}

async function abrirPortal(clone, grupo, item, cabecalho, arquivo) {
  const itemLoc = clone.locator('.submenu__item', { hasText: item }).first();
  if (!(await itemLoc.isVisible().catch(() => false))) {
    await clone.locator('.menu__item', { hasText: grupo }).first().click();
    await wait(500);
  }
  await itemLoc.click();
  await clone.locator('#content th', { hasText: cabecalho }).first().waitFor({ timeout: 30000 });
  await wait(900);
  await clone.screenshot({ path: `${OUT}/${arquivo}`, animations: 'disabled' });
  console.log(arquivo, 'OK');
}

try {
  let s = findSide();
  if (!s) s = await login('henriquecarvalho', '3246Hz!@#Hz');

  // Reexecuta somente o print de medicamentos (o anterior foi interceptado por outra consulta).
  await perguntar(s, 'Medicamentos cadastrados', ['SIM-', 'Código'], '15-IA-medicamentos.png', 'Intenção: medicamentos');

  // Portal clonado — estabelecimentos e fornecedores com Município/UF
  const clone = findClone();
  if (!clone) throw new Error('portal clone nao encontrado');
  await abrirPortal(clone, 'Cadastros', 'Estabelecimento de Saúde', 'Município', '20-portal-estabelecimentos.png');
  await abrirPortal(clone, 'Cadastros', 'Fornecedor/Fabricante', 'UF', '21-portal-fornecedores.png');

  // Administrador — insights
  await logout();
  s = await login('admin.sesab', 'Adm@2026!Senha');
  const btnIns = s.locator('#btn-insights');
  await esperar(async () => !(await btnIns.isDisabled()), 'botao insights');
  await btnIns.click();
  await s.getByText('RESUMO', { exact: false }).first().waitFor({ timeout: 60000 });
  await s.getByText('INSIGHTS', { exact: false }).first().waitFor({ timeout: 60000 });
  await s.locator('section[aria-labelledby="insights-title"]').scrollIntoViewIfNeeded();
  await wait(900);
  await s.screenshot({ path: `${OUT}/11-inteligencia-admin.png`, animations: 'disabled' });
  console.log('11-inteligencia-admin.png OK');

  // Assistente — IA permitida só para agregados e negada para pacientes
  await logout();
  s = await login('assistente.farma', 'Assist@2026!Senha', '12-conta-assistente.png');
  console.log('painel admin visivel assistente:', await s.locator('section[aria-labelledby="insights-title"]').isVisible());
  await perguntar(s, 'Quantos remédios existem?', ['medicamentos cadastrados'], '15b-assistente-IA-permitida.png', 'Intenção: contagem');
  await perguntar(s, 'Quais pacientes são de Salvador?', ['Acesso negado', 'RBAC aplicado'], '14-assistente-IA-negado.png', 'Intenção: pacientes');
  await s.screenshot({ path: `${OUT}/13-assistente-sidebar-completa.png`, animations: 'disabled' });
  console.log('13/14 OK');
} finally {
  await b.close();
}
