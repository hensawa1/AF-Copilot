import { chromium } from 'playwright';
const b = await chromium.connectOverCDP('http://127.0.0.1:9256');
const pages = b.contexts().flatMap((c) => c.pages());
for (const p of pages) {
  const info = await p.evaluate(() => ({
    url: location.href,
    innerWidth, innerHeight, outerWidth, outerHeight,
    dpr: devicePixelRatio,
    screenW: screen.width, screenH: screen.height,
    clientW: document.documentElement.clientWidth,
    bodyW: document.body.getBoundingClientRect().width,
    zoom: (window.visualViewport && window.visualViewport.scale) || 1,
  }));
  console.log(JSON.stringify(info, null, 2));
}
await b.close();
