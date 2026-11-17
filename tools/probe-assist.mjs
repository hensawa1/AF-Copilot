import { chromium } from 'playwright';
const b = await chromium.connectOverCDP('http://127.0.0.1:9251');
try {
  const s = b.contexts().flatMap(c => c.pages()).find(p => p.url().startsWith('af://af-desktop/index.html'));
  console.log('url:', s.url());
  console.log('ask:', (await s.locator('#ask-result').innerText()).replace(/\s+/g, ' ').slice(0, 400));
  console.log('admin visivel:', await s.locator('section[aria-labelledby="insights-title"]').isVisible());
} finally { await b.close(); }
