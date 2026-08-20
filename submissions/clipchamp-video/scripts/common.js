// common.js — shared launch/auth/UI helpers for a Copilot Studio agent demo recording.
// EDIT THE CONSTANTS BELOW before running: UD/OUT can stay as-is (they're derived from
// the current user profile), but ENV and AGENT_ID must point at YOUR agent, and the
// account-tile match inside settle() below must match YOUR sign-in tenant/email.
const fs = require('fs');
const path = require('path');
const os = require('os');

const UD = path.join(os.homedir(), '.copilot', 'video-work', 'edge-tenant');
const EXE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const OUT = path.join(os.homedir(), '.copilot', 'video-work', 'agent-demo');
const ENV = 'REPLACE_WITH_YOUR_ENVIRONMENT_ID';   // e.g. Default-XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
const AGENT_ID = 'REPLACE_WITH_YOUR_AGENT_ID';    // the GUID from the agent's Copilot Studio URL
// Current Copilot Studio experience uses /agents/<id>; /agents/designer/<id> renders blank.
const AGENT_URL = `https://copilotstudio.microsoft.com/environments/${ENV}/agents/${AGENT_ID}`;
const AGENT_URL_LEGACY = `https://copilotstudio.microsoft.com/environments/${ENV}/agents/designer/${AGENT_ID}`;

// Physical screen working area is 1536x976. Chrome ignores --window-size on this
// profile, so the window is maximized via Win32 after launch (maximize.ps1).
// dsf 0.8 turns the 1536px-wide window into a 1920 CSS px capture buffer.
// Measured: at dsf 0.8 the maximized window yields 2376 CSS px wide. CSS width scales
// as 1/dsf, so 0.8 * (2376/1920) = 0.99 lands on a ~1920 CSS px capture buffer.
const DSF = 0.99;
const ARGS = [
  '--profile-directory=Profile 1',
  '--test-type', '--disable-infobars',
  '--hide-crash-restore-bubble', '--disable-session-crashed-bubble',
  '--no-first-run', '--no-default-browser-check',
  '--disable-features=msEdgeSplitScreen,msUndersideButton,EdgeDiscoverEntrypoint',
  `--force-device-scale-factor=${DSF}`,
  '--start-maximized',
];

const sleep = ms => new Promise(r => setTimeout(r, ms));

// Chrome silently ignores --window-size/--start-maximized on profiles carrying saved
// bounds; drive the real Win32 window instead.
function maximizeWindow(log) {
  try {
    const out = require('child_process').execSync(
      `powershell -NoProfile -ExecutionPolicy Bypass -File "${path.join(__dirname, 'maximize.ps1')}"`,
      { encoding: 'utf8', timeout: 60000 });
    if (log) log('maximize: ' + out.trim());
  } catch (e) { if (log) log('maximize ERR ' + e.message); }
}

function mkLog(file) {
  fs.mkdirSync(OUT, { recursive: true });
  const p = path.join(OUT, file);
  fs.writeFileSync(p, '');
  return m => fs.appendFileSync(p, `[${new Date().toISOString()}] ${m}\n`);
}

async function dismissPopups(page) {
  for (const n of ['Close', 'Got it', 'Dismiss', 'No thanks', 'Skip', 'Not now', 'Accept', 'OK', 'Maybe later']) {
    try {
      const b = page.getByRole('button', { name: new RegExp(`^${n}$`, 'i') }).first();
      if (await b.isVisible({ timeout: 400 })) { await b.click({ timeout: 1500 }); await sleep(300); }
    } catch {}
  }
  try { await page.keyboard.press('Escape'); } catch {}
}

// Poll until the app host is stable for N consecutive polls; click through MSAL on the way.
// Match on HOST, not url.includes(): authorize URLs embed the app host in redirect_uri.
async function settle(page, log, budgetMs = 240000, needStable = 4) {
  const host = u => { try { return new URL(u).host.toLowerCase(); } catch { return ''; } };
  const t0 = Date.now(); let stable = 0;
  while (Date.now() - t0 < budgetMs) {
    const h = host(page.url());
    if (h.endsWith('login.microsoftonline.com') || h.endsWith('login.microsoft.com') || h.endsWith('login.live.com')) {
      stable = 0;
      // Replace 'youraccount@yourtenant' with the email/tenant you sign in with.
      try { const tile = page.locator('div[data-test-id="youraccount@yourtenant.onmicrosoft.com"], div[role="button"]:has-text("youraccount@yourtenant"), small:has-text("youraccount@yourtenant")').first();
        if (await tile.isVisible({ timeout: 700 })) { log('auth: tenant account tile'); await tile.click({ timeout: 3000 }); await sleep(4500); continue; } } catch {}
      try { const cb = page.locator('#KmsiCheckboxField').first();
        if (await cb.isVisible({ timeout: 400 })) await cb.check({ timeout: 2000 }).catch(() => {}); } catch {}
      try { const yes = page.locator('#idSIButton9').first();
        if (await yes.isVisible({ timeout: 800 })) { log('auth: #idSIButton9'); await yes.click({ timeout: 3000 }); await sleep(4000); continue; } } catch {}
      await sleep(2000); continue;
    }
    if (h.endsWith('copilotstudio.microsoft.com')) {
      const len = await page.evaluate(() => document.body.innerText.length).catch(() => 0);
      const busy = await page.locator('text=/Initializing|Loading your|Getting things ready/i').count().catch(() => 0);
      if (len > 400 && !busy) { stable++; if (stable >= needStable) { log(`settled len=${len}`); return true; } }
      else stable = 0;
    } else stable = 0;
    await sleep(2000);
  }
  log('SETTLE TIMEOUT ' + page.url());
  return false;
}

async function logViewport(page, log) {
  const v = await page.evaluate(() => ({
    css: `${innerWidth}x${innerHeight}`, dpr: devicePixelRatio,
    screen: `${screen.width}x${screen.height}`, avail: `${screen.availWidth}x${screen.availHeight}`,
    outer: `${outerWidth}x${outerHeight}`,
  }));
  log('VIEWPORT ' + JSON.stringify(v));
  return v;
}

module.exports = { UD, EXE, OUT, ENV, AGENT_ID, AGENT_URL, AGENT_URL_LEGACY, ARGS, DSF, sleep, mkLog, dismissPopups, settle, logViewport, maximizeWindow };
