/** Prints exatos pedidos na atividade, com espera explícita dos dados. */
import { chromium } from 'playwright';

const OUT = 'C:/Users/offsechen1/Desktop/AF/evidencias';
const b = await chromium.connectOverCDP('http://127.0.0.1:9247');
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

async function paginas() {
  return b.contexts().flatMap((c) => c.pages());
}
async function sidebar() {
  return (await paginas()).find((p) => p.url().startsWith('af://af-desktop/index.html'));
}
async function clone() {
  return (await paginas()).find((p) => p.url().includes('clone/index.html'));
}
async function loginPage() {
  return (await paginas()).find((p) => p.url().includes('login.html'));
}

async function fazerLogin(user, pass) {
  const login = await loginPage();
  if (!login) throw new Error('tela de login nao encontrada');
  await login.locator('#user').fill(user);
  await login.locator('#pass').fill(pass);
  return login;
}

try {
  // ---------------------------------------------------------------- perfil inicial
  let side = await sidebar();
  if (!side) {
    const login = await fazerLogin('henriquecarvalho', '3246Hz!@#Hz');
    await login.locator('#btn').click();
    await wait(3500);
    side = await sidebar();
  }

  // PRINT A — Perguntar à IA: fornecedor de Salvador
  const secaoAsk = side.locator('section[aria-labelledby="ask-title"]');
  await side.locator('#ask-input').fill('Qual o fornecedor de Salvador?');
  await side.locator('#btn-ask').click();
  await side.getByText('CNPJ', { exact: false }).first().waitFor({ timeout: 20000 });
  await side.getByText('Distribuidora Bahia Farma', { exact: false }).first().waitFor({ timeout: 20000 });
  await wait(1000);
  await secaoAsk.screenshot({ path: `${OUT}/10-perguntar-IA-fornecedor.png` });
  console.log('10-perguntar-IA-fornecedor.png OK');

  // PRINT B — Inteligência para o administrador
  const secaoInsights = side.locator('section[aria-labelledby="insights-title"]');
  await side.locator('#btn-insights').click();
  await side.getByText('RESUMO', { exact: false }).first().waitFor({ timeout: 25000 });
  await side.getByText('INSIGHTS', { exact: false }).first().waitFor({ timeout: 25000 });
  await wait(1000);
  await secaoInsights.screenshot({ path: `${OUT}/11-inteligencia-admin.png` });
  console.log('11-inteligencia-admin.png OK');

  // ---------------------------------------------------------------- logout -> login Assistente
  const cl = await clone();
  await cl.locator('#btn-logout').click();
  await wait(2200);

  const loginAssist = await fazerLogin('assistente.farma', 'Assist@2026!Senha');
  await loginAssist.screenshot({ path: `${OUT}/12-conta-assistente.png` });
  console.log('12-conta-assistente.png OK');
  await loginAssist.locator('#btn').click();
  await wait(3500);

  side = await sidebar();
  if (!side) throw new Error('sidebar nao abriu apos login do assistente');

  // PRINT D — Assistente tentando consultar IA e sendo negado
  const secaoAsk2 = side.locator('section[aria-labelledby="ask-title"]');
  await side.locator('#ask-input').fill('Arlindo');
  await side.locator('#btn-ask').click();
  await side.getByText('Acesso negado', { exact: false }).first().waitFor({ timeout: 20000 });
  await side.getByText('RBAC aplicado', { exact: false }).first().waitFor({ timeout: 20000 });
  await wait(1000);
  await secaoAsk2.screenshot({ path: `${OUT}/13-assistente-IA-negado.png` });
  console.log('13-assistente-IA-negado.png OK');

  // Confere o texto exibido (validação da informação, não só o print)
  const texto = await secaoAsk2.innerText();
  console.log('texto validado:', texto.replace(/\s+/g, ' ').slice(0, 240));
} finally {
  await b.close();
}
