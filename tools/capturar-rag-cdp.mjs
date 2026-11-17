/** Captura o RAG em blocos legíveis via CDP, com viewport lógico de 1584x911.
 *  O app Electron estava com a webContents do sidebar em 30 px (janela sobreposta);
 *  o override restaura o layout real de 30% (~475 px) para o print.
 */
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';

const OUT = 'C:/Users/offsechen1/Desktop/AF/evidencias';
const b = await chromium.connectOverCDP('http://127.0.0.1:9256');
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const s = b.contexts().flatMap((c) => c.pages())
  .find((p) => p.url().startsWith('af://af-desktop/index.html'));

try {
  if (!s) throw new Error('sidebar nao encontrada');
  const cdp = await s.context().newCDPSession(s);
  await cdp.send('Emulation.setDeviceMetricsOverride', {
    width: 1584, height: 911, deviceScaleFactor: 1, mobile: false,
  });
  await wait(600);

  await s.evaluate(() => {
    for (const sel of ['#context-view', '#analysis-result']) {
      const el = document.querySelector(sel);
      if (el) { el.style.maxHeight = 'none'; el.style.overflow = 'visible'; }
    }
    document.querySelectorAll('section.panel').forEach((sec) => {
      sec.style.maxHeight = 'none';
      sec.style.overflow = 'visible';
    });
  });
  await wait(600);

  async function shot(selector, innerSelector, scroll, arquivo) {
    const box = await s.evaluate(({ selector, innerSelector, scroll }) => {
      const el = document.querySelector(selector);
      const inner = innerSelector ? document.querySelector(innerSelector) : null;
      if (inner) inner.scrollTop = scroll === 'bottom' ? inner.scrollHeight : 0;
      el.scrollIntoView({ block: 'start' });
      const r = el.getBoundingClientRect();
      return {
        x: Math.round(r.x), y: Math.round(r.y + window.scrollY),
        width: Math.ceil(r.width), height: Math.ceil(r.height),
      };
    }, { selector, innerSelector, scroll });
    await wait(500);
    console.log('capturando', arquivo, JSON.stringify(box));
    const { data } = await cdp.send('Page.captureScreenshot', {
      format: 'png',
      clip: { x: box.x, y: box.y, width: box.width, height: box.height, scale: 1 },
      captureBeyondViewport: true,
    });
    writeFileSync(`${OUT}/${arquivo}`, Buffer.from(data, 'base64'));
    console.log('ok', arquivo);
  }

  await shot('section[aria-labelledby="ctx-title"]', '#context-view', 'top', '22a-RAG-contexto-topo.png');
  await shot('section[aria-labelledby="ctx-title"]', '#context-view', 'bottom', '22b-RAG-contexto-LGPD.png');
  await shot('section[aria-labelledby="analysis-title"]', '#analysis-result', 'top', '23a-RAG-resultado-topo.png');
  await shot('section[aria-labelledby="analysis-title"]', '#analysis-result', 'bottom', '23b-RAG-resultado-fontes.png');

  console.log('contexto:', (await s.locator('#context-view').innerText()).replace(/\s+/g, ' ').slice(0, 400));
  console.log('analise fim:', (await s.locator('#analysis-result').innerText()).replace(/\s+/g, ' ').slice(-450));
  await cdp.send('Emulation.clearDeviceMetricsOverride');
  console.log('fim');
} finally {
  await b.close();
}
