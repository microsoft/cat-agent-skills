// dual-capture.js — run the recorder while ffmpeg gdigrab captures the whole desktop,
// so the assistant conversation AND the automated browser are both in-frame, in sync.
//
// Usage: node dual-capture.js [outfile.mp4]
// Arrange windows first with arrange.ps1 (browser left half, Scout right half).
const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const OUT = __dirname;
const OUTFILE = path.resolve(process.argv[2] || path.join(OUT, 'dual.mp4'));
const LOG = path.join(OUT, 'dual.log');
const log = m => fs.appendFileSync(LOG, `[${new Date().toISOString()}] ${m}\n`);

const LEAD_IN_MS = 3000;   // a beat of context before the run starts
const LEAD_OUT_MS = 3000;  // let the last answer breathe before cutting

(async () => {
  fs.writeFileSync(LOG, '');
  try {
    execSync(`powershell -NoProfile -ExecutionPolicy Bypass -File "${path.join(OUT, 'arrange.ps1')}"`,
      { encoding: 'utf8', timeout: 60000 });
    log('windows arranged');
  } catch (e) { log('arrange skipped: ' + e.message); }

  // Capture the whole desktop: per-window gdigrab drops frames when occluded or redrawn.
  const ff = spawn('ffmpeg', [
    '-y', '-f', 'gdigrab', '-framerate', '15', '-i', 'desktop',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '23', '-preset', 'veryfast',
    OUTFILE,
  ], { stdio: ['pipe', 'ignore', 'pipe'] });
  ff.stderr.on('data', d => {
    const s = d.toString();
    if (/error|Error|Invalid/.test(s)) log('ffmpeg: ' + s.trim().slice(0, 200));
  });
  log('ffmpeg started pid=' + ff.pid + ' -> ' + OUTFILE);

  await new Promise(r => setTimeout(r, LEAD_IN_MS));

  let code = 0;
  try {
    log('running recorder');
    execSync(`node "${path.join(OUT, 'recorder.js')}"`, {
      encoding: 'utf8', stdio: 'inherit', timeout: 40 * 60 * 1000,
      env: { ...process.env, NODE_PATH: process.env.NODE_PATH || execSync('npm root -g', { encoding: 'utf8' }).trim() },
    });
    log('recorder finished');
  } catch (e) { code = 1; log('recorder ERR ' + e.message); }

  await new Promise(r => setTimeout(r, LEAD_OUT_MS));

  // Ask ffmpeg to stop so it writes the moov atom; killing it yields an unplayable file.
  log('stopping ffmpeg (q)');
  try { ff.stdin.write('q'); ff.stdin.end(); } catch {}
  await new Promise(res => {
    const t = setTimeout(() => { try { process.kill(ff.pid); } catch {} res(); }, 20000);
    ff.on('close', c => { clearTimeout(t); log('ffmpeg exited ' + c); res(); });
  });

  try {
    const probe = execSync(
      `ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${OUTFILE}"`,
      { encoding: 'utf8' }).trim();
    log('duration=' + probe + 's size=' + fs.statSync(OUTFILE).size);
  } catch (e) {
    log('probe failed (missing moov?) — remux: ffmpeg -i broken.mp4 -c copy fixed.mp4');
  }
  log('DONE');
  process.exit(code);
})();
