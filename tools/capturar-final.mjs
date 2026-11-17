/** Prints finais com espera explícita: IA Gemini, Município/UF, portal, insights, validador e RBAC. */
import { chromium } from 'playwright';

const OUT = 'C:/Users/offsechen1/Desktop/AF/evidencias';
const b = await chromium.connectOverCDP('http://127.0.0.1:9256');
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const pages = () => b.contexts().flatMap((c) => c.pages());
const findSide = () => pages().find((p) => p.url().startsWith('af://af-desktop/index.html'));
const findLogin = () => pages().find((p) => p.url().includes('login.html'));
const findClone = () => pages().find((p) => p.url().includes('clone/index.html'));

async function esperar(fn, rotulo, timeout = 30000) {
  const inicio = Date.now();
  while (Date.now() - inicio < timeout) {
    if (fn()) return true;
    await wait(300);
  }
  throw new Error(`timeout aguardando ${rotulo}`);
}

async function login(user, pass, printFile) {
  const l = findLogin();
  if (!l) throw new Error('login nao encontrado');
  await l.locator('#user').fill(user);
  await l.locator('#pass').fill(pass);
  if (printFile) {
    await wait(600);
    await l.screenshot({ path: `${OUT}/${printFile}` });
  }
  await l.locator('#btn').click();
  await esperar(findSide, 'sidebar');
  await wait(1500);
  return findSide();
}

async function logout() {
  const c = findClone();
  if (c) {
    await c.locator('#btn-logout').dispatchEvent('click');
    await esperar(findLogin, 'tela de login');
    await wait(800);
  }
}

async function perguntar(s, q, waitTexts, arquivo) {
  await s.locator('#ask-input').fill(q);
  await s.locator('#btn-ask').click();
  for (const t of waitTexts) {
    await s.locator('#ask-result').getByText(t, { exact: false }).first().waitFor({ timeout: 45000 });
  }
  await wait(1200);
  await s.screenshot({ path: `${OUT}/${arquivo}`, animations: 'disabled' });
  console.log(arquivo, 'OK');
  console.log('  resposta:', (await s.locator('#ask-result').innerText()).replace(/\s+/g, ' ').slice(0, 220));
}

async function abrirPortal(clone, grupo, item, cabecalho, arquivo) {
  await clone.locator('.menu__item', { hasText: grupo }).first().click();
  await wait(500);
  await clone.locator('.submenu__item', { hasText: item }).first().click();
  await clone.locator('#content th', { hasText: cabecalho }).first().waitFor({ timeout: 30000 });
  await wait(900);
  await clone.screenshot({ path: `${OUT}/${arquivo}`, animations: 'disabled' });
  console.log(arquivo, 'OK');
}

try {
  if (findSide()) await logout();

  // Perfil farmacêutico — IA ampla (Gemini interpreta e redige)
  let s = await login('henriquecarvalho', '3246Hz!@#Hz');
  await perguntar(s, 'Qual o fornecedor de Salvador?', ['CNPJ', 'Distribuidora Bahia Farma'], '10-perguntar-IA-fornecedor.png');
  await perguntar(s, 'Medicamentos cadastrados', ['Código', 'SIM-'], '15-IA-medicamentos.png');
  await perguntar(s, 'Quais pacientes são de Salvador?', ['Município', 'Salvador'], '16-IA-pacientes.png');
  await perguntar(s, 'Quantos pacientes estão em tratamento em Salvador?', ['2929'], '18-IA-contagem-salvador.png');

  // Validador de receita (OCR multimodal)
  await s.locator('#rx-file').setInputFiles(`${OUT}/receita-ficticia.png`);
  await s.locator('#btn-validate').click();
  await s.locator('#validation-result').getByText('Dados extraídos', { exact: false }).first().waitFor({ timeout: 90000 });
  await s.locator('#validation-result').scrollIntoViewIfNeeded();
  await wait(1200);
  await s.screenshot({ path: `${OUT}/17-validador-receita.png`, animations: 'disabled' });
  console.log('17-validador-receita.png OK');
  console.log('validacao:', (await s.locator('#validation-result').innerText()).replace(/\s+/g, ' ').slice(0, 300));

  // Portal clonado — Município/UF em pacientes, estabelecimentos e fornecedores
  const clone = findClone();
  if (!clone) throw new Error('portal clone nao encontrado');
  await abrirPortal(clone, 'Cadastros', 'Paciente', 'Município', '19-portal-pacientes.png');
  await abrirPortal(clone, 'Cadastros', 'Estabelecimento de Saúde', 'Município', '20-portal-estabelecimentos.png');
  await abrirPortal(clone, 'Cadastros', 'Fornecedor/Fabricante', 'UF', '21-portal-fornecedores.png');

  // Administrador — insights
  await logout();
  s = await login('admin.sesab', 'Adm@2026!Senha');
  await s.locator('#btn-insights').click();
  await s.getByText('RESUMO', { exact: false }).first().waitFor({ timeout: 30000 });
  await s.getByText('INSIGHTS', { exact: false }).first().waitFor({ timeout: 30000 });
  await s.locator('section[aria-labelledby="insights-title"]').scrollIntoViewIfNeeded();
  await wait(1000);
  await s.screenshot({ path: `${OUT}/11-inteligencia-admin.png`, animations: 'disabled' });
  console.log('11-inteligencia-admin.png OK');

  // Assistente — IA permitida só para agregados e negada para pacientes
  await logout();
  s = await login('assistente.farma', 'Assist@2026!Senha', '12-conta-assistente.png');
  console.log('painel admin visivel assistente:', await s.locator('section[aria-labelledby="insights-title"]').isVisible());
  await perguntar(s, 'Quantos remédios existem?', ['medicamentos cadastrados'], '15b-assistente-IA-permitida.png');
  await perguntar(s, 'Quais pacientes são de Salvador?', ['Acesso negado', 'RBAC aplicado'], '14-assistente-IA-negado.png');
  await s.screenshot({ path: `${OUT}/13-assistente-sidebar-completa.png`, animations: 'disabled' });
  console.log('13/14 OK');
} finally {
  await b.close();
}
