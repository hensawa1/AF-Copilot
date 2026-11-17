/** Gera prints da prova de RBAC via IA e da auditoria (comespera explícita). */
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';

const BASE = 'C:/Users/offsechen1/Desktop/AF';
const txt = readFileSync(`${BASE}/docs/evidencias/rbac.txt`, 'utf8');
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

const linhas = txt.split('\n');
const inicioAssist = linhas.findIndex((l) => l.includes('PERFIL: Assistente'));
const inicioAudit = linhas.findIndex((l) => l.includes('AUDITORIA DA IA'));
const blocoAssist = linhas.slice(inicioAssist, inicioAudit).join('\n');
const blocoAudit = linhas.slice(inicioAudit).join('\n');

const html = `<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">
<style>
body{font-family:"Segoe UI",sans-serif;background:#0b1320;color:#e7eef8;margin:0;padding:26px}
h1{color:#7fd1c4;font-size:20px;margin:0 0 4px}
p{color:#91a4bd;font-size:12px;margin:0 0 18px}
.card{background:#142337;border:1px solid #1d2f47;border-radius:12px;padding:18px;margin-bottom:16px}
.card h2{color:#7fd1c4;font-size:13px;margin:0 0 12px;text-transform:uppercase;letter-spacing:1px}
pre{white-space:pre-wrap;font-family:Consolas,monospace;font-size:12px;line-height:1.6;margin:0}
.denied{color:#ef6c6c;font-weight:bold}
.allowed{color:#69d69d}
</style></head><body>
<div id="secao-negado" class="card">
<h2>Prova 1 — Perfil sem permissão consultando a IA</h2>
<pre>${esc(blocoAssist)
  .replace(/NEGADO/g, '<span class="denied">NEGADO</span>')
  .replace(/RBAC aplicado/g, '<span class="denied">RBAC aplicado</span>')}</pre>
</div>
<div id="secao-auditoria" class="card">
<h2>Prova 2 — Auditoria da IA (quem, o quê, quando)</h2>
<pre>${esc(blocoAudit)
  .replace(/linhas=100/g, '<span class="allowed">linhas=100</span>')
  .replace(/linhas=0/g, '<span class="denied">linhas=0</span>')}</pre>
</div>
</body></html>`;

const file = `${BASE}/evidencias/rbac-IA-evidencia.html`;
writeFileSync(file, html, 'utf8');

const browser = await chromium.connectOverCDP('http://127.0.0.1:9222');
try {
  const page = await browser.contexts()[0].newPage();
  await page.setViewportSize({ width: 1100, height: 900 });
  await page.goto(`file:///${file}`, { waitUntil: 'domcontentloaded' });

  // AGUARDE explícito: as informações precisam aparecer antes do print.
  await page.getByText('PERFIL: Assistente', { exact: false }).waitFor({ timeout: 15000 });
  await page.locator('#secao-auditoria').waitFor({ timeout: 15000 });
  await page.waitForTimeout(1200);

  await page.locator('#secao-negado').screenshot({ path: `${BASE}/evidencias/08-IA-RBAC-negado.png` });
  await page.locator('#secao-auditoria').screenshot({ path: `${BASE}/evidencias/09-auditoria-IA.png` });
  console.log('prints 08 e 09 capturados apos wait');
  await page.close();
} finally { await browser.close(); }
