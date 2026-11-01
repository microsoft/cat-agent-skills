import assert from "node:assert/strict";
import { test } from "node:test";
import { GalleryHistory } from "../src/lib/gallery-history";

class TestHistory {
  entries: { url: string; state: Record<string, unknown> | null }[] = [{ url: "/", state: null }];
  index = 0;
  get state() { return this.entries[this.index].state; }
  replaceState(state: Record<string, unknown> | null, _unused: string, url?: string) {
    this.entries[this.index] = { url: url ?? this.entries[this.index].url, state: structuredClone(state) };
  }
  pushState(state: Record<string, unknown> | null, _unused: string, url?: string) {
    this.entries.splice(++this.index, Infinity, { url: url ?? this.entries[this.index - 1].url, state: structuredClone(state) });
  }
  push(url: string) {
    this.pushState(null, "", url);
  }
  go(delta: number) { this.index += delta; }
}

function setup() {
  const history = new TestHistory();
  const stored = new Map<string, string>();
  const storage = {
    getItem: (key: string) => stored.get(key) ?? null,
    setItem: (key: string, value: string) => { stored.set(key, value); },
  };
  const positions = new GalleryHistory(history, () => storage);
  return { history, positions, storage, stored };
}

test("Back and Forward capture the departure without overwriting the destination", () => {
  const { history, positions } = setup();
  positions.save({ shown: 24, y: 0 });
  history.push("/?platform=Cowork");
  positions.activate();

  history.go(-1);
  positions.capture({ shown: 56, y: 1800 });
  assert.deepEqual(history.state?.gallery, { shown: 24, y: 0 });
  positions.activate();
  assert.deepEqual(positions.read(), { shown: 24, y: 0 });

  history.go(1);
  positions.capture({ shown: 48, y: 900 });
  positions.activate();
  assert.deepEqual(positions.read(), { shown: 56, y: 1800 });
  history.go(-1);
  positions.capture({ shown: 56, y: 2000 });
  positions.activate();
  assert.deepEqual(positions.read(), { shown: 48, y: 900 });
  history.go(1);
  positions.activate();
  assert.deepEqual(positions.read(), { shown: 56, y: 2000 });
});

test("distinct history entries sharing a URL keep independent batch and scroll positions", () => {
  const { history, positions } = setup();
  const expected = [{ shown: 36, y: 600 }, { shown: 45, y: 1200 }, { shown: 56, y: 1800 }];
  for (const [index, url] of ["/?platform=Cowork", "/?platform=Scout", "/?platform=Cowork"].entries()) {
    history.push(url);
    positions.activate();
    positions.save(expected[index]);
  }
  assert.notEqual(history.entries[1].state?.galleryEntryId, history.entries[3].state?.galleryEntryId);
  for (const index of [2, 1, 2, 3]) {
    history.index = index;
    positions.activate();
    assert.deepEqual(positions.read(), expected[index - 1]);
  }
});

test("entry-keyed storage preserves the latest departing position across a document reload", () => {
  const { history, positions, storage } = setup();
  positions.save({ shown: 24, y: 0 });
  history.push("/?platform=Cowork");
  positions.activate();
  positions.save({ shown: 24, y: 0 });
  history.go(-1);
  positions.capture({ shown: 56, y: 1800 });
  positions.activate();
  const reloaded = new GalleryHistory(history, () => storage);
  assert.deepEqual(reloaded.read(), { shown: 24, y: 0 });
  history.go(1);
  reloaded.activate();
  assert.deepEqual(reloaded.read(), { shown: 56, y: 1800 });
});

test("a departure save after native traversal cannot write outgoing data into destination state", () => {
  const { history, positions } = setup();
  positions.save({ shown: 36, y: 500 });
  history.push("/?platform=Cowork");
  positions.activate();
  history.go(-1);
  const destination = structuredClone(history.state);
  positions.save({ shown: 56, y: 1800 });
  assert.deepEqual(history.state, destination);
  positions.activate();
  assert.deepEqual(positions.read(), { shown: 36, y: 500 });
  history.go(1);
  positions.activate();
  assert.deepEqual(positions.read(), { shown: 56, y: 1800 });
});

