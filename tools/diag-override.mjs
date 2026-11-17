import { chromium } from 'playwright';
const b = await chromium.connectOverCDP('http://127.0.0.1:9256');
const pages = b.contexts().flatMap((c) => c.pages());
const s = pages.find((p) => p.url().startsWith('af://af-desktop/index.html'));
const cdp = await s.context().newCDPSession(s);
console.log('antes', await s.evaluate(() => ({ iw: innerWidth, ih: innerHeight })));
await cdp.send('Emulation.setDeviceMetricsOverride', {
  width: 1584, height: 911, deviceScaleFactor: 1, mobile: false,
});
await new Promise((r) => setTimeout(r, 800));
console.log('depois', await s.evaluate(() => ({
  iw: innerWidth, ih: innerHeight,
  sidebar: (() => { const e = document.querySelector('.sidebar'); const r = e.getBoundingClientRect(); return {x:r.x,y:r.y,w:r.width,h:r.height}; })(),
  ctx: (() => { const e = document.querySelector('section[aria-labelledby="ctx-title"]'); const r = e.getBoundingClientRect(); return {x:r.x,y:r.y,w:r.width,h:r.height}; })(),
  ana: (() => { const e = document.querySelector('section[aria-labelledby="analysis-title"]'); const r = e.getBoundingClientRect(); return {x:r.x,y:r.y,w:r.width,h:r.height}; })(),
})));
await cdp.send('Emulation.clearDeviceMetricsOverride');
await b.close();
