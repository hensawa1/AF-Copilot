import { chromium } from 'playwright';
const b = await chromium.connectOverCDP('http://127.0.0.1:9256');
const s = b.contexts().flatMap((c) => c.pages())
  .find((p) => p.url().startsWith('af://af-desktop/index.html'));
const cdp = await s.context().newCDPSession(s);
await cdp.send('Emulation.setDeviceMetricsOverride', { width: 1584, height: 911, deviceScaleFactor: 1, mobile: false });
await new Promise((r) => setTimeout(r, 600));
const box = await s.evaluate(() => {
  const el = document.querySelector('section[aria-labelledby="ctx-title"]');
  el.scrollIntoView({ block: 'start' });
  const r = el.getBoundingClientRect();
  return { x: Math.round(r.x), y: Math.round(r.y), width: Math.ceil(r.width), height: Math.ceil(r.height) };
});
console.log('box', JSON.stringify(box));
try {
  await s.screenshot({ path: 'C:/Users/offsechen1/Desktop/AF/evidencias/teste-page.png', clip: box, animations: 'disabled', timeout: 20000 });
  console.log('page screenshot ok');
} catch (e) {
  console.log('page screenshot erro:', e.message);
}
await cdp.send('Emulation.clearDeviceMetricsOverride').catch(() => {});
await b.close();
