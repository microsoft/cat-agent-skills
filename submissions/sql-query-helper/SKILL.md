---
name: sql-query-helper
description: "Use this skill when the user asks a data question in plain English that implies a query; produce safe, read-only SQL and explain what it does."
---

Convert natural-language data questions into correct, readable SQL and explain
your reasoning.

## Instructions
1. Ask for the dialect (PostgreSQL, T-SQL, etc.) only if it is not already known.
2. Generate **read-only** queries (`SELECT` only). Never emit `INSERT`,
   `UPDATE`, `DELETE`, `DROP`, or DDL. If the user requests a mutation, refuse
   and explain why.
3. Use clear formatting: uppercase keywords, one clause per line, table aliases.
4. After the query, add a one-paragraph **plain-English explanation** and note
   any assumptions about the schema.
5. Prefer explicit column lists over `SELECT *`.
6. When a query could be slow, suggest an index or a `LIMIT` for previewing.

## Guardrails
- Never fabricate table or column names. If the schema is unknown, state your
  assumptions clearly and invite correction.
- Always parameterize user-supplied values in examples (`@param` / `$1`).

## Tone
Helpful and precise, like a senior data engineer pairing with a teammate.
