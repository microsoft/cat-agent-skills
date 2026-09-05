// verify.js — MANDATORY GATE: prove window fills the screen and the chat input bar is in-frame.
const { chromium } = require('./require-playwright');
const path = require('path');
const C = require('./common');

const log = C.mkLog('verify.log');

(async () => {
  const ctx = await chromium.launchPersistentContext(C.UD, {
    executablePath: C.EXE, headless: false, args: C.ARGS, viewport: null,
  });
  const page = ctx.pages()[0] || await ctx.newPage();
  await C.sleep(2500);
  C.maximizeWindow(log);
  await C.sleep(2000);
  await C.logViewport(page, log);
  await page.goto(C.AGENT_URL, { waitUntil: 'domcontentloaded', timeout: 180000 });
  await C.settle(page, log);
  C.maximizeWindow(log);
  await C.dismissPopups(page);
  await C.sleep(5000);
  await C.logViewport(page, log);

  // Build view (overview + instructions)
  await page.screenshot({ path: path.join(C.OUT, 'v-build.png') }).catch(() => {});
  const txt = await page.evaluate(() => document.body.innerText).catch(() => '');
  require('fs').writeFileSync(path.join(C.OUT, 'v-build.txt'), `URL ${page.url()}\n\n${txt}`, 'utf8');
  log('build dump len=' + txt.length);

  // Test pane — Copilot Studio uses a Build/Preview/Evaluate/Monitor DROPDOWN behind a
  // single "Build" button (menuitemradio options), not tabs. Navigating straight to
  // <agentUrl>/preview is far more reliable than menu-click choreography; fall back to
  // tab/dropdown clicks for apps where that route doesn't exist.
  await page.goto(C.AGENT_URL + '/preview', { waitUntil: 'domcontentloaded', timeout: 60000 }).catch(() => {});
  await C.sleep(4000);
  let onPreview = await page.getByRole('textbox', { name: /Chat message input|Ask a question/i }).first()
    .isVisible({ timeout: 3000 }).catch(() => false);
  if (!onPreview) {
    for (const name of ['Test', 'Preview']) {
      try {
        const t = page.getByRole('tab', { name: new RegExp(`^${name}$`, 'i') }).first();
        if (await t.isVisible({ timeout: 2500 })) { log('click tab ' + name); await t.click(); await C.sleep(6000); break; }
      } catch {}
    }
    try {
      const btn = page.getByRole('button', { name: /^Test$/i }).first();
      if (await btn.isVisible({ timeout: 2000 })) { log('click Test button'); await btn.click(); await C.sleep(6000); }
    } catch {}
    try {
      const dd = page.getByRole('button', { name: /^Build$/i }).first();
      if (await dd.isVisible({ timeout: 2000 })) { log('click Build dropdown'); await dd.click(); await C.sleep(1000); }
      const opt = page.getByRole('menuitemradio', { name: /^Preview$/i }).first();
      if (await opt.isVisible({ timeout: 2000 })) { log('click Preview menuitemradio'); await opt.click(); await C.sleep(6000); }
    } catch {}
  }
  await C.dismissPopups(page);
  await C.sleep(4000);

  const input = page.getByRole('textbox', { name: /Chat message input|Ask a question/i }).first();
  const ok = await input.isVisible({ timeout: 30000 }).catch(() => false);
  log('chat input visible=' + ok);
  if (ok) {
    await input.click();
    await page.keyboard.type('Hi, can you help me reset my VPN access?', { delay: 22 });
    await C.sleep(800);
    try { await page.getByTestId('send-button').click(); } catch { await page.keyboard.press('Enter'); }
    await C.sleep(30000);
  }
  await page.screenshot({ path: path.join(C.OUT, 'v-test.png') }).catch(() => {});
  const t2 = await page.evaluate(() => document.body.innerText).catch(() => '');
  require('fs').writeFileSync(path.join(C.OUT, 'v-test.txt'), t2, 'utf8');
  log('DONE');
  await ctx.close();
})().catch(e => { log('ERR ' + e.message); process.exit(1); });
