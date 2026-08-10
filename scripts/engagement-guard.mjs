#!/usr/bin/env node
// Lailara engagement deploy guard (Node) — for wiring into an npm `deploy` script.
// Exit 2 if an ACTIVE (non-demo) client engagement.yml is present. No-op otherwise,
// so demo builds and CI (clean checkout, no engagement.yml) are unaffected.
import { existsSync, readFileSync } from "node:fs";

let blocked = null;
for (const f of ["engagement.yml", "engagement.yaml"]) {
  if (existsSync(f)) {
    const txt = readFileSync(f, "utf8");
    if (/^\s*demo:\s*true\s*$/m.test(txt)) continue; // demo config -> safe
    blocked = f;
    break;
  }
}
if (blocked) {
  console.error(
    `ENGAGEMENT GUARD: active client engagement config present (${blocked}). ` +
      "Client mode is runtime-only and must never deploy. Deactivate it " +
      "(set 'demo: true', or use engagement.demo.yml) before deploying."
  );
  process.exit(2);
}
