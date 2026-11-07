import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test, type TestContext } from "node:test";
import { fileURLToPath } from "node:url";

const submissions = fileURLToPath(new URL("../../submissions/", import.meta.url));
const store = join(submissions, "store-associate-assist");
const policyLibrary = join(store, "policy-retrieve", "config", "policy-library.json");

function temporaryDirectory(t: TestContext) {
  const directory = mkdtempSync(join(tmpdir(), "cat-industry-"));
  t.after(() => rmSync(directory, { recursive: true, force: true }));
  return directory;
}

function writeJson(directory: string, name: string, value: unknown) {
  const path = join(directory, name);
  writeFileSync(path, JSON.stringify(value));
  return path;
}

function runPython(script: string, args: string[], expectedStatus = 0) {
  const python = process.platform === "win32" ? "python" : "python3";
  const result = spawnSync(python, [script, ...args], { encoding: "utf8", timeout: 10_000 });
  assert.equal(result.status, expectedStatus, result.error?.message ?? result.stderr);
  return result;
}

// policy_resolve reads receipt, stock and purchase date only from question.facts (written by question-intake).
const unclearFacts = {
  receipt: "unclear", stock_at_this_store: "unclear", purchase_date: null, evidence: {},
};
const returnContext = {
  question: {
    facts: {
      receipt: "in_hand", stock_at_this_store: "unclear", purchase_date: "2026-06-01",
      evidence: { receipt: "I have the receipt", purchase_date: "bought on 1 June" },
    },
  },
};
const raincheckContext = {
  question: {
    sku: "SKU-100",
    facts: {
      receipt: "unclear", stock_at_this_store: "out_of_stock", purchase_date: null,
      evidence: { stock: "shelf is empty" },
    },
  },
  store_context: { cluster: "metro" },
  promos: [{
    promo_id: "P-1", name: "Summer promo", skus: ["SKU-100"], clusters: ["metro"],
    start: "2026-06-01", end: "2026-06-30", citation: "promo pack P-1",
  }],
};

type Context = {
  question?: Record<string, unknown>;
  store_context?: Record<string, unknown>;
  promos?: unknown[];
};

for (const [question, clause, determination, context] of [
  ["Can we price match a listed brick-and-mortar competitor?", "PM-1.2", "eligible_if_listed_competitor", {}],
  ["Can we price-match a listed competitor's own website?", "PM-1.2", "eligible_if_listed_competitor", {}],
  ["Can we price match a marketplace seller?", "PM-1.4", "excluded", {}],
  ["Can we price-match an Amazon Marketplace item?", "PM-1.4", "excluded", {}],
  ["Can we price match a third-party seller?", "PM-1.4", "excluded", {}],
  ["Can we price match a third party seller?", "PM-1.4", "excluded", {}],
  ["Can we price match an eBay listing?", "PM-1.4", "excluded", {}],
  ["Can I get a refund on this jacket?", "RET-2.1", "eligible_within_window", returnContext],
  ["Can I get a raincheck for an out of stock promo?", "PRC-3.3", "offer_raincheck", raincheckContext],
  ["How do I renew my passport?", null, "out_of_scope", {}],
] as const satisfies readonly (readonly [string, string | null, string, Context])[]) {
  test(`store policy resolves: ${question}`, (t) => {
    const directory = temporaryDirectory(t);
    const { question: extra = {}, store_context, promos: promoList = [] } = context as Context;
    const input = writeJson(directory, "question.json", {
      contract_version: "rtl.store-associate-assist.v1",
      question: { text: question, asked_on: "2026-06-15", facts: unclearFacts, ...extra },
      ...(store_context ? { store_context } : {}),
    });
    const promos = writeJson(directory, "promos.json", promoList);
    const output = join(directory, "resolved.json");
    runPython(join(store, "policy-retrieve", "scripts", "policy_resolve.py"), [
      "--question", input, "--policies", policyLibrary, "--promos", promos, "--out", output,
    ]);
    const result = JSON.parse(readFileSync(output, "utf8"));
    assert.equal(result.policy_resolution.applicable_clause, clause);
    assert.equal(result.policy_resolution.determination, determination);
    assert.equal(result.policy_resolution.in_scope, clause !== null);
    assert.equal(result.policy_resolution.source, "engine:policy_resolve");
    assert.equal(result.policy_resolution.confidence, clause === null ? 0 : 0.9);
    if (clause) assert.equal(result.policy_resolution.citation, `policy clause ${clause}`);
    else assert.match(result.escalations[0], /no improvised policy/);
  });
}

test("every store policy mirror has the same specific seller exclusions", () => {
  const expected = JSON.parse(readFileSync(policyLibrary, "utf8"));
  assert.deepEqual(expected["price_match.marketplace_excluded"].topics, [
    "marketplace", "third-party", "third party", "amazon", "ebay",
  ]);
  for (const skill of ["answer-draft", "policy-retrieve", "product-compare", "promo-check", "question-intake"]) {
    const path = join(store, skill, "config", "policy-library.json");
    assert.deepEqual(JSON.parse(readFileSync(path, "utf8")), expected, path);
  }
});

