/** Captura prints de cada etapa do fluxo para o relatório acadêmico. */
import { chromium } from 'playwright';
import { mkdirSync } from 'node:fs';

const OUT = 'C:/Users/offsechen1/Desktop/AF/evidencias';
mkdirSync(OUT, { recursive: true });

const b = await chromium.connectOverCDP('http://127.0.0.1:9247');
try {
  const pages = b.contexts().flatMap(c => c.pages());
  const login = pages.find(p => p.url().includes('login.html'));

  // 01 — Login
  await login.screenshot({ path: `${OUT}/01-login.png` });
  console.log('01-login.png');

  // Login com as credenciais do perfil Farmacêutico
  await login.locator('#user').fill(process.env.AF_APP_USER);
  await login.locator('#pass').fill(process.env.AF_APP_PASSWORD);
  await login.locator('#btn').click();
  await new Promise(r => setTimeout(r, 3500));

  let all = b.contexts().flatMap(c => c.pages());
  const clone = all.find(p => p.url().includes('clone/index.html'));
  const sidebar = all.find(p => p.url().startsWith('af://af-desktop/index.html'));

  // 02 — Dashboard com gráficos e alertas
  await clone.waitForTimeout(1500);
  await clone.screenshot({ path: `${OUT}/02-dashboard.png` });
  console.log('02-dashboard.png');

  // 03 — Tela de LME com ações e pacientes
  await clone.locator('.menu__item').filter({ hasText: 'Componente Especializado' }).first().click();
  await clone.locator('.submenu__item').filter({ hasText: 'LME' }).first().click();
  await clone.waitForTimeout(1200);
  await clone.screenshot({ path: `${OUT}/03-lme-acoes.png` });
  console.log('03-lme-acoes.png');

  // 04 — Relatório com consumo/estoque/%
  await clone.locator('.menu__item').filter({ hasText: 'Relatórios' }).first().click();
  await clone.locator('.submenu__item').filter({ hasText: 'Comprometimento Estoque' }).first().click();
  await clone.waitForTimeout(1000);
  await clone.screenshot({ path: `${OUT}/04-relatorio-estoque.png` });
  console.log('04-relatorio-estoque.png');

  // 05 — Sidebar: insights da IA
  await sidebar.locator('#btn-insights').click();
  await sidebar.waitForTimeout(3500);
  await sidebar.screenshot({ path: `${OUT}/05-insights-ia.png` });
  console.log('05-insights-ia.png');

  // 06 — Sidebar: pergunta à IA (fornecedor)
  await sidebar.locator('#ask-input').fill('Qual o fornecedor de Salvador?');
  await sidebar.locator('#btn-ask').click();
  await sidebar.waitForTimeout(1500);
  await sidebar.screenshot({ path: `${OUT}/06-ask-fornecedor.png` });
  console.log('06-ask-fornecedor.png');

  // 07 — Auditoria no clone
  await clone.evaluate(() => document.getElementById('modal-info')?.classList.remove('open'));
  await clone.locator('#btn-audit-view').click();
  await clone.waitForTimeout(1200);
  await clone.screenshot({ path: `${OUT}/07-auditoria.png` });
  console.log('07-auditoria.png');

  // 08 — Login novamente (perfil sem permissão já evidenciado no TXT)
  console.log('capturas concluidas');
} finally { await b.close(); }
