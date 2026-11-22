// Render the MANGFALL cards with the anonymised sample home and save screenshots.
// Usage (needs Playwright): node tools/shots.mjs <out-dir> [card ...]
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { createRequire } from "module";

const require = createRequire(process.env.PW_FROM || import.meta.url);
const { chromium } = require("playwright");
const HERE = path.dirname(fileURLToPath(import.meta.url));
const SRC = fs.readFileSync(path.join(HERE, "../mangfall-cards/app/mangfall-cards.js"), "utf8");
const SNAP = fs.readFileSync(process.env.SNAP || path.join(HERE, "demo-home.json"), "utf8");
const out = process.argv[2] || "shots";
const only = process.argv.slice(3);
fs.mkdirSync(out, { recursive: true });

const page = `<!doctype html><html lang="de"><head><meta charset="utf-8">
<style>body{margin:0;background:#f4f2ee;font-family:-apple-system,"Segoe UI",Roboto,sans-serif}
#wrap{width:420px;padding:24px}
:root{--card-background-color:#fff;--primary-text-color:#1c1c1c;--secondary-text-color:#6b6b6b;--ha-card-border-radius:16px;--ha-card-box-shadow:0 1px 3px rgba(0,0,0,.08)}
ha-card{display:block;background:#fff;border-radius:16px;box-shadow:0 1px 3px rgba(0,0,0,.08);overflow:hidden}</style>
</head><body><div id="wrap"></div>
<script>
customElements.define("ha-card", class extends HTMLElement {});
customElements.define("ha-icon", class extends HTMLElement {});
const snap = ${SNAP};
window.hass = { ...snap, language: "de", locale: { language: "de", number_format: "language", time_format: "24" },
  themes: { darkMode: false }, user: { name: "Demo", is_admin: true }, config: { unit_system: { temperature: "°C" }, time_zone: "Europe/Berlin" },
  callWS: async () => ({}), callApi: async () => [], callService: async () => ({}), localize: (k) => k,
  formatEntityState: (s) => s.state, connection: { subscribeMessage: async () => () => {} } };
</script>
<script>${SRC.replace(/<\/script>/g, "<\\/script>")}</script>
</body></html>`;

const browser = await chromium.launch();
const ctx = await browser.newContext({ deviceScaleFactor: 2, viewport: { width: 470, height: 1200 }, locale: "de-DE", timezoneId: "Europe/Berlin" });
const p = await ctx.newPage();
const errors = [];
p.on("pageerror", (e) => errors.push(String(e)));
await p.setContent(page, { waitUntil: "load" });
const cards = await p.evaluate(() => (window.customCards || []).map((c) => c.type));
const done = [];
for (const type of cards) {
  if (only.length && !only.includes(type)) continue;
  const box = await p.evaluate(async (type) => {
    const wrap = document.getElementById("wrap");
    wrap.innerHTML = "";
    const C = customElements.get(type);
    const el = document.createElement(type);
    const cfg = C.getStubConfig ? C.getStubConfig(window.hass) : {};
    el.setConfig(cfg || {});
    el.hass = window.hass;
    wrap.appendChild(el);
    await new Promise((r) => setTimeout(r, 900));
    el.hass = { ...window.hass };
    await new Promise((r) => setTimeout(r, 400));
    const r = el.getBoundingClientRect();
    return { h: r.height, err: !!el.shadowRoot?.querySelector(".error,hui-error-card") };
  }, type);
  if (box.h < 40) continue;
  const el = await p.$("#wrap > *");
  await el.screenshot({ path: path.join(out, `${type}.png`) });
  done.push(`${type} ${Math.round(box.h)}px${box.err ? " (error box!)" : ""}`);
}
await browser.close();
console.log(done.join("\n"));
if (errors.length) console.log("page errors:\n" + [...new Set(errors)].slice(0, 8).join("\n"));
