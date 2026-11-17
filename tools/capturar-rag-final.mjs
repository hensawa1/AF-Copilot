/** Captura final do RAG em blocos. O CDP fromSurface:false entrega a janela
 *  inteira; o Node salva o frame e o Python recorta o painel desejado. */
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';

const OUT = 'C:/Users/offsechen1/Desktop/AF/evidencias';
const b = await chromium.connectOverCDP('http://127.0.0.1:9256');
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const pages = b.contexts().flatMap((c) => c.pages());
const s = pages.find((p) => p.url().startsWith('af://af-desktop/index.html'));
const clone = pages.find((p) => p.url().includes('clone/index.html'));

try {
  if (!s) throw new Error('sidebar nao encontrada');
  const cdp = await s.context().newCDPSession(s);
  await cdp.send('Emulation.setDeviceMetricsOverride', {
    width: 1584, height: 911, deviceScaleFactor: 1, mobile: false,
  });
  await wait(600);
  if (clone) {
    await clone.locator('#info-close').click({ timeout: 3000 }).catch(() => {});
  }
  await s.evaluate(() => {
    for (const sel of ['#context-view', '#analysis-result']) {
      const el = document.querySelector(sel);
      if (el) { el.style.maxHeight = 'none'; el.style.overflow = 'visible'; }
    }
    const sb = document.querySelector('.sidebar');
    if (sb) sb.scrollTop = 0;
  });
  await wait(500);

  const boxes = {};
  async function capture(nome, selector, innerSelector, scroll) {
    const box = await s.evaluate(({ selector, innerSelector, scroll }) => {
      const el = document.querySelector(selector);
      const inner = innerSelector ? document.querySelector(innerSelector) : null;
      if (inner) inner.scrollTop = scroll === 'bottom' ? inner.scrollHeight : 0;
      el.scrollIntoView({ block: 'start' });
      const r = el.getBoundingClientRect();
      return {
        x: Math.round(r.x), y: Math.round(r.y),
        width: Math.ceil(r.width), height: Math.ceil(r.height),
      };
    }, { selector, innerSelector, scroll });
    await wait(500);
    const { data } = await Promise.race([
      cdp.send('Page.captureScreenshot', { format: 'png', fromSurface: false }),
      new Promise((_, rej) => setTimeout(() => rej(new Error('timeout cdp')), 20000)),
    ]);
    writeFileSync(`${OUT}/tmp-${nome}.png`, Buffer.from(data, 'base64'));
    boxes[nome] = box;
    console.log(nome, JSON.stringify(box), data.length);
  }

  await capture('22a', 'section[aria-labelledby="ctx-title"]', '#context-view', 'top');
  await capture('22b', 'section[aria-labelledby="ctx-title"]', '#context-view', 'bottom');
  await capture('23a', 'section[aria-labelledby="analysis-title"]', '#analysis-result', 'top');
  await capture('23b', 'section[aria-labelledby="analysis-title"]', '#analysis-result', 'bottom');
  writeFileSync(`${OUT}/rag-boxes.json`, JSON.stringify(boxes, null, 2));

  console.log('contexto:', (await s.locator('#context-view').innerText()).replace(/\s+/g, ' ').slice(0, 450));
  console.log('analise fim:', (await s.locator('#analysis-result').innerText()).replace(/\s+/g, ' ').slice(-500));
  await cdp.send('Emulation.clearDeviceMetricsOverride').catch(() => {});
  console.log('frames salvos');
} finally {
  await b.close();
}
