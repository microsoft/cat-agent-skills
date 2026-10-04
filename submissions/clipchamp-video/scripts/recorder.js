// recorder.js — records a Copilot Studio agent demo: overview/instructions/skills/tools
// + a handful of live test turns. Edit PROMPTS/MAXES/HOLDS below for your own scenario.
const { chromium } = require('./require-playwright');
const fs = require('fs');
const path = require('path');
const C = require('./common');

const log = C.mkLog('progress.log');
const OUTDIR = path.join(C.OUT, 'video');

const PROMPTS = [
  "Hi, I can't connect to the company VPN from home. Is there a knowledge article that can help me fix this?",
  "It still fails with a timeout and this is blocking my work. Can you escalate to a human and book an appointment with the IT support team?",
  "I also need a Microsoft Project license for my new role. Please create a request ticket for that.",
];
const MAXES = [110000, 150000, 150000];
const HOLDS = [5000, 5500, 6000];

async function typeHuman(page, box, text) {
  await box.click();
  for (const ch of text) { await page.keyboard.type(ch); await C.sleep(12 + Math.random() * 30); }
}

async function scrollBottom(page) {
  await page.evaluate(() => {
    const els = [...document.querySelectorAll('*')].filter(e => e.scrollHeight > e.clientHeight + 60);
    els.forEach(e => { e.scrollTop = e.scrollHeight; });
    window.scrollTo(0, document.body.scrollHeight);
  }).catch(() => {});
}

// A finished assistant turn adds a feedback ("Dislike") button.
async function waitForTurn(page, prev, maxMs) {
  const t0 = Date.now();
  while (Date.now() - t0 < maxMs) {
    let c = 0;
    try { c = await page.getByRole('button', { name: /Dislike/i }).count(); } catch {}
    if (c > prev) { await C.sleep(1500); return c; }
    await C.sleep(700);
  }
  try { return await page.getByRole('button', { name: /Dislike/i }).count(); } catch { return prev; }
}

// Copilot Studio's Build/Preview/Evaluate/Monitor switcher is a menuitemradio DROPDOWN
// behind one "Build" button, not tabs — a tab-role locator finds nothing and this used
// to time out waiting for the chat input. Navigating straight to <agentUrl>/preview is
// far more reliable than any menu-click choreography.
async function openTestPane(page) {
  log('goto preview url');
  await page.goto(C.AGENT_URL + '/preview', { waitUntil: 'domcontentloaded', timeout: 60000 }).catch(() => {});
  await C.sleep(5000);
  // Fallback for apps where /preview isn't a valid route: try tab, then dropdown+menuitemradio.
  const input = page.getByRole('textbox', { name: /Chat message input|Ask a question|Type your message/i }).first();
  if (await input.isVisible({ timeout: 3000 }).catch(() => false)) return;
  for (const n of ['Test', 'Preview']) {
    try {
      const t = page.getByRole('tab', { name: new RegExp(`^${n}$`, 'i') }).first();
      if (await t.isVisible({ timeout: 2500 })) { log('tab ' + n); await t.click(); await C.sleep(6000); return; }
    } catch {}
  }
  try {
    const dd = page.getByRole('button', { name: /^Build$/i }).first();
    if (await dd.isVisible({ timeout: 2500 })) { log('dropdown Build'); await dd.click(); await C.sleep(1000); }
    const opt = page.getByRole('menuitemradio', { name: /^Preview$/i }).first();
    if (await opt.isVisible({ timeout: 2500 })) { log('menuitemradio Preview'); await opt.click(); await C.sleep(6000); }
  } catch {}
}

(async () => {
  fs.rmSync(OUTDIR, { recursive: true, force: true });
  fs.mkdirSync(OUTDIR, { recursive: true });

  const ctx = await chromium.launchPersistentContext(C.UD, {
    executablePath: C.EXE, headless: false, args: C.ARGS, viewport: null,
    recordVideo: { dir: OUTDIR, size: { width: 1920, height: 1160 } },
  });
  const page = ctx.pages()[0] || await ctx.newPage();
  await C.sleep(1500);
  C.maximizeWindow(log);

  log('goto agent');
  await page.goto(C.AGENT_URL, { waitUntil: 'domcontentloaded', timeout: 180000 });
  await C.settle(page, log, 240000, 3);
  C.maximizeWindow(log);
  await C.dismissPopups(page);
  await C.sleep(6000);
  log('BEAT overview');
  await C.logViewport(page, log);

  // --- Beat 1: overview + instructions ---
  await C.sleep(6000);
  log('BEAT instructions-scroll');
  try {
    const instr = page.getByRole('textbox', { name: /Agent instructions|Instructions/i }).first();
    if (await instr.isVisible({ timeout: 4000 })) await instr.hover();
  } catch {}
  for (let i = 0; i < 5; i++) { await page.mouse.wheel(0, 200); await C.sleep(1500); }
  await C.sleep(2500);

  // --- Beat 2: skills / tools / knowledge ---
  log('BEAT tools');
  for (let i = 0; i < 5; i++) { await page.mouse.wheel(0, 240); await C.sleep(1600); }
  await C.sleep(3000);
  await page.mouse.wheel(0, -1600); await C.sleep(2500);

  // --- Beat 3-5: the three live tests ---
  log('BEAT open-test');
  await openTestPane(page);
  await C.dismissPopups(page);
  const input = page.getByRole('textbox', { name: /Chat message input|Ask a question|Type your message/i }).first();
  await input.waitFor({ state: 'visible', timeout: 90000 });
  await C.sleep(5000);

  for (let i = 0; i < PROMPTS.length; i++) {
    log(`BEAT test${i + 1}-start`);
    let prev = 0;
    try { prev = await page.getByRole('button', { name: /Dislike/i }).count(); } catch {}
    await typeHuman(page, input, PROMPTS[i]);
    await C.sleep(600);
    try { await page.getByTestId('send-button').click(); }
    catch { try { await page.getByRole('button', { name: /^Send/i }).first().click(); } catch { await page.keyboard.press('Enter'); } }
    log(`BEAT test${i + 1}-sent`);
    await C.sleep(1500);
    await waitForTurn(page, prev, MAXES[i]);
    await scrollBottom(page);
    log(`BEAT test${i + 1}-answered`);
    await C.sleep(HOLDS[i]);
    await scrollBottom(page);
  }

  log('BEAT end');
  await C.sleep(4000);
  await ctx.close();

  const files = fs.readdirSync(OUTDIR).filter(f => f.endsWith('.webm'));
  log('VIDEO ' + JSON.stringify(files));
})().catch(e => { log('ERR ' + e.message + '\n' + (e.stack || '')); process.exit(1); });
