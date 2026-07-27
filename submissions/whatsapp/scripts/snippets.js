// snippets.js
//
// REFERENCE PATTERNS, NOT A RUNNABLE SCRIPT.
// Scout drives the browser through a Playwright-based MCP tool, not a standalone
// Node process, so there is no `page` object handed to this file to execute.
// Use these as the shape of each interaction (selectors, order, waits, fallbacks)
// when issuing browser-tool actions. Keep the selectors in sync with
// references/selectors.md - WhatsApp Web changes its DOM often, so treat every
// selector as best-effort and verify it live before relying on a run.

// Normalise a name for comparison: trim, collapse spaces, lowercase.
function norm(s) {
  return (s || '').replace(/\s+/g, ' ').trim().toLowerCase();
}

// A chat/contact row's real NAME lives in a title attribute (span[title]), not
// in the row's full innerText - which also contains the last-message preview and
// timestamp. Matching innerText lets an incoming message preview hijack the
// target, so always match the title. Returns the row's title, or ''.
async function rowTitle(row) {
  // The name span is typically a dir="auto" titled span; prefer it over other
  // titled elements in the row (badge/pin/verified icons can also carry title).
  const titled =
    (await row.$('span[title][dir="auto"]')) || (await row.$('span[title]'));
  if (titled) {
    const t = await titled.getAttribute('title');
    if (t) return t;
  }
  return '';
}

// Wait for the app to be ready (logged in), not a fixed sleep. Returns true when
// the chat list is present. If it never appears, the profile is likely on the
// QR/login screen (set up login manually: QR or phone-pairing).
async function waitForReady(page, timeoutMs = 120000) {
  try {
    // Language-independent first (#pane-side / #side), then localized aria-labels.
    await page.waitForSelector(
      '#pane-side, #side, [aria-label="Chat list"], [aria-label="Liste des discussions"]',
      { timeout: timeoutMs }
    );
    return true;
  } catch {
    return false;
  }
}

// Return the chat list to a known state after a stuck step. Recover once, then
// let the caller fail explicitly if the retry still does not work.
async function recover(page) {
  const back =
    (await page.$('span[data-icon="back"]')) ||
    (await page.$('button[aria-label="Back"]')) ||
    (await page.$('button[aria-label="Retour"]'));
  if (back) {
    await back.click();
  } else {
    await page.keyboard.press('Escape');
  }
  await page.waitForTimeout(800);
  return waitForReady(page, 15000);
}

// Reset the chat-list view so a scan sees ALL chats, not a filtered subset.
// A leftover search term or an active filter tab (Unread / Favorites / Groups)
// hides chats, which is why a "what did I receive" check can wrongly come back
// empty. Clears the search box and selects the All / Toutes filter. Best-effort.
async function resetChatListView(page) {
  // 1. Clear the search box: prefer the cancel/clear control, else select-all+del.
  const cancel =
    (await page.$('[aria-label="Cancel search"]')) ||
    (await page.$('[aria-label="Annuler la recherche"]')) ||
    (await page.$('span[data-icon="x-alt"]')) ||
    (await page.$('button[aria-label*="lear" i]'));
  if (cancel) {
    await cancel.click();
  } else {
    const search = page
      .locator('div[contenteditable="true"][data-tab="3"], [aria-label*="Search"], [aria-label*="Recherch"]')
      .first();
    if ((await search.count()) && norm(await search.innerText().catch(() => '')) !== '') {
      await search.click();
      await page.keyboard.press('Control+A');
      await page.keyboard.press('Delete');
    } else {
      await page.keyboard.press('Escape');   // leave search mode if in it
    }
  }

  // 2. Select the "All" filter tab if some other filter is active.
  const allTab =
    (await page.$('[role="tab"]:has-text("All")')) ||
    (await page.$('[role="tab"]:has-text("Toutes")')) ||
    (await page.$('div[role="button"]:has-text("All")')) ||
    (await page.$('div[role="button"]:has-text("Toutes")'));
  if (allTab) {
    const selected = await allTab.getAttribute('aria-selected');
    if (selected !== 'true') await allTab.click();
  }

  // 3. Turn off a legacy "unread only" funnel filter if it is engaged.
  const unreadOn = await page.$('[aria-label*="unread" i][aria-pressed="true"], [aria-label*="non lus" i][aria-pressed="true"]');
  if (unreadOn) await unreadOn.click();

  await page.waitForTimeout(800);
}

