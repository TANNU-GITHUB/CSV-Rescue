import { test, expect } from "@playwright/test";

test("dashboard renders clay shell", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.getByText(/Good (Morning|Afternoon|Evening)/)).toBeVisible();
});
