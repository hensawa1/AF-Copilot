/** Captura: auditoria com usuário no RAG + validador de receita (válida/inválida). */
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';

const OUT = 'C:/Users/offsechen1/Desktop/AF/evidencias';
const TXT = 'C:/Users/offsechen1/Desktop/AF/docs/evidencias';
const b = await chromium.connectOverCDP('http://127.0.0.1:9256');
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const pages = b.contexts().flatMap((c) => c.pages());
const s = pages.find((p) => p.url().startsWith('af://af-desktop/index.html'));
const clone = pages.find((p) => p.url().includes('clone/index.html'));

try {
  if (!s || !clone) throw new Error('paginas do app nao encontradas');
  const cdp = await s.context().newCDPSession(s);
  await cdp.send('Emulation.setDeviceMetricsOverride', {
    width: 1584, height: 911, deviceScaleFactor: 1, mobile: false,
  });
  await wait(500);
  await clone.locator('#info-close').click({ timeout: 3000 }).catch(() => {});

  async function frame(nome) {
    const { data } = await Promise.race([
      cdp.send('Page.captureScreenshot', { format: 'png', fromSurface: false }),
      new Promise((_, rej) => setTimeout(() => rej(new Error('timeout cdp')), 20000)),
    ]);
    writeFileSync(`${OUT}/tmp-${nome}.png`, Buffer.from(data, 'base64'));
    console.log('frame', nome, data.length);
  }

  // --- RAG com auditoria (agora com usuario/perfil no log) ---
  // A clone já está na tela LME; só é preciso alimentar o campo de contexto.
  if (await clone.locator('#filtro').count() === 0) {
    await clone.locator('.menu__item').filter({ hasText: 'Componente Especializado' }).first().click();
    await clone.locator('.submenu__item').filter({ hasText: 'LME' }).first().evaluate((el) => el.click());
  }
  await wait(800);
  await clone.locator('#filtro').fill('metformina 850 mg E11 diabetes CPF 123.456.789-00');
  await wait(1000);
  await s.locator('#btn-analyze').click();
  await s.locator('#analysis-result').getByText('glicemia', { exact: false }).first()
    .waitFor({ timeout: 90000 });
  await wait(1200);
  console.log('RAG ok');

  await clone.locator('#btn-audit-view').click();
  await clone.getByText('Log de auditoria', { exact: false }).first().waitFor({ timeout: 30000 });
  await wait(1200);
  const modal = await clone.locator('#modal-info').innerText();
  writeFileSync(`${TXT}/auditoria_rag.txt`, modal, 'utf8');
  console.log('auditoria RAG:', modal.replace(/\s+/g, ' ').slice(0, 400));
  await frame('auditoria-RAG');
  await clone.locator('#info-close').click().catch(() => {});
  await wait(500);

  // --- Validador de receita ---
  const boxes = {};
  async function validar(rotulo, arquivo) {
    await s.evaluate(() => {
      const r = document.querySelector('#validation-result');
      if (r) { r.style.maxHeight = 'none'; r.style.overflow = 'visible'; }
    });
    await s.locator('#rx-file').setInputFiles(arquivo);
    await s.locator('#nome').count().catch(() => {});
    await wait(700);
    const nomeArquivo = arquivo.split(/[\\/]/).pop();
    console.log(rotulo, 'arquivo:', (await s.locator('#rx-file-name').innerText()).trim());
    await s.locator('#btn-validate').click();
    await s.locator('#validation-result').getByText('Extraindo', { exact: false }).first()
      .waitFor({ timeout: 10000 }).catch(() => {});
    const esperado = rotulo === 'validador-valido' ? 'Dados extraídos' : 'Inconsistências';
    await s.locator('#validation-result').getByText(esperado, { exact: false }).first()
      .waitFor({ timeout: 120000 });
    await wait(1200);
    const box = await s.evaluate(() => {
      const el = document.querySelector('section[aria-labelledby="rx-title"]');
      el.scrollIntoView({ block: 'start' });
      const r = el.getBoundingClientRect();
      return { x: Math.round(r.x), y: Math.round(r.y), width: Math.ceil(r.width), height: Math.ceil(r.height) };
    });
    await wait(500);
    await frame(rotulo);
    boxes[rotulo] = box;
    const texto = await s.locator('#validation-result').innerText();
    console.log(rotulo, 'resultado:', texto.replace(/\s+/g, ' ').slice(0, 500));
    return texto;
  }

  const valido = await validar('validador-valido', 'C:/Users/offsechen1/Desktop/AF/evidencias/receita-ficticia.png');
  const invalido = await validar('validador-invalido', 'C:/Users/offsechen1/Desktop/AF/evidencias/receita-invalida-ficticia.png');
  writeFileSync(`${TXT}/validacao_receitas.txt`,
    'VALIDAÇÕES REAIS DO VALIDADOR MULTIMODAL\n' + '='.repeat(55) + '\n\n' +
    'RECEITA VÁLIDA (fictícia)\n' + valido + '\n\n' +
    'RECEITA INVÁLIDA (fictícia — Losartana/CID I10/emissão 2020)\n' + invalido + '\n',
    'utf8');
  writeFileSync(`${OUT}/validacao-boxes.json`, JSON.stringify(boxes, null, 2));
  await cdp.send('Emulation.clearDeviceMetricsOverride').catch(() => {});
  console.log('concluido');
} finally {
  await b.close();
}