// Click the "use here" dialog if WhatsApp Web is open elsewhere. Text is
// localized, so every supported language is listed.
async function handleUseHereDialog(page) {
  const candidates = [
    'button:has-text("Use here")',
    'button:has-text("Utiliser ici")',
    'button:has-text("Utiliser")'
  ];
  for (const selector of candidates) {
    const btn = await page.$(selector);
    if (btn) {
      await btn.click();
      await page.waitForTimeout(2000);
      return true;
    }
  }
  return false;
}

// Open a chat by NAME, matched on each row's title attribute (never the full row
// text). Requires an exact normalised title match so a partial name or a
// message preview cannot open the wrong chat. Returns true, or 'ambiguous' when
// more than one row shares the title, or false when none match.
async function openChat(page, chatName) {
  const want = norm(chatName);
  // Primary selector, both scoped to #pane-side; only fall back if it is empty.
  let rows = await page.$$('#pane-side div[role="listitem"]');
  if (rows.length === 0) rows = await page.$$('#pane-side div[role="row"]');
  const matches = [];
  for (const row of rows) {
    if (norm(await rowTitle(row)) === want) matches.push(row);
  }
  if (matches.length === 1) {
    await matches[0].click();
    await page.waitForTimeout(2000);
    return true;
  }
  if (matches.length > 1) return 'ambiguous';
  return false;
}

// Read the last `limit` messages, INCLUDING media/system messages that carry no
// `data-pre-plain-text` (calls, deleted, encryption notices) - label those by
// type rather than dropping them. `data-pre-plain-text` is locale-dependent, so
// both 24h and AM/PM time forms and both date orders are accepted; unparseable
// metadata is returned raw.
async function readMessages(page, limit = 20) {
  return await page.evaluate((max) => {
    // Candidate message rows in the open conversation, including media/system
    // rows that have no metadata. A text row and its inner [data-pre-plain-text]
    // span both match, so keep only OUTERMOST nodes to avoid double-counting.
    const candidates = [
      ...document.querySelectorAll(
        '#main [data-id], #main div.message-in, #main div.message-out, #main [data-pre-plain-text]'
      )
    ];
    const rows = candidates.filter(
      (el) => !candidates.some((other) => other !== el && other.contains(el))
    );
    const out = [];
    rows.forEach((row) => {
      const metaEl = row.matches('[data-pre-plain-text]')
        ? row
        : row.querySelector('[data-pre-plain-text]');
      const meta = metaEl ? metaEl.getAttribute('data-pre-plain-text') || '' : '';
      const text = (row.innerText || '').trim();
      if (!meta) {
        // No metadata: a media or system message. Keep it, labelled.
        out.push({ type: 'media-or-system', time: null, date: null, sender: null, text });
        return;
      }
      const m = meta.match(
        /\[(\d{1,2}:\d{2}(?:\s?[APap][Mm])?),\s*(\d{1,2}\/\d{1,2}\/\d{2,4})\]\s*(.+?):\s*$/
      );
      out.push({
        type: 'message',
        time: m ? m[1] : null,
        date: m ? m[2] : null,
        sender: m ? m[3].trim() : null,
        rawMeta: m ? null : meta,
        text
      });
    });
    return out.slice(-max);
  }, limit);
}

// Submit the current composer content and CONFIRM it left. `fill()` may not
// register on WhatsApp's rich editor, so fall back to typing; confirmation
// requires BOTH the composer clearing AND a new outgoing bubble carrying the
// text (composer-clear alone can happen on a reconnect with nothing sent).
async function submitAndConfirm(page, composer, message) {
  // Baseline count of outgoing bubbles BEFORE sending, so a NEW bubble is what
  // confirms the send - resending text identical to a previous message must not
  // match a pre-existing bubble. A 120-char fingerprint keeps the match specific.
  const needle = norm(message).slice(0, 120);
  const before = await page
    .$$eval('#main .message-out', (els) => els.length)
    .catch(() => 0);

  // True once ANY new outgoing bubble (beyond `before`) carries the fingerprint.
  // Matches any new bubble, not just the last, so a message the user sends from
  // their phone in-window does not hide our own confirmation.
  const waitForNewBubble = () =>
    page
      .waitForFunction(
        (args) => {
          const outs = [...document.querySelectorAll('#main .message-out')];
          return outs.slice(args.before).some((el) =>
            (el.innerText || '').replace(/\s+/g, ' ').trim().toLowerCase().includes(args.n)
          );
        },
        { n: needle, before },
        { timeout: 12000 }
      )
      .then(() => true)
      .catch(() => false);

  await page.keyboard.press('Enter');
  // Wait the FULL window for Enter's bubble BEFORE deciding Enter failed, so DOM
  // lag can never trigger a Send-button click on a message that already sent.
  let bubbleSeen = await waitForNewBubble();

  if (!bubbleSeen && norm(await composer.innerText()) !== '') {
    // No bubble in 12s and the text is still in the composer: Enter genuinely did
    // not submit. Click Send once, then confirm again. (Not a retry of a sent
    // message - there is provably no new bubble yet.)
    const sendBtn =
      (await page.$('span[data-icon="send"]')) ||
      (await page.$('button[aria-label="Send"]')) ||
      (await page.$('button[aria-label="Envoyer"]'));
    if (sendBtn) {
      await sendBtn.click();
      bubbleSeen = await waitForNewBubble();
    }
  }

  // Re-sample composer-empty now (it can clear late, like the bubble).
  const empty = norm(await composer.innerText()) === '';
  // NEVER resend beyond the single genuine-failure fallback above. An unconfirmed
  // result means "maybe sent"; the caller must not auto-retry (that double-posts).
  return bubbleSeen && empty ? { result: 'sent' } : { result: 'send-unconfirmed' };
}

