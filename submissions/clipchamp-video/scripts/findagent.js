// findagent.js — list agents (name + id) and environments to locate your target agent
const { chromium } = require('./require-playwright');
const fs = require('fs');
const path = require('path');
const C = require('./common');

const log = C.mkLog('findagent.log');
const BOTS = `https://copilotstudio.microsoft.com/environments/${C.ENV}/bots`;

(async () => {
  const ctx = await chromium.launchPersistentContext(C.UD, {
    executablePath: C.EXE, headless: false, args: C.ARGS, viewport: null,
  });
  const page = ctx.pages()[0] || await ctx.newPage();
  await C.sleep(2000);
  C.maximizeWindow(log);
  await page.goto(BOTS, { waitUntil: 'domcontentloaded', timeout: 180000 });
  await C.settle(page, log);
  C.maximizeWindow(log);
  await C.dismissPopups(page);
  await C.sleep(6000);

  // Rows in the agents grid: capture visible name + any id we can find
  const rows = await page.evaluate(() => {
    const out = [];
    document.querySelectorAll('[role="row"]').forEach(r => {
      const t = r.innerText.replace(/\s+/g, ' ').trim();
      if (!t) return;
      const a = r.querySelector('a[href]');
      out.push({ text: t.slice(0, 140), href: a ? a.getAttribute('href') : null });
    });
    return out;
  });
  fs.writeFileSync(path.join(C.OUT, 'agent-rows.json'), JSON.stringify(rows, null, 2), 'utf8');
  log('rows=' + rows.length);

  // Click each candidate row to harvest its agent id from the URL
  const wanted = process.argv.slice(2);
  for (const name of wanted) {
    try {
      log('--- opening ' + name);
      await page.goto(BOTS, { waitUntil: 'domcontentloaded', timeout: 120000 });
      await C.settle(page, log, 120000, 3);
      await C.sleep(3000);
      await page.getByText(name, { exact: false }).first().click({ timeout: 15000 });
      await C.settle(page, log, 150000, 3);
      await C.sleep(6000);
      const u = page.url();
      const txt = await page.evaluate(() => document.body.innerText).catch(() => '');
      const slug = name.replace(/[^a-z0-9]+/gi, '-').toLowerCase();
      fs.writeFileSync(path.join(C.OUT, `agent-${slug}.txt`), `URL ${u}\n\n${txt}`, 'utf8');
      await page.screenshot({ path: path.join(C.OUT, `agent-${slug}.png`) }).catch(() => {});
      log(`${name} -> ${u} len=${txt.length}`);
    } catch (e) { log(name + ' ERR ' + e.message); }
  }
  log('DONE');
  await ctx.close();
})().catch(e => { log('ERR ' + e.message); process.exit(1); });
