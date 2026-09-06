// require-playwright.js — resolve a GLOBALLY installed Playwright even when NODE_PATH
// isn't set in the current shell. `npm install -g playwright` alone does NOT make
// `require('playwright')` work from an arbitrary working directory unless NODE_PATH
// points at the global node_modules root — this shim finds that root and requires
// straight from it so every script in this folder "just works" without the caller
// having to remember an env var.
const path = require('path');
const { execSync } = require('child_process');

function loadPlaywright() {
  // 1) Already resolvable (NODE_PATH set, or playwright installed locally) — use it.
  try { return require('playwright'); } catch {}

  // 2) Fall back to the global npm root and require the package straight from there.
  const globalRoot = execSync('npm root -g', { encoding: 'utf8' }).trim();
  return require(path.join(globalRoot, 'playwright'));
}

module.exports = loadPlaywright();

