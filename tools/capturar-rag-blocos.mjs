/** Captura o RAG em blocos legíveis: topo e rodapé (safeText/fontes). */
import { chromium } from 'playwright';

const OUT = 'C:/Users/offsechen1/Desktop/AF/evidencias';
const b = await chromium.connectOverCDP('http://127.0.0.1:9256');
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const s = b.contexts().flatMap((c) => c.pages())
  .find((p) => p.url().startsWith('af://af-desktop/index.html'));

try {
  if (!s) throw new Error('sidebar nao encontrada');
  await s.evaluate(() => {
    const c = document.querySelector('#context-view');
    if (c) { c.style.maxHeight = '320px'; c.style.overflow = 'auto'; }
    const a = document.querySelector('#analysis-result');
    if (a) { a.style.maxHeight = '520px'; a.style.overflow = 'auto'; }
  });
  await wait(600);

  const ctx = s.locator('section[aria-labelledby="ctx-title"]');
  const ana = s.locator('section[aria-labelledby="analysis-title"]');
  const cview = s.locator('#context-view');
  const aview = s.locator('#analysis-result');

  // Topo do contexto: fármacos, dosagem, CID.
  await cview.evaluate((el) => { el.scrollTop = 0; });
  await wait(300);
  await ctx.screenshot({ path: `${OUT}/22a-RAG-contexto-topo.png`, animations: 'disabled', timeout: 15000 });

  // Rodapé do contexto: clinicalTerms + safeText (CPF removido) + origem.
  await cview.evaluate((el) => { el.scrollTop = el.scrollHeight; });
  await wait(300);
  console.log('contexto rodape:', (await ctx.innerText()).replace(/\s+/g, ' ').slice(-300));
  await ctx.screenshot({ path: `${OUT}/22b-RAG-contexto-LGPD.png`, animations: 'disabled', timeout: 15000 });

  // Topo da análise: critérios, exames, alertas.
  await aview.evaluate((el) => { el.scrollTop = 0; });
  await wait(300);
  await ana.screenshot({ path: `${OUT}/23a-RAG-resultado-topo.png`, animations: 'disabled', timeout: 15000 });

  // Rodapé da análise: como fazer, exemplo e fontes.
  await aview.evaluate((el) => { el.scrollTop = el.scrollHeight; });
  await wait(300);
  console.log('analise rodape:', (await ana.innerText()).replace(/\s+/g, ' ').slice(-420));
  await ana.screenshot({ path: `${OUT}/23b-RAG-resultado-fontes.png`, animations: 'disabled', timeout: 15000 });

  console.log('prints RAG topo/rodape OK');
} finally {
  await b.close();
}
