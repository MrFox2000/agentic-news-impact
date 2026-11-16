/**
 * Captures README screenshots from a running app.
 *
 *   node scripts/screenshot.mjs
 *
 * Expects the backend on :8001 and `npm run start` on :3001.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const here = path.dirname(fileURLToPath(import.meta.url));
const project = path.resolve(here, "..");
const out = path.resolve(project, "..", "docs", "screenshots");

fs.mkdirSync(out, { recursive: true });

// Reuse the locally installed Chrome instead of downloading a browser.
const browser = await chromium.launch({ channel: process.env.PW_CHANNEL ?? "chrome" });
const page = await browser.newPage({
  viewport: { width: 1440, height: 900 },
  deviceScaleFactor: 2,
  colorScheme: "dark",
});

const shot = async (name) => {
  await page.screenshot({ path: path.join(out, name) });
  console.log(`saved ${name}`);
};

await page.goto("http://127.0.0.1:3001", { waitUntil: "networkidle" });
await page.waitForTimeout(500);
await shot("01-start.png");

await page.fill('input[placeholder="e.g. supply chain, regulation, earnings"]', "Apple earnings");
await page.getByRole("button", { name: "Analyse" }).click();

await page.waitForTimeout(1200);
await shot("02-running.png");

// Wait until the report has rendered.
let previous = "";
for (let attempt = 0; attempt < 90; attempt += 1) {
  await page.waitForTimeout(500);
  const current = await page.evaluate(() => document.body.innerText);
  if (current === previous && current.includes("Window")) break;
  previous = current;
}
await page.waitForTimeout(500);
await shot("03-report.png");

await browser.close();
console.log("done");
