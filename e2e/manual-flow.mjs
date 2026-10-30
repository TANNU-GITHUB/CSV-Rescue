import { chromium } from "@playwright/test";

const browser = await chromium.launch({ channel: "chrome", headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.on("pageerror", (e) => console.log("PAGEERROR", e.message));
page.on("console", (m) => {
  if (m.type() === "error") console.log("CONSOLE", m.text());
});
await page.goto("http://127.0.0.1:5173/", { waitUntil: "networkidle" });
if (await page.getByText("What should I call you?").isVisible().catch(() => false)) {
  await page.locator("input").last().fill("Mia");
  await page.getByRole("button", { name: /let's go/i }).click();
}
await page.waitForTimeout(800);
await page.screenshot({ path: "/tmp/dash.png", fullPage: true });
console.log("dash title", await page.locator("h1").first().innerText());
await page.getByRole("button", { name: /load sample/i }).click();
await page.getByRole("button", { name: /students/i }).click();
await page.waitForTimeout(2000);
console.log("url after sample", page.url());
await page.screenshot({ path: "/tmp/profile.png", fullPage: true });
await page.getByRole("link", { name: /issues/i }).first().click();
await page.waitForTimeout(1000);
console.log("issues url", page.url());
await page.screenshot({ path: "/tmp/issues.png", fullPage: true });
await page.getByRole("link", { name: /cleaning studio/i }).first().click();
await page.waitForTimeout(1000);
await page.getByRole("button", { name: /apply all safe/i }).click().catch(() => {});
await page.waitForTimeout(1500);
await page.screenshot({ path: "/tmp/studio.png", fullPage: true });
console.log("studio url", page.url());
await page.getByRole("link", { name: /reports/i }).first().click();
await page.waitForTimeout(500);
await page.getByRole("button", { name: /run verification/i }).click();
await page.waitForTimeout(1500);
await page.screenshot({ path: "/tmp/reports.png", fullPage: true });
await page.setViewportSize({ width: 390, height: 844 });
await page.goto("http://127.0.0.1:5173/", { waitUntil: "networkidle" });
await page.waitForTimeout(600);
await page.screenshot({ path: "/tmp/mobile.png", fullPage: true });
await browser.close();
console.log("done");
