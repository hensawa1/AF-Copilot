import { chromium } from 'playwright';
console.log('conectando...');
const b = await chromium.connectOverCDP('http://127.0.0.1:9256');
console.log('conectado');
const pages = b.contexts().flatMap((c) => c.pages());
console.log('paginas:', pages.map((p) => p.url()));
const s = pages.find((p) => p.url().startsWith('af://af-desktop/index.html'));
console.log('sidebar:', Boolean(s));
if (s) {
  console.log('title:', await s.title());
  const info = await s.evaluate(() => {
    const c = document.querySelector('section[aria-labelledby="ctx-title"]');
    const a = document.querySelector('section[aria-labelledby="analysis-title"]');
    const cv = document.querySelector('#context-view');
    const av = document.querySelector('#analysis-result');
    return {
      scrollY: window.scrollY,
      docH: document.documentElement.scrollHeight,
      innerH: window.innerHeight,
      ctx: c ? c.getBoundingClientRect().toJSON() : null,
      ana: a ? a.getBoundingClientRect().toJSON() : null,
      ctxText: cv ? cv.innerText.length : 0,
      anaText: av ? av.innerText.length : 0,
    };
  });
  console.log(JSON.stringify(info, null, 2));
}
await b.close();
console.log('fim');
