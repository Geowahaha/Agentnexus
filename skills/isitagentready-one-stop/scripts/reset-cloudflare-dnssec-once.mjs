#!/usr/bin/env node
import { readFile } from "node:fs/promises";

const args = parseArgs(process.argv.slice(2));
const zoneId = args["zone-id"];
const token = args.token || process.env.CLOUDFLARE_API_TOKEN || process.env.CF_API_TOKEN || (args["env-file"] ? await tokenFromEnvFile(args["env-file"]) : "");
const waitDisabledMs = Number(args["wait-disabled-ms"] || 15000);
const disabledHoldMs = Number(args["disabled-hold-ms"] || 60000);

if (!zoneId) fail("Missing --zone-id <cloudflare-zone-id>");
if (!token) fail("Missing Cloudflare token. Set CLOUDFLARE_API_TOKEN/CF_API_TOKEN or pass --env-file <file>.");

const headers = {
  authorization: `Bearer ${token}`,
  "content-type": "application/json",
};

const events = [];

try {
  events.push({ step: "before", dnssec: summarize(await readDnssec()) });
  events.push({ step: "disable-request", dnssec: summarize(await patchDnssec("disabled")) });

  let disabled = null;
  for (let i = 0; i < 12; i += 1) {
    await sleep(waitDisabledMs);
    disabled = await readDnssec();
    events.push({ step: `wait-disabled-${i + 1}`, dnssec: summarize(disabled) });
    if (disabled.result?.status === "disabled" && !disabled.result?.ds) break;
  }

  if (disabled?.result?.status !== "disabled") {
    throw new Error(`DNSSEC did not reach disabled state; last status=${disabled?.result?.status || "unknown"}`);
  }

  if (disabledHoldMs > 0) {
    events.push({ step: "hold-disabled", ms: disabledHoldMs });
    await sleep(disabledHoldMs);
  }
} finally {
  const enable = await patchDnssec("active").catch((error) => ({ success: false, errors: [{ message: String(error) }] }));
  events.push({ step: "enable-request", dnssec: summarize(enable) });
  await sleep(10000);
  const after = await readDnssec().catch((error) => ({ success: false, errors: [{ message: String(error) }] }));
  events.push({ step: "after", dnssec: summarize(after) });

  if (after.result?.status === "disabled") {
    const retry = await patchDnssec("active").catch((error) => ({ success: false, errors: [{ message: String(error) }] }));
    events.push({ step: "enable-retry", dnssec: summarize(retry) });
  }
}

console.log(JSON.stringify({
  zoneId,
  rule: "reset-once-complete-leave-dnssec-enabled",
  next: "Stop resetting. Poll parent DS and AD validation while Cloudflare/registrar propagates.",
  events,
}, null, 2));

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (!arg.startsWith("--")) continue;
    const key = arg.slice(2);
    out[key] = argv[i + 1];
    i += 1;
  }
  return out;
}

async function tokenFromEnvFile(file) {
  const text = await readFile(file, "utf8");
  const match = text.match(/^\s*(?:CLOUDFLARE_API_TOKEN|CF_API_TOKEN)\s*=\s*(.+)\s*$/m);
  return match?.[1]?.trim().replace(/^['"]|['"]$/g, "") || "";
}

async function readDnssec() {
  return cf(`/zones/${zoneId}/dnssec`);
}

async function patchDnssec(status) {
  return cf(`/zones/${zoneId}/dnssec`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

async function cf(path, init = {}) {
  const response = await fetch(`https://api.cloudflare.com/client/v4${path}`, {
    ...init,
    headers,
  });
  const json = await response.json();
  if (!json.success && response.status >= 400) {
    throw new Error(`Cloudflare API ${response.status}: ${JSON.stringify(json.errors || json)}`);
  }
  return json;
}

function summarize(payload) {
  return {
    success: payload?.success,
    status: payload?.result?.status,
    ds: payload?.result?.ds || null,
    modified_on: payload?.result?.modified_on,
    errors: payload?.errors || [],
  };
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function fail(message) {
  console.error(message);
  process.exit(1);
}