// Fingerprint check: does an identical outgoing message already exist among the
// recent outgoing bubbles? Use before any manual resend so a message that DID
// go out (but was reported unconfirmed) is never sent twice.
async function outgoingExists(page, message) {
  const needle = norm(message).slice(0, 120);
  return page
    .$$eval(
      '#main .message-out',
      (els, n) =>
        els.slice(-10).some((el) =>
          (el.innerText || '').replace(/\s+/g, ' ').trim().toLowerCase().includes(n)
        ),
      needle
    )
    .catch(() => false);
}

// Clear the composer completely (select-all + delete), for the dry-run path so
// no draft is left in a real chat. Verifies it is actually empty.
async function clearComposer(page, composer) {
  await composer.click();
  await page.keyboard.press('Control+A');
  await page.keyboard.press('Delete');
  await page.waitForTimeout(200);
  return norm(await composer.innerText()) === '';
}

// Type a message. On dry_run, capture the preview and CLEAR the composer, then
// return the preview and whether the clear succeeded. Otherwise submit+confirm.
async function sendMessage(page, message, options = {}) {
  const dryRun = Boolean(options.dryRun);
  const composer = page
    .locator(
      'div[contenteditable="true"][data-tab="10"], footer div[contenteditable="true"], [aria-label="Type a message"], [aria-label="Tapez un message"]'
    )
    .first();
  await composer.click();
  await composer.fill(message);
  // fill() can no-op on WhatsApp's rich editor; if nothing registered, type it.
  if (norm(await composer.innerText()) === '') {
    await composer.pressSequentially(message, { delay: 10 });
  }
  if (dryRun) {
    await page.waitForTimeout(300);
    const preview = (await composer.innerText()) || message;
    const cleared = await clearComposer(page, composer);
    return { result: 'dry-run-preview', preview, cleared };
  }
  return submitAndConfirm(page, composer, message);
}

// Return the rows in the CHATS section of the search results only, each tagged
// with data-wa-idx so the caller can click it. WhatsApp search groups results
// into sections: Chats / Discussions (actual conversations), Contacts, and
// Messages (occurrences of the query INSIDE a chat - NOT separate chats). Only
// the Chats section is a real target; counting the Messages section is what
// makes one chat with several matching messages look like "3 different groups".
// Best-effort section detection - verify against the live DOM.
async function chatSectionResults(page) {
  return page.evaluate(() => {
    const pane = document.querySelector('#pane-side');
    if (!pane) return [];
    const nv = (s) => (s || '').replace(/\s+/g, ' ').trim().toLowerCase();
    const CHATS = new Set(['chats', 'discussions']);
    const OTHER = new Set(['contacts', 'messages']);
    let section = 'chats';   // results begin with the chats section
    let idx = 0;
    const out = [];
    for (const el of pane.querySelectorAll('*')) {
      const role = el.getAttribute && el.getAttribute('role');
      if (role === 'listitem' || role === 'row') {
        if (section === 'chats') {
          const titleEl =
            el.querySelector('span[title][dir="auto"]') || el.querySelector('span[title]');
          const title = titleEl ? titleEl.getAttribute('title') || '' : '';
          if (title) {
            el.setAttribute('data-wa-idx', String(idx));
            out.push({ idx, title });
            idx += 1;
          }
        }
        continue;
      }
      // A short exact section label with no children is a section header.
      const t = nv(el.textContent);
      if (t.length <= 12 && el.children.length === 0 && (CHATS.has(t) || OTHER.has(t))) {
        section = CHATS.has(t) ? 'chats' : 'other';
      }
    }
    return out;
  });
}

