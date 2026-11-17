import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
const OUT = 'C:/Users/offsechen1/Desktop/AF/evidencias';
const TXT = 'C:/Users/offsechen1/Desktop/AF/docs/evidencias';
const b = await chromium.connectOverCDP('http://127.0.0.1:9256');
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const pages = b.contexts().flatMap((c) => c.pages());
const s = pages.find((p) => p.url().startsWith('af://af-desktop/index.html'));
const clone = pages.find((p) => p.url().includes('clone/index.html'));
const cdp = await s.context().newCDPSession(s);
try {
  await cdp.send('Emulation.setDeviceMetricsOverride', { width: 1584, height: 911, deviceScaleFactor: 1, mobile: false });
  await wait(400);
  const aberto = await clone.locator('#modal-info.open').count();
  if (!aberto) await clone.locator('#btn-audit-view').click();
  await clone.getByText('Log de auditoria', { exact: false }).first().waitFor({ timeout: 30000 });
  await clone.evaluate(() => {
    const m = document.querySelector('#modal-info');
    if (!m) return;
    const candidatos = [m, ...m.querySelectorAll('*')];
    for (const el of candidatos) {
      if (el.scrollHeight > el.clientHeight + 4) el.scrollTop = 0;
    }
  });
  await wait(800);
  const texto = await clone.locator('#modal-info').innerText();
  writeFileSync(`${TXT}/auditoria_rag.txt`, texto, 'utf8');
  console.log('topo:', texto.replace(/\s+/g, ' ').slice(0, 320));
  const { data } = await cdp.send('Page.captureScreenshot', { format: 'png', fromSurface: false });
  writeFileSync(`${OUT}/26-auditoria-RAG-usuario.png`, Buffer.from(data, 'base64'));
  console.log('26 recapturado');
  await cdp.send('Emulation.clearDeviceMetricsOverride').catch(() => {});
} finally { await b.close(); }
