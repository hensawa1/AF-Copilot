import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
const b = await chromium.connectOverCDP('http://127.0.0.1:9256');
const s = b.contexts().flatMap((c) => c.pages())
  .find((p) => p.url().startsWith('af://af-desktop/index.html'));
const cdp = await s.context().newCDPSession(s);
await cdp.send('Emulation.setDeviceMetricsOverride', { width: 1584, height: 911, deviceScaleFactor: 1, mobile: false });
await new Promise((r) => setTimeout(r, 500));
const box = await s.evaluate(() => {
  const el = document.querySelector('section[aria-labelledby="ctx-title"]');
  el.scrollIntoView({ block: 'start' });
  const r = el.getBoundingClientRect();
  return { x: Math.round(r.x), y: Math.round(r.y + window.scrollY), width: Math.ceil(r.width), height: Math.ceil(r.height) };
});
console.log('box', JSON.stringify(box));
try {
  const res = await Promise.race([
    cdp.send('Page.captureScreenshot', {
      format: 'png',
      clip: { ...box, scale: 1 },
      captureBeyondViewport: true,
      fromSurface: false,
    }),
    new Promise((_, rej) => setTimeout(() => rej(new Error('timeout cdp')), 15000)),
  ]);
  writeFileSync('C:/Users/offsechen1/Desktop/AF/evidencias/teste-cdp.png', Buffer.from(res.data, 'base64'));
  console.log('salvou teste-cdp.png', res.data.length);
} catch (e) {
  console.log('erro:', e.message);
}
await cdp.send('Emulation.clearDeviceMetricsOverride').catch(() => {});
await b.close();