// Open the search box, type a query, and open a matching chat FROM THE CHATS
// SECTION ONLY. Returns true, 'ambiguous' (several distinct chats match),
// 'no-match' (chats exist but none is titled like the query), or 'no-results'.
async function searchAndOpenChat(page, query) {
  const searchBtn = await page.$('[data-icon="search"]');
  if (searchBtn) await searchBtn.click();
  const searchInput = page
    .locator(
      'div[contenteditable="true"][data-tab="3"], [aria-label*="Search"], [aria-label*="Recherch"]'
    )
    .first();
  await searchInput.click();
  await searchInput.fill(query);
  await page.waitForTimeout(1500);

  const want = norm(query);
  const rows = await chatSectionResults(page);   // chats section only
  const exact = rows.filter((r) => norm(r.title) === want);
  const partial = rows.filter((r) => norm(r.title) !== want && norm(r.title).includes(want));
  const pick = exact.length ? exact : partial;
  if (pick.length === 1) {
    await page.click(`[data-wa-idx="${pick[0].idx}"]`);
    await page.waitForTimeout(2000);
    return true;
  }
  if (pick.length > 1) return 'ambiguous';
  const noResults =
    (await page.$('span:has-text("No results found")')) ||
    (await page.$('span:has-text("Aucun résultat")'));
  return noResults || rows.length === 0 ? 'no-results' : 'no-match';
}

// Create a group. Selectors on the group dialog are the least stable in
// WhatsApp Web; verify each step live. Participants are matched by title inside
// the group dialog (scoped to #app, NOT #pane-side, which is the main chat list).
async function createGroup(page, groupName, participants, options = {}) {
  const dryRun = Boolean(options.dryRun);

  const newChat =
    (await page.$('[data-icon="new-chat-outline"]')) ||
    (await page.$('span[data-icon="chat"]')) ||
    (await page.$('[aria-label="New chat"]')) ||
    (await page.$('[aria-label="Nouvelle discussion"]'));
  if (!newChat) throw new Error('New chat button not found.');
  await newChat.click();
  await page.waitForTimeout(600);

  const newGroup =
    (await page.$('div[role="button"]:has-text("New group")')) ||
    (await page.$('div[role="button"]:has-text("Nouveau groupe")'));
  if (!newGroup) throw new Error('New group entry not found.');
  await newGroup.click();
  await page.waitForTimeout(1000);

  for (const participant of participants) {
    const want = norm(participant);
    const input = page
      .locator('div[contenteditable="true"], [aria-label*="Search"], [aria-label*="Recherch"]')
      .first();
    await input.click();
    await input.fill(participant);
    await page.waitForTimeout(1200);
    // Results live in the group dialog, NOT #pane-side (the main chat list stays
    // visible behind it). Skip any row inside #pane-side and match by title.
    const rows = await page.$$('div[role="listitem"]');
    let picked = null;
    for (const row of rows) {
      const inMainList = await row.evaluate((el) => !!el.closest('#pane-side'));
      if (inMainList) continue;
      if (norm(await rowTitle(row)) === want) { picked = row; break; }
    }
    if (!picked) {
      // Surface the miss so the caller can ask the user for a phone number.
      throw new Error(`No exact participant match for: ${participant}`);
    }
    await picked.click();
    await page.waitForTimeout(400);
  }

  const next =
    (await page.$('span[data-icon="arrow-forward"]')) ||
    (await page.$('[aria-label*="Next" i]')) ||
    (await page.$('[aria-label*="Suivant" i]'));
  if (!next) throw new Error('Next button not found while creating group.');
  await next.click();
  await page.waitForTimeout(800);

  const nameInput = page
    .locator('div[contenteditable="true"], [aria-label*="group subject" i], [aria-label*="objet du groupe" i]')
    .first();
  await nameInput.click();
  await nameInput.fill(groupName);
  await page.waitForTimeout(400);

  const create =
    (await page.$('span[data-icon="checkmark-medium"]')) ||
    (await page.$('span[data-icon="checkmark"]')) ||
    (await page.$('[aria-label*="Create" i]')) ||
    (await page.$('[aria-label*="Créer" i]'));
  if (!create) throw new Error('Create group button not found.');
  if (!dryRun) {
    await create.click();
  }
  await page.waitForTimeout(1500);
  return dryRun
    ? { result: 'dry-run-preview', name: groupName, participants }
    : { result: 'group-created', name: groupName };
}

module.exports = {
  norm,
  rowTitle,
  waitForReady,
  recover,
  resetChatListView,
  handleUseHereDialog,
  openChat,
  readMessages,
  submitAndConfirm,
  outgoingExists,
  clearComposer,
  sendMessage,
  chatSectionResults,
  searchAndOpenChat,
  createGroup
};
