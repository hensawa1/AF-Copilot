/** Reexpande os painéis de RAG/contexto para o print mostrar TODOS os campos. */
import { chromium } from 'playwright';

const OUT = 'C:/Users/offsechen1/Desktop/AF/evidencias';
const b = await chromium.connectOverCDP('http://127.0.0.1:9256');
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const s = b.contexts().flatMap((c) => c.pages())
  .find((p) => p.url().startsWith('af://af-desktop/index.html'));

try {
  if (!s) throw new Error('sidebar nao encontrada');
  await s.evaluate(() => {
    window.scrollTo(0, 0);
    for (const sel of ['#context-view', '#analysis-result']) {
      const el = document.querySelector(sel);
      if (el) {
        el.style.maxHeight = 'none';
        el.style.overflow = 'visible';
      }
    }
    document.querySelectorAll('section.panel').forEach((sec) => {
      sec.style.maxHeight = 'none';
      sec.style.overflow = 'visible';
    });
  });
  await wait(800);

  const ctx = s.locator('section[aria-labelledby="ctx-title"]');
  const ana = s.locator('section[aria-labelledby="analysis-title"]');
  console.log('contexto:', (await ctx.innerText()).replace(/\s+/g, ' ').slice(0, 260));
  console.log('analise:', (await ana.innerText()).replace(/\s+/g, ' ').slice(-300));

  await ctx.screenshot({ path: `${OUT}/22-RAG-contexto-LGPD.png` });
  await ana.screenshot({ path: `${OUT}/23-RAG-resultado.png` });
  await s.screenshot({ path: `${OUT}/24-RAG-sidebar-completa.png`, fullPage: true });
  console.log('22/23/24 recapturados com paineis expandidos');
} finally {
  await b.close();
}
