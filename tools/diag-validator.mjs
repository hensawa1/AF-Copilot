import { chromium } from 'playwright';
const b = await chromium.connectOverCDP('http://127.0.0.1:9256');
const s = b.contexts().flatMap(c=>c.pages()).find(p=>p.url().startsWith('af://af-desktop/index.html'));
console.log('validation:', (await s.locator('#validation-result').innerText()).slice(0,1500));
console.log('name:', await s.locator('#rx-file-name').innerText());
await b.close();
