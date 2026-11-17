import { chromium } from 'playwright';
const b = await chromium.connectOverCDP('http://127.0.0.1:9256');
const pages = b.contexts().flatMap((c) => c.pages());
const s = pages.find((p) => p.url().startsWith('af://af-desktop/index.html'));
const c = pages.find((p) => p.url().includes('clone/index.html'));
for (const [name, p] of [['sidebar', s], ['clone', c]]) {
  if (!p) continue;
  const cdp = await p.context().newCDPSession(p);
  try {
    const info = await cdp.send('Browser.getWindowForTarget');
    console.log(name, JSON.stringify(info));
    await cdp.send('Browser.setWindowBounds', {
      windowId: info.windowId,
      bounds: { width: 1600, height: 1000, windowState: 'normal' },
    });
    const after = await cdp.send('Browser.getWindowBounds', { windowId: info.windowId });
    console.log(name, 'depois', JSON.stringify(after));
  } catch (e) {
    console.log(name, 'erro', e.message);
  }
  const dims = await p.evaluate(() => ({ w: innerWidth, h: innerHeight, dpr: devicePixelRatio }));
  console.log(name, 'viewport', dims);
}
await b.close();
