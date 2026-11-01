import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test, type TestContext } from "node:test";
import { fileURLToPath } from "node:url";

const submissions = fileURLToPath(new URL("../../submissions/", import.meta.url));
const store = join(submissions, "store-associate-assist", "skills");
const trade = join(submissions, "trade-promotion-deduction-recovery", "skills");
const policyLibrary = join(store, "policy-retrieve", "policy-library.json");
const classifier = join(trade, "validity-classify", "scripts", "deduction_classify.py");
const scoping = join(trade, "validity-classify", "config", "rgm-scoping.json");

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

for (const [question, clause, determination] of [
  ["Can we price match a listed brick-and-mortar competitor?", "PM-1.2", "eligible_if_listed_competitor"],
  ["Can we price-match a listed competitor's own website?", "PM-1.2", "eligible_if_listed_competitor"],
  ["Can we price match a marketplace seller?", "PM-1.4", "excluded"],
  ["Can we price-match an Amazon Marketplace item?", "PM-1.4", "excluded"],
  ["Can we price match a third-party seller?", "PM-1.4", "excluded"],
  ["Can we price match a third party seller?", "PM-1.4", "excluded"],
  ["Can we price match an eBay listing?", "PM-1.4", "excluded"],
  ["What is the refund policy?", "RET-2.1", "eligible_within_window"],
  ["Can I get a raincheck for an out of stock promo?", "PRC-3.3", "offer_raincheck"],
  ["How do I renew my passport?", null, "out_of_scope"],
] as const) {
  test(`store policy resolves: ${question}`, (t) => {
    const directory = temporaryDirectory(t);
    const input = writeJson(directory, "question.json", {
      contract_version: "rtl.store-associate-assist.v1",
      question: { text: question, asked_on: "2026-06-15" },
    });
    const promos = writeJson(directory, "promos.json", []);
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
    "marketplace", "third-party", "third party", "ebay",
  ]);
  for (const skill of ["answer-draft", "policy-retrieve", "product-compare", "promo-check", "question-intake"]) {
    for (const directory of ["", "config"]) {
      const path = join(store, skill, directory, "policy-library.json");
      assert.deepEqual(JSON.parse(readFileSync(path, "utf8")), expected, path);
    }
  }
});

test("claim matching and classification handle flat and percentage entitlements", (t) => {
  const directory = temporaryDirectory(t);
  const flat = { type: "slotting", period: "2026-06", backup_doc: "signed-backup.pdf" };
  const percentage = { ...flat, type: "promo_allowance", actual_volume_value: 100_000 };
  const input = writeJson(directory, "deduction.json", {
    contract_version: "rtl.trade-deduction-recovery.v1",
    customer: "Summit Grocers",
    claims: [
      { ...flat, claim_id: "FLAT-BELOW", claimed_amount: 4_000 },
      { ...flat, claim_id: "FLAT-EXACT", claimed_amount: 5_000 },
      { ...flat, claim_id: "FLAT-TOLERANCE", claimed_amount: 5_000.01 },
      { ...flat, claim_id: "FLAT-OVER", claimed_amount: 6_000 },
      { ...percentage, claim_id: "RATE-EXACT", claimed_amount: 8_000 },
      { ...percentage, claim_id: "RATE-OVER", claimed_amount: 10_000 },
      { ...flat, claim_id: "NO-BACKUP", claimed_amount: 6_000, backup_doc: "" },
      { ...flat, claim_id: "NO-TERM", claimed_amount: 4_000, period: "2026-07" },
    ],
  });
  const matched = join(directory, "matched.json");
  runPython(join(trade, "claim-match", "scripts", "claim_match.py"), [
    "--deduction", input, "--terms", join(trade, "claim-match", "trade-terms.json"), "--out", matched,
  ]);
  const output = join(directory, "governed.json");
  const execution = runPython(classifier, ["--matched", matched, "--scoping", scoping, "--out", output]);
  const result: {
    validity: {
      claim_id: string; verdict: string; disputable_amount: number;
      calculation: string; source: string; citation: string;
    }[];
    escalations: string[];
    promo_lift: { skipped: boolean };
    provenance: { engines: string[] };
  } = JSON.parse(readFileSync(output, "utf8"));
  assert.deepEqual(result.validity.map(({ claim_id, verdict, disputable_amount }) =>
    [claim_id, verdict, disputable_amount]), [
    ["FLAT-BELOW", "valid", 0], ["FLAT-EXACT", "valid", 0], ["FLAT-TOLERANCE", "valid", 0],
    ["FLAT-OVER", "partial", 1_000], ["RATE-EXACT", "valid", 0], ["RATE-OVER", "partial", 2_000],
    ["NO-BACKUP", "unsupported", 6_000], ["NO-TERM", "unsupported", 4_000],
  ]);
  for (const verdict of result.validity) {
    assert.equal(verdict.source, "engine:deduction_classify");
    assert.match(verdict.citation, /deduction-rules\.md #2\.[123]/);
    if (verdict.claim_id.startsWith("FLAT-")) {
      assert.match(verdict.calculation, /flat amount 5000/);
      assert.doesNotMatch(verdict.calculation, /%/);
    } else if (verdict.claim_id.startsWith("RATE-")) {
      assert.match(verdict.calculation, /8\.0% x 100000/);
    }
  }
  assert.ok(result.escalations.some((message) => /FLAT-OVER: claimed amount exceeds signed flat amount 5000.*disputable 1000/.test(message)));
  assert.ok(result.escalations.some((message) => /RATE-OVER: claimed rate exceeds signed 8\.0%.*disputable 2000/.test(message)));
  assert.ok(result.escalations.filter((message) => message.includes("disputable")).every((message) => message.includes("Write-off is a human decision")));
  assert.equal(result.promo_lift.skipped, true);
  assert.ok(result.provenance.engines.includes("claim_match/1.0"));
  assert.ok(result.provenance.engines.includes("deduction_classify/1.0"));
  assert.match(execution.stdout, /disputable total 13000/);
});

test("a signed term with no entitlement field fails explicitly instead of assuming zero", (t) => {
  const directory = temporaryDirectory(t);
  const matched = writeJson(directory, "matched.json", {
    contract_version: "rtl.trade-deduction-recovery.v1",
    claims: [{ claim_id: "MALFORMED", claimed_amount: 6_000 }],
    matches: [{
      claim_id: "MALFORMED", term_id: "NO-AMOUNT", backup_present: true,
      term: { term_id: "NO-AMOUNT", citation: "signed term NO-AMOUNT" },
      citation: "signed term NO-AMOUNT",
    }],
  });
  const output = join(directory, "governed.json");
  const result = runPython(classifier, ["--matched", matched, "--scoping", scoping, "--out", output], 1);
  assert.match(result.stderr, /NO-AMOUNT.*rate_pct or flat_amount/);
  assert.equal(existsSync(output), false);
});

test("deduction rule mirrors document both entitlement models consistently", () => {
  const canonical = readFileSync(join(trade, "validity-classify", "deduction-rules.md"), "utf8");
  assert.match(canonical, /rate x actual volume.*flat amount/);
  for (const skill of ["claim-ingest", "term-retrieve", "claim-match", "validity-classify", "dispute-packet"]) {
    assert.equal(readFileSync(join(trade, skill, "references", "deduction-rules.md"), "utf8"), canonical);
  }
});
