// diag.js — screenshot the bots list at intervals to see what actually renders
const { chromium } = require('./require-playwright');
const fs = require('fs');
const path = require('path');
const C = require('./common');

const log = C.mkLog('diag.log');
const BOTS = `https://copilotstudio.microsoft.com/environments/${C.ENV}/bots`;

(async () => {
  const ctx = await chromium.launchPersistentContext(C.UD, {
    executablePath: C.EXE, headless: false, args: C.ARGS, viewport: null,
  });
  const page = ctx.pages()[0] || await ctx.newPage();
  page.on('console', m => { if (m.type() === 'error') log('CONSOLE ' + m.text().slice(0, 200)); });
  page.on('response', r => { if (r.status() >= 400) log(`HTTP ${r.status()} ${r.url().slice(0, 160)}`); });

  await C.sleep(2000);
  C.maximizeWindow(log);
  await page.goto(BOTS, { waitUntil: 'domcontentloaded', timeout: 180000 });

  for (let i = 1; i <= 8; i++) {
    await C.sleep(15000);
    const info = await page.evaluate(() => ({
      url: location.href, len: document.body.innerText.length,
      html: document.documentElement.outerHTML.length,
      css: `${innerWidth}x${innerHeight}`,
      head: document.body.innerText.replace(/\s+/g, ' ').slice(0, 200),
    })).catch(e => ({ err: e.message }));
    log(`t=${i * 15}s ` + JSON.stringify(info));
    await page.screenshot({ path: path.join(C.OUT, `d-${String(i).padStart(2, '0')}.png`) }).catch(() => {});
  }
  log('DONE');
  await ctx.close();
})().catch(e => { log('ERR ' + e.message); process.exit(1); });
