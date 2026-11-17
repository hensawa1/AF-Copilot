/** Prints finais: painéis pedidos + prova visual do perfil Assistente. */
import { chromium } from 'playwright';

const OUT = 'C:/Users/offsechen1/Desktop/AF/evidencias';
const b = await chromium.connectOverCDP('http://127.0.0.1:9251');
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const pages = () => b.contexts().flatMap((c) => c.pages());
const side = () => pages().find((p) => p.url().startsWith('af://af-desktop/index.html'));
const login = () => pages().find((p) => p.url().includes('login.html'));

async function entrar(user, pass) {
  const l = await login();
  if (!l) throw new Error('login nao encontrado');
  await l.locator('#user').fill(user);
  await l.locator('#pass').fill(pass);
  return l;
}

try {
  // ---- Perfil farmacêutico (painéis pedidos nas imagens)
  let l = await entrar('henriquecarvalho', '3246Hz!@#Hz');
  await l.locator('#btn').click();
  await wait(3500);
  let s = await side();
  if (!s) throw new Error('sidebar nao abriu');

  // Print: PERGUNTAR À IA com fornecedor
  await s.locator('#ask-input').fill('Qual o fornecedor de Salvador?');
  await s.locator('#btn-ask').click();
  await s.getByText('CNPJ', { exact: false }).first().waitFor({ timeout: 20000 });
  await s.getByText('Distribuidora Bahia Farma', { exact: false }).first().waitFor({ timeout: 20000 });
  await wait(1200);
  await s.locator('section[aria-labelledby="ask-title"]').screenshot({ path: `${OUT}/10-perguntar-IA-fornecedor.png` });
  console.log('10 OK');

  // Print: INTELIGÊNCIA PARA O ADMINISTRADOR com insights
  await s.locator('#btn-insights').click();
  await s.getByText('RESUMO', { exact: false }).first().waitFor({ timeout: 30000 });
  await s.getByText('INSIGHTS', { exact: false }).first().waitFor({ timeout: 30000 });
  await wait(1200);
  await s.locator('section[aria-labelledby="insights-title"]').screenshot({ path: `${OUT}/11-inteligencia-admin.png` });
  console.log('11 OK');

  const cl = await pages().then((ps) => ps.find((p) => p.url().includes('clone/index.html')));
  await cl.locator('#btn-logout').click();
  await wait(2500);

  // ---- Perfil Assistente (sem painel admin, com IA negada)
  l = await entrar('assistente.farma', 'Assist@2026!Senha');
  await l.screenshot({ path: `${OUT}/12-conta-assistente.png` });
  await l.locator('#btn').click();
  await wait(3500);
  s = await side();
  if (!s) throw new Error('sidebar assistente nao abriu');

  const adminVisivel = await s.locator('section[aria-labelledby="insights-title"]').isVisible();
  console.log('painel admin visivel para assistente:', adminVisivel);

  await s.locator('#ask-input').fill('Arlindo');
  await s.locator('#btn-ask').click();
  await s.getByText('Acesso negado', { exact: false }).first().waitFor({ timeout: 20000 });
  await s.getByText('RBAC aplicado', { exact: false }).first().waitFor({ timeout: 20000 });
  await wait(1200);

  // Print da sidebar inteira (como na imagem enviada) + print do recado
  await s.screenshot({ path: `${OUT}/13-assistente-sidebar-completa.png` });
  await s.locator('section[aria-labelledby="ask-title"]').screenshot({ path: `${OUT}/14-assistente-IA-negado.png` });
  console.log('13 e 14 OK');
  console.log('texto:', (await s.locator('#ask-result').innerText()).replace(/\s+/g, ' ').slice(0, 200));
} finally {
  await b.close();
}