test("search replacement preserves entry identity and foreign state while updating its position", () => {
  const { history, positions, storage, stored } = setup();
  history.replaceState({ ...history.state, marker: { preserve: true } }, "");
  const id = history.state?.galleryEntryId;
  positions.save({ shown: 56, y: 1800 });
  positions.updateUrl("/?q=report", true);
  assert.equal(history.entries.length, 1);
  assert.equal(history.entries[0].url, "/?q=report");
  assert.equal(history.state?.galleryEntryId, id);
  assert.deepEqual(history.state?.marker, { preserve: true });

  // A committed replacement saves the refiltered position, not its pre-search snapshot.
  positions.save({ shown: 12, y: 0 });
  assert.deepEqual(positions.read(), { shown: 12, y: 0 });
  assert.deepEqual(history.state?.gallery, { shown: 12, y: 0 });
  assert.equal(stored.size, 1);
  assert.deepEqual(new GalleryHistory(history, () => storage).read(), { shown: 12, y: 0 });
});

test("pushed filters get a fresh entry without inheriting the replaced entry's state", () => {
  const { history, positions } = setup();
  history.replaceState({ ...history.state, marker: "preserve" }, "");
  positions.save({ shown: 24, y: 0 });
  positions.updateUrl("/?q=skill", true);
  const id = history.state?.galleryEntryId;
  positions.updateUrl("/?q=skill&platform=Cowork", false);
  assert.equal(history.entries.length, 2);
  assert.notEqual(history.state?.galleryEntryId, id);
  assert.equal(history.state?.marker, undefined);
  assert.equal(positions.read(), undefined);
  positions.save({ shown: 36, y: 500 });

  history.go(-1);
  positions.activate();
  assert.equal(history.state?.galleryEntryId, id);
  assert.equal(history.state?.marker, "preserve");
  assert.equal(history.entries[history.index].url, "/?q=skill");
  assert.deepEqual(positions.read(), { shown: 24, y: 0 });
  history.go(1);
  positions.activate();
  assert.deepEqual(positions.read(), { shown: 36, y: 500 });
});

test("repeated search replacements keep the latest query and position through reload and traversal", () => {
  const { history, positions, storage } = setup();
  positions.save({ shown: 48, y: 900 });
  positions.updateUrl("/?platform=Cowork", false);
  const id = history.state?.galleryEntryId;
  for (const query of ["s", "skill", "reports"]) {
    positions.updateUrl(`/?platform=Cowork&q=${query}`, true);
    positions.save({ shown: 12, y: 0 });
    assert.equal(history.state?.galleryEntryId, id);
    assert.equal(history.entries.length, 2);
  }
  positions.save({ shown: 24, y: 300 });
  const reloaded = new GalleryHistory(history, () => storage);
  assert.deepEqual(reloaded.read(), { shown: 24, y: 300 });
  history.go(-1);
  reloaded.activate();
  assert.deepEqual(reloaded.read(), { shown: 48, y: 900 });
  history.go(1);
  reloaded.activate();
  assert.equal(history.entries[history.index].url, "/?platform=Cowork&q=reports");
  assert.equal(history.state?.galleryEntryId, id);
  assert.deepEqual(reloaded.read(), { shown: 24, y: 300 });
});

test("legacy history position survives assigning an entry ID", () => {
  const history = new TestHistory();
  history.replaceState({ gallery: { shown: 48, y: 1000 }, marker: "preserve" }, "");
  const positions = new GalleryHistory(history, () => ({ getItem: () => null, setItem: () => {} }));
  assert.deepEqual(positions.read(), { shown: 48, y: 1000 });
  assert.equal(history.state?.marker, "preserve");
  assert.equal(typeof history.state?.galleryEntryId, "string");
});

test("blocked storage reports errors but retains in-memory and history-state restoration", (t) => {
  const warn = t.mock.method(console, "warn", () => {});
  const history = new TestHistory();
  const positions = new GalleryHistory(history, () => { throw new Error("Storage disabled"); });
  positions.save({ shown: 48, y: 1000 });
  assert.deepEqual(positions.read(), { shown: 48, y: 1000 });
  const reloaded = new GalleryHistory(history, () => { throw new Error("Storage disabled"); });
  assert.deepEqual(reloaded.read(), { shown: 48, y: 1000 });
  assert.equal(warn.mock.callCount(), 2);
});

test("invalid stored positions are reported rather than restored", (t) => {
  const warn = t.mock.method(console, "warn", () => {});
  const { history, positions, stored } = setup();
  stored.set(`gallery-scroll:${history.state?.galleryEntryId}`, '{"shown":"many","y":10}');
  assert.equal(positions.read(), undefined);
  assert.equal(warn.mock.callCount(), 1);
});
